"""Which numbers in the finals deck must be replaced after a re-run?

Tables, charts and some sentences are filled from outputs/ automatically. The numbers below
are written into slide text, so they do NOT update themselves. This script recomputes each one
from the current outputs and checks whether the deck still shows it.

    OK      the deck shows the current value
    UPDATE  the outputs changed: edit the slide text (and the Q&A doc) to the new value

Policy numbers (duty rates, the PVC floor, anti-dumping rates and dates) are not pipeline
outputs; they are listed at the end to re-check against their sources before presenting.
"""
import json
import math
import sys
from pathlib import Path

import numpy as np
import pandas as pd
from pptx import Presentation

SB = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(SB))
SC = SB / "outputs" / "scorecards"
DECK = SB / "outputs" / "SmartBuy_Finals_Deck.pptx"
NAME = {1: "1 Opening", 2: "2 Problem", 3: "3 Solution", 4: "4 Drivers", 5: "5 Tested", 6: "6 Results",
        7: "7 Models", 8: "8 Replay", 9: "9 Demo", 10: "10 Explain", 11: "11 Landed cost", 12: "12 Pilot",
        13: "13 Risks", 14: "14 Ask", 15: "A1", 16: "A2", 17: "A3"}
# old 17-slide order -> new order (old positions are how the checks below were written)
OLD2NEW = {1: 1, 2: 2, 3: 3, 4: 6, 5: 8, 6: 9, 7: 11, 8: 12, 9: 13, 10: 14, 11: 15, 12: 16, 13: 4, 14: 7, 15: 10, 16: 5, 17: 17}

prs = Presentation(str(DECK))
TEXT = {}
for i, s in enumerate(prs.slides, 1):
    parts = []
    for sh in s.shapes:
        if sh.has_text_frame:
            parts.append(sh.text_frame.text)
        if getattr(sh, "has_table", False) and sh.has_table:
            parts += [c.text for r in sh.table.rows for c in r.cells]
    TEXT[i] = " ".join(parts).replace("\u2212", "-")

sc = {m: pd.read_csv(SC / f"{m}_scorecard.csv") for m in ("aluminium", "pvc")}
bands = {m: pd.read_csv(SC / f"{m}_bands.csv") for m in ("aluminium", "pvc")}
regs = {m: pd.read_csv(SC / f"{m}_regimes.csv").set_index("regime") for m in ("aluminium", "pvc")}
drv = pd.read_csv(SB / "outputs" / "drivers" / "lead_lag_granger.csv")
RP = json.loads((SB / "outputs" / "replay_summary.json").read_text())


def head(m, h, w="development", model="gated_equal_weight"):
    s = sc[m]
    return s[(s.window == w) & (s.h == h) & (s.model == model)].iloc[0]


def d(m, x):
    return drv[(drv.material == m) & (drv.driver == x)].iloc[0]


def cov(m, w, h, b="conf"):
    g = bands[m]
    return g[(g.window == w) & (g.h == h) & (g.band == b)].coverage_pct.iloc[0]


p1, p2, p3, a3 = head("pvc", 1), head("pvc", 2), head("pvc", 3), head("aluminium", 3)
rv, ra = RP["pvc"]["development"], RP["aluminium"]["development"]
dev_cov = [cov(m, "development", h) for m in ("aluminium", "pvc") for h in range(1, 7)]
gauss_gain = max(cov(m, "development", h) - cov(m, "development", h, "gauss") for m in ("aluminium", "pvc") for h in range(1, 7))
shock_cov = [regs[m].loc[r].band_coverage_pct for m in ("aluminium", "pvc") for r in ("covid", "spike")]
ho3 = head("pvc", 3, "holdout")
ho_n = sc["pvc"][(sc["pvc"].window == "holdout") & (sc["pvc"].model == "gated_equal_weight")].n

from src.sb.data import raw_panel  # noqa: E402
raw = raw_panel()
fx_s = raw.usd_inr.dropna()
fx = fx_s.iloc[-1]
lp = np.log(raw[["aluminium", "ppi_plastic_resins"]].dropna(how="all"))
both = pd.concat([lp.diff(), np.log(raw.usd_inr).diff()], axis=1)
both = both[(both.index >= "2010-01-01") & (both.index <= "2024-12-01")]
def fx_share(col):
    x = both[[col, "usd_inr"]].dropna()
    return 100 * (x.usd_inr.var() + x.cov().iloc[0, 1]) / x.sum(axis=1).var()
cif = 766.0
duty = cif * 0.075 * (1 + 0.075) * 1.10
ec = {m: pd.read_csv(SC / f"{m}_error_corr_h3.csv", index_col=0) for m in ("aluminium", "pvc")}
ecm = {m: ec[m].values[np.triu_indices_from(ec[m].values, 1)].mean() for m in ec}

