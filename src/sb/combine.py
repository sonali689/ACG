"""
Combine member forecasts and score everything.

Gate and ensemble (sequential, no look-ahead):
  At origin T, horizon h, only forecasts whose outcome was known at T
  (origin <= T - h) are used to judge the models. A model is eligible if,
  on those realised forecasts (>= 12 of them), its MAPE is below naive's.
    gated_equal_weight  mean of eligible members        (HEADLINE, pre-specified)
    gated_inv_mse       inverse-MSE weights over eligible members
    all_equal           mean of every member, no gate
  No eligible member -> the forecast is naive (no change).

Bands (normalised split-conformal, sequential):
  score_s = |y_s - yhat_s| / sigma_s over realised origins s;
  q = conformal 80% quantile of the scores; band = yhat +/- q * sigma_T,
  where sigma_T is the GARCH(1,1) volatility forecast made at T.
  P(up) = Phi(yhat / (q * sigma_T / 1.2816)).

Scoring windows: development (2018-01 .. 2024-06) and holdout (>= 2025-01).
"""
from __future__ import annotations

import math
from pathlib import Path

import numpy as np
import pandas as pd
import yaml
from scipy import stats

from .data import BASE, CFG

PRED = BASE / "outputs" / "predictions"
SC = BASE / "outputs" / "scorecards"
SC.mkdir(parents=True, exist_ok=True)
H = CFG["backtest"]["horizons"]
MIN_R = CFG["backtest"]["min_realised_for_gate"]
NOM = CFG["bands"]["nominal_coverage"]
Z = stats.norm.ppf(0.5 + NOM / 2)          # 1.2816 for 80%
BASE_MEMBERS = ["seasonal_naive", "drift", "ets", "arima", "vecm", "enet",
                "lgb_local", "lgb_global", "nbeats"]
COMBOS = ["gated_equal_weight", "gated_inv_mse", "all_equal"]
REGIMES = yaml.safe_load((BASE / "config" / "thresholds.yaml").read_text())["regimes"]


def load(material: str) -> tuple[pd.DataFrame, list[str]]:
    d = pd.read_csv(PRED / f"{material}_local.csv", parse_dates=["origin", "target_date"])
    members = [m for m in BASE_MEMBERS if f"f_{m}" in d.columns]
    for f, cols in [("global_lgb.csv", ["f_lgb_global", "p_up_global_clf"]),
                    ("nbeats.csv", ["f_nbeats"]), ("chronos.csv", ["f_chronos"])]:
        p = PRED / f
        if p.exists():
            g = pd.read_csv(p, parse_dates=["origin"])
            g = g[g.material == material][["origin", "h"] + cols]
            d = d.merge(g, on=["origin", "h"], how="left")
            members += [c[2:] for c in cols if c.startswith("f_") and c[2:] not in members]
    return d.sort_values(["h", "origin"]).reset_index(drop=True), members


def ape(f, y):
    return np.abs(np.exp(f - y) - 1.0)


