"""Re-estimate the ensemble at EVERY horizon with weights from strictly prior
folds only, so the whole scorecard is leak-free rather than just h=3.

Writes outputs/scorecards/<mat>_horizon_scorecard_leakfree.csv
"""
from pathlib import Path

import numpy as np
import pandas as pd
from scipy import stats

BASE = Path(__file__).resolve().parents[2]
SC = BASE / "outputs/scorecards"
MODELS = ["naive", "seasonal_naive", "ets", "elasticnet",
          "bayesian_ridge", "lightgbm", "lstm", "nbeats"]
SC.mkdir(parents=True, exist_ok=True)
MIN_FOLDS = 12


def dm_hac(e1, e2, h):
    """Diebold-Mariano, HAC variance at lag h-1, HLN small-sample correction.

    ONE-SIDED, matching the convention already used in metrics.py: the
    hypothesis is directional ("the model beats naive"), not two-tailed.
    The t-distribution and HLN factor are added because overlapping h-step
    forecasts are serially correlated and the sample is short - both make
    this test STRICTER than the Round 1 version, which used a normal
    distribution and no small-sample correction.

    Returns (dm_stat, p_one_sided, p_two_sided).
    """
    d = np.abs(e1) - np.abs(e2)          # negative when the model wins
    d = d[~np.isnan(d)]
    n = len(d)
    if n < 8:
        return np.nan, np.nan, np.nan
    db = d.mean()
    var = ((d - db) ** 2).mean()
    for k in range(1, h):
        var += 2 * ((d[k:] - db) * (d[:-k] - db)).mean()
    dm = db / np.sqrt(max(var, 1e-12) / n)
    dmc = dm * np.sqrt((n + 1 - 2 * h + h * (h - 1) / n) / n)
    p_two = 2 * (1 - stats.t.cdf(abs(dmc), df=n - 1))
    p_one = stats.t.cdf(dmc, df=n - 1) if db < 0 else 1 - stats.t.cdf(dmc, df=n - 1)
    return dmc, p_one, p_two


for mat in ("aluminium", "pvc"):
    wf = pd.read_csv(SC / f"{mat}_walk_forward_predictions.csv",
                     parse_dates=["origin_date", "target_date"])
    rows, weight_log = [], []

    for h in range(1, 7):
        g = wf[wf.horizon == h].sort_values("origin_date").reset_index(drop=True)
        origins = list(g.origin_date)
        recs = []

        for i, t in enumerate(origins):
            hist = g[g.origin_date < t]
            if len(hist) < MIN_FOLDS:
                continue
            mape = {}
            for m in MODELS:
                e = (hist[f"pred_price_{m}"] - hist.actual_price).abs() / hist.actual_price
                mape[m] = e.mean()
            nm = mape["naive"]
            elig = {m: v for m, v in mape.items() if v < nm and m != "naive"}

            w = {m: 0.0 for m in MODELS}
            if not elig:
                w["naive"] = 1.0                       # nobody cleared the gate
            else:
                raw = {m: (1.0 / v) ** 2 for m, v in elig.items()}
                tot = sum(raw.values())
                w.update({m: v / tot for m, v in raw.items()})

            cur = g.iloc[i]
            pred = sum(w[m] * cur[f"pred_price_{m}"] for m in MODELS)
            # bands: scale the stored conformal band around the new point
            shift = pred - cur.pred_price_ensemble
            recs.append({
                "origin": t, "actual": cur.actual_price, "pred": pred,
                "p0": cur.current_price,
                "p10": cur.p10_price + shift, "p90": cur.p90_price + shift,
                "naive": cur.pred_price_naive, **{f"w_{m}": w[m] for m in MODELS}})

        r = pd.DataFrame(recs)
        if r.empty:
            continue

        ape_e = (r.pred - r.actual).abs() / r.actual
        ape_n = (r.naive - r.actual).abs() / r.actual
        dir_e = (np.sign(r.pred - r.p0) == np.sign(r.actual - r.p0)).mean()
        dmc, p1, p2 = dm_hac(((r.pred - r.actual) / r.actual).values,
                        ((r.naive - r.actual) / r.actual).values, h)

        rows.append({
            "horizon": f"h={h}", "n_origins": len(r),
            "ensemble_mape": round(100 * ape_e.mean(), 2),
            "naive_mape": round(100 * ape_n.mean(), 2),
            "skill_vs_naive_pct": round(100 * (1 - ape_e.mean() / ape_n.mean()), 2),
            "directional_accuracy_pct": round(100 * dir_e, 2),
            "band_coverage_p10_p90_pct": round(
                100 * ((r.actual >= r.p10) & (r.actual <= r.p90)).mean(), 2),
            "bias_pct": round(100 * ((r.pred - r.actual) / r.actual).mean(), 2),
            "dm_stat": round(dmc, 3),
            "dm_p_value": round(p1, 4),          # one-sided, headline
            "dm_p_two_sided": round(p2, 4),      # reported in the footnote
        })
        weight_log.append({"horizon": f"h={h}",
                           **{m: round(r[f"w_{m}"].mean() * 100, 1) for m in MODELS}})

    out = pd.DataFrame(rows)
    out.to_csv(SC / f"{mat}_horizon_scorecard_leakfree.csv", index=False)
    pd.DataFrame(weight_log).to_csv(SC / f"{mat}_ensemble_weights_leakfree.csv", index=False)
    print(f"\n=== {mat.upper()} (leak-free, weights from prior folds only) ===")
    print(out.to_string(index=False))
    print("\nmean ensemble weight %:")
    print(pd.DataFrame(weight_log).to_string(index=False))