f1 = lambda v: f"{v:+.1f}%"
CHECKS = [
    # (slides, what it is, text the deck must contain)
    ([1], "PVC 1-month skill", f1(p1.skill_pct)),
    ([1], "PVC 1-month DM p", f"p = {p1.dm_p_one_sided:.4f}"),
    ([2], "PVC 1 / 2-month skill", f"{f1(p1.skill_pct)} / {f1(p2.skill_pct)}"),
    ([2], "Aluminium 3-month skill", f"({f1(a3.skill_pct)}, n.s.)"),
    ([1], "PVC replay saving, rupees", f"₹{rv['net_saving_after_carry_pct']:.2f} Cr"),
    ([2], "PVC replay net saving", f"PVC {rv['net_saving_after_carry_pct']:+.2f}% net"),
    ([1, 2], "PVC timing permutation p", f"p = {rv['permutation_p_value']:.3f}"),
    ([1, 2, 9], "Backtest length (months)", f"{rv['months']} months"),
    ([1, 17], "Calibrated band coverage range", f"{math.floor(min(dev_cov))}–{math.floor(max(dev_cov) + .5)}%"),
    ([9, 16, 17], "Band coverage in shocks", f"{min(shock_cov):.0f}–{max(shock_cov):.0f}%"),
    ([17], "Largest calibration gain (points)", f"up to {gauss_gain:.0f} points"),
    ([4], "PVC holdout 3-month skill", f"({ho3.skill_pct:+.1f}%)"),
    ([4], "PVC holdout origins", f"({ho_n.min()}–{ho_n.max()} origins)"),
    ([7, 9], "FX share of Al monthly rupee variance", f"~{fx_share('aluminium'):.0f}%"),
    ([7, 9], "FX share of PVC monthly rupee variance", f"~{fx_share('ppi_plastic_resins'):.0f}%"),
    ([7], "Latest USD/INR used in worked example", f"₹{fx:.2f}/$"),
    ([7], "Worked example, landed ₹/kg", f"₹{(cif + duty) * fx / 1000:.1f}/kg"),
    ([7], "Worked example, CIF ₹/kg", f"₹{cif * fx / 1000:.1f}/kg CIF"),
    ([13], "Copper–aluminium same-month correlation", f"copper ρ = {d('aluminium', 'copper').best_rho:+.2f}"),
    ([13], "Zinc–aluminium correlation", f"zinc {d('aluminium', 'zinc').best_rho:+.2f}"),
    ([13], "China CLI lead, aluminium", f"ρ = {d('aluminium', 'cli_china').best_rho:+.2f} (Al)"),
    ([13], "China CLI lead, PVC", f"{d('pvc', 'cli_china').best_rho:+.2f} (PVC)"),
    ([13], "Brent lead on PVC", f"ρ = {d('pvc', 'brent').best_rho:+.2f}"),
    ([13], "Energy index lead on PVC", f"energy index ({d('pvc', 'wb_energy').best_rho:+.2f})"),
    ([15], "Mean member error correlation, PVC / Al", f"{ecm['pvc']:.2f} (aluminium {ecm['aluminium']:.2f})"),
]

rows, todo = [], 0
for slides, what, needle in CHECKS:
    slides = sorted(OLD2NEW[x] for x in slides)
    hay = " ".join(TEXT[s] for s in slides).replace("\u2212", "-")
    ok = needle.replace("\u2212", "-") in hay
    todo += not ok
    rows.append((", ".join(NAME[s] for s in slides), what, needle, "OK" if ok else "UPDATE"))

w = max(len(r[1]) for r in rows)
print(f"\nDeck: {DECK.name}   data: aluminium to {raw.aluminium.dropna().index.max():%b %Y}, "
      f"PVC to {raw.ppi_plastic_resins.dropna().index.max():%b %Y}, USD/INR to {fx_s.index[-1]:%b %Y}\n")
print(f"{'STATUS':7} {'SLIDE(S)':14} {'WHAT':{w}}  CURRENT VALUE FROM OUTPUTS")
for where, what, needle, st in rows:
    print(f"{st:7} {where:14} {what:{w}}  {needle}")
print(f"\n{todo} item(s) to update." if todo else "\nAll pipeline numbers in the deck match the outputs.")
print("""
ALWAYS RE-CHECK BY HAND (not pipeline outputs; verify at the source before presenting):
  Slide 11, 13    BCD 7.5%, AIDC 7.5% of BCD, SWS 10%  -> 8.87% of CIF     ICEGATE (also check PVC 39041020: 7.5% vs 10%)
  Slide 11, 13    S-PVC minimum import price $766/t CIF, ends ~late Jan 2027   DGFT Notification 25/2026-27
  Slide 11, 13    Foil ADD China $479-721/t, in force to 15 Dec 2026           CBIC Customs (ADD) notifications / DGTR
  Slide 13        S-PVC ADD recommendation (Aug 2025), CVD probe (Mar 2026)     DGTR
  Slide 2         Aluminium $1,450 -> $3,985/t (2.7x); resin +62%, ~40% given back   change only if you change the text
  Slide 12, 14    Pilot dates (Nov 2026 - Feb 2027) and ~25 hours of ACG time   your plan, not data
""")
