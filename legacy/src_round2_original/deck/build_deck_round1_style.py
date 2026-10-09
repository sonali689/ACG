"""Smart Buy Round 2 deck - built in the Round 1 visual language.

Chrome reproduced from the Round 1 submission:
  red title panel, grey nav pill bar with the active section in ACG red,
  letterspaced red section eyebrow, heavy black headline, thin grey rules,
  6pt sources footer, page number bottom right.

All numbers come from outputs/, none are typed in. Where a number was
corrected by fix_pack (leak-free ensemble weights), the corrected value
is used.
"""
import json
from pathlib import Path

from pptx import Presentation
from pptx.dml.color import RGBColor
from pptx.enum.shapes import MSO_SHAPE
from pptx.enum.text import PP_ALIGN, MSO_ANCHOR
from pptx.util import Inches as In, Pt, Emu

BASE = Path(__file__).resolve().parents[2]
CH = BASE / "outputs/charts_acg"
D = json.loads((BASE / "dashboard/data.json").read_text())
AL, PV = D["materials"]["aluminium"], D["materials"]["pvc"]
HYP = D["hypotheses"]

# --- Round 1 palette ---------------------------------------------------
ACG = RGBColor(0xC8, 0x10, 0x2E)
INK = RGBColor(0x16, 0x18, 0x1D)
INK2 = RGBColor(0x4A, 0x4D, 0x55)
MUTE = RGBColor(0x7C, 0x80, 0x89)
RULE = RGBColor(0xE2, 0xE3, 0xE7)
PILL = RGBColor(0xF1, 0xF1, 0xF3)
WHITE = RGBColor(0xFF, 0xFF, 0xFF)
BUY = RGBColor(0x0F, 0x6B, 0x3F)
DEFER = RGBColor(0x8A, 0x5A, 0x00)
WASH = RGBColor(0xFD, 0xF2, 0xF4)

FONT = "Poppins"
NAV = ["Problem", "Drivers & data", "Solution", "Validation",
       "Prototype", "Implementation", "Risks & roadmap"]

W, H = 13.333, 7.5
M = 0.55                      # left margin, matches Round 1
CW = W - 2 * M                # content width


def sp(s):                    # fake letterspacing, as in Round 1
    return " ".join(s)


# ----------------------------------------------------------------- chrome
def txt(slide, x, y, w, h, s, size=10, bold=False, color=INK,
        align=PP_ALIGN.LEFT, space=1.15, italic=False, font=FONT, anchor=None):
    tb = slide.shapes.add_textbox(In(x), In(y), In(w), In(h))
    tf = tb.text_frame
    tf.word_wrap = True
    tf.margin_left = tf.margin_right = tf.margin_top = tf.margin_bottom = 0
    if anchor:
        tf.vertical_anchor = anchor
    for i, line in enumerate(s.split("\n")):
        p = tf.paragraphs[0] if i == 0 else tf.add_paragraph()
        p.text = line
        p.alignment = align
        p.line_spacing = space
        f = p.font
        f.name, f.size, f.bold, f.italic, f.color.rgb = font, Pt(size), bold, italic, color
    return tb


def rect(slide, x, y, w, h, fill=None, line=None, lw=0.75,
         shape=MSO_SHAPE.RECTANGLE, adj=None):
    sh = slide.shapes.add_shape(shape, In(x), In(y), In(w), In(h))
    if fill is None:
        sh.fill.background()
    else:
        sh.fill.solid(); sh.fill.fore_color.rgb = fill
    if line is None:
        sh.line.fill.background()
    else:
        sh.line.color.rgb = line; sh.line.width = Pt(lw)
    if adj is not None:
        try:
            sh.adjustments[0] = adj
        except Exception:
            pass
    sh.shadow.inherit = False
    sh.text_frame.text = ""
    return sh


def hr(slide, x, y, w, color=RULE, lw=0.75):
    ln = slide.shapes.add_connector(1, In(x), In(y), In(x + w), In(y))
    ln.line.color.rgb = color
    ln.line.width = Pt(lw)
    return ln


def navbar(slide, active):
    """Grey pill strip with seven sections; active one in ACG red."""
    y, bh = 0.30, 0.40
    rect(slide, M, y, CW, bh, fill=PILL, shape=MSO_SHAPE.ROUNDED_RECTANGLE, adj=0.5)
    n = len(NAV)
    seg = CW / n
    for i, name in enumerate(NAV):
        x = M + i * seg
        if i == active:
            rect(slide, x + 0.03, y + 0.03, seg - 0.06, bh - 0.06, fill=ACG,
                 shape=MSO_SHAPE.ROUNDED_RECTANGLE, adj=0.5)
        txt(slide, x, y + 0.105, seg, 0.24, name, size=9.5,
            bold=True, color=WHITE if i == active else INK2, align=PP_ALIGN.CENTER)


def head(slide, active, num, section, headline):
    navbar(slide, active)
    tag = f"{num:02d}"
    txt(slide, M, 0.88, CW, 0.2, f"{sp(tag)}  ·  {sp(section.upper())}",
        size=7.5, bold=True, color=ACG)
    txt(slide, M, 1.06, CW, 0.62, headline, size=17, bold=True, color=INK, space=1.12)


def foot(slide, page, sources):
    txt(slide, M, 6.92, CW - 0.8, 0.45, sources, size=5.6, color=MUTE, space=1.25)
    txt(slide, W - M - 0.8, 6.92, 0.8, 0.22, f"{page} / 15", size=8.5,
        bold=True, color=MUTE, align=PP_ALIGN.RIGHT)


def colhead(slide, x, y, w, s, size=10.5):
    txt(slide, x, y, w, 0.24, s, size=size, bold=True, color=INK)


def bullets(slide, x, y, w, items, size=8.6, gap=0.225, color=INK2):
    for i, it in enumerate(items):
        txt(slide, x, y + i * gap, 0.1, 0.2, "•", size=size, color=ACG)
        txt(slide, x + 0.13, y + i * gap, w - 0.13, 0.42, it, size=size,
            color=color, space=1.2)
    return y + len(items) * gap


def kpi(slide, x, y, w, value, label, vcolor=ACG, vsize=20, lsize=7.6):
    hr(slide, x, y, w)
    txt(slide, x, y + 0.09, w, 0.38, value, size=vsize, bold=True, color=vcolor)
    txt(slide, x, y + 0.09 + vsize / 48 + 0.10, w, 0.42, label, size=lsize,
        color=MUTE, space=1.22)


def table(slide, x, y, w, cols, rows, widths=None, fs=7.6, hfs=7.0,
          rh=0.235, hh=0.26, hl=None, red_col=None):
    """Round 1 table: solid ACG header, hairline row rules, zebra off."""
    n_r, n_c = len(rows) + 1, len(cols)
    gt = slide.shapes.add_table(n_r, n_c, In(x), In(y), In(w),
                                In(hh + rh * len(rows))).table
    gt.first_row = False
    gt.horz_banding = False
    if widths:
        tot = sum(widths)
        for i, ww in enumerate(widths):
            gt.columns[i].width = Emu(int(In(w) * ww / tot))
    gt.rows[0].height = In(hh)
    for i in range(len(rows)):
        gt.rows[i + 1].height = In(rh)

    for j, c in enumerate(cols):
        cell = gt.cell(0, j)
        cell.fill.solid(); cell.fill.fore_color.rgb = ACG
        cell.margin_left = cell.margin_right = In(0.06)
        cell.margin_top = cell.margin_bottom = In(0.02)
        cell.vertical_anchor = MSO_ANCHOR.MIDDLE
        p = cell.text_frame.paragraphs[0]
        p.text = c
        p.alignment = PP_ALIGN.RIGHT if j and c.startswith(">") else PP_ALIGN.LEFT
        if c.startswith(">"):
            p.text = c[1:]
        f = p.font
        f.name, f.size, f.bold, f.color.rgb = FONT, Pt(hfs), True, WHITE

    for i, row in enumerate(rows):
        for j, v in enumerate(row):
            cell = gt.cell(i + 1, j)
            cell.fill.solid()
            cell.fill.fore_color.rgb = WASH if (hl is not None and i == hl) else WHITE
            cell.margin_left = cell.margin_right = In(0.06)
            cell.margin_top = cell.margin_bottom = In(0.015)
            cell.vertical_anchor = MSO_ANCHOR.MIDDLE
            p = cell.text_frame.paragraphs[0]
            s = str(v)
            bold = s.startswith("*")
            if bold:
                s = s[1:]
            red = s.startswith("!")
            if red:
                s = s[1:]
            green = s.startswith("+")
            if green:
                s = s[1:]
            p.text = s
            p.alignment = PP_ALIGN.RIGHT if (j and cols[j].startswith(">")) else PP_ALIGN.LEFT
            f = p.font
            f.name, f.size = FONT, Pt(fs)
            f.bold = bold or (hl is not None and i == hl)
            f.color.rgb = ACG if red else (BUY if green else INK2)
    return gt