def combine(material: str) -> pd.DataFrame:
    d, members = load(material)
    out = []
    for h in H:
        g = d[d.h == h].sort_values("origin").reset_index(drop=True)
        head, scores = [], []
        for i, r in g.iterrows():
            T = r.origin
            real = g[(g.origin <= T - pd.DateOffset(months=h)) & g.y.notna()]
            rec = {"elig": [], "w": {}}
            if len(real) >= MIN_R:
                naive_ape = ape(0.0, real.y)
                for m in members:
                    fm = real[f"f_{m}"]
                    ok = fm.notna()
                    if ok.sum() >= MIN_R and pd.notna(r[f"f_{m}"]):
                        if ape(fm[ok], real.y[ok]).mean() < naive_ape[ok].mean():
                            rec["elig"].append(m)
                            rec["w"][m] = 1.0 / np.mean((fm[ok] - real.y[ok]) ** 2)
            if rec["elig"]:
                f_ge = float(np.mean([r[f"f_{m}"] for m in rec["elig"]]))
                tw = sum(rec["w"].values())
                f_im = float(sum(rec["w"][m] / tw * r[f"f_{m}"] for m in rec["elig"]))
            else:
                f_ge = f_im = 0.0
            avail = [r[f"f_{m}"] for m in members if pd.notna(r[f"f_{m}"])]
            f_all = float(np.mean(avail)) if avail else 0.0

            # conformal band around the headline, using realised past headline errors
            past = [s for (t_s, s) in scores if t_s <= T - pd.DateOffset(months=h)]
            if len(past) >= MIN_R:
                n = len(past)
                q = float(np.quantile(past, min(1.0, math.ceil((n + 1) * NOM) / n), method="higher"))
            else:
                q = Z
            sig = r.sigma
            if pd.notna(r.y):
                scores.append((T, abs(r.y - f_ge) / sig))
            out.append({
                "material": material, "origin": T, "h": h, "target_date": r.target_date,
                "p0": r.p0, "y": r.y, "sigma": sig, "vol_model": r.vol_model,
                "f_naive": 0.0, **{f"f_{m}": r[f"f_{m}"] for m in members},
                "f_gated_equal_weight": f_ge, "f_gated_inv_mse": f_im, "f_all_equal": f_all,
                "n_eligible": len(rec["elig"]), "eligible": "|".join(rec["elig"]),
                "conformal_q": q,
                "lo_conf": f_ge - q * sig, "hi_conf": f_ge + q * sig,
                "lo_gauss": f_ge - Z * sig, "hi_gauss": f_ge + Z * sig,
                "p_up": float(stats.norm.cdf(f_ge / max(q * sig / Z, 1e-9))),
                "p_up_global_clf": r.get("p_up_global_clf", np.nan),
            })
    c = pd.DataFrame(out)
    c.to_csv(SC / f"{material}_combined.csv", index=False)
    return c


# --------------------------------------------------------------------------- #
def dm_test(e_model, e_naive, h):
    """Diebold-Mariano on absolute % errors, Newey-West variance (lag h-1),
    Harvey-Leybourne-Newbold small-sample correction, t(n-1).
    Returns one-sided p (model better) and two-sided p."""
    d = np.abs(e_model) - np.abs(e_naive)
    d = d[~np.isnan(d)]
    n = len(d)
    if n < 8 or np.allclose(d, 0):
        return np.nan, np.nan
    db = d.mean()
    var = ((d - db) ** 2).mean()
    var0 = var
    for k in range(1, h):
        var += 2 * ((d[k:] - db) * (d[:-k] - db)).mean()
    if var <= 0.1 * var0:          # HAC estimate degenerate on short samples: fall back to plain variance
        var = var0
    dm = db / math.sqrt(max(var, 1e-12) / n)
    dm *= math.sqrt(max((n + 1 - 2 * h + h * (h - 1) / n) / n, 1e-9))
    return float(stats.t.cdf(dm, n - 1)), float(2 * (1 - stats.t.cdf(abs(dm), n - 1)))


def window_of(t: pd.Timestamp) -> str:
    b = CFG["backtest"]
    if pd.Timestamp(b["score_start"]) <= t <= pd.Timestamp(b["dev_end"]):
        return "development"
    if t >= pd.Timestamp(b["holdout_start"]):
        return "holdout"
    return "unscored"


def score_block(g: pd.DataFrame, fcol: str, h: int) -> dict:
    y, f = g.y.values, g[fcol].values
    ok = ~np.isnan(f)
    y, f = y[ok], f[ok]
    if len(y) == 0:
        return {}
    e_m = np.exp(f - y) - 1.0
    e_n = np.exp(-y) - 1.0
    mape, nm = np.mean(np.abs(e_m)) * 100, np.mean(np.abs(e_n)) * 100
    called = (np.sign(f) != 0) & (np.sign(y) != 0)
    dir_acc = np.mean(np.sign(f[called]) == np.sign(y[called])) * 100 if called.any() else np.nan
    p1, p2 = dm_test(e_m, e_n, h)
    return {"n": int(len(y)), "mape": round(mape, 2), "naive_mape": round(nm, 2),
            "skill_pct": round(100 * (1 - mape / nm), 1),
            "dir_acc_pct": round(dir_acc, 1) if not np.isnan(dir_acc) else np.nan,
            "call_rate_pct": round(100 * called.mean(), 1),
            "bias_pct": round(np.mean(e_m) * 100, 2),
            "dm_p_one_sided": round(p1, 4) if not np.isnan(p1) else np.nan,
            "dm_p_two_sided": round(p2, 4) if not np.isnan(p2) else np.nan}


