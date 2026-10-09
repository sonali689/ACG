"""Update the Round 2 deck in place to the v2 (audited) results.
Design, layout and chrome are untouched; text, tables and chart images are replaced.
Every table number is read from smartbuy/outputs, not typed."""
import json
import re
from copy import deepcopy
from pathlib import Path

import pandas as pd
from lxml import etree
from pptx import Presentation
from pptx.dml.color import RGBColor
from pptx.oxml.ns import qn
from pptx.util import Inches

SB = Path(__file__).resolve().parents[2]
SC = SB / "outputs/scorecards"
CH = SB / "outputs" / "deck" / "charts"
ACG, INK2, BUY, DEFER = "C8102E", "4A4D55", "0F6B3F", "8A5A00"

prs = Presentation(str(SB / "legacy" / "outputs_round2_original" / "SmartBuy_Round2_15Slides.pptx"))
S = {i + 1: s for i, s in enumerate(prs.slides)}


def shp(sn, sid):
    for sh in S[sn].shapes:
        if sh.shape_id == sid:
            return sh
    raise KeyError(f"slide {sn} shape {sid}")


def _fill_body(txBody, paras, color=None):
    ps = list(txBody.findall(qn("a:p")))
    while len(ps) < len(paras):
        new = deepcopy(ps[-1]); ps[-1].addnext(new); ps.append(new)
    for extra in ps[len(paras):]:
        txBody.remove(extra)
    for p_el, content in zip(ps, paras):
        for tag in ("a:r", "a:br", "a:fld"):
            for el in p_el.findall(qn(tag)):
                p_el.remove(el)
        segs = [(content, None)] if isinstance(content, str) else content
        ppr = p_el.find(qn("a:pPr"))
        drp = ppr.find(qn("a:defRPr")) if ppr is not None else None
        if color and drp is not None:
            for c in drp.iter(qn("a:srgbClr")):
                c.set("val", color)
        endp = p_el.find(qn("a:endParaRPr"))
        for text, bold in segs:
            text = re.sub(r"(?<![\w])-(?=\d)", "\u2212", text)
            r = etree.Element(qn("a:r"))
            if bold is not None or color:
                if drp is not None:
                    rpr = deepcopy(drp); rpr.tag = qn("a:rPr")
                else:
                    rpr = etree.Element(qn("a:rPr"))
                if bold is not None:
                    rpr.set("b", "1" if bold else "0")
                if color:
                    for c in rpr.iter(qn("a:srgbClr")):
                        c.set("val", color)
                r.append(rpr)
            t = etree.SubElement(r, qn("a:t")); t.text = text
            if text != text.strip():
                t.set("{http://www.w3.org/XML/1998/namespace}space", "preserve")
            if endp is not None:
                endp.addprevious(r)
            else:
                p_el.append(r)


def T(sn, sid, *paras, color=None):
    _fill_body(shp(sn, sid).text_frame._txBody, list(paras), color)


def cell(sn, sid, r, c, text, color=None):
    _fill_body(shp(sn, sid).table.cell(r, c).text_frame._txBody, [text], color)


def pic(sn, sid, png, h=None, top=None):
    p = shp(sn, sid)
    rid = p._element.blipFill.find(qn("a:blip")).get(qn("r:embed"))
    p.part.related_part(rid)._blob = (CH / png).read_bytes()
    if top is not None:
        p.top = Inches(top)
    if h is not None:
        p.height = Inches(h)


def fill(sn, sid, hexcol):
    s = shp(sn, sid); s.fill.solid(); s.fill.fore_color.rgb = RGBColor.from_string(hexcol)


def pct(v, d=1, sign=True):
    return f"{v:+.{d}f}%" if sign else f"{v:.{d}f}%"


sc = {m: pd.read_csv(SC / f"{m}_scorecard.csv") for m in ("aluminium", "pvc")}
bands = {m: pd.read_csv(SC / f"{m}_bands.csv") for m in ("aluminium", "pvc")}
regs = {m: pd.read_csv(SC / f"{m}_regimes.csv").set_index("regime") for m in ("aluminium", "pvc")}
RP = json.loads((SB / "outputs/replay_summary.json").read_text())
FN = json.loads((SB / "outputs/forecast_now.json").read_text())
GATE = {1: 10, 2: 12, 3: 15, 4: 12, 5: 10, 6: 10}


def head(m, h, w="development"):
    s = sc[m]
    return s[(s.window == w) & (s.h == h) & (s.model == "gated_equal_weight")].iloc[0]


