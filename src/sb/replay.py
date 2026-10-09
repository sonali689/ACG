"""
Buying replay v2: apply the Round 1 decision rule to the honest forecasts.

Rule (unchanged from Round 1), decision horizon h = 3:
    S = (P_hat - P0)/P0 - c*3,  c = 1%/month
    BUY NOW    S > +2%  and P(up)   >= 60%  -> hold 3.0 months of cover
    DEFER      S < -2%  and P(down) >= 60%  -> hold 1.0 month
    BUY NORMAL otherwise                    -> hold 1.5 months
Baseline: BUY NORMAL every month.

Accounting fixes vs the Round 2 version:
  * Purchases execute at NEXT month's average price (the decision is made on
    the first day of the month, after this month's price is known). The old
    replay bought at the price it had just observed, which is optimistic.
  * Inventory left at the end is valued at the final price, so both policies
    are compared on the same consumption.
  * Permutation test: the same number of BUY NOW / DEFER signals, placed at
    random months, 2,000 times. If random timing saves as much, the forecast
    is not what produced the saving.
  * Perfect-foresight bound: the same rule fed the realised price, to show how
    much the rule could capture with a perfect forecast.
Monthly requirement is constant (we hold no ACG demand data).
"""
from __future__ import annotations

import json

import numpy as np
import pandas as pd

from .combine import SC, window_of
from .data import BASE, CFG

D = CFG["decision"]
C, Q, LEAD = D["carrying_cost_per_month"], 1000.0, D["lead_time_months"]
COVER = {"BUY NOW": D["cover_buy_now"], "BUY NORMAL": D["cover_normal"], "DEFER": D["cover_defer"]}


def signal(f, p_up, h=3):
    S = np.exp(f) - 1 - C * h
    if S > D["buy_now_threshold"] and p_up >= D["min_confidence"]:
        return "BUY NOW", S
    if S < D["defer_threshold"] and (1 - p_up) >= D["min_confidence"]:
        return "DEFER", S
    return "BUY NORMAL", S


def simulate(covers, exec_px, last_px):
    inv = COVER["BUY NORMAL"] * Q
    spend = carry = qty = 0.0
    days = []
    for cov, px in zip(covers, exec_px):
        order = max(0.0, cov * Q + LEAD * Q - inv)
        spend += order * px
        qty += order
        inv = max(inv + order - Q, 0.0)
        carry += inv * px * C
        days.append(inv / Q * 30.44)
    consumed = Q * len(covers)
    total = spend + carry - inv * last_px + COVER["BUY NORMAL"] * Q * exec_px[0]
    return {"avg_purchase_price": spend / qty, "cost_per_unit": total / consumed,
            "inventory_days": float(np.mean(days))}


def replay_block(r: pd.DataFrame, rng) -> dict:
    exec_px = r.exec_px.values
    last_px = exec_px[-1]
    base = simulate([COVER["BUY NORMAL"]] * len(r), exec_px, last_px)
    sb = simulate([COVER[s] for s in r.signal], exec_px, last_px)
    net = 100 * (1 - sb["cost_per_unit"] / base["cost_per_unit"])
    gross = 100 * (1 - sb["avg_purchase_price"] / base["avg_purchase_price"])
    perms = []
    sig = np.array(r.signal.tolist())
    for _ in range(D["permutation_draws"]):
        rng.shuffle(sig)
        perms.append(100 * (1 - simulate([COVER[s] for s in sig], exec_px, last_px)["cost_per_unit"]
                            / base["cost_per_unit"]))
    perms = np.array(perms)
    pf = simulate([COVER[s] for s in r.signal_perfect], exec_px, last_px)
    dd = sb["inventory_days"] - base["inventory_days"]
    return {
        "months": len(r),
        "signals": r.signal.value_counts().to_dict(),
        "gross_price_saving_pct": round(gross, 2),
        "net_saving_after_carry_pct": round(net, 2),
        "permutation_p_value": round(float((perms >= net).mean()), 3),
        "random_timing_median_pct": round(float(np.median(perms)), 2),
        "perfect_foresight_net_pct": round(100 * (1 - pf["cost_per_unit"] / base["cost_per_unit"]), 2),
        "inventory_days_baseline": round(base["inventory_days"], 1),
        "inventory_days_smartbuy": round(sb["inventory_days"], 1),
        "inventory_days_change": round(dd, 1),
        "rupees_cr_saved_per_100cr_spend": round(net, 2),
        "extra_working_capital_cr_per_100cr_spend": round(dd * 100 / 365, 2),
    }


def run():
    rng = np.random.default_rng(42)
    h = CFG["backtest"]["decision_horizon"]
    summary, frames = {}, []
    for m in ("aluminium", "pvc"):
        c = pd.read_csv(SC / f"{m}_combined.csv", parse_dates=["origin"])
        c3 = c[c.h == h].set_index("origin")
        c1 = c[c.h == 1].set_index("origin")
        r = c3.copy()
        # execution at next month's average price = P0 * exp(realised 1-month return)
        r["exec_px"] = r.p0 * np.exp(c1.y.reindex(r.index))
        r = r[r.exec_px.notna() & r.y.notna()].copy()
        sig = [signal(f, p) for f, p in zip(r.f_gated_equal_weight, r.p_up)]
        r["signal"], r["S"] = [s for s, _ in sig], [x for _, x in sig]
        r["signal_perfect"] = [signal(y, 1.0 if y > 0 else 0.0)[0] for y in r.y]
        r["window"] = r.index.map(window_of)
        summary[m] = {}
        for w in ("development", "holdout"):
            rw = r[r.window == w]
            if len(rw) >= 6:
                summary[m][w] = replay_block(rw, rng)
        r["material"] = m
        frames.append(r.reset_index())
    pd.concat(frames).to_csv(BASE / "outputs" / "replay_signals.csv", index=False)
    (BASE / "outputs" / "replay_summary.json").write_text(json.dumps(summary, indent=1, default=str))
    print(json.dumps(summary, indent=1, default=str))
    return summary


if __name__ == "__main__":
    run()