def scorecards(material: str, c: pd.DataFrame):
    c = c.copy()
    c["window"] = c.origin.map(window_of)
    models = ["naive"] + [m for m in BASE_MEMBERS + ["chronos"] if f"f_{m}" in c.columns] + COMBOS
    rows, bands = [], []
    for w in ("development", "holdout"):
        for h in H:
            g = c[(c.window == w) & (c.h == h) & c.y.notna()]
            if len(g) == 0:
                continue
            for m in models:
                s = score_block(g, f"f_{m}", h)
                if s:
                    rows.append({"material": material, "window": w, "h": h, "model": m, **s})
            for kind in ("conf", "gauss"):
                inside = (g.y >= g[f"lo_{kind}"]) & (g.y <= g[f"hi_{kind}"])
                bands.append({"material": material, "window": w, "h": h, "band": kind,
                              "coverage_pct": round(100 * inside.mean(), 1),
                              "mean_width_pct": round(100 * (np.exp(g[f"hi_{kind}"]) - np.exp(g[f"lo_{kind}"])).mean(), 1),
                              "n": len(g)})
            # direction probability quality (Brier vs a no-skill 50/50 and vs base rate)
            up = (g.y > 0).astype(float)
            for pcol in ("p_up", "p_up_global_clf"):
                if pcol in g and g[pcol].notna().all():
                    brier = np.mean((g[pcol] - up) ** 2)
                    rows.append({"material": material, "window": w, "h": h, "model": f"[{pcol}]",
                                 "n": len(g), "brier": round(brier, 4),
                                 "brier_coinflip": 0.25})
    sc = pd.DataFrame(rows)
    sc.to_csv(SC / f"{material}_scorecard.csv", index=False)
    bd = pd.DataFrame(bands)
    bd.to_csv(SC / f"{material}_bands.csv", index=False)

    # regimes, decision horizon, development window
    reg = []
    dh = CFG["backtest"]["decision_horizon"]
    for name, r in REGIMES.items():
        g = c[(c.h == dh) & c.y.notna() & (c.origin >= r["start"]) & (c.origin <= r["end"])]
        if len(g) == 0:
            continue
        s = score_block(g, "f_gated_equal_weight", dh)
        inside = ((g.y >= g.lo_conf) & (g.y <= g.hi_conf)).mean() * 100
        reg.append({"material": material, "regime": name, **s, "band_coverage_pct": round(inside, 1)})
    pd.DataFrame(reg).to_csv(SC / f"{material}_regimes.csv", index=False)

    # error correlation between members, decision horizon, development window
    g = c[(c.window == "development") & (c.h == dh) & c.y.notna()]
    mem = [m for m in BASE_MEMBERS + ["chronos"] if f"f_{m}" in g.columns]
    E = pd.DataFrame({m: g[f"f_{m}"] - g.y for m in mem}).dropna()
    E.corr().round(3).to_csv(SC / f"{material}_error_corr_h{dh}.csv")

    # how often each member was eligible (= its effective weight in the headline)
    wrows = []
    for h in H:
        gg = c[(c.h == h) & (c.window == "development")]
        tot = gg.n_eligible.replace(0, np.nan)
        rec = {"material": material, "h": h,
               "share_months_naive_fallback_pct": round(100 * (gg.n_eligible == 0).mean(), 1)}
        for m in mem:
            share = gg.eligible.fillna("").str.split("|").apply(lambda L: m in L)
            rec[m] = round(100 * (share / tot).fillna(0).mean(), 1)
        wrows.append(rec)
    pd.DataFrame(wrows).to_csv(SC / f"{material}_weights.csv", index=False)
    return sc, bd


if __name__ == "__main__":
    for m in ("aluminium", "pvc"):
        c = combine(m)
        sc, bd = scorecards(m, c)
        dh = CFG["backtest"]["decision_horizon"]
        pd.set_option("display.width", 220)
        print(f"\n===== {m.upper()} =====")
        print(sc[(sc.h == dh) & sc.mape.notna()].drop(columns=["material"]).to_string(index=False))
        print(bd[bd.band == "conf"].to_string(index=False))
