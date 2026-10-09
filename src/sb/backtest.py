"""
Walk-forward backtest v2.

THE EMBARGO (the fix for the Round 2 look-ahead leak):
    at origin T, a training row dated t is allowed only if t + h <= T,
    i.e. its h-month outcome had already been published on the forecast day.
The original code trained on every row before T, so rows T-1 ... T-h+1
carried labels that used prices from AFTER the forecast day.

Origins run monthly from config.backtest.first_origin to the last month the
target was published. Origins whose outcome is not yet known are still
forecast (that is the live forecast) and simply carry actual = NaN.

Run:
    python -m src.sb.backtest local     # statistical + local driver models
    python -m src.sb.backtest global    # global LightGBM (regression + classifier)
    python -m src.sb.backtest nbeats    # global N-BEATS
"""
from __future__ import annotations

import sys
import time
from pathlib import Path

import numpy as np
import pandas as pd

from . import models as M
from .data import BASE, CFG, last_observed, visible_panel
from .features import build_features, feature_columns
from .panel import PANEL_FEATURES, panel_frame, panel_series, training_rows

OUT = BASE / "outputs" / "predictions"
OUT.mkdir(parents=True, exist_ok=True)
H = CFG["backtest"]["horizons"]
NHIST = CFG["backtest"]["history_months_stat"]
TRAIN_START = pd.Timestamp("2000-01-01")
VECM_VARS = {"aluminium": ["aluminium", "copper", "coal_aus", "gas_eu"],
             "pvc": ["ppi_plastic_resins", "ppi_organic_chem", "brent", "gas_us"]}


def origins_for(material: str) -> list[pd.Timestamp]:
    v = visible_panel(material)[CFG["materials"][material]["target"]]
    start = pd.Timestamp(CFG["backtest"]["first_origin"])
    return [t for t in v.index if start <= t <= last_observed(material) and pd.notna(v[t])]


def embargoed(df: pd.DataFrame, origin: pd.Timestamp, h: int) -> pd.DataFrame:
    """Training rows whose h-month outcome was known at `origin`."""
    cutoff = origin - pd.DateOffset(months=h)
    return df[(df.index >= TRAIN_START) & (df.index <= cutoff) & df[f"y_h{h}"].notna()]


# --------------------------------------------------------------------------- #
def run_local(material: str) -> pd.DataFrame:
    tgt = CFG["materials"][material]["target"]
    feats = build_features(material)
    fc = feature_columns(feats)
    vis = visible_panel(material)
    lp_all = np.log(vis[tgt])
    recs, t0 = [], time.time()
    origins = origins_for(material)
    for i, T in enumerate(origins):
        lp = lp_all[:T].dropna().iloc[-NHIST:]
        stat = {"naive": np.zeros(len(H)), "seasonal_naive": M.seasonal_naive(lp),
                "drift": M.drift(lp), "ets": M.ets(lp), "arima": M.arima(lp)}
        logs = np.log(vis.loc[:T, VECM_VARS[material]].iloc[-NHIST:])
        stat["vecm"], rank = M.vecm(logs, tgt)
        sigma, volm = M.garch_sigma(lp)
        x_te = feats.loc[[T], fc]
        for j, h in enumerate(H):
            tr = embargoed(feats, T, h)
            p_en, sel = M.enet(tr[fc], tr[f"y_h{h}"], x_te, h)
            p_lgb, _ = M.lgb_local(tr[fc], tr[f"y_h{h}"], x_te)
            y = feats.at[T, f"y_h{h}"]
            recs.append({
                "material": material, "origin": T, "h": h,
                "target_date": T + pd.DateOffset(months=h),
                "p0": float(np.exp(lp.iloc[-1])), "y": y,
                **{f"f_{k}": float(v[j]) for k, v in stat.items()},
                "f_enet": p_en, "f_lgb_local": p_lgb,
                "sigma": float(sigma[j]), "vol_model": volm, "vecm_rank": rank,
                "n_train": len(tr), "max_train_target_date": (tr.index.max() + pd.DateOffset(months=h)),
                "enet_features": "|".join(sel),
            })
        if i % 12 == 0:
            print(f"  {material} {T.date()}  ({i + 1}/{len(origins)})  {time.time() - t0:.0f}s", flush=True)
    df = pd.DataFrame(recs)
    # hard guarantee: no training label was published after its forecast day
    assert (df.max_train_target_date <= df.origin).all(), "EMBARGO VIOLATED"
    df.to_csv(OUT / f"{material}_local.csv", index=False)
    return df