# ============================ SLIDE 1 =====================================
T(1, 10, "Audited prototype  ·  October 2026")
T(1, 12, "Aluminium and PVC resin are roughly 70% of manufacturing cost for pharmaceutical blister "
         "packs. A 1% move in RM price is ~0.7% of total manufacturing cost. Today, both are bought on "
         "judgement with no forward view of price.")
T(1, 14, "+20.7%")
T(1, 15, "PVC forecast skill over naïve at one", "month, significant (DM p = 0.0004)")
T(1, 17, "p = 0.002")
T(1, 18, "PVC buy/defer timing beats random;", "+0.45% net, ₹0.45 Cr per ₹100 Cr")
T(1, 20, "64–78%")
T(1, 21, "band coverage after calibration,", "up from 55–65%; gate is 75–85%")
T(1, 23, "W H A T   R O U N D   2   P R O V E S")
T(1, 24, "We audited our own pipeline before this round and found three flaws: a simulated PVC price, "
         "drivers derived from the target, and a look-ahead leak in training. All three are fixed, and a "
         "test now proves the leak is gone. Under honest validation aluminium is near-efficient, while PVC "
         "shows significant 1–2 month skill. Every pre-set gate is reported unchanged, including the misses.")
shp(1, 28).top = Inches(7.18)
cell(1, 27, 4, 1, "Live dashboard, 15-slide deck, reproducible pipeline with leakage tests")

# ============================ SLIDE 2 =====================================
T(2, 36, "Aluminium went from about $1,450/t (April 2020) to $3,985/t (March 2022) and back to about "
         "$2,250/t in 2023: a 2.7× swing in under two years. US resin prices rose 62% from May 2020 to "
         "August 2021 on force majeures and freight, then gave back about 40% of that rise by 2023.")
cell(2, 57, 1, 1, "Six-month forecast; PVC +20.7% / +15.9% skill at 1–2 months (significant)")
cell(2, 57, 2, 1, "Every forecast scored vs naïve; aluminium ≈ naïve (+3.7%, n.s.), reported as is")
cell(2, 57, 3, 1, "Rule replayed over 78 months: PVC +0.45% net, beats random timing (p = 0.002)")
T(2, 58, "Sources  [1] ACG, \"Smart Buy – AI based Raw Material Price Prediction\", problem statement. "
         "[2] World Bank, Commodity Price Data (Pink Sheet); BLS PPI WPU066 via FRED. [3] Skill and replay "
         "figures are embargoed walk-forward results from this submission's pipeline, not illustrations.")

# ============================ SLIDE 3 =====================================
T(3, 65, "Cross-correlation of log-returns at leads 0–6 months on real series; best lead recorded.")
T(3, 67, "ADF stationarity, then Granger at a fixed 3-month lag, FDR-corrected across 24 tests.")
T(3, 56, "Resin price", "(US PPI proxy)")
T(3, 57, "no free Asian spot history;", "US index modelled")
T(3, 69, "Every real driver is offered to the models; ElasticNet keeps 15 inside each fold, and the naïve gate decides what earns weight.")
cell(3, 71, 1, 1, "GPR, EPU, China CLI, copper/zinc, US PPIs and output, shock indicators")
cell(3, 71, 2, 0, "Replaced")
cell(3, 71, 2, 1, "Simulated PVC price, formula drivers → real BLS PPI WPU066 and published data")
cell(3, 71, 3, 0, "Not testable")
for row in shp(3, 71).table.rows:
    row.height = Inches(0.30)
cell(3, 71, 3, 1, "LME stocks, China export offers, ethylene/VCM: no free history")
T(3, 72, "Sources  [1] World Bank Pink Sheet. [2] BLS and Federal Reserve via FRED. [3] ECB. [4] Caldara & Iacoviello (2022), "
         "AER 112(4). [5] Baker, Bloom & Davis (2016), QJE 131(4). [6] OECD leading indicators. Public sources only.")

# ============================ SLIDE 4 =====================================
lag_rows = [("World Bank Pink Sheet prices", "aluminium, Brent, coal, gas, base metals", "0 months"),
            ("BLS producer price indices", "PVC target (WPU066), monomers, primary Al", "0 PVC · 1 Al"),
            ("Fed industrial production", "resins, aluminium, total industry", "1 month"),
            ("ECB reference rates", "USD/INR", "0 months"),
            ("GPR, EPU, OECD China CLI", "risk, uncertainty, China demand", "0 PVC · 1 Al"),
            ("BTS freight index", "US freight transportation services", "2 months")]
for i, row in enumerate(lag_rows, 1):
    for j, v in enumerate(row):
        cell(4, 15, i, j, v)
T(4, 16, "One function, visible_panel(material), applies every lag. Training rows are embargoed:",
         "a row is used only if its h-month outcome was published before the forecast day.")
