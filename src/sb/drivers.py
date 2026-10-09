"""
Driver study v2 (lead-lag econometrics), real series only.

For each candidate driver X and material price P, on monthly log-returns:
  * cross-correlation corr(dX[t-k], dP[t]) for leads k = 0..6
  * ADF test that both return series are stationary
  * Granger causality at a FIXED lag of 3 months (no lag shopping)
  * Benjamini-Hochberg FDR across every Granger test for both materials

Verdict rule (fixed before running):
  SUPPORTED      Granger FDR q < 0.10 AND the largest |rho| falls inside the hypothesised lead window
  PARTIAL        exactly one of the two
  NOT SUPPORTED  neither
  NOT TESTABLE   no free, real data exists for the indicator (we say so instead of simulating it)

Caveat that applies to every row: these are in-sample associations over
2000-2024. They justify which drivers to offer the models; whether a driver
actually improves FORECASTS is answered only by the walk-forward backtest.
"""
from __future__ import annotations

import json
import warnings
warnings.filterwarnings("ignore")

import numpy as np
import pandas as pd
from statsmodels.stats.multitest import multipletests
from statsmodels.tsa.stattools import adfuller, grangercausalitytests

from .data import BASE, CFG, SERIES, raw_panel

OUT = BASE / "outputs" / "drivers"
OUT.mkdir(parents=True, exist_ok=True)
DC = CFG["drivers"]

DRIVERS = {
    "aluminium": ["coal_aus", "gas_eu", "wb_energy", "brent", "copper", "zinc", "cli_china",
                  "indpro", "ip_aluminium", "usd_inr", "gpr", "epu", "freight_tsi"],
    "pvc": ["brent", "ppi_organic_chem", "gas_us", "wb_energy", "cli_china", "indpro",
            "ip_resin", "usd_inr", "gpr", "epu", "freight_tsi"],
}


def study():
    raw = raw_panel()
    raw = raw[(raw.index >= "2000-01-01") & (raw.index <= DC["sample_end"])]
    rows = []
    for m, drivers in DRIVERS.items():
        tgt = CFG["materials"][m]["target"]
        dp = np.log(raw[tgt]).diff()
        for x in drivers:
            dx = np.log(raw[x]).diff() if (raw[x] > 0).all() else raw[x].diff()
            pair = pd.concat([dp.rename("p"), dx.rename("x")], axis=1).dropna()
            corrs = {k: pair.p.corr(pair.x.shift(k)) for k in range(DC["max_lead"] + 1)}
            best = max(corrs, key=lambda k: abs(corrs[k]) if pd.notna(corrs[k]) else -1)
            adf_p = max(adfuller(pair.p)[1], adfuller(pair.x)[1])
            g = grangercausalitytests(pair[["p", "x"]], maxlag=[DC["granger_lag"]])
            gp = g[DC["granger_lag"]][0]["ssr_ftest"][1]
            rows.append({"material": m, "driver": x, "label": SERIES[x][1], "source": SERIES[x][2],
                         "n": len(pair), **{f"rho_lead{k}": round(v, 3) for k, v in corrs.items()},
                         "best_lead": best, "best_rho": round(corrs[best], 3),
                         "adf_p_max": round(adf_p, 4), "granger_p": gp})
    d = pd.DataFrame(rows)
    d["granger_q_fdr"] = multipletests(d.granger_p, method="fdr_bh")[1]
    d["granger_sig_fdr"] = d.granger_q_fdr < DC["fdr_q"]
    d["granger_p"] = d.granger_p.round(4)
    d["granger_q_fdr"] = d.granger_q_fdr.round(4)
    d.to_csv(OUT / "lead_lag_granger.csv", index=False)
    return d


def _verdict(row, lo, hi):
    a = bool(row.granger_sig_fdr)
    b = lo <= row.best_lead <= hi
    return "SUPPORTED" if (a and b) else ("PARTIAL" if (a or b) else "NOT SUPPORTED")


