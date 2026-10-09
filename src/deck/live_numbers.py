"""Numbers written into slide text, recomputed from the current outputs.

TEMPLATE maps the value as it was written when the slide text was drafted -> the value now.
edit_finals.py applies it to every slide and speaker note, so the deck text always matches
the outputs you just produced. deck_numbers.py then double-checks the result.
"""
import json
import math
import sys
from pathlib import Path

import numpy as np
import pandas as pd

SB = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(SB))
SC = SB / "outputs" / "scorecards"


def compute():
    sc = {m: pd.read_csv(SC / f"{m}_scorecard.csv") for m in ("aluminium", "pvc")}
    bands = {m: pd.read_csv(SC / f"{m}_bands.csv") for m in ("aluminium", "pvc")}
    regs = {m: pd.read_csv(SC / f"{m}_regimes.csv").set_index("regime") for m in ("aluminium", "pvc")}
    drv = pd.read_csv(SB / "outputs" / "drivers" / "lead_lag_granger.csv")
    RP = json.loads((SB / "outputs" / "replay_summary.json").read_text())

    def head(m, h, w="development"):
        s = sc[m]
        return s[(s.window == w) & (s.h == h) & (s.model == "gated_equal_weight")].iloc[0]

    def cov(m, w, h, b="conf"):
        g = bands[m]
        return g[(g.window == w) & (g.h == h) & (g.band == b)].coverage_pct.iloc[0]

    def rho(m, x):
        return drv[(drv.material == m) & (drv.driver == x)].iloc[0].best_rho

    p1, p2, a3, ho3 = head("pvc", 1), head("pvc", 2), head("aluminium", 3), head("pvc", 3, "holdout")
    rv = RP["pvc"]["development"]
    dev = [cov(m, "development", h) for m in ("aluminium", "pvc") for h in range(1, 7)]
    gain = max(cov(m, "development", h) - cov(m, "development", h, "gauss") for m in ("aluminium", "pvc") for h in range(1, 7))
    shock = [regs[m].loc[r].band_coverage_pct for m in ("aluminium", "pvc") for r in ("covid", "spike")]
    ho_n = sc["pvc"][(sc["pvc"].window == "holdout") & (sc["pvc"].model == "gated_equal_weight")].n
    ec = {m: pd.read_csv(SC / f"{m}_error_corr_h3.csv", index_col=0).values for m in ("aluminium", "pvc")}
    ecm = {m: v[np.triu_indices_from(v, 1)].mean() for m, v in ec.items()}

    from src.sb.data import raw_panel
    raw = raw_panel()
    fxs = raw.usd_inr.dropna(); fx = fxs.iloc[-1]
    both = pd.concat([np.log(raw[["aluminium", "ppi_plastic_resins"]]).diff(), np.log(raw.usd_inr).diff()], axis=1)
    both = both[(both.index >= "2010-01-01") & (both.index <= "2024-12-01")]
    def share(c):
        x = both[[c, "usd_inr"]].dropna()
        return 100 * (x.usd_inr.var() + x.cov().iloc[0, 1]) / x.sum(axis=1).var()
    cif = 766.0; duty = cif * 0.075 * 1.075 * 1.10
    sa, sp = share("aluminium"), share("ppi_plastic_resins")
    f1 = lambda v: f"{v:+.1f}%"
    return {  # template literal (as drafted) : current value
        "+20.7%": f1(p1.skill_pct),
        "p = 0.0004": f"p = {p1.dm_p_one_sided:.4f}",
        "+15.9%": f1(p2.skill_pct),
        "(+3.7%, n.s.)": f"({f1(a3.skill_pct)}, n.s.)",
        "0.45 Cr": f"{rv['net_saving_after_carry_pct']:.2f} Cr",
        "+0.45%": f"{rv['net_saving_after_carry_pct']:+.2f}%",
        "p = 0.002)": f"p = {rv['permutation_p_value']:.3f})",
        "(p = 0.002": f"(p = {rv['permutation_p_value']:.3f}",
        "64–78%": f"{math.floor(min(dev))}–{math.floor(max(dev) + .5)}%",
        "42–67%": f"{min(shock):.0f}–{max(shock):.0f}%",
        "up to 13 points": f"up to {gain:.0f} points",
        "71–81%": f"{min(cov('pvc', 'holdout', h) for h in range(1, 7)):.0f}–{max(cov('pvc', 'holdout', h) for h in range(1, 7)):.0f}%",
        "(−13.7%)": f"({ho3.skill_pct:+.1f}%)".replace("-", "−"),
        "(14–19 origins)": f"({ho_n.min()}–{ho_n.max()} origins)",
        "Al 1%, PVC 36%": f"Al {sa:.0f}%, PVC {sp:.0f}%",
        "~1% of": f"~{sa:.0f}% of",
        "~36%": f"~{sp:.0f}%",
        "₹95.45/$": f"₹{fx:.2f}/$",
        "₹79.6/kg": f"₹{(cif + duty) * fx / 1000:.1f}/kg",
        "₹73.1/kg": f"₹{cif * fx / 1000:.1f}/kg",
        "copper ρ = +0.68": f"copper ρ = {rho('aluminium', 'copper'):+.2f}",
        "zinc +0.63": f"zinc {rho('aluminium', 'zinc'):+.2f}",
        "+0.20 (Al)": f"{rho('aluminium', 'cli_china'):+.2f} (Al)",
        "+0.18 (PVC)": f"{rho('pvc', 'cli_china'):+.2f} (PVC)",
        "ρ = +0.41, Granger": f"ρ = {rho('pvc', 'brent'):+.2f}, Granger",
        "energy index (+0.44)": f"energy index ({rho('pvc', 'wb_energy'):+.2f})",
        "0.84 (aluminium 0.87)": f"{ecm['pvc']:.2f} (aluminium {ecm['aluminium']:.2f})",
    }


if __name__ == "__main__":
    for k, v in compute().items():
        print(f"{k:28} -> {v}{'' if k == v else '   (changed)'}")