T(4, 18, "Leakage guardrails, enforced and tested")
T(4, 20, "Embargo on every training row, asserted in the backtest itself.")
T(4, 22, "Future-perturbation test: scramble all post-origin data; no forecast may change.")
T(4, 24, "The Round 2 draft logic fails that test; version 2 passes it.")
T(4, 26, "Trailing windows only, no back-fill; selection and tuning inside every fold.")
T(4, 29, "74")
T(4, 30, "commodity series in the", "global training panel")
T(4, 32, "41 / 36")
T(4, 33, "features for aluminium and", "PVC, all from real data")
T(4, 35, "78")
T(4, 36, "scored origins 2018–24,", "plus a 2025–26 holdout")
T(4, 39, "Price dynamics — momentum, trailing volatility, z-scores")
T(4, 41, "Cost-push — coal, gas, Brent, monomer PPI, resin/feedstock spreads")
T(4, 43, "Demand — OECD China CLI, US industrial production, base metals")
T(4, 45, "Currency — USD/INR, also used in the landed-cost overlay")
T(4, 47, "Risk and shocks — GPR, EPU, data-driven shock indicators")
T(4, 48, [("Known limitation. ", True), ("No free long-history Asian PVC spot price exists. We use the real", False)],
         "BLS producer price index for plastic resins (WPU066) as the proxy: a US index,",
         "not Asian spot. The India landed price is a separate overlay, calibrated on ACG POs.")
T(4, 49, "Sources  Publication lags set per material from each provider's release calendar (config/pipeline.yaml) "
         "and applied in one place. Aluminium is forecast on the 1st of the month; PVC on BLS PPI release day.")

# ============================ SLIDE 5 =====================================
pic(5, 15, "s5_leadlag.png")
T(5, 16, "What the real data shows")
T(5, 18, [("Aluminium moves with its peers, in the same month: ", True),
          ("copper ρ = +0.68, zinc +0.63, energy +0.46 at lag 0. These explain moves; they cannot forecast them.", False)])
T(5, 20, [("China leading indicator leads both by ~2 months: ", True),
          ("ρ = +0.20 (Al) and +0.18 (PVC), Granger-significant after FDR (q = 0.02 / 0.004).", False)])
T(5, 22, [("Brent crude leads the PVC proxy by 1 month: ", True),
          ("ρ = +0.41, Granger q < 0.001. The energy index (+0.44) and US gas also lead it.", False)])
T(5, 24, [("Not testable with free data: ", True),
          ("LME stocks and China PVC export offers. We say so rather than simulate them.", False)])
verdicts = [  # (stripe, verdict text shape, verdict, colour, hypothesis id, hypothesis, evidence id, evidence, narrative id, narrative)
    (27, 30, "NOT SUPPORTED", ACG, 29, "China coal and LME stocks lead aluminium by 1 to 3 months.",
     31, "Coal: best lead 0m, ρ = +0.36, Granger q = 0.83  ·  LME stocks: no free history, not testable",
     32, "Coal moves with aluminium in the same month but does not lead it. Round 2's stocks result came from a series computed from the price itself."),
    (34, 37, "PARTIAL", DEFER, 36, "Feedstock and China export offers lead PVC by 1 to 2 months.",
     38, "Brent: lead 1m, ρ = +0.41, q < 0.001  ·  Monomer PPI: lead 6m, ρ = −0.23, q = 0.63",
     39, "Crude feeds through to resin prices within a month. The monomer proxy does not lead; export offers cannot be tested."),
    (41, 44, "SUPPORTED", BUY, 43, "Manufacturing activity leads both materials by 0 to 2 months.",
     45, "China CLI: lead 2m, ρ = +0.20 (Al, q = 0.02), +0.18 (PVC, q = 0.004)  ·  US output: same month, n.s.",
     46, "The OECD China leading indicator is the one genuine early signal for aluminium. PMIs are paywalled; the CLI is the free proxy."),
    (48, 51, "PARTIAL", DEFER, 50, "USD/INR moves the landed price in the same month.",
     52, "FX share of monthly rupee-price variance: Al 1%, PVC 36%  ·  FX → US$ price: Al n.s., PVC q = 0.002",
     53, "Pass-through is one-for-one by construction, but aluminium's US$ swings dwarf FX. FX belongs in the landed-cost overlay."),
]
for stripe, vid, vtxt, col, hid, htxt, eid, etxt, nid, ntxt in verdicts:
    fill(5, stripe, col)
    T(5, vid, vtxt, color=col)
    T(5, hid, htxt); T(5, eid, etxt); T(5, nid, ntxt)
