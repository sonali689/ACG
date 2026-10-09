"""Assemble dashboard/data.json from the v2 pipeline outputs. Nothing is typed by hand."""
import json
from pathlib import Path

import numpy as np
import pandas as pd

BASE = Path(__file__).resolve().parents[1]
OUT = BASE / "outputs"
SC = OUT / "scorecards"
D = json.loads((OUT / "forecast_now.json").read_text())
RP = json.loads((OUT / "replay_summary.json").read_text())
DRV = pd.read_csv(OUT / "drivers" / "lead_lag_granger.csv")
GATES = {"skill": {1: 10, 2: 12, 3: 15, 4: 12, 5: 10, 6: 10},
         "dir": {1: 65, 2: 63, 3: 62, 4: 60, 5: 59, 6: 58}}
COVER = {"BUY NOW": 3.0, "BUY NORMAL": 1.5, "DEFER": 1.0}
NAMES = {"naive": "Naïve (no change)", "seasonal_naive": "Seasonal naïve", "drift": "Drift",
         "ets": "ETS (damped)", "arima": "ARIMA", "vecm": "VECM (cost drivers)",
         "enet": "ElasticNet + drivers", "lgb_local": "LightGBM + drivers",
         "lgb_global": "LightGBM, global panel", "nbeats": "N-BEATS, global panel",
         "chronos": "Chronos (zero-shot)", "gated_equal_weight": "Smart Buy ensemble (headline)",
         "gated_inv_mse": "Ensemble, inverse-MSE", "all_equal": "Average of all, no gate"}


def r(x, d=2):
    try:
        if x is None or np.isnan(float(x)):
            return None
    except (TypeError, ValueError):
        return None
    return round(float(x), d)


