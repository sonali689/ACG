"""Re-run the buying replay using the LEAK-FREE ensemble predictions.

The earlier replay used ensemble forecasts whose weights had seen the fold
being scored. This version rebuilds the h=3 forecast at every origin with
weights from strictly prior folds, then applies the published rule.

Rule (unchanged from Round 1):
    S(3) = (P_hat(3) - P0)/P0 - c*3,  c = 1.0%/month
    BUY NOW    S > +2% and P(up)   >= 60%  -> cover 3.0 months
    DEFER      S < -2% and P(down) >= 60%  -> cover 1.0 month
    BUY NORMAL otherwise                   -> cover 1.5 months
Baseline: buy one month's requirement every month, 1.5 months cover held.
"""
import json
from pathlib import Path

import numpy as np
import pandas as pd

BASE = Path(__file__).resolve().parents[2]
SC = BASE / "outputs/scorecards"
MODELS = ["naive", "seasonal_naive", "ets", "elasticnet",
          "bayesian_ridge", "lightgbm", "lstm", "nbeats"]
MIN_FOLDS, C, Q, LEAD = 12, 0.01, 1000.0, 1

summary = {}
for mat in ("aluminium", "pvc"):
    wf = pd.read_csv(SC / f"{mat}_walk_forward_predictions.csv",
                     parse_dates=["origin_date"])
    g = wf[wf.horizon == 3].sort_values("origin_date").reset_index(drop=True)

    recs = []
    for i, t in enumerate(g.origin_date):
        hist = g[g.origin_date < t]
        if len(hist) < MIN_FOLDS:
            continue
        mape = {m: ((hist[f"pred_price_{m}"] - hist.actual_price).abs()
                    / hist.actual_price).mean() for m in MODELS}
        nm = mape["naive"]
        elig = {m: v for m, v in mape.items() if v < nm and m != "naive"}
        if not elig:
            w = {m: (1.0 if m == "naive" else 0.0) for m in MODELS}
        else:
            raw = {m: (1 / v) ** 2 for m, v in elig.items()}
            tot = sum(raw.values())
            w = {m: raw.get(m, 0.0) / tot for m in MODELS}

        cur = g.iloc[i]
        pred = sum(w[m] * cur[f"pred_price_{m}"] for m in MODELS)
        shift = pred - cur.pred_price_ensemble
        p10, p90 = cur.p10_price + shift, cur.p90_price + shift
        p0 = cur.current_price

        p_up = float(np.clip(1 - (0.10 + 0.80 * (p0 - p10) / max(p90 - p10, 1e-9)),
                             0.02, 0.98))
        S = (pred - p0) / p0 - C * 3
        if S > 0.02 and p_up >= 0.60:
            sig, cover = "BUY NOW", 3.0
        elif S < -0.02 and (1 - p_up) >= 0.60:
            sig, cover = "DEFER", 1.0
        else:
            sig, cover = "BUY NORMAL", 1.5
        recs.append({"date": t, "price": p0, "pred": pred, "p_up": p_up,
                     "S_pct": 100 * S, "signal": sig, "cover": cover})

    r = pd.DataFrame(recs)

    # ---- inventory simulation, both policies -----------------------------
    def simulate(covers):
        inv, spend, qty, carry, days = 1.5 * Q, 0.0, 0.0, 0.0, []
        for cov, px in zip(covers, r.price):
            target = cov * Q + LEAD * Q
            order = max(0.0, target - inv)
            spend += order * px
            qty += order
            inv = max(inv + order - Q, 0.0)
            carry += inv * px * C
            days.append(inv / Q * 30.44)
        return dict(wavg=spend / qty if qty else np.nan, spend=spend,
                    carry=carry, total=spend + carry,
                    inv_days=float(np.mean(days)), peak=float(np.max(days)))

    sb = simulate(r.cover.values)
    bl = simulate([1.5] * len(r))

    gross = 100 * (1 - sb["wavg"] / bl["wavg"])
    net = 100 * (1 - sb["total"] / bl["total"])
    dd = sb["inv_days"] - bl["inv_days"]

    # cumulative saving curve
    cum_sb = (r.cover.values * Q).cumsum() * 0  # placeholder, recompute properly
    sp_sb, sp_bl, curve, inv_s, inv_b = 0.0, 0.0, [], 1.5 * Q, 1.5 * Q
    q_s, q_b = 0.0, 0.0
    for cov, px in zip(r.cover.values, r.price):
        o_s = max(0.0, cov * Q + LEAD * Q - inv_s); inv_s = max(inv_s + o_s - Q, 0)
        o_b = max(0.0, 1.5 * Q + LEAD * Q - inv_b); inv_b = max(inv_b + o_b - Q, 0)
        sp_s = sp_sb = sp_sb + o_s * px; sp_bl = sp_bl + o_b * px
        q_s += o_s; q_b += o_b
        a = sp_sb / q_s if q_s else np.nan
        b = sp_bl / q_b if q_b else np.nan
        curve.append(round(100 * (1 - a / b), 3) if b else 0.0)

    summary[mat] = {
        "months": len(r),
        "base_price": round(bl["wavg"], 2), "sb_price": round(sb["wavg"], 2),
        "gross_pct": round(gross, 2), "net_pct": round(net, 2),
        "inv_base": round(bl["inv_days"], 1), "inv_sb": round(sb["inv_days"], 1),
        "inv_delta": round(dd, 1),
        "wc_shift": round(dd * 100 / 365, 2),
        "signals": r.signal.value_counts().to_dict(),
        "curve": {"labels": [d.strftime("%Y-%m") for d in r.date],
                  "cum": curve, "signal": list(r.signal), 
                  "price": [round(float(v), 1) for v in r.price]},
    }
    r.to_csv(BASE / f"outputs/{mat}_buying_replay_leakfree.csv", index=False)

    print(f"\n=== {mat.upper()} replay, leak-free ===")
    print(f"  months          {len(r)}")
    print(f"  avg price       ${sb['wavg']:,.2f}  vs baseline ${bl['wavg']:,.2f}")
    print(f"  gross saving    {gross:+.2f}%")
    print(f"  net after carry {net:+.2f}%")
    print(f"  inventory days  {sb['inv_days']:.1f} vs {bl['inv_days']:.1f}  ({dd:+.1f})")
    print(f"  signals         {r.signal.value_counts().to_dict()}")

(BASE / "outputs/replay_leakfree.json").write_text(json.dumps(summary, indent=1))
print(f"\nwrote outputs/replay_leakfree.json")