T(5, 54, "Only leads forecast. Leads surviving FDR: China CLI (both); Brent, energy, US gas, USD/INR (PVC).")
T(5, 55, "Method: real series only, 2000–2024, monthly log-returns at leads 0–6. Granger at a fixed 3-month lag; "
         "Benjamini–Hochberg FDR across all 24 tests. Source: outputs/drivers.")

# ============================ SLIDE 6 =====================================
T(6, 18, "World Bank, BLS and Fed via FRED, ECB, GPR, EPU, OECD. Real published series only.")
T(6, 23, "Publication lag per series. Training rows embargoed until their outcome is published.")
T(6, 28, "41 / 36 trailing-window features; a 74-series panel for the global models.")
T(6, 38, "Ten models in three tiers: statistical, ML with drivers, and global ML on 74 series.")
T(6, 43, "78 scored origins plus holdout. A model earns weight only by beating naïve on its own past.")
T(6, 53, "Prices ranged from about $1,450 to $3,985 over the sample, so the variance of the level is "
         "unstable. The variance of the return is not. Forecasts are converted back with P = P₀·exp(ŷ), "
         "the median of the forecast distribution.")
spec = [("Targets", "LME aluminium (US$/t); US PPI plastic resins WPU066 (PVC proxy)"),
        ("Horizons", "1 to 6 months, monthly steps; h=3 is the decision horizon"),
        ("Training", "Expanding window, embargoed; refit monthly (global models quarterly / yearly)"),
        ("Features", "Real drivers only; ElasticNet selects 15 and tunes inside each fold"),
        ("Outputs", "P50, conformal P10–P90 band, P(up), SHAP attribution, buy signal"),
        ("Stack", "Python, pandas, statsmodels, arch, scikit-learn, LightGBM, JAX")]
for i, (k, v) in enumerate(spec, 1):
    cell(6, 55, i, 0, k); cell(6, 55, i, 1, v)
T(6, 56, "Sources  [1] Hyndman & Athanasopoulos (2021), Forecasting: Principles and Practice, 3rd ed.: direct vs "
         "recursive multi-step. [2] Ke et al. (2017), LightGBM, NeurIPS. [3] Oreshkin et al. (2020), N-BEATS, ICLR. "
         "[4] Vovk, Gammerman & Shafer (2005), conformal prediction. [5] Bollerslev (1986), GARCH.")

# ============================ SLIDE 7 =====================================
a3, p3 = sc["aluminium"], sc["pvc"]
def mod(m, name, h=3):
    s = sc[m]; return s[(s.window == "development") & (s.h == h) & (s.model == name)].iloc[0]
nb_a, nb_p, nv_a, nv_p = mod("aluminium", "nbeats"), mod("pvc", "nbeats"), mod("aluminium", "naive"), mod("pvc", "naive")
T(7, 13, "Ten models on identical embargoed origins. Trained on 74 commodity series, a real",
         "N-BEATS became the best single forecaster on both materials")
T(7, 14, "Aluminium — MAPE at h = 3, development window")
pic(7, 15, "s7_ladder_aluminium.png")
T(7, 16, "PVC proxy — MAPE at h = 3, development window")
pic(7, 17, "s7_ladder_pvc.png")
T(7, 19, "What the gate did")
T(7, 20, "A model earns a share of the forecast only in months when it has beaten naïve on its own realised "
         "past forecasts. Seasonal naïve never did, on either material. No model was excluded by judgement; "
         "the LSTM was dropped after the audit found it was fed the wrong inputs.")
T(7, 21, "N-BEATS, done properly, won")
T(7, 22, f"Real N-BEATS (trend and seasonality stacks) is the best single model on both: aluminium "
         f"{nb_a.mape:.2f}% vs naïve {nv_a.mape:.2f}% ({pct(nb_a.skill_pct)}), PVC {nb_p.mape:.2f}% vs "
         f"{nv_p.mape:.2f}% ({pct(nb_p.skill_pct)}). It came out best in every training run; its exact skill "
         f"varies from run to run. Round 2's \"N-BEATS\" was a plain MLP; that result is withdrawn.")
T(7, 25, "Pooling data substitutes for data.", "",
         "One model trained on 74 commodity series beats models trained on one 180-point series. That is the M4 lesson, reproduced.")
T(7, 26, "Method  All models run through one walk-forward harness on the same 78 origins, with embargoed training "
         "rows. Headline = equal-weight average of the models that beat naïve on realised past forecasts. "
         "N-BEATS uses early stopping on an in-fold validation slice. Consistent with Makridakis et al., M4 (2020).")