def material(m):
    f = D[m]
    c = pd.read_csv(SC / f"{m}_combined.csv", parse_dates=["origin"])
    sc = pd.read_csv(SC / f"{m}_scorecard.csv")
    bd = pd.read_csv(SC / f"{m}_bands.csv")
    rg = pd.read_csv(SC / f"{m}_regimes.csv")
    wt = pd.read_csv(SC / f"{m}_weights.csv")
    ec = pd.read_csv(SC / f"{m}_error_corr_h3.csv", index_col=0)
    h1 = c[c.h == 1].set_index("origin").sort_index()

    T = h1.index.max()
    hist = h1.p0.iloc[-36:]
    fwd_lab = [(T + pd.DateOffset(months=h)).strftime("%b %y") for h in range(1, 7)]
    n_h = len(hist)
    hz = {}
    for h, v in f["horizons"].items():
        hz[h] = {"p50": v["p50"], "p10": v["p10"], "p90": v["p90"], "change_pct": v["change_pct"],
                 "p_up": round(100 * v["p_up"], 1), "exp_saving_pct": v["expected_saving_net_pct"],
                 "signal": v["signal"], "cover": COVER[v["signal"]], "models": v["eligible_models"]}
    last = r(hist.iloc[-1], 1)
    series = {"labels": [d.strftime("%b %y") for d in hist.index] + fwd_lab,
              "actual": [r(x, 1) for x in hist.values] + [None] * 6,
              "p50": [None] * (n_h - 1) + [last] + [hz[str(h)]["p50"] for h in range(1, 7)],
              "p10": [None] * (n_h - 1) + [last] + [hz[str(h)]["p10"] for h in range(1, 7)],
              "p90": [None] * (n_h - 1) + [last] + [hz[str(h)]["p90"] for h in range(1, 7)],
              "naive": [None] * (n_h - 1) + [last] * 7}

    b = c[(c.h == 3) & c.y.notna() & (c.origin >= "2018-01-01")].sort_values("origin")
    tgt = b.origin + pd.DateOffset(months=3)
    backtest = {"labels": [d.strftime("%b %y") for d in tgt],
                "actual": [r(x, 1) for x in b.p0 * np.exp(b.y)],
                "pred": [r(x, 1) for x in b.p0 * np.exp(b.f_gated_equal_weight)],
                "p10": [r(x, 1) for x in b.p0 * np.exp(b.lo_conf)],
                "p90": [r(x, 1) for x in b.p0 * np.exp(b.hi_conf)]}

    hd = sc[sc.model == "gated_equal_weight"]
    scorecard = [{"window": x.window, "h": int(x.h), "n": int(x.n), "ens": x.mape, "naive": x.naive_mape,
                  "skill": x.skill_pct, "dir": r(x.dir_acc_pct, 1), "dm_p": r(x.dm_p_one_sided, 4),
                  "gate_skill": GATES["skill"][int(x.h)], "gate_dir": GATES["dir"][int(x.h)]}
                 for x in hd.itertuples()]

    dev3 = sc[(sc.window == "development") & (sc.h == 3) & sc.mape.notna()]
    w3 = wt[wt.h == 3].iloc[0]
    ladder = []
    for x in dev3.sort_values("mape").itertuples():
        ens = x.model in ("gated_equal_weight", "gated_inv_mse", "all_equal")
        ladder.append({"model": NAMES.get(x.model, x.model), "key": x.model, "is_ensemble": ens,
                       "is_headline": x.model == "gated_equal_weight",
                       "mape": x.mape, "skill": x.skill_pct, "dir": r(x.dir_acc_pct, 1),
                       "dm_p": r(x.dm_p_one_sided, 4),
                       "weight": None if ens or x.model == "naive" else r(w3.get(x.model, 0.0), 1)})
    off = ec.values[np.triu_indices_from(ec.values, 1)]
    div = (ec.sum() - 1) / (len(ec) - 1)
    most_div = div.idxmin()

    dv = DRV[DRV.material == m].sort_values("best_rho", key=np.abs, ascending=False)
    drivers = [{"name": x.label, "rho": x.best_rho, "lead": int(x.best_lead), "q": x.granger_q_fdr,
                "sig": bool(x.granger_sig_fdr)} for x in dv.itertuples()][:10]

    bands = [{"window": x.window, "h": int(x.h), "cov": x.coverage_pct, "width": x.mean_width_pct, "n": int(x.n)}
             for x in bd[bd.band == "conf"].itertuples()]
    bands_gauss = {int(x.h): x.coverage_pct for x in bd[(bd.band == "gauss") & (bd.window == "development")].itertuples()}
    regimes = [{"name": x.regime.title(), "n": int(x.n), "mape": x.mape, "skill": x.skill_pct,
                "dir": r(x.dir_acc_pct, 1), "cov": x.band_coverage_pct} for x in rg.itertuples()]

    rs = pd.read_csv(OUT / "replay_signals.csv", parse_dates=["origin"])
    rs = rs[(rs.material == m) & (rs.window == "development")].sort_values("origin")
    replay = {**RP[m].get("development", {}),
              "curve": {"labels": [d.strftime("%b %y") for d in rs.origin],
                        "signal": list(rs.signal), "price": [r(x, 1) for x in rs.exec_px]},
              "holdout": RP[m].get("holdout")}

    return {"name": f["display"], "short": "Aluminium" if m == "aluminium" else "PVC proxy",
            "unit": f["unit"], "cur": "$" if m == "aluminium" else "", "spot": f["spot"],
            "origin": f["origin"], "stale": f["stale_warning"], "note": f["note"],
            "shap": f["shap_drivers_h3"], "landed": f["landed"], "horizons": hz,
            "series": series, "backtest": backtest, "scorecard": scorecard, "ladder": ladder,
            "fallback_pct": r(w3.share_months_naive_fallback_pct, 1),
            "err_corr": {"mean_off_diag": r(off.mean(), 2), "most_diversifying": NAMES.get(most_div, most_div),
                         "its_mean_corr": r(div[most_div], 2)},
            "drivers": drivers, "bands": bands, "bands_gauss": bands_gauss, "regimes": regimes,
            "replay": replay}


data = {"materials": {m: material(m) for m in ("aluminium", "pvc")},
        "hypotheses": json.loads((OUT / "drivers" / "hypotheses.json").read_text()),
        "generated": pd.Timestamp.now().strftime("%d %b %Y")}
(Path(__file__).parent / "data.json").write_text(json.dumps(data, indent=1, default=str))
print("wrote dashboard/data.json")