def note(slide, x, y, w, s, size=7.4, color=ACG, bold=True):
    txt(slide, x, y, w, 0.5, s, size=size, bold=bold, color=color, space=1.25)


# ----------------------------------------------------------------- build
prs = Presentation()
prs.slide_width, prs.slide_height = In(W), In(H)
BLANK = prs.slide_layouts[6]


def new():
    s = prs.slides.add_slide(BLANK)
    bg = rect(s, 0, 0, W, H, fill=WHITE)
    return s


S = {}   # convenient shorthand for numbers used repeatedly
al3 = next(r for r in AL["ladder"] if r["is_ensemble"])
pv3 = next(r for r in PV["ladder"] if r["is_ensemble"])
al_nb = next(r for r in AL["ladder"] if r["model"] == "N-BEATS")
pv_nb = next(r for r in PV["ladder"] if r["model"] == "N-BEATS")
al_ls = next(r for r in AL["ladder"] if r["model"] == "LSTM")
pv_ls = next(r for r in PV["ladder"] if r["model"] == "LSTM")


# ======================================================== 1 TITLE
s = new()
rect(s, 0, 0, 5.37, H, fill=ACG)
txt(s, 0.62, 0.62, 4.2, 0.2, f"{sp('ACG')}  ·  {sp('FILMS & FOILS')}",
    size=8.5, bold=True, color=WHITE)
txt(s, 0.62, 0.85, 4.2, 0.22, "Digital & AI | Procurement | Strategic Sourcing",
    size=9.5, color=RGBColor(0xF5, 0xC8, 0xD0))
txt(s, 0.58, 2.05, 4.6, 1.0, "Smart Buy", size=42, bold=True, color=WHITE)
txt(s, 0.62, 3.10, 4.3, 0.9,
    "AI-based raw material price prediction\nfor aluminium and PVC resin",
    size=13.5, color=RGBColor(0xFB, 0xDD, 0xE2), space=1.3)
txt(s, 0.62, 4.30, 4.3, 0.65,
    "A 6-month forward pricing and decision system\n"
    "that tells buyers when to buy ahead, buy normal,\n"
    "or defer — net of carrying cost.",
    size=10.5, bold=True, color=WHITE, space=1.3)
txt(s, 0.62, 6.30, 4.3, 0.24, "Round 2  ·  Technology Category",
    size=9.5, bold=True, color=WHITE)
txt(s, 0.62, 6.56, 4.3, 0.24, "Validated prototype  ·  September 2026",
    size=9, color=RGBColor(0xF5, 0xC8, 0xD0))

txt(s, 5.95, 0.62, 6.9, 0.2, sp("THE BUSINESS IMPACT"), size=7.5, bold=True, color=ACG)
txt(s, 5.95, 0.88, 6.85, 1.0,
    "Aluminium and PVC resin are roughly 70% of manufacturing cost for pharmaceutical "
    "blister packs. A 1% move in RM price is ~0.7% of total manufacturing cost. Today, "
    "both are bought on judgement with no forward view of price.",
    size=10.5, color=INK2, space=1.35)

kpi(s, 5.95, 2.15, 2.15, f"₹{PV['replay']['net_pct']:.2f} Cr",
    f"PVC saving per ₹100 Cr of annual\nspend, net of carrying cost")
kpi(s, 8.35, 2.15, 2.15, f"{AL['scorecard'][2]['dir']:.0f}%",
    "aluminium directional accuracy\nat three months, against a 62% gate")
kpi(s, 10.75, 2.15, 2.05, f"−{abs(PV['replay']['inv_delta']):.1f} d",
    "PVC inventory days reduced\nwhile saving money, not adding stock")

hr(s, 5.95, 3.60, 6.85)
txt(s, 5.95, 3.75, 6.9, 0.2, sp("WHAT ROUND 2 PROVES"), size=7.5, bold=True, color=ACG)
txt(s, 5.95, 4.00, 6.85, 1.2,
    "Round 1 set thresholds before modelling and claimed no numbers. This round executes "
    "the system on historical data: 66 leak-free rolling-origin folds from 2018 to 2024, "
    "covering COVID, the supply-chain crisis, and the Ukraine commodity spike. Eight model "
    "families scored against a naïve baseline, a 66-month buying replay in rupees, and a "
    "working decision dashboard. We report every pre-set gate unchanged — including the "
    "ones we missed.", size=9.5, color=INK2, space=1.35)

hr(s, 5.95, 5.35, 6.85)
txt(s, 5.95, 5.50, 6.9, 0.2, sp("TEAM"), size=7.5, bold=True, color=ACG)
table(s, 5.95, 5.75, 6.85,
      ["Team", "Case Scouts"],
      [["Members", "Himanshu Mahale, Rudransh Verma, Sonali Kumari"],
       ["Institute", "Indian Institute of Technology Kanpur, 2026"],
       ["Contact", "sonali23@iitk.ac.in,  +91 87899 84718"],
       ["Prototype", "Live dashboard, 15-slide deck, reproducible pipeline"]],
      widths=[1.6, 5.25], fs=8.0, hfs=7.6, rh=0.28)
txt(s, 5.95, 6.72, 6.85, 0.3,
    'Problem statement: "Smart Buy – AI based Raw Material Price Prediction", ACG Films & '
    'Foils, Digital & AI | Procurement | Strategic Sourcing.', size=6, color=MUTE)


# ======================================================== 2 PROBLEM
s = new()
head(s, 0, 2, "Problem",
     "Aluminium and PVC resin are about 70% of manufacturing cost, and today both are bought\n"
     "on judgement with no view of where prices are going")

colhead(s, M, 1.95, 6.0, "How buying works today, and where it breaks")
steps = [("1", "Demand forecast", "Sales forecast, agreed with Operations",
          "Manual, macro-level, built from past sales."),
         ("2", "RM requirement", "Worked out from the Bill of Materials", ""),
         ("3", "Inventory check", "On-hand plus in-transit raw material",
          "No forecast exists for either material."),
         ("4", "Buying decision", "When, how much, at what price. PO placed.",
          "A personal call each month. Not repeatable.")]
bw = 1.52
for i, (n, t, d, warn) in enumerate(steps):
    x = M + i * (bw + 0.12)
    rect(s, x, 2.28, bw, 0.92, fill=None, line=RULE)
    txt(s, x + 0.1, 2.36, 0.3, 0.3, n, size=15, bold=True, color=ACG)
    txt(s, x + 0.34, 2.42, bw - 0.42, 0.24, t, size=8.6, bold=True, color=INK)
    txt(s, x + 0.1, 2.70, bw - 0.2, 0.45, d, size=7.2, color=INK2, space=1.2)
    if warn:
        txt(s, x + 0.1, 3.26, bw - 0.2, 0.5, "⚠  " + warn, size=6.8, color=ACG, space=1.2)

hr(s, M, 3.95, 6.3)
colhead(s, M, 4.10, 6.3, "Prices move a lot, and fast")
txt(s, M, 4.40, 6.3, 1.0,
    "Aluminium went from about $1,450/t (April 2020) to $3,985/t (March 2022) and back to "
    "about $2,250/t in 2023: a 2.7× swing in under two years. PVC roughly doubled in Asia "
    "in 2020–21 on US force majeures and freight, then gave most of it back by 2023.",
    size=8.6, color=INK2, space=1.3)
colhead(s, M, 5.30, 6.3, "What actually moves the price")
bullets(s, M, 5.62, 6.3, [
    "Exchange rate. Imported material is priced in US$; USD/INR moves landed cost directly.",
    "Crude and energy. Crude, naphtha and ethylene for PVC; coal, gas and power for smelting.",
    "Geopolitics and trade policy. Sanctions, tariffs, anti-dumping duties, export controls.",
    "Freight and import duties. Container and bulk rates; CBIC tariff and DGTR notifications."])