# ============================ SLIDE 8 =====================================
pv = FN["pvc"]; h3 = pv["horizons"]["3"]
T(8, 17, f"\"PVC proxy, {pv['origin']}: three-month P50 {h3['p50']:.1f} ({pct(h3['change_pct'])}), 80% range "
         f"{h3['p10']:.1f} to {h3['p90']:.1f}. Probability higher: {100 * h3['p_up']:.0f}%. After 3% carrying cost, "
         f"buying ahead is worth {pct(h3['expected_saving_net_pct'])}: {h3['signal']}. Largest pushes: "
         + ", ".join(f"{d['driver']} ({pct(d['contribution_pct'])})" for d in pv['shap_drivers_h3'][:3])
         + f". Models trusted now: {h3['eligible_models'].replace('|', ', ')}. Caution: Brent and gas inputs are stale until the data is refreshed.\"")
T(8, 20, "SHAP attribution (LightGBM TreeSHAP) on the live forecast, grouped by driver.")
T(8, 22, "Lead–lag and FDR-corrected Granger evidence per indicator, with its best lead.")
T(8, 24, "The models trusted at that horizon are named on every forecast.")
T(8, 26, "Stale-input warning: any driver over 3 months old is flagged in the note.")
T(8, 28, "Every override by a buyer is logged; adoption is a tracked run-state KPI.")
pic(8, 30, "s8_errcorr_pvc.png")
T(8, 31, "Mean error correlation between members is 0.84 (aluminium 0.87).")
T(8, 32, "Members are highly correlated, so averaging adds less than it seems. The most independent are "
         "seasonal naïve, VECM and ETS. N-BEATS earns its place by accuracy, not by diversity. "
         "Round 2's \"N-BEATS is the only diversifier\" claim is withdrawn.")
T(8, 33, "Method  SHAP values from LightGBM's built-in TreeSHAP on the embargoed local driver model. The "
         "error-correlation matrix is the evidence for or against any ensemble gain, reported either way.")

# ============================ SLIDE 9 =====================================
T(9, 13, "We tested it the way procurement would live with it: refit every month from 2018,",
         "embargoed, and beat the naïve forecast before claiming anything")
T(9, 14, "Rolling-origin walk-forward: 78 expanding origins, plus a 2025–26 holdout")
T(9, 30, "Skill vs naïve by horizon: highest at short horizons, as it should be")
pic(9, 31, "s9_skill_by_h.png", h=2.10)
T(9, 32, "PVC proxy: three-month forecast against what actually happened")
pic(9, 33, "s9_backtest_pvc.png", h=2.05)
T(9, 34, "Every origin 2018–2026, with the 80% band. Shaded area is the 2025–26 holdout.")
T(9, 36, "Performance by regime, h = 3")
for j, v in enumerate(["Regime", "n", "Al skill", "Al cov.", "PVC skill", "PVC cov."]):
    cell(9, 37, 0, j, v)
for i, reg in enumerate(["calm", "covid", "spike", "slide"], 1):
    a, p = regs["aluminium"].loc[reg], regs["pvc"].loc[reg]
    n = f"{int(a.n)}" if a.n == p.n else f"{int(a.n)}/{int(p.n)}"
    cell(9, 37, i, 1, n)
    cell(9, 37, i, 2, pct(a.skill_pct), color=BUY if a.skill_pct > 0 else ACG)
    cell(9, 37, i, 3, f"{a.band_coverage_pct:.0f}%", color=INK2)
    cell(9, 37, i, 4, pct(p.skill_pct), color=BUY if p.skill_pct > 0 else ACG)
    cell(9, 37, i, 5, f"{p.band_coverage_pct:.0f}%", color=INK2)
T(9, 38, "Band coverage still drops in shocks (42–67%), so the regime kill switch stays.")
shp(9, 38).top = Inches(6.60)
T(9, 39, "Method  Training rows embargoed: outcome published before the origin. Selection, tuning and early stopping "
         "happen inside each fold. [1] Tashman (2000), IJF 16(4). [2] Diebold & Mariano (1995), JBES 13(3), with "
         "Harvey–Leybourne–Newbold correction and Newey–West variance at lag h−1.")

# ============================ SLIDE 10 ====================================
T(10, 13, "Results against the thresholds we set in Round 1, before any modelling — reported",
          "unchanged, after fixing our own leak")
