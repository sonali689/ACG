import re
from pathlib import Path

BASE = Path("c:/Users/dubey/Downloads/ACG/smartbuy")
src_file = BASE / "src/deck/build_deck_round1_style.py.bak"
dst_file = BASE / "src/deck/build_deck_round1_style.py"

with open(src_file, "r", encoding="utf-8") as f:
    text = f.read()

s5_marker = '# ======================================================== 5 LEAD-LAG'
s7_marker = '# ======================================================== 7 ARCHITECTURE'
s14_marker = '# ======================================================== 14 PROTOTYPE'
s15_marker = '# ======================================================== 15 IMPLEMENTATION'
end_marker = 'out = BASE /'

p_s5 = text.find(s5_marker)
p_s7 = text.find(s7_marker)
p_s14 = text.find(s14_marker)
p_s15 = text.find(s15_marker)
p_end = text.find(end_marker)

# Section 1: Intro up to Slide 4
part1 = text[:p_s5]

# Section 2: Combined Slide 5 (Drivers & Hypotheses)
slide5 = '''# ======================================================== 5 DRIVERS & HYPOTHESES
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

'''

# Section 3: Slides 7 to 13 renumbered as 6 to 12
part3 = text[p_s7:p_s14]

# Renumber slide 7 -> 6
part3 = part3.replace('head(s, 2, 7, "Solution"', 'head(s, 2, 6, "Solution"')
part3 = part3.replace('foot(s, 7,', 'foot(s, 6,')

# Renumber slide 8 -> 7
part3 = part3.replace('head(s, 2, 8, "Solution"', 'head(s, 2, 7, "Solution"')
part3 = part3.replace('foot(s, 8,', 'foot(s, 7,')

# Renumber slide 9 -> 8
part3 = part3.replace('head(s, 2, 9, "Solution"', 'head(s, 2, 8, "Solution"')
part3 = part3.replace('foot(s, 9,', 'foot(s, 8,')

# Renumber slide 10 -> 9
part3 = part3.replace('head(s, 3, 10, "Validation"', 'head(s, 3, 9, "Validation"')
part3 = part3.replace('foot(s, 10,', 'foot(s, 9,')

# Renumber slide 11 -> 10
part3 = part3.replace('head(s, 3, 11, "Validation"', 'head(s, 3, 10, "Validation"')
part3 = part3.replace('foot(s, 11,', 'foot(s, 10,')

# Renumber slide 12 -> 11
part3 = part3.replace('head(s, 3, 12, "Validation"', 'head(s, 3, 11, "Validation"')
part3 = part3.replace('foot(s, 12,', 'foot(s, 11,')

# Renumber slide 13 -> 12
part3 = part3.replace('head(s, 4, 13, "Prototype"', 'head(s, 4, 12, "Prototype"')
part3 = part3.replace('foot(s, 13,', 'foot(s, 12,')

# Update Section headers comments in part3
part3 = part3.replace('# ======================================================== 7 ARCHITECTURE', '# ======================================================== 6 ARCHITECTURE')
part3 = part3.replace('# ======================================================== 8 MODEL LADDER', '# ======================================================== 7 MODEL LADDER')
part3 = part3.replace('# ======================================================== 9 EXPLAINABILITY', '# ======================================================== 8 EXPLAINABILITY')
part3 = part3.replace('# ======================================================== 10 PROTOCOL', '# ======================================================== 9 PROTOCOL')
part3 = part3.replace('# ======================================================== 11 RESULTS VS GATES', '# ======================================================== 10 RESULTS VS GATES')
part3 = part3.replace('# ======================================================== 12 UNCERTAINTY', '# ======================================================== 11 UNCERTAINTY')
part3 = part3.replace('# ======================================================== 13 REPLAY', '# ======================================================== 12 REPLAY')

# Section 4: Slide 13 (was 14) Prototype Decision Desk with REAL screenshot embedded
slide13 = '''# ======================================================== 13 PROTOTYPE
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

'''

# Section 5: Slide 14 Implementation (active=5)
slide14 = '''# ======================================================== 14 IMPLEMENTATION
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
     "Pilot cost: ₹0 capex. Runs entirely on open-source Python and free public macro data.\\n"
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

'''

# Section 6: Slide 15 Risks & Roadmap (active=6)
slide15 = '''# ======================================================== 15 RISKS & ROADMAP
s = new()
head(s, 6, 15, "Risks & roadmap",
     "Landed-cost model defense, residual risk mitigations, scaling roadmap, and leadership ask")

# ---- Left column: Landed-cost bridge defense ----
colhead(s, M, 1.95, 5.9, "Landed-cost bridge: global index → ACG gate")
rect(s, M, 2.25, 5.9, 1.55, fill=None, line=RULE)
txt(s, M + 0.15, 2.35, 5.6, 1.35,
    "Global benchmark (LME Aluminium / Asia CFR PVC in US$)\\n"
    "  + Ocean freight and bunker surcharges (Nhava Sheva / Mundra)\\n"
    "  + Material grade premium (pharma blister 8011 foil / suspension PVC)\\n"
    "  × (1 + Basic Customs Duty 7.5–10%) × (1 + SWS 10%) + ADD\\n"
    "  × USD/INR (contemporaneous pass-through, H4 confirmed)\\n"
    "  + Port handling, clearance and domestic plant delivery\\n"
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

'''

# Section 7: Output file saving
part7 = text[p_end:]

new_content = part1 + slide5 + part3 + slide13 + slide14 + slide15 + part7

with open(dst_file, "w", encoding="utf-8") as f:
    f.write(new_content)

print(f"Successfully wrote {dst_file} ({len(new_content)} bytes)")