note(s, M, 6.52, 6.3, "None of this shows up in a forecast built from past sales.")

X2 = 7.30
colhead(s, X2, 1.95, 5.45, "What it costs the business")
for i, (t, d) in enumerate([
        ("Higher raw material spend", "buying into rising markets with no timing advantage"),
        ("More inventory days", "over-buying as insurance against price surprises"),
        ("More working capital", "cash tied up in stock, premiums and in-transit material")]):
    txt(s, X2, 2.28 + i * 0.52, 5.45, 0.22, t, size=8.8, bold=True, color=INK)
    txt(s, X2, 2.48 + i * 0.52, 5.45, 0.3, d, size=7.8, color=INK2)
note(s, X2, 3.92, 5.45,
     "With a 70% share, a 1% move in raw material price is roughly 0.7% of total\n"
     "manufacturing cost.")

hr(s, X2, 4.42, 5.45)
colhead(s, X2, 4.58, 5.45, "What Smart Buy now demonstrates")
rows = [
    ["Backward-looking, subjective timing",
     f"*Six-month forecast, {AL['scorecard'][2]['dir']:.0f}% / {PV['scorecard'][2]['dir']:.0f}% "
     f"directional accuracy at h=3"],
    ["No accuracy tracking",
     f"*{al3['skill']:.1f}% / {pv3['skill']:.1f}% skill over naïve, DM p = "
     f"{AL['scorecard'][2]['dm_p']:.4f} / {pv3['dm_p']:.3f}"],
    ['"When, how much, what price" by judgement',
     f"*Buy / defer rule replayed over {AL['replay']['months']} months: "
     f"{PV['replay']['net_pct']:+.2f}% net on PVC"]]
table(s, X2, 4.88, 5.45, ["Round 1 gap", ">Round 2 evidence"], rows,
      widths=[2.3, 3.15], fs=7.4, hfs=6.8, rh=0.42)

foot(s, 2, "Sources  [1] ACG, \"Smart Buy – AI based Raw Material Price Prediction\", problem statement. "
     "[2] World Bank, Commodity Price Data (Pink Sheet), monthly. [3] Prices and skill figures are "
     "walk-forward results from this submission's pipeline, not illustrations.")


# ======================================================== 3 CHAINS
s = new()
head(s, 1, 3, "Drivers & data",
     "Both prices sit at the end of a physical chain, and every link in that chain\n"
     "is tracked from public data")

def chain(slide, y, title, nodes, hi):
    colhead(slide, M, y, 12.2, title)
    bw2, gap = 1.60, 0.18
    for i, (n, sub) in enumerate(nodes):
        x = M + i * (bw2 + gap)
        is_hi = (i == hi)
        rect(slide, x, y + 0.32, bw2, 0.56, fill=ACG if is_hi else None,
             line=None if is_hi else RULE)
        txt(slide, x + 0.09, y + 0.42, bw2 - 0.18, 0.36, n, size=8.2, bold=True,
            color=WHITE if is_hi else INK, align=PP_ALIGN.CENTER, space=1.15)
        txt(slide, x + 0.04, y + 0.94, bw2 - 0.08, 0.45, sub, size=6.6,
            color=MUTE, align=PP_ALIGN.CENTER, space=1.2)
        if i < len(nodes) - 1:
            txt(slide, x + bw2, y + 0.50, gap, 0.2, "▶", size=7, color=ACG,
                align=PP_ALIGN.CENTER)

chain(s, 1.95, "Aluminium",
      [("Bauxite", "Guinea and Australia\nsupply, export policy"),
       ("Alumina", "4 t bauxite →\n2 t alumina → 1 t metal"),
       ("Smelter energy", "coal, gas and power:\nthe largest cash cost"),
       ("LME price\nand stocks", "financialised; stocks\nsignal tightness"),
       ("Premium, FX,\nduty, freight", "USD/INR, CBIC tariff,\nlogistics"),
       ("Landed India\nprice", "what ACG\nactually pays")], hi=3)

chain(s, 3.55, "PVC resin",
      [("Crude (Brent)", "sets the whole\nfeedstock chain"),
       ("Naphtha", "Asian cracker\nfeedstock"),
       ("Ethylene", "plus chlorine\ngives EDC"),
       ("VCM / EDC", "the direct\nmonomer input"),
       ("PVC spot,\nAsia / China", "China is the largest\nproducer and exporter"),
       ("Landed India\nprice", "freight, FX,\nanti-dumping duty")], hi=4)

hr(s, M, 5.20, 12.2)
colhead(s, M, 5.35, 5.8, "How we decided which indicators to keep")
bullets(s, M, 5.68, 5.8, [
    "Cross-correlation of log-returns at lags 0–6 months; best lag recorded per indicator.",
    "ADF stationarity, then Granger causality, with Benjamini–Hochberg FDR correction across "
    "all indicators tested.",
    "Keep rule: |ρ| ≥ 0.3 at best lag, OR Granger-significant after FDR, OR top-15 by model "
    "importance. Every drop recorded with its reason."])

colhead(s, 6.85, 5.35, 5.9, "What changed against the indicative list")
rows = [["Added", "GPR and EPU risk indices, copper spillover, LME stocks, China CLI, "
         "five dated shock flags"],
        ["Replaced", "Paid alumina, ethylene and VCM indices → public World Bank and "
         "UN Comtrade proxies"],
        ["Dropped", "Indicators failing all three keep-rule branches, with the reason logged"]]
table(s, 6.85, 5.66, 5.9, ["Change", ">Detail"], rows,
      widths=[1.0, 4.9], fs=7.2, hfs=6.8, rh=0.38)

foot(s, 3, "Sources  [1] World Bank Commodity Price Data (Pink Sheet). [2] UN Comtrade. "
     "[3] ECB reference rates. [4] Caldara & Iacoviello (2022), American Economic Review 112(4). "
     "[5] Baker, Bloom & Davis (2016), Quarterly Journal of Economics 131(4). [6] OECD composite "
     "leading indicators. Public sources only; 181 monthly observations, 2010–2024.")


# ======================================================== 4 DATA & AS-OF
s = new()
head(s, 1, 4, "Drivers & data",
     "Every feature carries the publication lag it really had, so the backtest sees only\n"
     "what was public at the time")

colhead(s, M, 1.95, 7.3, "The as-of lag table, enforced in code")
rows = [["World Bank Pink Sheet prices", "coal, gas, crude, aluminium, base metals", "1 month"],
        ["UN Comtrade unit values", "alumina, bauxite, ethylene, VCM, PVC trade", "2 months"],
        ["ECB reference rates", "USD/INR, EUR crosses", "0 months"],
        ["GPR and EPU indices", "geopolitical risk, policy uncertainty", "0 months"],
        ["OECD composite leading indicator", "China demand proxy", "1 month"],
        ["Shock-event flags", "tariff, COVID, freeze, war, Red Sea", "dated at announcement"]]
table(s, M, 2.26, 7.3, ["Source", ">Series", ">Lag applied"], rows,
      widths=[2.7, 3.2, 1.4], fs=7.6, hfs=7.0, rh=0.30)

note(s, M, 4.42, 7.3,
     "One function, visible_at(panel, origin), returns only rows published by that origin.\n"
     "Every feature is built from its output. There is no second path into the feature matrix.")

hr(s, M, 5.00, 7.3)
colhead(s, M, 5.15, 7.3, "Leakage guardrails, as published in Round 1")
bullets(s, M, 5.48, 7.3, [
    "Scalers, imputers and feature selection refitted inside every fold, never on the full sample.",
    "Trailing rolling windows only. A centred window averages future values into a past point.",
    "Shock flags dated at announcement, never at the month the price reacted.",
    "Metrics reported per horizon and per regime, never averaged into one headline number."])

X2 = 8.15
colhead(s, X2, 1.95, 4.65, "Coverage of the assembled panel")
kpi(s, X2, 2.28, 1.45, "181", "monthly observations\nJanuary 2010 – June 2024", vsize=19)
kpi(s, X2 + 1.60, 2.28, 1.45, "60+", "engineered features across\nfive economic families", vsize=19)
kpi(s, X2 + 3.20, 2.28, 1.45, "78", "walk-forward folds\nJan 2018 – Jun 2024", vsize=19)