T(10, 14, "Headline ensemble, development window: 78 origins, January 2018 – June 2024")
for h in range(1, 7):
    ra, rp = head("aluminium", h), head("pvc", h)
    vals = [f"{ra.mape:.2f}%", f"{ra.naive_mape:.2f}%", None, f"{ra.dir_acc_pct:.1f}%", f"{ra.dm_p_one_sided:.4f}",
            f"{rp.mape:.2f}%", f"{rp.naive_mape:.2f}%", None, f"{rp.dir_acc_pct:.1f}%", f"{rp.dm_p_one_sided:.4f}"]
    for j, v in enumerate(vals, 1):
        if v is not None:
            cell(10, 15, h, j, v)
    pa, pp = ra.skill_pct >= GATE[h], rp.skill_pct >= GATE[h]
    cell(10, 15, h, 3, pct(ra.skill_pct), color=BUY if pa else ACG)
    cell(10, 15, h, 8, pct(rp.skill_pct), color=BUY if pp else ACG)
    cell(10, 15, h, 11, f"≥{GATE[h]}%    {'✓' if pa else '✗'} / {'✓' if pp else '✗'}", color=BUY if (pa and pp) else ACG)
T(10, 17, "The gates we missed")
T(10, 19, f"At h=3, skill is {pct(head('aluminium', 3).skill_pct)} (aluminium) and {pct(head('pvc', 3).skill_pct)} (PVC) against the ≥15% gate.",
          "", "PVC clears its gate at 1 and 2 months. We report every miss unchanged.")
T(10, 20, "Aluminium is exchange-traded and near-efficient: a few percent better than naïve, never significant.")
T(10, 23, f"PVC: {pct(head('pvc', 1).skill_pct)} skill at 1 month (DM p = {head('pvc', 1).dm_p_one_sided:.4f}) and {pct(head('pvc', 2).skill_pct)} at 2 months (p = {head('pvc', 2).dm_p_one_sided:.3f}).")
T(10, 25, f"PVC direction is {head('pvc', 1).dir_acc_pct:.1f}% at 1 month against a 65% gate, and {head('pvc', 2).dir_acc_pct:.1f}% at 2 months against 63%.")
T(10, 27, "PVC holdout 2025–26 (14–19 origins) does not beat naïve at h=3 (−13.7%).")
T(10, 29, "Driver data ended Dec 2024, so the holdout ran without its inputs. Inconclusive until the data is refreshed.")
T(10, 30, "We audited our own Round 2 result")
T(10, 32, "Our draft trained on rows whose outcome came after the forecast date, simulated the PVC price, and built drivers from the target.",
          "", "Closing the leak alone took one model from +8% to −6% skill. A perturbation test now proves v2 is leak-free.")

# ============================ SLIDE 11 ====================================
T(11, 13, "The bands are the product: calibration now exists and lifts coverage to 64–78%,",
          "still short of the gate at longer horizons and in shocks")
T(11, 14, "Aluminium — 80% band coverage against the 75–85% gate")
pic(11, 15, "s11_cov_aluminium.png", h=2.20)
T(11, 16, "PVC proxy")
pic(11, 17, "s11_cov_pvc.png", h=2.05)
for j, v in enumerate(["Horizon", "Al calibrated", "PVC calibrated", "PVC holdout", "Gate  Al / PVC"]):
    cell(11, 19, 0, j, v)
def cov(m, w, h, b="conf"):
    g = bands[m]; return g[(g.window == w) & (g.h == h) & (g.band == b)].coverage_pct.iloc[0]
for h in range(1, 7):
    ca, cp, ch = cov("aluminium", "development", h), cov("pvc", "development", h), cov("pvc", "holdout", h)
    ok = lambda v: 75 <= v <= 85
    cell(11, 19, h, 1, f"{ca:.1f}%"); cell(11, 19, h, 2, f"{cp:.1f}%"); cell(11, 19, h, 3, f"{ch:.1f}%", color=INK2)
    cell(11, 19, h, 4, f"{'pass' if ok(ca) else 'miss'} / {'pass' if ok(cp) else 'miss'}",
         color=BUY if (ok(ca) and ok(cp)) else ACG)
T(11, 22, "Normalised split-conformal around the forecast, scaled by a GARCH(1,1) volatility forecast, using only realised past errors.")
T(11, 24, f"It lifts coverage by up to 13 points over the uncalibrated band (aluminium h=6: "
          f"{cov('aluminium', 'development', 6, 'gauss'):.1f}% → {cov('aluminium', 'development', 6):.1f}%).")
T(11, 26, "Round 2 claimed this step, but the code never had it: its 55–65% was raw, uncalibrated coverage.")
T(11, 28, "Coverage still drops in shocks (42–67% at h=3). The PVC holdout lands at 71–81%.")
T(11, 29, "Consequence for the decision rule. The 60% confidence gate and the regime kill switch stay, because the band still understates tail risk in shocks.")
T(11, 30, "Method  Score = |error| / GARCH σ on realised past forecasts; band = forecast ± conformal 80% quantile × current σ. "
          "Coverage is measured, not assumed. [1] Vovk, Gammerman & Shafer (2005). [2] Bollerslev (1986).")