def hypotheses(d: pd.DataFrame) -> dict:
    g = lambda m, x: d[(d.material == m) & (d.driver == x)].iloc[0]
    ev = lambda r: (f"best lead {r.best_lead}m, rho={r.best_rho:+.2f}; "
                    f"Granger(3) p={r.granger_p:.3f}, FDR q={r.granger_q_fdr:.3f}")
    raw = raw_panel()
    raw = raw[(raw.index >= "2010-01-01") & (raw.index <= DC["sample_end"])]
    fx_share = {}
    for m in ("aluminium", "pvc"):
        usd = np.log(raw[CFG["materials"][m]["target"]]).diff()
        fx = np.log(raw.usd_inr).diff()
        both = pd.concat([usd, fx], axis=1).dropna()
        tot = both.sum(axis=1)
        fx_share[m] = float((both.iloc[:, 1].var() + both.cov().iloc[0, 1]) / tot.var())

    coal, cu = g("aluminium", "coal_aus"), g("aluminium", "copper")
    mono, br = g("pvc", "ppi_organic_chem"), g("pvc", "brent")
    cli_a, cli_p = g("aluminium", "cli_china"), g("pvc", "cli_china")
    ip_a, ip_p = g("aluminium", "indpro"), g("pvc", "indpro")
    fx_a, fx_p = g("aluminium", "usd_inr"), g("pvc", "usd_inr")

    H = {
        "H1": {"hypothesis": "China coal and LME stocks lead aluminium by 1-3 months.",
               "coal (Australian thermal, proxy)": ev(coal) + f" -> {_verdict(coal, 1, 3)}",
               "LME stocks": "NOT TESTABLE: no free historical LME stock series. The Round 2 'stocks' series was computed from the aluminium price itself.",
               "verdict": _verdict(coal, 1, 3) + " (coal only; stocks not testable)"},
        "H2": {"hypothesis": "Ethylene/VCM and China export offers lead PVC by 1-2 months.",
               "monomers (US PPI basic organic chemicals, proxy)": ev(mono) + f" -> {_verdict(mono, 1, 2)}",
               "Brent crude": ev(br) + f" -> {_verdict(br, 1, 2)}",
               "China export offers": "NOT TESTABLE with free data. The Round 2 'exports' series was the PVC price lagged two months.",
               "verdict": ("PARTIAL" if "SUPPORTED" in (_verdict(mono, 1, 2), _verdict(br, 1, 2)) and _verdict(mono, 1, 2) != _verdict(br, 1, 2)
                           else _verdict(mono, 1, 2))
                          + f" (monomer proxy: {_verdict(mono, 1, 2)}; Brent: {_verdict(br, 1, 2)}; exports not testable)"},
        "H3": {"hypothesis": "Manufacturing activity leads both materials by 0-2 months.",
               "aluminium vs OECD China CLI": ev(cli_a) + f" -> {_verdict(cli_a, 0, 2)}",
               "aluminium vs US industrial production": ev(ip_a) + f" -> {_verdict(ip_a, 0, 2)}",
               "PVC vs OECD China CLI": ev(cli_p) + f" -> {_verdict(cli_p, 0, 2)}",
               "PVC vs US industrial production": ev(ip_p) + f" -> {_verdict(ip_p, 0, 2)}",
               "note": "PMIs are paywalled; the OECD China CLI and US industrial production are free activity proxies.",
               "verdict": "see per-row verdicts"},
        "H4": {"hypothesis": "USD/INR moves the landed (rupee) price in the same month.",
               "share of monthly rupee-price variance due to USD/INR, aluminium": f"{100 * fx_share['aluminium']:.1f}%",
               "share of monthly rupee-price variance due to USD/INR, PVC proxy": f"{100 * fx_share['pvc']:.1f}%",
               "does USD/INR forecast the US$ price? aluminium": ev(fx_a),
               "does USD/INR forecast the US$ price? PVC": ev(fx_p),
               "verdict": (f"PARTIAL. Pass-through is one-for-one by construction (rupee price = US$ price x USD/INR), "
                           f"but USD/INR explains only {100 * fx_share['aluminium']:.0f}% of aluminium's monthly rupee-price variance "
                           f"(the US$ price dominates) and {100 * fx_share['pvc']:.0f}% for the less volatile PVC index. "
                           f"Handle FX in the landed-cost overlay; as a predictor of the US$ price it is "
                           f"{'significant' if fx_p.granger_sig_fdr else 'not significant'} for PVC and "
                           f"{'significant' if fx_a.granger_sig_fdr else 'not significant'} for aluminium.")},
        "extra": {"copper -> aluminium": ev(cu)},
    }
    (OUT / "hypotheses.json").write_text(json.dumps(H, indent=1))
    return H


if __name__ == "__main__":
    d = study()
    pd.set_option("display.width", 250)
    print(d[["material", "driver", "n", "best_lead", "best_rho", "granger_p", "granger_q_fdr", "granger_sig_fdr", "adf_p_max"]].to_string(index=False))
    print(json.dumps(hypotheses(d), indent=1))