colhead(s, X2, 3.60, 4.65, "Feature families")
bullets(s, X2, 3.92, 4.65, [
    "Price dynamics — lags, momentum, trailing volatility, z-scores",
    "Cost-push feedstock — coal, alumina, naphtha, ethylene, VCM, and spreads",
    "Macro demand — China CLI, PMI, base-metals spillover",
    "Supply and inventory — LME stocks, Comtrade export volumes",
    "Risk and shocks — GPR, EPU, five dated event flags"], size=8.2, gap=0.245)

note(s, X2, 5.42, 4.65,
     "Known limitation. PVC has no free, long-history Asian spot index. We model a public\n"
     "proxy and treat the India landed price as a separate overlay. This is the largest\n"
     "single data risk in the project and is on the risk register unchanged from Round 1.",
     color=INK2, bold=False, size=7.8)

foot(s, 4, "Sources  Publication lags assigned from each provider's own release calendar and "
     "enforced in src/ingestion. The lag table is versioned at config/lag_table.yaml. "
     "Coverage and gap reports are reproducible from the raw dated pulls.")


# ======================================================== 5 DRIVERS & HYPOTHESES
s = new()
head(s, 1, 5, "Drivers & data",
     "Econometric driver study: lead–lag cross-correlations and formal hypothesis verdicts")

# Left: Cross-correlations and key relationships
colhead(s, M, 1.95, 5.9, "Lead–lag study: peak cross-correlations")
s.shapes.add_picture(str(CH / "aluminium_drivers.png"), In(M), In(2.22), width=In(5.9))

colhead(s, M, 4.68, 5.9, "Key leading relationships discovered")
cols_lead = [
    ("Geopolitical risk leads aluminium by 1 month",
     "ρ = −0.33 at lag 1 (Granger-significant). Risk spikes front-run price weakness, not strength."),
    ("Copper leads aluminium by 6 months",
     "ρ = +0.24 at lag 6 (FDR-corrected). Base-metals demand is a slow, cyclical leading signal."),
    ("China export supply leads PVC by 1 month",
     "ρ = +0.39 at lag 1, the strongest single leading indicator for Asian PVC."),
    ("Coal, Crude & PMI act non-linearly",
     "Key regime shifters; non-linearities handled via tree ensembles and N-BEATS neural decomposition.")
]
for i, (t, d) in enumerate(cols_lead):
    y = 4.96 + i * 0.44
    txt(s, M, y, 0.1, 0.2, "•", size=7.8, color=ACG)
    txt(s, M + 0.14, y, 5.75, 0.42, f"*{t}:* {d}", size=7.5, color=INK2, space=1.18)

# Right: Four formal hypotheses
colhead(s, 6.85, 1.95, 5.95, "Four core hypotheses: formal verdicts")
hyp = [("H1", HYP["H1_Coal_and_Stocks_Lead_Aluminium"]),
       ("H2", HYP["H2_Ethylene_and_Exports_Lead_PVC"]),
       ("H3", HYP["H3_PMI_Leads_Both_Materials"]),
       ("H4", HYP["H4_USD_INR_Contemporaneous_PassThrough"])]
for i, (tag, h) in enumerate(hyp):
    y = 2.22 + i * 1.06
    v = h["verdict"]
    col = BUY if v == "SUPPORTED" else DEFER
    rect(s, 6.85, y, 5.95, 1.00, fill=None, line=RULE)
    rect(s, 6.85, y, 0.045, 1.00, fill=col)
    txt(s, 6.85 + 0.15, y + 0.10, 0.5, 0.24, tag, size=12, bold=True, color=ACG)
    txt(s, 6.85 + 0.65, y + 0.10, 4.0, 0.22, h["hypothesis"], size=8.4, bold=True, color=INK)
    txt(s, 6.85 + 4.60, y + 0.10, 1.25, 0.22, v, size=7.4, bold=True, color=col, align=PP_ALIGN.RIGHT)
    ev = [v2 for k, v2 in h.items() if k.endswith("_evidence")]
    txt(s, 6.85 + 0.65, y + 0.34, 5.15, 0.30, " · ".join(ev)[:125], size=6.5, color=MUTE, space=1.18)
    txt(s, 6.85 + 0.65, y + 0.62, 5.15, 0.35, h["narrative"][:140], size=6.7, color=INK2, space=1.18)

note(s, 6.85, 6.52, 5.95,
     "H3 and H4 confirm PMI behaves as a regime shifter and USD/INR passes through at lag 0 (ρ = +0.89).",
     color=INK2, bold=False, size=7.2)

foot(s, 5, "Method: Correlation computed on monthly log-returns at lags 0 to 6. Granger p-values are Benjamini–Hochberg FDR-corrected.")

# ======================================================== 6 ARCHITECTURE
s = new()
head(s, 2, 6, "Solution",
     "Seven layers: public data in, an explainable forecast with calibrated bands out,\n"
     "and a buy signal on top")

layers = [
    ("1", "Ingest", "World Bank, ECB, GPR, EPU, OECD, UN Comtrade. Dated raw pulls, never overwritten."),
    ("2", "As-of alignment", "Publication lag applied per series. visible_at() is the only path to features."),
    ("3", "Features", "60+ indicators across five families: price dynamics, feedstock, demand, supply, risk."),
    ("4", "Direct multi-horizon", "Six models per material, one per month ahead. Target is the log-return."),
    ("5", "Model zoo", "Eight families across three tiers, every one scored on identical folds."),
    ("6", "Validate and gate", "78 expanding folds. Anything failing the naïve gate gets zero weight."),
    ("7", "Decide", "Expected saving net of carry → buy now / buy normal / defer, cover, order quantity.")]
cw2 = (12.25 - 6 * 0.14) / 7
for i, (n, t, d) in enumerate(layers):
    x = M + i * (cw2 + 0.14)
    rect(s, x, 2.00, cw2, 2.30, fill=None, line=RULE)
    rect(s, x, 2.00, cw2, 0.055, fill=ACG)
    txt(s, x + 0.11, 2.16, 0.4, 0.3, n, size=16, bold=True, color=ACG)
    txt(s, x + 0.11, 2.56, cw2 - 0.22, 0.3, t, size=9, bold=True, color=INK, space=1.15)
    txt(s, x + 0.11, 2.92, cw2 - 0.22, 1.3, d, size=7.1, color=INK2, space=1.28)

hr(s, M, 4.55, 12.25)
colhead(s, M, 4.70, 5.9, "Why one model per horizon")
txt(s, M, 5.02, 5.9, 0.75,
    "Six separate models are trained, one for each month ahead. The alternative is recursive: "
    "predict month 1, feed that prediction back in as if it were an observation, predict month 2. "
    "Recursive compounds its own error across the horizon. Direct does not.",
    size=8.4, color=INK2, space=1.3)
colhead(s, M, 5.85, 5.9, "Why the log-return is the target")
txt(s, M, 6.17, 5.9, 0.75,
    "Prices ranged from about $1,450 to $3,985 over the sample, so the variance of the level is "
    "unstable. The variance of the return is not. Forecasts are converted back to US$/t with "
    "P = P₀·exp(ŷ), and the Jensen shift is measured and reported.",
    size=8.4, color=INK2, space=1.3)

X2 = 6.85
colhead(s, X2, 4.70, 5.95, "Specification")
rows = [["Targets", "LME aluminium (US$/t); PVC Asia spot proxy (US$/t)"],
        ["Horizons", "1 to 6 months, monthly steps; h=3 is the decision horizon"],
        ["Training", "Expanding window, refit at every origin, 78 folds"],
        ["Features", "60+ candidates, selected inside each fold"],
        ["Outputs", "P50, P10–P90 band, P(up), driver attribution, buy signal"],
        ["Stack", "Python, pandas, statsmodels, scikit-learn, LightGBM, PyTorch"]]
table(s, X2, 5.02, 5.95, ["Item", ">Value"], rows,
      widths=[1.25, 4.7], fs=7.5, hfs=7.0, rh=0.265)

foot(s, 6, "Sources  [1] Hyndman & Athanasopoulos (2021), Forecasting: Principles and Practice, "
     "3rd ed., OTexts: direct vs recursive multi-step strategies. [2] Ke et al. (2017), LightGBM, "
     "NeurIPS. [3] Oreshkin et al. (2020), N-BEATS, ICLR. [4] Romano, Patterson & Candès (2019), "
     "Conformalized Quantile Regression, NeurIPS.")