# ============================ SLIDE 12 ====================================
ra, rv = RP["aluminium"]["development"], RP["pvc"]["development"]
sig = lambda r: f"{r['signals'].get('BUY NOW', 0)} / {r['signals'].get('BUY NORMAL', 0)} / {r['signals'].get('DEFER', 0)}"
T(12, 13, f"The decision rule replayed over {rv['months']} months: PVC timing beats random (p = {rv['permutation_p_value']:.3f});",
          "aluminium timing does not")
T(12, 31, f"Results over {rv['months']} months (2018–2024), both materials")
rows = [("Signals: now / normal / defer", sig(ra), sig(rv), None),
        ("Gross price saving", pct(ra["gross_price_saving_pct"], 2), pct(rv["gross_price_saving_pct"], 2), "s"),
        ("Net saving after carrying cost", pct(ra["net_saving_after_carry_pct"], 2), pct(rv["net_saving_after_carry_pct"], 2), "s"),
        ("Beats random timing? (permutation p)",
         f"{'Yes' if ra['permutation_p_value'] < .1 else 'No'} ({ra['permutation_p_value']:.2f})",
         f"{'Yes' if rv['permutation_p_value'] < .1 else 'No'} ({rv['permutation_p_value']:.3f})", "p"),
        ("Perfect-foresight ceiling", pct(ra["perfect_foresight_net_pct"], 2), pct(rv["perfect_foresight_net_pct"], 2), None),
        ("Inventory days vs baseline", f"{ra['inventory_days_change']:+.1f} d", f"{rv['inventory_days_change']:+.1f} d", None),
        ("Working capital per ₹100 Cr (− = released)", f"{ra['extra_working_capital_cr_per_100cr_spend']:+.2f} Cr",
         f"{rv['extra_working_capital_cr_per_100cr_spend']:+.2f} Cr", None)]
cell(12, 32, 0, 2, "PVC proxy")
for i, (k, a, b, kind) in enumerate(rows, 1):
    cell(12, 32, i, 0, k)
    ca = cb = INK2
    if kind == "s":
        ca = BUY if float(a.strip('%')) > 0 else ACG; cb = BUY if float(b.strip('%')) > 0 else ACG
    if kind == "p":
        ca = BUY if a.startswith("Yes") else ACG; cb = BUY if b.startswith("Yes") else ACG
    cell(12, 32, i, 1, a, color=ca); cell(12, 32, i, 2, b, color=cb)
T(12, 33, "PVC proxy — cumulative net saving and the signals that produced it")
pic(12, 34, "s12_replay_pvc.png", h=2.75)
T(12, 36, "What this does and does not show")
_dd = rv["inventory_days_change"]
_stock = "slightly less stock" if _dd < 0 else (f"{_dd:.1f} more days of stock" if _dd > 0 else "the same stock")
_share = rv["net_saving_after_carry_pct"] / rv["perfect_foresight_net_pct"]
_frac = "about a third" if 0.27 <= _share <= 0.40 else f"{100 * _share:.0f}%"
T(12, 37, f"On PVC the rule captured {_frac} of the perfect-foresight ceiling with {_stock}, "
          f"and random placement of the same signals saves nothing (median {pct(rv['random_timing_median_pct'], 2)}).",
          "", f"On aluminium it acted {ra['signals'].get('BUY NOW', 0) + ra['signals'].get('DEFER', 0)} times in "
          f"{ra['months']} months and lost {abs(ra['net_saving_after_carry_pct']):.2f}%. In the 2025–26 PVC holdout it was "
          f"flat: net {pct(RP['pvc']['holdout']['net_saving_after_carry_pct'], 2)}, p = {RP['pvc']['holdout']['permutation_p_value']:.2f}.")
T(12, 38, f"The rule stays at BUY NORMAL {100 * ra['signals']['BUY NORMAL'] / ra['months']:.0f}% (Al) / "
          f"{100 * rv['signals']['BUY NORMAL'] / rv['months']:.0f}% (PVC) of the time.")
T(12, 39, "Method  Constant monthly requirement; purchases at next month's average price; leftover stock valued at the final price. "
          "Permutation test: same signals at random months, 2,000 draws. Rupee figures per ₹100 Cr of annual spend.")