# --------------------------------------------------------------------------- #
def run_global() -> pd.DataFrame:
    p = panel_frame()
    every = CFG["backtest"]["global_refit_every_months"]
    targets = {"aluminium": "aluminium", "pvc": "ppi_plastic_resins"}
    all_origins = {m: origins_for(m) for m in targets}
    first = min(min(o) for o in all_origins.values())
    last = max(max(o) for o in all_origins.values())
    refits = list(pd.date_range(first, last, freq=f"{every}MS"))
    recs, t0 = [], time.time()
    for k, R in enumerate(refits):
        nxt = refits[k + 1] if k + 1 < len(refits) else last + pd.DateOffset(months=1)
        for h in H:
            tr = training_rows(p, R, h)
            assert (tr["date"] + pd.DateOffset(months=h) <= R).all(), "EMBARGO VIOLATED"
            reg, clf = M.lgb_global_fit(tr[PANEL_FEATURES], tr[f"y_h{h}"])
            for m, s in targets.items():
                rows = p[(p.series == s)].set_index("date")
                for T in all_origins[m]:
                    if R <= T < nxt and T in rows.index:
                        x = rows.loc[[T], PANEL_FEATURES]
                        recs.append({"material": m, "origin": T, "h": h,
                                     "f_lgb_global": float(reg.predict(x.values)[0]),
                                     "p_up_global_clf": float(clf.predict(x.values)[0]),
                                     "global_refit": R})
        print(f"  global refit {R.date()} ({k + 1}/{len(refits)})  {time.time() - t0:.0f}s", flush=True)
    df = pd.DataFrame(recs)
    df.to_csv(OUT / "global_lgb.csv", index=False)
    return df


# --------------------------------------------------------------------------- #
def run_nbeats(seeds=(0, 1, 2)) -> pd.DataFrame:
    from . import nbeats_jax as nb
    ps = panel_series()
    targets = {"aluminium": "aluminium", "pvc": "ppi_plastic_resins"}
    all_origins = {m: origins_for(m) for m in targets}
    first = min(min(o) for o in all_origins.values())
    last = max(max(o) for o in all_origins.values())
    refits = list(pd.date_range(first, last, freq="12MS"))
    recs, t0 = [], time.time()
    for k, R in enumerate(refits):
        nxt = refits[k + 1] if k + 1 < len(refits) else last + pd.DateOffset(months=1)
        sl, co = [], []
        for name, (s, g, lag) in ps.items():
            s = s[s.index <= R - pd.DateOffset(months=lag)]   # forecast END must be visible at R
            if len(s) > nb.L + nb.HZ:
                sl.append(np.log(s.values)); co.append(len(s) - 1)
        X, Y, age = nb.make_windows(sl, co)
        params = [nb.fit(X, Y, age, seed=sd) for sd in seeds]
        for m, s_name in targets.items():
            s = ps[s_name][0]
            for T in all_origins[m]:
                if R <= T < nxt:
                    w = np.log(s[s.index <= T].values[-nb.L:])
                    f = nb.predict(params, w)
                    for j, h in enumerate(H):
                        recs.append({"material": m, "origin": T, "h": h,
                                     "f_nbeats": float(f[j]), "nbeats_refit": R})
        print(f"  nbeats refit {R.date()} ({k + 1}/{len(refits)}) windows={len(X)}  {time.time() - t0:.0f}s", flush=True)
    df = pd.DataFrame(recs)
    df.to_csv(OUT / "nbeats.csv", index=False)
    return df


if __name__ == "__main__":
    part = sys.argv[1] if len(sys.argv) > 1 else "local"
    if part == "local":
        for m in ("aluminium", "pvc"):
            run_local(m)
    elif part == "global":
        run_global()
    elif part == "nbeats":
        run_nbeats()