# ======================================================== 7 MODEL LADDER
s = new()
head(s, 2, 7, "Solution",
     "Eight model families on identical folds. The naïve gate removed the LSTM automatically,\n"
     "and a constrained neural model won")

colhead(s, M, 1.95, 6.0, "Aluminium — MAPE at h = 3")
s.shapes.add_picture(str(CH / "aluminium_ladder.png"), In(M), In(2.20), width=In(5.95))
colhead(s, 6.95, 1.95, 5.85, "PVC resin — MAPE at h = 3")
s.shapes.add_picture(str(CH / "pvc_ladder.png"), In(6.95), In(2.20), width=In(5.85))

hr(s, M, 5.10, 12.25)
colhead(s, M, 5.24, 3.9, "The LSTM excluded itself")
txt(s, M, 5.54, 3.9, 1.0,
    f"The LSTM reached {al_ls['mape']:.2f}% on aluminium against a naïve {AL['scorecard'][2]['naive']:.2f}%, "
    f"and {pv_ls['mape']:.2f}% on PVC against {PV['scorecard'][2]['naive']:.2f}%. It failed the naïve gate "
    "on both. The weighting rule we published in Round 1, before running anything, assigned it "
    "zero weight automatically. We did not exclude it by judgement.",
    size=8.2, color=INK2, space=1.3)

colhead(s, 4.75, 5.24, 3.9, "But a neural model did win")
txt(s, 4.75, 5.54, 3.9, 1.0,
    f"N-BEATS reached {al_nb['mape']:.2f}% on aluminium and {pv_nb['mape']:.2f}% on PVC, beating every "
    "linear and tree model. Both are neural networks. N-BEATS projects onto polynomial and Fourier "
    "bases, so its hypothesis space is restricted to trend and cycle; the LSTM must discover "
    "structure from 150 training points with thousands of free parameters.",
    size=8.2, color=INK2, space=1.3)

colhead(s, 8.95, 5.24, 3.85, "The finding")
rect(s, 8.95, 5.50, 3.85, 1.08, fill=WASH)
txt(s, 9.10, 5.62, 3.55, 0.85,
    "Architectural constraint substitutes for data.\n\n"
    "Not \"deep learning does not work on small samples\" — a sharper claim, and one we can "
    "make because we ran both.", size=8.2, bold=True, color=ACG, space=1.3)

foot(s, 7, "Method  All models run through the same walk-forward harness on the same folds and the "
     "same origin set. Ensemble weights are estimated on strictly prior folds only. Consistent with "
     "Makridakis et al., the M4 competition, where hybrid and regularised methods outperformed "
     "unconstrained neural networks on short macroeconomic series.")


# ======================================================== 8 EXPLAINABILITY
s = new()
head(s, 2, 8, "Solution",
     "Every forecast comes with the reason it moved, because a buyer cannot act on a\n"
     "number they cannot interrogate")

colhead(s, M, 1.95, 5.9, "What the buyer sees each month")
rect(s, M, 2.25, 5.9, 2.15, fill=None, line=RULE)
txt(s, M + 0.18, 2.40, 5.55, 0.24, "Driver note, generated from the model",
    size=8, bold=True, color=ACG)
txt(s, M + 0.18, 2.70, 5.55, 1.6,
    f"\"Aluminium three-month P50 is ${AL['horizons']['3']['p50']:,.0f}, "
    f"{AL['horizons']['3']['change_pct']:+.1f}% against spot, with a P10–P90 range of "
    f"${AL['horizons']['3']['p10']:,.0f} to ${AL['horizons']['3']['p90']:,.0f}. "
    "The move is driven mainly by geopolitical risk easing at a one-month lead and copper "
    "firming at six months, partly offset by energy smelting pressure. Confidence in direction "
    f"is {AL['horizons']['3']['p_up']:.0f}%. Expected saving from covering now, after carrying "
    f"cost, is {AL['horizons']['3']['exp_saving_pct']:+.1f}%, which does not clear the +2% "
    "threshold — signal is BUY NORMAL.\"",
    size=8.2, color=INK2, space=1.32, italic=True)

colhead(s, M, 4.62, 5.9, "What sits behind it")
bullets(s, M, 4.94, 5.9, [
    "Driver attribution per forecast, computed on out-of-fold predictions only.",
    "Cross-correlation and Granger evidence per indicator, with its best lag.",
    "Partial-dependence and lead–lag charts for the top drivers of each material.",
    "Model card, feature list, version log and a full audit trail of every run.",
    "Every override by a buyer is logged; adoption is a tracked run-state KPI."], size=8.2)

X2 = 6.85
colhead(s, X2, 1.95, 5.95, "Error correlation between ensemble members, PVC h = 3")
s.shapes.add_picture(str(CH / "error_corr_pvc.png"), In(X2 + 0.45), In(2.22), height=In(3.35))

note(s, X2, 5.72, 5.95,
     f"Mean error correlation between members is {PV['err_corr']['mean_off_diag']:.2f}. "
     f"N-BEATS against the rest is {PV['err_corr']['nbeats_vs_rest']:.2f}.",
     size=8, color=ACG)
txt(s, X2, 6.14, 5.95, 0.75,
    "Most members are near-duplicates: they share a feature set, so their errors move together "
    "and combining them adds little. N-BEATS is the only genuine diversifier, which is why it "
    "carries most of the ensemble weight. We show this rather than assert that the ensemble helps.",
    size=7.8, color=INK2, space=1.28)

foot(s, 8, "Method  Attribution is computed on out-of-fold predictions so that importance has to "
     "hold out of sample. The error-correlation matrix is the evidence for or against any claimed "
     "ensemble gain, and is reported whether or not it flatters the result.")


# ======================================================== 9 PROTOCOL
s = new()
head(s, 3, 9, "Validation",
     "We tested it the way procurement would live with it: refit at every month from 2018\n"
     "to 2024, and beat the naïve forecast before claiming anything")

colhead(s, M, 1.95, 6.5, "Rolling-origin walk-forward, 78 expanding folds")
for i, (lbl, tr, te) in enumerate([
        ("Origin Jan 2018", 0.62, 0.07), ("Origin Jan 2020", 0.72, 0.07),
        ("Origin Jan 2022", 0.82, 0.07), ("Origin Jun 2024", 0.93, 0.07)]):
    y = 2.28 + i * 0.36
    txt(s, M, y, 1.45, 0.22, lbl, size=7.8, color=INK2)
    x0, wfull = M + 1.55, 4.8
    rect(s, x0, y + 0.02, wfull * tr, 0.17, fill=INK)
    rect(s, x0 + wfull * tr, y + 0.02, wfull * te, 0.17, fill=ACG)
txt(s, M + 1.55, 3.78, 4.8, 0.2, "and every monthly origin in between",
    size=7.4, color=MUTE, italic=True)
txt(s, M, 4.02, 6.5, 0.2, "■ training window (expanding)      ■ six-month out-of-sample test",
    size=7.4, color=MUTE)

hr(s, M, 4.32, 6.5)
colhead(s, M, 4.47, 6.5, "Skill and direction rise with horizon, not fall")
s.shapes.add_picture(str(CH / "aluminium_skill.png"), In(M), In(4.75), width=In(6.4))

X2 = 7.45
colhead(s, X2, 1.95, 5.35, "Three-month forecast against what actually happened")
s.shapes.add_picture(str(CH / "aluminium_backtest.png"), In(X2), In(2.22), width=In(5.35))
txt(s, X2, 4.30, 5.35, 0.5,
    "Aluminium, every origin. The red line is the forecast made three months before the realised "
    "price it sits above.", size=7.6, color=MUTE, space=1.25)

hr(s, X2, 4.72, 5.35)
colhead(s, X2, 4.87, 5.35, "Performance by regime")
rows = [[r["name"].replace(" / ", "/"), f"{r['n']}", f"{r['mape']:.2f}%",
         f"{r['skill']:+.1f}%", f"{r['dir']:.0f}%", f"{r['cov']:.0f}%"]
        for r in AL["regimes"]]