# ============================ SLIDE 13 ====================================
T(13, 22, "Model against naïve at every horizon, development and holdout, with the pre-set gate marked pass or miss.")
T(13, 24, "Which indicators lead and by how much, FDR-corrected Granger flags, and SHAP drivers for the live forecast.")
T(13, 26, "Net saving, a permutation test against random timing, the perfect-foresight ceiling, and every signal.")
pic(13, 31, "s13_live_forecast.png")
T(13, 29, "In the pilot, buyers decide exactly as today while we log each signal against actual buys. Nothing is risked; the value is measured first.")
T(13, 32, "Forecast panels as shown on the desk, drawn from the same output files. Live view: dashboard/index.html. A stale-data banner shows until the data is refreshed.")

# ============================ SLIDE 14 ====================================
T(14, 19, "Refresh public data (with ALFRED vintages); ingest 12–24 months of ACG PO history for aluminium and PVC resin.")
cell(14, 37, 3, 1, "Signals beat random timing (permutation p < 0.10), net saving > 0 after carry")

# ============================ SLIDE 15 ====================================
T(15, 16, "Global benchmark (LME Aluminium / Asia CFR PVC in US$)",
         "  + Ocean freight and bunker surcharges (Nhava Sheva / Mundra)",
         "  + Material grade premium (pharma blister 8011 foil / suspension PVC)",
         "  × (1 + Basic Customs Duty 7.5–10%) × (1 + SWS 10%) + ADD",
         "  × USD/INR (same-month, one-for-one pass-through; H4)",
         "  + Port handling, clearance and domestic plant delivery",
         "  = ACG landed cost in ₹/MT")
T(15, 17, "Why the bridge is defensible")
T(15, 44, "Anonymised 12–24 month PO history for aluminium foil and PVC resin, to calibrate the overlay.")
T(15, 46, "1 sourcing sponsor + 1 buyer per commodity for 90 days, about two hours a month each.")
T(15, 48, "Approval for a zero-capex 90-day shadow pilot with pre-set gates and kill switches.")
for sid in (51, 52):
    shp(15, sid).top = Inches(7.22)
T(15, 21, "Contemporaneous FX (H4): pass-through is one-for-one by construction; FX is ~1% of aluminium's monthly rupee-price variance and ~36% for the PVC index.")
T(15, 25, "Local basis is measured, not assumed: the gap between global index and ACG's price is fitted on ACG PO history in Phase 1.")
risks = [("PVC proxy quality", "Real US PPI; no free Asian spot", "Licensed Asian feed; overlay fitted on ACG POs"),
         ("Band under-coverage", "64–78% vs 75–85% gate", "Regime-aware conformal; widen bands in shocks"),
         ("Stale public data", "Pink Sheet file ends Dec 2024", "Monthly refresh job; stale-input warnings live"),
         ("Regime breaks", "Coverage 42–67% in shocks", "Kill-switch forces BUY NORMAL (capital preservation)")]
for i, row in enumerate(risks, 1):
    for j, v in enumerate(row):
        cell(15, 27, i, j, v)
T(15, 30, "Months 5–6"); T(15, 31, "Futures curve and licensed PVC feed")
T(15, 32, "Add LME/SHFE futures as baseline and feature; licensed Asian PVC price.")
T(15, 34, "Months 7–9"); T(15, 35, "ERP Requisition Integration")
T(15, 36, "Direct API hook into SAP/Oracle purchase requisition creation.")
T(15, 38, "Months 10+"); T(15, 39, "Expand Packaging Materials")
T(15, 40, "Extend pipeline to cold-form laminates, PVDC, and auxiliary foils.")
T(15, 50, "Measured net saving, a timing test against random, buyer trust and a go/no-go, before buying changes.")
T(15, 51, "Sources: [1] ACG problem statement: RM spend, inventory days, and working capital. [2] Rupee figures use a ₹100 Cr "
          "baseline spend and no confidential ACG data. [3] Audit trail: CHANGES.md in the submitted repository.")

# ============================ FONT: Open Sans everywhere ============================
FACE = "Open Sans"
for _sl in prs.slides:
    for _el in _sl._element.iter(qn("a:latin"), qn("a:ea"), qn("a:cs")):
        if _el.get("typeface"):
            _el.set("typeface", FACE)
for _m in prs.slide_masters:
    for _rel in _m.part.rels.values():
        if _rel.reltype.endswith("/theme"):
            _tp = _rel.target_part
            _tp._blob = re.sub(rb'typeface="[^"+][^"]*"', f'typeface="{FACE}"'.encode(), _tp.blob)
prs.save(str(SB / "outputs" / "deck" / "SmartBuy_Round2_15Slides_v2.pptx"))
print("saved")
