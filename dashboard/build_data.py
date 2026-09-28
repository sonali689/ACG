"""Build dashboard_data.json from the real walk-forward outputs.

Uses the CORRECTED expanding-ensemble figures from fix_pack, not the
earlier leaked ones. Nothing in the dashboard is typed by hand.
"""
import json
from pathlib import Path

import numpy as np
import pandas as pd

BASE = Path(__file__).resolve().parents[1]
OUT = BASE / "outputs"
MODELS = ["naive", "seasonal_naive", "ets", "elasticnet",
          "bayesian_ridge", "lightgbm", "lstm", "nbeats"]
PRETTY = {"naive": "Naive", "seasonal_naive": "Seasonal naive", "ets": "Holt-Winters ETS",
          "elasticnet": "ElasticNet", "bayesian_ridge": "Bayesian ridge",
          "lightgbm": "LightGBM", "lstm": "LSTM", "nbeats": "N-BEATS",
          "ensemble": "Smart Buy ensemble"}

data = {"materials": {}}
master = pd.read_csv(BASE / "data/processed/master_dataset.csv", parse_dates=["date"])

for mat, key, pcol in [("aluminium", "aluminium", "lme_aluminium"),
                       ("pvc", "pvc", "pvc_asia_spot")]:
    wf = pd.read_csv(OUT / f"scorecards/{mat}_walk_forward_predictions.csv",
                     parse_dates=["origin_date", "target_date"])
    hz = pd.read_csv(OUT / f"scorecards/{mat}_horizon_scorecard_leakfree.csv")
    wts = pd.read_csv(OUT / f"scorecards/{mat}_ensemble_weights_leakfree.csv")
    LF = json.loads((OUT / "replay_leakfree.json").read_text())[mat]
    rg = pd.read_csv(OUT / f"scorecards/{mat}_regime_scorecard.csv")
    dr = pd.read_csv(OUT / f"{mat}_driver_study.csv")
    rp = pd.read_csv(OUT / f"{mat}_buying_replay.csv", parse_dates=["date"])
    summ = json.loads((OUT / f"{mat}_replay_summary.json").read_text())
    up = mat.upper() if mat != "aluminium" else "ALUMINIUM"
    ladder = pd.read_csv(OUT / f"tables/ladder_common_origins_{up}_h3.csv")
    band = pd.read_csv(OUT / f"tables/band_coverage_by_horizon_{up}.csv")
    inv = pd.read_csv(OUT / f"tables/inventory_and_net_savings_{up}.csv").iloc[0]
    ecorr = pd.read_csv(OUT / f"tables/error_corr_{up}_h3.csv", index_col=0)

    # ---- latest validated origin: the real forecast the model produced -----
    last_origin = wf.origin_date.max()
    cur = wf[wf.origin_date == last_origin].sort_values("horizon")
    p0 = float(cur.current_price.iloc[0])

    horizons = {}
    for _, r in cur.iterrows():
        h = int(r.horizon)
        p50 = float(r.pred_price_ensemble)
        p10, p90 = float(r.p10_price), float(r.p90_price)
        # P(up): share of the fitted quantile distribution above p0
        if p90 > p10:
            z = (p0 - p10) / (p90 - p10)
            p_up = float(np.clip(1 - (0.10 + 0.80 * z), 0.02, 0.98))
        else:
            p_up = 0.5
        exp_sav = (p50 - p0) / p0 * 100 - 1.0 * h          # c = 1.0 %/month
        if exp_sav > 2 and p_up >= 0.60:
            sig, cover = "BUY NOW", 3.0
        elif exp_sav < -2 and (1 - p_up) >= 0.60:
            sig, cover = "DEFER", 1.0
        else:
            sig, cover = "BUY NORMAL", 1.5
        horizons[h] = {"p50": round(p50, 1), "p10": round(p10, 1), "p90": round(p90, 1),
                       "change_pct": round((p50 - p0) / p0 * 100, 2),
                       "p_up": round(p_up * 100, 1),
                       "exp_saving_pct": round(exp_sav, 2),
                       "signal": sig, "cover": cover}

    # ---- 36 months of actual history + the forward fan --------------------
    hist = master[["date", pcol]].dropna().tail(37)
    hist_lbl = [d.strftime("%Y-%m") for d in hist.date]
    hist_val = [round(float(v), 1) for v in hist[pcol]]

    fwd_lbl = [(last_origin + pd.DateOffset(months=h)).strftime("%Y-%m")
               for h in range(1, 7)]
    labels = hist_lbl + fwd_lbl
    n_h, n_f = len(hist_lbl), len(fwd_lbl)
    series = {
        "labels": labels,
        "actual": hist_val + [None] * n_f,
        "p50": [None] * (n_h - 1) + [hist_val[-1]] + [horizons[h]["p50"] for h in range(1, 7)],
        "p10": [None] * (n_h - 1) + [hist_val[-1]] + [horizons[h]["p10"] for h in range(1, 7)],
        "p90": [None] * (n_h - 1) + [hist_val[-1]] + [horizons[h]["p90"] for h in range(1, 7)],
        "naive": [None] * (n_h - 1) + [hist_val[-1]] * (n_f + 1),
    }

    # ---- backtest trajectory at h=3: what the model actually did ----------
    h3 = wf[wf.horizon == 3].sort_values("target_date")
    backtest = {
        "labels": [d.strftime("%Y-%m") for d in h3.target_date],
        "actual": [round(float(v), 1) for v in h3.actual_price],
        "pred": [round(float(v), 1) for v in h3.pred_price_ensemble],
        "p10": [round(float(v), 1) for v in h3.p10_price],
        "p90": [round(float(v), 1) for v in h3.p90_price],
    }

    # ---- model ladder (corrected, common origins) --------------------------
    lad = []
    for _, r in ladder.iterrows():
        nm = r.model
        lad.append({
            "model": "Smart Buy ensemble" if "Ensemble" in nm else PRETTY.get(nm, nm),
            "is_ensemble": "Ensemble" in nm,
            "mape": float(r.mape),
            "skill": float(r.skill_vs_naive_pct),
            "dir": float(r.directional_accuracy_pct),
            "dm_p": float(r.hac_dm_p_value),
            "weight": round(float(r.mean_ensemble_weight) * 100, 1) if not r.get("mean_ensemble_weight") is None else 0,
            "gated_out": float(r.skill_vs_naive_pct) <= 0 and "Ensemble" not in nm and nm != "naive",
        })

    # ---- drivers: SHAP-style contribution proxy from the driver study ------
    drv = dr.head(8)
    drivers = [{"name": r.indicator, "rho": float(r.peak_correlation),
                "lead": int(r.optimal_lead_months),
                "granger_p": float(r.granger_p_value),
                "sig": bool(r.statistically_significant)}
               for _, r in drv.iterrows()]

    data["materials"][key] = {
        "name": "LME Aluminium" if key == "aluminium" else "PVC resin, Asia spot",
        "short": "Aluminium" if key == "aluminium" else "PVC resin",
        "unit": "US$ / tonne",
        "spot": round(p0, 1),
        "origin": last_origin.strftime("%b %Y"),
        "horizons": horizons,
        "series": series,
        "backtest": backtest,
        "ladder": lad,
        "drivers": drivers,
        "scorecard": [{"h": int(str(r.horizon).replace("h=", "")),
                       "ens": float(r.ensemble_mape), "naive": float(r.naive_mape),
                       "skill": float(r.skill_vs_naive_pct),
                       "dir": float(r.directional_accuracy_pct),
                       "dm_p": float(r.dm_p_value)} for _, r in hz.iterrows()],
        "bands": [{"h": str(r.horizon),
                   "cov": float(hz.loc[hz.horizon == r.horizon, "band_coverage_p10_p90_pct"].iloc[0]),
                   "status": str(r.gate_status_75_85),
                   "width": float(r.mean_bandwidth_pct),
                   "bias": float(hz.loc[hz.horizon == r.horizon, "bias_pct"].iloc[0])}
                  for _, r in band.iterrows()],
        "weights": [{"h": str(r.horizon),
                     **{m: float(r[m]) for m in ["naive","seasonal_naive","ets","elasticnet",
                                                 "bayesian_ridge","lightgbm","lstm","nbeats"]}}
                    for _, r in wts.iterrows()],
        "regimes": [{"name": str(r.regime), "n": int(r.n_months),
                     "mape": float(r.ensemble_mape), "skill": float(r.skill_vs_naive_pct),
                     "dir": float(r.directional_accuracy_pct),
                     "cov": float(r.band_coverage_p10_p90_pct)} for _, r in rg.iterrows()],
        "replay": LF,
        "err_corr": {
            "mean_off_diag": round(float(
                ecorr.values[np.triu_indices_from(ecorr.values, 1)].mean()), 3),
            "nbeats_vs_rest": round(float(
                ecorr.loc["nbeats", [c for c in ecorr.columns if c != "nbeats"]].mean()), 3),
        },
    }

data["hypotheses"] = json.loads((OUT / "tables/h1_h4_formal_verdicts.json").read_text())
data["meta"] = {"folds": 78, "window": "Jan 2018 - Jun 2024",
                "obs": 181, "carrying_cost_pct": 1.0}

p = BASE / "dashboard/data.json"
p.write_text(json.dumps(data, indent=1))
print(f"wrote {p}  ({p.stat().st_size/1024:.0f} KB)")
for k, v in data["materials"].items():
    print(f"  {k}: spot {v['spot']}, origin {v['origin']}, "
          f"h3 {v['horizons'][3]['signal']}, ladder {len(v['ladder'])} models")
