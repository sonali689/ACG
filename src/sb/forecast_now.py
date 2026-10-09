"""
The live forecast: what a buyer would receive today, per material.

Uses the most recent origin in the backtest (the last month the price was
published). Driver attribution uses real SHAP values: LightGBM's built-in
TreeSHAP (pred_contrib=True) on the local driver model at the decision horizon,
refitted with the same embargo as the backtest. The note is generated from the
numbers, never typed.
"""
from __future__ import annotations

import json

import numpy as np
import pandas as pd

from . import models as M
from .backtest import embargoed
from .combine import SC
from .data import BASE, CFG, SERIES, raw_panel
from .features import build_features, feature_columns
from .replay import signal

OUT = BASE / "outputs"
# raw series -> substrings of the feature names built from it
FEATURE_SOURCES = {
    "brent": ["brent"], "coal_aus": ["coal"], "gas_us": ["gas_us"], "gas_eu": ["gas_eu"],
    "copper": ["copper"], "zinc": ["zinc"], "nickel": ["nickel"], "wb_energy": ["energy_idx"],
    "wb_basemetals": ["basemetals"], "usd_inr": ["fx_"], "gpr": ["gpr"], "epu": ["epu"],
    "cli_china": ["cli_"], "indpro": ["indpro"], "ppi_organic_chem": ["monomer"],
    "ppi_primary_al": ["ppi_primary"], "ip_resin": ["ip_resin"], "ip_aluminium": ["ip_aluminium"],
    "freight_tsi": ["freight"],
}
NICE = {
    "own_": "own price momentum", "copper": "copper", "zinc": "zinc", "nickel": "nickel",
    "basemetals": "base-metals index", "coal": "coal", "gas": "natural gas", "brent": "Brent crude",
    "energy": "energy index", "fx_": "USD/INR", "gpr": "geopolitical risk", "epu": "policy uncertainty",
    "cli": "China leading indicator", "indpro": "US industrial production", "ip_": "US sector output",
    "freight": "freight", "monomer": "monomer prices", "resin_vs": "resin margin vs feedstock",
    "al_vs": "aluminium vs peers", "ppi_primary": "US aluminium PPI", "month": "seasonality",
    "shock": "shock indicator",
}


def nice(c):
    for k, v in NICE.items():
        if c.startswith(k) or k in c:
            return v
    return c


def shap_drivers(material, T, h):
    feats = build_features(material)
    fc = feature_columns(feats)
    tr = embargoed(feats, T, h)
    _, booster = M.lgb_local(tr[fc], tr[f"y_h{h}"], feats.loc[[T], fc])
    contrib = booster.predict(feats.loc[[T], fc].values, pred_contrib=True)[0]
    s = pd.Series(contrib[:-1], index=fc)
    grouped = s.groupby(s.index.map(nice)).sum().sort_values(key=np.abs, ascending=False)
    return [{"driver": k, "contribution_pct": round(100 * v, 2)} for k, v in grouped.head(8).items()]


def run():
    res = {}
    dh = CFG["backtest"]["decision_horizon"]
    raw = raw_panel()
    for m in ("aluminium", "pvc"):
        c = pd.read_csv(SC / f"{m}_combined.csv", parse_dates=["origin"])
        T = c.origin.max()
        cur = c[c.origin == T].sort_values("h")
        p0 = float(cur.p0.iloc[0])
        hz = {}
        for _, r in cur.iterrows():
            sig, S = signal(r.f_gated_equal_weight, r.p_up, int(r.h))
            hz[int(r.h)] = {
                "target_month": (T + pd.DateOffset(months=int(r.h))).strftime("%b %Y"),
                "p50": round(p0 * np.exp(r.f_gated_equal_weight), 1),
                "p10": round(p0 * np.exp(r.lo_conf), 1), "p90": round(p0 * np.exp(r.hi_conf), 1),
                "change_pct": round(100 * (np.exp(r.f_gated_equal_weight) - 1), 2),
                "p_up": round(float(r.p_up), 3),
                "expected_saving_net_pct": round(100 * S, 2), "signal": sig,
                "eligible_models": r.eligible if isinstance(r.eligible, str) else "",
            }
        drivers = shap_drivers(m, T, dh)
        d3 = hz[dh]
        top = [x for x in drivers if x["driver"] != "seasonality"][:3]
        push = ", ".join(f"{x['driver']} ({x['contribution_pct']:+.1f}%)" for x in top)
        unit = CFG["materials"][m]["unit"]
        conf = max(d3["p_up"], 1 - d3["p_up"])
        note = (f"{CFG['materials'][m]['display']}: latest {T.strftime('%b %Y')} = {p0:,.1f} {unit}. "
                f"Three-month median forecast {d3['p50']:,.1f} ({d3['change_pct']:+.1f}%), 80% range "
                f"{d3['p10']:,.1f} to {d3['p90']:,.1f}. Probability the price is higher: {100 * d3['p_up']:.0f}%. "
                f"After {100 * CFG['decision']['carrying_cost_per_month'] * dh:.0f}% carrying cost, buying ahead now is worth "
                f"{d3['expected_saving_net_pct']:+.1f}% (threshold +/-2%, confidence {100 * conf:.0f}% vs 60% needed): "
                f"{d3['signal']}. Largest pushes in the tree model: {push}. "
                f"Models currently trusted at this horizon: {d3['eligible_models'].replace('|', ', ') or 'none (naive)'}.")
        landed = None
        if m == "aluminium":
            fx = float(raw.usd_inr.dropna().iloc[-1])
            landed = {"usd_inr_latest": round(fx, 2), "usd_inr_month": raw.usd_inr.dropna().index[-1].strftime("%b %Y"),
                      "lme_in_inr_per_t": round(p0 * fx, 0),
                      "note": "Index converted at latest USD/INR only. Premium, freight, BCD, SWS and ADD to be calibrated on ACG POs."}
        used = feature_columns(build_features(m))
        stale_inputs = sorted({SERIES[col][1] for col, keys in FEATURE_SOURCES.items()
                               if col != CFG["materials"][m]["target"]
                               and raw[col].dropna().index.max() < T - pd.DateOffset(months=3)
                               and any(k in f for k in keys for f in used)})
        warn = []
        if (pd.Timestamp.today() - T).days > 75:
            warn.append(f"Latest published price is {T.strftime('%b %Y')}. Refresh data/raw to forecast from today.")
        if stale_inputs:
            warn.append("These driver inputs are more than 3 months older than the forecast date and are treated as "
                        "missing, so the driver models are running blind on them: " + "; ".join(stale_inputs) +
                        ". Refresh data/raw (see SETUP.md).")
            note += " Caution: some driver inputs are stale (see warning)."
        res[m] = {"origin": T.strftime("%b %Y"), "spot": round(p0, 1), "unit": unit,
                  "display": CFG["materials"][m]["display"], "horizons": hz,
                  "shap_drivers_h3": drivers, "note": note, "landed": landed,
                  "stale_warning": " ".join(warn), "stale_inputs": stale_inputs}
    (OUT / "forecast_now.json").write_text(json.dumps(res, indent=1))
    for m in res:
        print(f"\n{m.upper()}  ({res[m]['origin']})  {res[m]['stale_warning']}")
        print(res[m]["note"])
    return res


if __name__ == "__main__":
    run()