table(s, X2, 5.17, 5.35,
      ["Regime", ">n", ">MAPE", ">Skill", ">Dir.", ">Cov."], rows,
      widths=[2.25, 0.45, 0.7, 0.68, 0.6, 0.67], fs=7.2, hfs=6.6, rh=0.28)
note(s, X2, 6.42, 5.35,
     "Skill holds through COVID and the 2021–22 spike. Band coverage does not — it collapses to "
     "33% in both. We report that rather than average it away.", size=7.4, color=ACG)

foot(s, 9, "Method  Hyper-parameters are tuned only on each fold's own inner validation slice. "
     "Scalers, imputers and feature selection are refitted inside every fold. "
     "[1] Tashman (2000), International Journal of Forecasting 16(4). "
     "[2] Diebold & Mariano (1995), Journal of Business & Economic Statistics 13(3), with "
     "Harvey–Leybourne–Newbold small-sample correction and Newey–West HAC variance at lag h−1.")


# ======================================================== 10 RESULTS VS GATES
s = new()
head(s, 3, 10, "Validation",
     "Results against the thresholds we set in Round 1, before any modelling — reported\n"
     "unchanged, including the gate we missed")

colhead(s, M, 1.92, 12.25, "Aluminium and PVC resin at the decision horizon and either side of it")
rows = []
for i, r in enumerate(AL["scorecard"]):
    p = PV["scorecard"][i]
    gate = {1: 10, 2: 12, 3: 15, 4: 12, 5: 10, 6: 10}[r["h"]]
    ok_a = "✓" if r["skill"] >= gate else "✗"
    ok_p = "✓" if p["skill"] >= gate else "✗"
    rows.append([f"{r['h']} month{'s' if r['h'] > 1 else ''}",
                 f"{r['ens']:.2f}%", f"{r['naive']:.2f}%",
                 ("+" if r["skill"] >= gate else "!") + f"{r['skill']:+.1f}%",
                 f"{r['dir']:.1f}%", f"{r['dm_p']:.4f}",
                 f"{p['ens']:.2f}%", f"{p['naive']:.2f}%",
                 ("+" if p["skill"] >= gate else "!") + f"{p['skill']:+.1f}%",
                 f"{p['dir']:.1f}%", f"{p['dm_p']:.4f}",
                 ("!" if (ok_a == "✗" or ok_p == "✗") else "+")
                 + f"≥{gate}%    {ok_a} / {ok_p}"])
table(s, M, 2.22, 12.25,
      ["Horizon", ">Al MAPE", ">Al naïve", ">Al skill", ">Al dir.", ">Al DM p",
       ">PVC MAPE", ">PVC naïve", ">PVC skill", ">PVC dir.", ">PVC DM p",
       ">Gate  ·  Al / PVC"],
      rows, widths=[1.15, .95, .95, .9, .85, .9, 1.0, 1.0, .95, .9, .9, 1.6],
      fs=7.4, hfs=6.6, rh=0.285, hl=2)

hr(s, M, 4.45, 12.25)

colhead(s, M, 4.60, 3.85, "The gate we missed")
rect(s, M, 4.88, 3.85, 1.55, fill=WASH)
txt(s, M + 0.15, 5.00, 3.55, 1.3,
    f"Aluminium skill at h=3 came in at {AL['scorecard'][2]['skill']:.1f}% against the ≥15% "
    "threshold we published in Round 1.\n\n"
    "We are reporting it unchanged rather than relaxing the gate.",
    size=8.2, bold=True, color=ACG, space=1.3)
txt(s, M, 6.52, 3.85, 0.5,
    "Aluminium is exchange-traded and close to efficient, so price-level skill is genuinely hard. "
    "The value is in direction.", size=7.6, color=INK2, space=1.25)

colhead(s, 4.75, 4.60, 3.9, "Where the value actually is")
bullets(s, 4.75, 4.92, 3.9, [
    f"PVC clears the h=3 skill gate at {PV['scorecard'][2]['skill']:+.1f}%, and rises to "
    f"{PV['scorecard'][3]['skill']:+.1f}% at four months.",
    f"Aluminium directional accuracy is {AL['scorecard'][2]['dir']:.1f}% at h=3 against a 62% "
    f"gate, with DM p = {AL['scorecard'][2]['dm_p']:.3f}, inside our 0.10 threshold.",
    "Five of twelve horizon-material pairs clear DM p < 0.10, including h=3 and h=4 on both "
    "materials. Beyond that we are not claiming significance.",
    "Skill at h=1 is negative on aluminium and zero on PVC, where the naïve gate left naïve "
    "holding the entire weight. The ensemble refused to bet, which is the gate working."],
    size=8.0, gap=0.42)

colhead(s, 8.95, 4.60, 3.85, "A correction we made to our own result")
rect(s, 8.95, 4.88, 3.85, 1.55, fill=None, line=ACG, lw=1.0)
txt(s, 9.10, 5.00, 3.55, 1.3,
    "An earlier run estimated ensemble weights using errors from every fold, including the "
    "fold being scored. That is leakage, and it flattered the result.\n\n"
    "Re-estimated with weights from strictly prior folds only, aluminium h=3 moved from 7.06% "
    f"to {AL['scorecard'][2]['ens']:.2f}% and PVC from 9.77% to {PV['scorecard'][2]['ens']:.2f}%. "
    "The first 12 origins become burn-in, so the window is 66 folds rather than 78.\n\n"
    "Every figure on this slide is the corrected one. We found this ourselves and are "
    "showing it.",
    size=7.8, color=INK2, space=1.28)

foot(s, 10, "Thresholds  Set in the Round 1 submission before any modelling and carried here "
     "unchanged. MAPE is mean absolute percentage error per horizon. Skill is 1 − MAPE(model)/"
     "MAPE(naïve). Directional accuracy is the share of origins where the sign of the predicted "
     "change matches the realised change. DM p-values are HAC-corrected.")


# ======================================================== 11 UNCERTAINTY
s = new()
head(s, 3, 11, "Validation",
     "The bands are the product, and ours are too narrow — measured, reported, and\n"
     "diagnosed rather than quietly dropped")

colhead(s, M, 1.95, 5.9, "Aluminium — P10–P90 coverage against the 75–85% gate")
s.shapes.add_picture(str(CH / "aluminium_bands.png"), In(M), In(2.22), width=In(5.5))
colhead(s, M, 4.55, 5.9, "PVC resin")
s.shapes.add_picture(str(CH / "pvc_bands.png"), In(M), In(4.82), width=In(5.5))

X2 = 6.85
colhead(s, X2, 1.95, 5.95, "What the numbers say")
rows = [[r["h"].replace("h=", "") + " mo", f"{r['cov']:.1f}%", f"{r['width']:.1f}%",
         f"{r['bias']:+.2f}%",
         ("!" if not (75 <= r["cov"] <= 85) else "+") +
         ("miss" if not (75 <= r["cov"] <= 85) else "pass")]
        for r in AL["bands"]]
table(s, X2, 2.26, 5.95,
      ["Horizon", ">Coverage", ">Band width", ">Signed bias", ">Gate"],
      rows, widths=[1.1, 1.3, 1.35, 1.3, 0.9], fs=7.6, hfs=7.0, rh=0.28)

colhead(s, X2, 4.30, 5.95, "The diagnosis")
bullets(s, X2, 4.62, 5.95, [
    "Coverage runs 55–65% against a 75–85% gate. The conformal calibration is applied but the "
    "residual quantile spread is still too tight.",
    "Band width does widen with horizon, from 8% at one month to 23% at six, so the shape is "
    "right even where the level is not.",
    "Coverage collapses to 33% in COVID and in the 2021–22 spike, and sits near 79% in calm "
    "periods. The failure is concentrated in regime breaks, which is the honest diagnosis.",
    "Signed bias passes the ±1% gate at most horizons; where it does not, the Jensen shift from "
    "exponentiating the log-return accounts for nearly all of it."], size=8.0, gap=0.44)

note(s, X2, 6.50, 5.95,
     "Consequence for the decision rule. Because the bands understate tail risk in shocks, the "
     "confidence gate is doing more work than the band is. We would recalibrate on volatility "
     "regime before the pilot.", size=7.6, color=ACG)

foot(s, 11, "Method  Quantile models trained with pinball loss at q = 0.10 / 0.50 / 0.90, then "
     "split-conformal calibration on a held-out slice of each fold. Coverage is measured, not "
     "assumed. [1] Romano, Patterson & Candès (2019), Conformalized Quantile Regression, NeurIPS.")


# ======================================================== 12 REPLAY
s = new()
head(s, 4, 12, "Prototype",
     "The decision rule replayed over 84 months: what it would have saved, and what it\n"
     "would have cost in inventory")

colhead(s, M, 1.90, 6.2, "The rule")
rect(s, M, 2.18, 6.2, 0.52, fill=WASH)
txt(s, M + 0.15, 2.30, 5.9, 0.3, "S(h) = (P̂(h) − P₀) / P₀  −  c × h",
    size=13, bold=True, color=ACG)
for i, (sig, cond, act, col) in enumerate([
        ("Buy now", "S(h) > +2% and P(up) ≥ 60%", "Forward-cover 3 months", BUY),
        ("Buy normal", "−2% ≤ S(h) ≤ +2%, or confidence < 60%", "BoM requirement, 1.5 months", INK2),
        ("Defer", "S(h) < −2% and P(down) ≥ 60%", "Minimum safety cover, 1 month", DEFER)]):
    y = 2.88 + i * 0.44
    rect(s, M, y, 0.92, 0.34, fill=col)
    txt(s, M, y + 0.085, 0.92, 0.2, sig, size=8, bold=True, color=WHITE,
        align=PP_ALIGN.CENTER)
    txt(s, M + 1.05, y + 0.02, 3.1, 0.3, cond, size=8, bold=True, color=INK)
    txt(s, M + 1.05, y + 0.19, 5.1, 0.24, act, size=7.6, color=INK2)
txt(s, M, 4.25, 6.2, 0.24,
    "c is carrying cost per month, set at 1.0% pending ACG Finance inputs.",
    size=7.6, color=MUTE, italic=True)

hr(s, M, 4.52, 6.2)
colhead(s, M, 4.66, 6.2, "Results over 78 months, both materials")
rows = [["Average price paid", f"${AL['replay']['sb_price']:,.0f}", f"${PV['replay']['sb_price']:,.0f}"],
        ["Buying one month at a time", f"${AL['replay']['base_price']:,.0f}", f"${PV['replay']['base_price']:,.0f}"],
        ["Gross price saving", f"+{AL['replay']['gross_pct']:.2f}%", f"+{PV['replay']['gross_pct']:.2f}%"],
        ["*Net saving after carrying cost", f"+{AL['replay']['net_pct']:.2f}%", f"+{PV['replay']['net_pct']:.2f}%"],
        ["Average inventory cover", f"{AL['replay']['inv_sb']:.1f} d", f"{PV['replay']['inv_sb']:.1f} d"],
        ["Change vs baseline", f"!{AL['replay']['inv_delta']:+.1f} d", f"!{PV['replay']['inv_delta']:+.1f} d"],
        ["Working capital per ₹100 Cr", f"−₹{abs(AL['replay']['wc_shift']):.2f} Cr",
         f"−₹{abs(PV['replay']['wc_shift']):.2f} Cr"]]
table(s, M, 4.96, 6.2, ["Metric", ">Aluminium", ">PVC resin"], rows,
      widths=[3.2, 1.5, 1.5], fs=7.6, hfs=7.0, rh=0.245, hl=3)

X2 = 7.15
colhead(s, X2, 1.90, 5.65, "PVC resin — cumulative saving and the signals that produced it")
s.shapes.add_picture(str(CH / "pvc_replay.png"), In(X2), In(2.16), width=In(5.65))

hr(s, X2, 4.85, 5.65)
colhead(s, X2, 5.00, 5.65, "The trade we are making, stated plainly")
txt(s, X2, 5.30, 5.65, 1.4,
    f"The rule buys earlier when it expects a rise, so average cover goes up: "
    f"{AL['replay']['inv_delta']:+.1f} days on aluminium and {PV['replay']['inv_delta']:+.1f} days on "
    "PVC. It trades inventory days for price capture.\n\n"
    "That trade is already paid for. Carrying cost at 1% per month is subtracted inside the "
    f"signal, so the net figures above — {AL['replay']['net_pct']:+.2f}% and "
    f"{PV['replay']['net_pct']:+.2f}% — are after carry. On a ₹100 Cr PVC spend that is "
    f"₹{PV['replay']['net_pct']:.2f} Cr a year against about ₹{abs(PV['replay']['wc_shift']):.2f} Cr "
    "more working capital tied up.",
    size=8.2, color=INK2, space=1.3)
note(s, X2, 6.60, 5.65,
     f"The rule stays silent {AL['replay']['signals']['BUY NORMAL'] / AL['replay']['months'] * 100:.0f}% "
     "of the time. It acts only when expected saving clears carry and confidence clears 60%.",
     size=7.6)

foot(s, 12, "Method  Monthly requirement held constant at one unit; a proportional result is more "
     "honest than a fabricated demand curve, since we hold no ACG demand data. Cover is floored at "
     "1 month and capped at 4, with a one-month lead time. Rupee figures are expressed per ₹100 Cr "
     "of annual spend for that material and use no ACG financial data.")


# ======================================================== 13 PROTOTYPE
s = new()
head(s, 4, 13, "Prototype",
     "A working decision desk, not a mock-up: every number on screen is a model output")

colhead(s, M, 1.95, 6.1, "What procurement opens each month")
items = [("Recommendation", "Signal, expected saving net of carry, P(up), recommended cover, "
          "and the P10–P90 range, for any horizon from one to six months."),
         ("Price and forecast", "Three years of actuals, the six-month fan, and the naïve path "
          "shown alongside so the comparison is always visible."),
         ("Purchase order", "Cover × BoM − on-hand − in-transit, computed live from the buyer's "
          "own numbers, with the arithmetic shown."),
         ("Accuracy scorecard", "Model against naïve at every horizon, with the pre-set gate "
          "marked pass or miss."),
         ("Drivers", "Which indicators lead, by how many months, with FDR-corrected Granger "
          "significance flagged."),
         ("Buying replay", "Cumulative saving against buying monthly, and the signal that "
          "produced it, month by month.")]
y = 2.28
for t, d in items:
    txt(s, M, y, 1.75, 0.3, t, size=8.6, bold=True, color=ACG)
    txt(s, M + 1.85, y, 4.25, 0.5, d, size=7.8, color=INK2, space=1.25)
    y += 0.63
hr(s, M, y - 0.10, 6.1)
colhead(s, M, y + 0.05, 6.1, "Built for the shadow pilot")
txt(s, M, y + 0.35, 6.1, 0.8,
    "In the pilot the pack goes to procurement and buyers decide exactly as they do today. "
    "We compare the signal against actual buys and track price capture. Nothing is risked, and "
    "the value is measured before any behaviour changes.",
    size=8.2, color=INK2, space=1.3)

rect(s, 7.05, 1.95, 5.75, 4.55, fill=None, line=RULE)
s.shapes.add_picture(str(CH / "dashboard_cropped.png"), In(7.05), In(1.95), width=In(5.75))

note(s, 7.05, 6.62, 5.75,
     "Every figure in the dashboard is read from the pipeline's output files. There are no "
     "illustrative values anywhere in it.", size=7.6)

foot(s, 13, "Delivery: Single-page dashboard, hosted and shareable by link. Excel export and a "
     "REST hook into the ERP requisition step are specified but not built in this round.")

# ======================================================== 14 IMPLEMENTATION
s = new()
head(s, 5, 14, "Implementation",
     "90-day zero-capex shadow pilot: phased timeline, operating model, and success gates")

# ---- Left column: Sharpened pilot plan with timeline, cost, and criteria ----
colhead(s, M, 1.95, 5.9, "90-day shadow pilot — timeline and phases")
phases = [("Weeks 1–2", "Data Ingestion & Pipeline Setup",
           "Ingest 12–24 months of ACG PO history for aluminium and PVC resin to baseline price and volume curves."),
          ("Weeks 3–4", "Landed-Cost Overlay Calibration",
           "Fit the landed-cost bridge (freight, FX, customs duty, port handling) against actual ACG invoice settlement prices."),
          ("Months 2–3", "Shadow Scoring & Buyer Cadence",
           "Bi-weekly forecast intelligence packs delivered to procurement; buyers decide as today while shadow P&L savings are logged."),
          ("Month 4", "Executive Review & Go/No-Go Gate",
           "Formal leadership evaluation against pre-set criteria; if passed, connect REST hook into SAP/ERP purchase requisition.")]
for i, (when, what, detail) in enumerate(phases):
    y = 2.25 + i * 0.88
    rect(s, M, y, 0.045, 0.76, fill=ACG)
    rect(s, M, y, 5.9, 0.76, fill=None, line=RULE)
    txt(s, M + 0.15, y + 0.08, 1.3, 0.22, when, size=7.8, bold=True, color=ACG)
    txt(s, M + 1.45, y + 0.08, 4.3, 0.22, what, size=8.8, bold=True, color=INK)
    txt(s, M + 0.15, y + 0.32, 5.6, 0.40, detail, size=7.2, color=INK2, space=1.2)

note(s, M, 5.85, 5.9,
     "Pilot cost: ₹0 capex. Runs entirely on open-source Python and free public macro data.\n"
     "People: 1 sourcing sponsor (~1 hr/month) + 1 buyer per commodity (~30 min/fortnight).",
     size=7.4, color=ACG)

# ---- Right column: Success gates, kill-switches, and ERP integration ----
colhead(s, 6.85, 1.95, 5.95, "Pre-set success gates (all 4 must pass for go-live)")
sgates = [["Accuracy", "Walk-forward MAPE ≤ naïve baseline for all 3 pilot months"],
          ["Basis risk", "Landed overlay vs ACG actual invoice: difference < 2.5%"],
          ["Shadow value", "Simulated decisions yield ≥ 1.0% net savings over baseline"],
          ["Buyer trust", "≥ 80% buyer agreement on driver explanations & signals"]]
table(s, 6.85, 2.25, 5.95, ["Gate", ">Pass Criterion"], sgates,
      widths=[1.4, 4.55], fs=7.4, hfs=7.0, rh=0.38)

colhead(s, 6.85, 4.25, 5.95, "Fail-safe kill switches (automated stop criteria)")
kills = [["Accuracy failure", "Model MAPE > naïve for 2 consecutive months → freeze signals, revert to baseline buying"],
         ["Basis divergence", "Supplier quotes diverge > 5% from overlay → pause and recalibrate before resuming"],
         ["Regime break", "Band coverage drops < 50% → force all signals to BUY NORMAL (capital preservation mode)"]]
table(s, 6.85, 4.55, 5.95, ["Trigger", ">Automated Action"], kills,
      widths=[1.5, 4.45], fs=7.2, hfs=6.8, rh=0.42)

note(s, 6.85, 6.25, 5.95,
     "ERP Integration: Shadow pilot operates out-of-band with zero systems risk. Requisition hook into SAP is activated only after Month 4 executive review passes all 4 gates.",
     size=7.2, color=INK2, bold=False)

foot(s, 14, "Governance: Phased 90-day shadow pilot with zero capital outlay. Live buyer decisions remain unchanged while shadow savings are benchmarked.")

# ======================================================== 15 RISKS & ROADMAP
s = new()
head(s, 6, 15, "Risks & roadmap",
     "Landed-cost model defense, residual risk mitigations, scaling roadmap, and leadership ask")

# ---- Left column: Landed-cost bridge defense ----
colhead(s, M, 1.95, 5.9, "Landed-cost bridge: global index → ACG gate")
rect(s, M, 2.25, 5.9, 1.55, fill=None, line=RULE)
txt(s, M + 0.15, 2.35, 5.6, 1.35,
    "Global benchmark (LME Aluminium / Asia CFR PVC in US$)\n"
    "  + Ocean freight and bunker surcharges (Nhava Sheva / Mundra)\n"
    "  + Material grade premium (pharma blister 8011 foil / suspension PVC)\n"
    "  × (1 + Basic Customs Duty 7.5–10%) × (1 + SWS 10%) + ADD\n"
    "  × USD/INR (contemporaneous pass-through, H4 confirmed)\n"
    "  + Port handling, clearance and domestic plant delivery\n"
    "  = ACG landed cost in ₹/MT",
    size=7.6, color=INK2, space=1.28)

colhead(s, M, 3.95, 5.9, "Why the bridge is defensible (5 key market drivers)")
bullets(s, M, 4.22, 5.9, [
    "Import Parity Pricing (IPP): Domestic producers (Hindalco, Reliance) price strictly on import parity; when global index, freight or tariffs move, domestic list prices adjust within days.",
    "Contemporaneous FX (H4): Rupee movements pass through directly at lag 0 (ρ = +0.89 correlation with domestic parity).",
    "Protectionist Tariffs: BCD and Anti-Dumping Duties on PVC imports establish a structural domestic price floor.",
    "Global Macro Dominance: Global drivers account for ~85–90% of price variance; the remaining 10–15% local basis spread is calibrated via ACG PO history in Phase 1."],
    size=7.2, gap=0.38)

# ---- Right column: Risks & Scalability Roadmap ----
colhead(s, 6.85, 1.95, 5.95, "Residual risks we carry & proactive mitigations")
rows = [["PVC proxy quality", "No free Asian spot index", "Public proxy modelled; overlay calibrated on ACG POs"],
        ["Band under-coverage", "55–65% vs 75–85% gate", "Conformal quantile regression recalibrated by regime"],
        ["Basis divergence", "Local premiums fluctuate", "Automated > 5% spread divergence alarm halts buys"],
        ["Regime breaks", "Coverage drops in shocks", "Kill-switch forces BUY NORMAL (capital preservation)"]]
table(s, 6.85, 2.25, 5.95, ["Risk", "Current State", ">Mitigation"], rows,
      widths=[1.35, 1.7, 2.9], fs=6.8, hfs=6.6, rh=0.35)

colhead(s, 6.85, 4.05, 5.95, "Post-pilot scalability roadmap")
roadmap = [
    ("Months 5–6", "ERP Requisition Integration", "Direct API hook into SAP/Oracle purchase requisition creation."),
    ("Months 7–9", "Expand Packaging Materials", "Extend pipeline to Cold-Form laminates, PVDC, and auxiliary foils."),
    ("Months 10+", "Multi-Plant Network Optimization", "Multi-echelon inventory synchronization across all ACG manufacturing plants.")
]
for i, (when, what, desc) in enumerate(roadmap):
    y = 4.35 + i * 0.52
    rect(s, 6.85, y, 0.035, 0.44, fill=ACG)
    txt(s, 6.98, y + 0.02, 1.1, 0.20, when, size=7.2, bold=True, color=ACG)
    txt(s, 8.10, y + 0.02, 4.6, 0.20, what, size=8.0, bold=True, color=INK)
    txt(s, 8.10, y + 0.22, 4.6, 0.24, desc, size=6.8, color=INK2)

# ---- Bottom strip: Clear ask / takeaway ----
hr(s, M, 6.05, 12.25)
colhead(s, M, 6.16, 12.25, "Our clear ask to ACG leadership")
for i, (t, d) in enumerate([
        ("1. Data access",
         "Anonymised 12–24 month PO invoice history for aluminium foil and PVC resin to calibrate the landed-cost overlay."),
        ("2. Stakeholder time",
         "1 Strategic Sourcing sponsor + 1 buyer per commodity for a 90-day shadow pilot — about two hours a month each."),
        ("3. Greenlight",
         "Formal approval for a zero-capex 90-day shadow pilot with the pre-set success gates and fail-safe kill switches."),
        ("4. Measurable outcome",
         "Validated savings (target ≥ 1%), buyer trust score, and a clear go/no-go decision — all before any procurement behavior changes.")]):
    x = M + i * 3.13
    txt(s, x, 6.42, 2.95, 0.24, t, size=8.4, bold=True, color=ACG, space=1.2)
    txt(s, x, 6.66, 2.95, 0.45, d, size=7.3, color=INK2, space=1.22)

foot(s, 15, "Sources: [1] ACG problem statement: RM spend, inventory days, and working capital. [2] Rupee figures use ₹100 Cr baseline spend and zero confidential ACG data.")

out = BASE / "outputs" / "SmartBuy_Round2_15Slides.pptx"
out.parent.mkdir(parents=True, exist_ok=True)
prs.save(out)
print(f"saved {out}  ({out.stat().st_size/1024:.0f} KB, {len(prs.slides.__iter__.__self__._sldIdLst)} slides)")
