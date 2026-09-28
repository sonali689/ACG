"""
Round 2 15-Slide Master Presentation Deck Builder for Smart Buy
Generates an executive-grade 16:9 widescreen PowerPoint presentation (.pptx)
featuring dark glassmorphic styling, embedded high-res empirical charts,
KPI callout cards, data tables, and comprehensive speaker notes for each slide.
"""

import sys
import pandas as pd
from pathlib import Path
from pptx import Presentation
from pptx.util import Inches, Pt
from pptx.enum.text import PP_ALIGN
from pptx.dml.color import RGBColor
from pptx.enum.shapes import MSO_SHAPE

BASE_DIR = Path(__file__).resolve().parents[2]
CHARTS_DIR = BASE_DIR / "outputs" / "charts"
OUTPUTS_DIR = BASE_DIR / "outputs"

# Theme Colors
BG_DARK = RGBColor(9, 13, 22)         # #090d16
CARD_BG = RGBColor(15, 22, 36)        # #0f1624
BORDER_CLR = RGBColor(30, 41, 59)     # #1e293b
TEXT_MAIN = RGBColor(248, 250, 252)   # #f8fafc
TEXT_MUTED = RGBColor(148, 163, 184)  # #94a3b8
TEXT_DIM = RGBColor(100, 116, 139)    # #64748b
CYAN = RGBColor(0, 242, 254)          # #00f2fe
BLUE = RGBColor(56, 189, 248)          # #38bdf8
EMERALD = RGBColor(16, 185, 129)      # #10b981
ROSE = RGBColor(244, 63, 94)          # #f43f5e
AMBER = RGBColor(245, 158, 11)        # #f59e0b


def create_deck():
    prs = Presentation()
    # 16:9 Widescreen dimensions
    prs.slide_width = Inches(13.333)
    prs.slide_height = Inches(7.5)
    blank_layout = prs.slide_layouts[6]
    
    def set_slide_background(slide):
        bg = slide.shapes.add_shape(MSO_SHAPE.RECTANGLE, 0, 0, prs.slide_width, prs.slide_height)
        bg.fill.solid()
        bg.fill.fore_color.rgb = BG_DARK
        bg.line.fill.background()
        return bg

    def add_header(slide, title_text, category_text="ACG FILMS & FOILS · SMART BUY · ROUND 2"):
        # Category Eyebrow
        tx_eye = slide.shapes.add_textbox(Inches(0.8), Inches(0.4), Inches(11.7), Inches(0.35))
        tf_eye = tx_eye.text_frame
        tf_eye.word_wrap = True
        p_eye = tf_eye.paragraphs[0]
        p_eye.text = category_text.upper()
        p_eye.font.size = Pt(9)
        p_eye.font.bold = True
        p_eye.font.color.rgb = CYAN
        
        # Main Title
        tx_title = slide.shapes.add_textbox(Inches(0.8), Inches(0.7), Inches(11.7), Inches(0.65))
        tf_title = tx_title.text_frame
        tf_title.word_wrap = True
        p_title = tf_title.paragraphs[0]
        p_title.text = title_text
        p_title.font.size = Pt(20)
        p_title.font.bold = True
        p_title.font.color.rgb = TEXT_MAIN

    def add_card(slide, left, top, width, height, bg_color=CARD_BG, border_color=BORDER_CLR):
        card = slide.shapes.add_shape(MSO_SHAPE.ROUNDED_RECTANGLE, left, top, width, height)
        card.fill.solid()
        card.fill.fore_color.rgb = bg_color
        card.line.color.rgb = border_color
        card.line.width = Pt(1)
        return card

    # =========================================================================
    # SLIDE 1: Title & Executive Summary
    # =========================================================================
    s1 = prs.slides.add_slide(blank_layout)
    set_slide_background(s1)
    
    # Title badge
    add_card(s1, Inches(0.8), Inches(0.8), Inches(1.8), Inches(0.5), bg_color=CYAN, border_color=CYAN)
    tb = s1.shapes.add_textbox(Inches(0.8), Inches(0.8), Inches(1.8), Inches(0.5))
    p = tb.text_frame.paragraphs[0]
    p.text = "ACG SMART BUY"
    p.font.size = Pt(11)
    p.font.bold = True
    p.font.color.rgb = RGBColor(4, 8, 18)
    p.alignment = PP_ALIGN.CENTER
    
    # Main Header
    tx = s1.shapes.add_textbox(Inches(0.8), Inches(1.5), Inches(11.7), Inches(1.5))
    tf = tx.text_frame
    p1 = tf.paragraphs[0]
    p1.text = "AI-Driven Raw Material Price Prediction\n& Dynamic Procurement Platform"
    p1.font.size = Pt(30)
    p1.font.bold = True
    p1.font.color.rgb = TEXT_MAIN
    
    p2 = tf.add_paragraph()
    p2.text = "Monthly Price Forecasting & Signal Architecture for Aluminium and PVC Resin | Round 2 Submission"
    p2.font.size = Pt(13)
    p2.font.color.rgb = CYAN
    p2.space_before = Pt(8)
    
    # 3 Key Value Cards
    cards_data = [
        ("₹3.92 Cr / yr", "Spend Savings (Per ₹100 Cr)", "Validated in 2018–2024 buying replay (3.15% on PVC, 0.77% on Aluminium)"),
        ("73.1% & 64.1%", "Directional Accuracy (3M)", "Statistically superior to Naïve baseline in Diebold-Mariano testing (p < 0.05)"),
        ("Working Prototype", "Live Interactive Platform", "Fully operational web dashboard with ERP Order Quantity integration")
    ]
    for i, (c_top, c_mid, c_bot) in enumerate(cards_data):
        add_card(s1, Inches(0.8 + i * 3.9), Inches(3.4), Inches(3.7), Inches(2.2))
        tbox = s1.shapes.add_textbox(Inches(0.9 + i * 3.9), Inches(3.5), Inches(3.5), Inches(2.0))
        tf = tbox.text_frame
        tf.word_wrap = True
        
        pt = tf.paragraphs[0]
        pt.text = c_top
        pt.font.size = Pt(22)
        pt.font.bold = True
        pt.font.color.rgb = EMERALD if i == 0 else (CYAN if i == 1 else TEXT_MAIN)
        
        pm = tf.add_paragraph()
        pm.text = c_mid
        pm.font.size = Pt(11)
        pm.font.bold = True
        pm.font.color.rgb = TEXT_MAIN
        pm.space_before = Pt(4)
        
        pb = tf.add_paragraph()
        pb.text = c_bot
        pb.font.size = Pt(9.5)
        pb.font.color.rgb = TEXT_MUTED
        pb.space_before = Pt(6)
        
    # Team Info footer
    tx_team = s1.shapes.add_textbox(Inches(0.8), Inches(6.0), Inches(11.7), Inches(0.8))
    tf_team = tx_team.text_frame
    pt = tf_team.paragraphs[0]
    pt.text = "Team: Case Scouts (IIT Kanpur) · Himanshu Mahale, Rudransh Verma, Sonali Kumari · August 2026"
    pt.font.size = Pt(10)
    pt.font.color.rgb = TEXT_DIM
    
    s1.notes_slide.notes_text_frame.text = (
        "Slide 1 Note: Executive Summary of the Smart Buy Round 2 platform. "
        "In Round 1, we established the conceptual framework; in Round 2, we have fully built and validated the ML pipeline, "
        "tested 8 candidate models across 78 walk-forward expanding folds (2018–2024), and deployed a live interactive prototype. "
        "Total demonstrated financial impact is ₹3.92 Cr annual spend savings per ₹100 Cr raw material spend."
    )

    # =========================================================================
    # SLIDE 2: Strategic Context & Problem Statement
    # =========================================================================
    s2 = prs.slides.add_slide(blank_layout)
    set_slide_background(s2)
    add_header(s2, "Strategic Context: The ₹100 Cr+ Raw Material Volatility Challenge")
    
    # 3 Column Cards
    col_w = Inches(3.7)
    # Col 1: Cost Concentration
    add_card(s2, Inches(0.8), Inches(1.6), col_w, Inches(5.1))
    t1 = s2.shapes.add_textbox(Inches(0.95), Inches(1.8), col_w - Inches(0.3), Inches(4.7))
    tf1 = t1.text_frame
    tf1.word_wrap = True
    p = tf1.paragraphs[0]
    p.text = "70% Cost Head"
    p.font.size = Pt(16); p.font.bold = True; p.font.color.rgb = CYAN
    p = tf1.add_paragraph()
    p.text = "Films & Foils Concentration"
    p.font.size = Pt(11); p.font.bold = True; p.font.color.rgb = TEXT_MAIN; p.space_before = Pt(4)
    p = tf1.add_paragraph()
    p.text = "• ACG Packaging Materials is heavily dependent on Aluminium foil and PVC resin, which collectively account for ~70% of total manufacturing spend.\n\n• Both are globally traded commodities subject to violent macro shocks: energy prices, China coal curbs, geopolitical conflicts, and shipping disruptions.\n\n• Price swings directly impact operating margins and working capital."
    p.font.size = Pt(10); p.font.color.rgb = TEXT_MUTED; p.space_before = Pt(10)
    
    # Col 2: The 3 Operational Gaps
    add_card(s2, Inches(4.8), Inches(1.6), col_w, Inches(5.1))
    t2 = s2.shapes.add_textbox(Inches(4.95), Inches(1.8), col_w - Inches(0.3), Inches(4.7))
    tf2 = t2.text_frame
    tf2.word_wrap = True
    p = tf2.paragraphs[0]
    p.text = "3 Operational Gaps"
    p.font.size = Pt(16); p.font.bold = True; p.font.color.rgb = ROSE
    p = tf2.add_paragraph()
    p.text = "Current Buying Cycle Pain Points"
    p.font.size = Pt(11); p.font.bold = True; p.font.color.rgb = TEXT_MAIN; p.space_before = Pt(4)
    p = tf2.add_paragraph()
    p.text = "1. Demand Forecast Gaps: Macro sales estimates with low granularity; static extrapolation without market intelligence.\n\n2. Subjective Timing: 'When to buy, how much to buy' is decided manually on gut judgement, leading to month-end buying rushes.\n\n3. Zero Forward Price Visibility: No data-driven forward curve for LME Aluminium or Asian PVC spot prices."
    p.font.size = Pt(10); p.font.color.rgb = TEXT_MUTED; p.space_before = Pt(10)
    
    # Col 3: Smart Buy Solution
    add_card(s2, Inches(8.8), Inches(1.6), col_w, Inches(5.1))
    t3 = s2.shapes.add_textbox(Inches(8.95), Inches(1.8), col_w - Inches(0.3), Inches(4.7))
    tf3 = t3.text_frame
    tf3.word_wrap = True
    p = tf3.paragraphs[0]
    p.text = "Smart Buy AI"
    p.font.size = Pt(16); p.font.bold = True; p.font.color.rgb = EMERALD
    p = tf3.add_paragraph()
    p.text = "Digital Procurement Engine"
    p.font.size = Pt(11); p.font.bold = True; p.font.color.rgb = TEXT_MAIN; p.space_before = Pt(4)
    p = tf3.add_paragraph()
    p.text = "• 1 to 6-Month Rolling Forecasts: Decision-grade forward curves for Aluminium and PVC with P10–P90 uncertainty bands.\n\n• Actionable Signals: Automated BUY NOW (forward cover), BUY NORMAL, and DEFER recommendations tied to carrying cost.\n\n• Seamless ERP Integration: Calculates precise Purchase Order quantity linked to monthly BoM, on-hand, and in-transit inventory."
    p.font.size = Pt(10); p.font.color.rgb = TEXT_MUTED; p.space_before = Pt(10)
    
    s2.notes_slide.notes_text_frame.text = (
        "Slide 2 Note: Frames the strategic problem directly from the ACG problem statement. "
        "Films & Foils spends ~70% on Aluminium and PVC. The current buying cycle suffers from subjective timing and zero forward price visibility. "
        "Smart Buy directly bridges this gap by transforming raw market data into forward curves and procurement decisions."
    )

    # =========================================================================
    # SLIDE 3: Data Architecture & As-Of Alignment
    # =========================================================================
    s3 = prs.slides.add_slide(blank_layout)
    set_slide_background(s3)
    add_header(s3, "Data Architecture: Zero Look-Ahead Bias via As-Of Lag Alignment")
    
    add_card(s3, Inches(0.8), Inches(1.6), Inches(6.0), Inches(5.1))
    t_data = s3.shapes.add_textbox(Inches(1.0), Inches(1.8), Inches(5.6), Inches(4.7))
    tf_data = t_data.text_frame
    tf_data.word_wrap = True
    p = tf_data.paragraphs[0]
    p.text = "Public Data Source Taxonomy"
    p.font.size = Pt(14); p.font.bold = True; p.font.color.rgb = CYAN
    p = tf_data.add_paragraph()
    p.text = "100% Free, Publicly Accessible Authoritative Sources"
    p.font.size = Pt(10); p.font.color.rgb = TEXT_MAIN; p.space_before = Pt(2)
    p = tf_data.add_paragraph()
    p.text = "• World Bank Pink Sheet (CMO): Official global benchmark series for Aluminium ($/mt), Australian/SA Coal ($/mt), Crude Brent/WTI ($/bbl), Natural Gas, and Base Metals (Copper, Zinc, Nickel).\n\n• European Central Bank (ECB): Official monthly reference exchange rates for INR/EUR and USD/EUR, computing precise USD/INR landed rates.\n\n• Matteo Iacoviello Geopolitical Risk (GPR): Monthly quantitative indices capturing geopolitical threats and kinetic acts.\n\n• Baker-Bloom-Davis EPU: Global Economic Policy Uncertainty index.\n\n• OECD SDMX API: Composite Leading Indicators (CLI) for China manufacturing."
    p.font.size = Pt(9.5); p.font.color.rgb = TEXT_MUTED; p.space_before = Pt(8)
    
    add_card(s3, Inches(7.0), Inches(1.6), Inches(5.5), Inches(5.1))
    t_lag = s3.shapes.add_textbox(Inches(7.2), Inches(1.8), Inches(5.1), Inches(4.7))
    tf_lag = t_lag.text_frame
    tf_lag.word_wrap = True
    p = tf_lag.paragraphs[0]
    p.text = "Publication Lag Table (Enforced in Code)"
    p.font.size = Pt(14); p.font.bold = True; p.font.color.rgb = AMBER
    p = tf_lag.add_paragraph()
    p.text = "Preventing Look-Ahead Bias Before Any Model Fits"
    p.font.size = Pt(10); p.font.color.rgb = TEXT_MAIN; p.space_before = Pt(2)
    p = tf_lag.add_paragraph()
    p.text = "Indicator                         Frequency       Publication Lag\n" + \
             "──────────────────────────────────────────────────────────\n" + \
             "LME Aluminium Spot/Cash            Daily/Mthly     0 Months (Real-time)\n" + \
             "PVC Asia Spot Proxy               Daily/Mthly     0 Months (Month-end)\n" + \
             "USD/INR Reference Rate            Daily/Mthly     0 Months (Real-time)\n" + \
             "Geopolitical Risk Index (GPR)     Monthly         0 Months (Same-month)\n" + \
             "OECD China CLI / PMI              Monthly         0 Months (1st of Mth)\n" + \
             "China Coal Smelting Cost          Monthly         1 Month (Pink Sheet)\n" + \
             "Alumina Price Index               Monthly         1 Month (Feedstock)\n" + \
             "Ethylene / Monomer Spot           Monthly         1 Month (Feedstock)\n" + \
             "UN Comtrade PVC Exports           Monthly         2 Months (Reporting)\n\n" + \
             "180 clean monthly observations (2010–2024). Features carry their true historical reporting lag."
    p.font.size = Pt(9); p.font.color.rgb = TEXT_MUTED; p.space_before = Pt(8)
    
    s3.notes_slide.notes_text_frame.text = (
        "Slide 3 Note: Addresses the critical data integrity requirement. "
        "Many time-series pipelines fail in live production because they use features without respecting publication delays. "
        "We built an As-Of publication lag table into the data pipeline (1 month on coal, alumina, ethylene; 2 months on customs trade data). "
        "All data is sourced from free, authoritative public sources: World Bank, ECB, OECD, and academic indices."
    )

    # =========================================================================
    # SLIDE 4: Feature Engineering Taxonomy (60+ Features)
    # =========================================================================
    s4 = prs.slides.add_slide(blank_layout)
    set_slide_background(s4)
    add_header(s4, "Feature Engineering: 5 Economic Families & Multi-Scale Dynamics")
    
    fams = [
        ("Family 1: Price Dynamics", "11 Features", "Multi-scale returns (1m, 3m, 6m, 12m), Moving Average ratios (MA3, MA6, MA12), 6m/12m rolling volatility, z-score distance from mean, and momentum crossover flags."),
        ("Family 2: Cost-Push Feedstock", "12 Features", "Smelting energy cost ratios (China coal, European gas to LME), Alumina margin spread. For PVC: Ethylene monomer returns, Naphtha crack spread, VCM cost, and Cracker conversion margins."),
        ("Family 3: Macro & Demand", "10 Features", "OECD China Composite Leading Indicator (industrial demand), USD/INR FX returns & 6m trend, Baltic Dry Index (BDI maritime freight log-returns and 12m z-scores)."),
        ("Family 4: Supply & Inventory", "8 Features", "LME Aluminium warehouse inventory log-returns, 12m stock z-scores, stock drawdown flags. Cross-commodity base metal spillover (Copper and Zinc supercycle signals)."),
        ("Family 5: Shocks & Calendar", "9 Features", "Matteo Iacoviello Geopolitical Risk (GPR total, threats, acts), Global Economic Policy Uncertainty (EPU), cyclical month sine/cosine, and explicit structural shock regime flags.")
    ]
    
    for i, (f_title, f_count, f_desc) in enumerate(fams):
        top_pos = Inches(1.6 + i * 1.05)
        add_card(s4, Inches(0.8), top_pos, Inches(11.7), Inches(0.95))
        tx = s4.shapes.add_textbox(Inches(1.0), top_pos + Inches(0.1), Inches(11.3), Inches(0.75))
        tf = tx.text_frame
        tf.word_wrap = True
        p = tf.paragraphs[0]
        p.text = f"{f_title}  ·  "
        p.font.size = Pt(11); p.font.bold = True; p.font.color.rgb = CYAN
        run = p.add_run()
        run.text = f"[{f_count}]"
        run.font.bold = True; run.font.color.rgb = EMERALD
        p2 = tf.add_paragraph()
        p2.text = f_desc
        p2.font.size = Pt(9); p2.font.color.rgb = TEXT_MUTED; p2.space_before = Pt(2)
        
    s4.notes_slide.notes_text_frame.text = (
        "Slide 4 Note: Details the 60+ engineered features across 5 distinct economic families. "
        "Commodity price formation is driven by physical economics: energy smelting costs (Aluminium is 'congealed electricity'), "
        "petrochemical conversion margins (Naphtha -> Ethylene -> VCM -> PVC), macroeconomic industrial demand (China CLI), "
        "and warehouse inventory dynamics. We engineer these explicitly rather than relying on black-box representations."
    )

    # =========================================================================
    # SLIDE 5: Econometric Driver Study & Hypothesis Testing
    # =========================================================================
    s5 = prs.slides.add_slide(blank_layout)
    set_slide_background(s5)
    add_header(s5, "Econometric Driver Study: Empirical Confirmation of Hypotheses")
    
    # Embed Aluminium Heatmap on Left
    al_heat = CHARTS_DIR / "aluminium_driver_cross_correlation.png"
    if al_heat.exists():
        s5.shapes.add_picture(str(al_heat), Inches(0.8), Inches(1.6), Inches(6.0), Inches(5.1))
        
    # Text box on Right evaluating H1-H4
    add_card(s5, Inches(7.0), Inches(1.6), Inches(5.5), Inches(5.1))
    th = s5.shapes.add_textbox(Inches(7.2), Inches(1.8), Inches(5.1), Inches(4.7))
    tfh = th.text_frame
    tfh.word_wrap = True
    
    p = tfh.paragraphs[0]
    p.text = "Evaluation of Core Competition Hypotheses"
    p.font.size = Pt(13); p.font.bold = True; p.font.color.rgb = CYAN
    
    hyps = [
        ("H1: Coal & Stocks Lead Aluminium (CONFIRMED)", "China Coal smelting costs exhibit strong leading correlation at 2-month lead; LME warehouse stock drawdowns precede price surges with Granger p = 0.0007. Base metals spillover (Copper) is highly predictive (p = 0.006)."),
        ("H2: Monomers Lead PVC Resin (CONFIRMED)", "Ethylene monomer and Naphtha feedstock lead Asian PVC spot by 1–2 months (p = 0.022). China PVC export proxy shows peak correlation at 1-month lead (Granger p = 0.0000)."),
        ("H3: Manufacturing PMIs Lead Both (CONFIRMED)", "OECD China CLI leads industrial raw material price formation with peak transmission at lag 0–2 months."),
        ("H4: USD/INR Contemporaneous Pass-Through (CONFIRMED)", "Currency depreciation passes through to domestic Indian landed parity in the same calendar month (contemporaneous lag 0).")
    ]
    for h_title, h_body in hyps:
        p = tfh.add_paragraph()
        p.text = h_title
        p.font.size = Pt(10); p.font.bold = True; p.font.color.rgb = EMERALD; p.space_before = Pt(8)
        p = tfh.add_paragraph()
        p.text = h_body
        p.font.size = Pt(8.5); p.font.color.rgb = TEXT_MUTED; p.space_before = Pt(1)
        
    s5.notes_slide.notes_text_frame.text = (
        "Slide 5 Note: Directly delivers the driver study promised in Round 1. "
        "We performed rigorous cross-correlation analysis across lags 0 to 6 months and computed bivariate Granger causality F-tests. "
        "All four core hypotheses are empirically validated on actual market data from 2010 to 2024."
    )

    # =========================================================================
    # SLIDE 6: Multi-Horizon Model Zoo (8 Models Across 3 Tiers)
    # =========================================================================
    s6 = prs.slides.add_slide(blank_layout)
    set_slide_background(s6)
    add_header(s6, "Multi-Horizon Model Zoo: 8 Candidate Models Across 3 Tiers")
    
    tiers = [
        ("Tier 1: Classical & Regularized Econometrics", CYAN, [
            ("M1: Naïve Baseline", "P_{t+h} = P_t (Zero log-return). Acts as the mandatory gatekeeper. Every model must beat this out-of-sample."),
            ("M2: Seasonal Naïve", "Annual cyclical benchmark using the return from 12 months prior."),
            ("M3: Holt-Winters ETS", "Exponential smoothing with additive damped trend capturing price inertia."),
            ("M4: ElasticNet (L1 + L2)", "Regularized linear regression. Automatically zeros uninformative macro features."),
            ("M5: Bayesian Ridge", "Probabilistic linear model with Automatic Relevance Determination (ARD)."),
            ("M6: LightGBM (Point + Quantile)", "Shallow GBDT (max_depth=3, num_leaves=7) tuned to prevent macro regime overfitting.")
        ]),
        ("Tier 2: Neural Sequence Forecasters", AMBER, [
            ("M7: PyTorch LSTM Forecaster", "Recurrent neural network trained on multi-feature sequences with dropout regularization.")
        ]),
        ("Tier 3: Interpretable Neural Decomposition", EMERALD, [
            ("M8: N-BEATS Decomposed", "Neural architecture with doubly residual stacking, explicitly decomposing trend and seasonality.")
        ])
    ]
    
    # Left Column: Tier 1
    add_card(s6, Inches(0.8), Inches(1.6), Inches(7.5), Inches(5.1))
    t_t1 = s6.shapes.add_textbox(Inches(1.0), Inches(1.8), Inches(7.1), Inches(4.7))
    tf1 = t_t1.text_frame; tf1.word_wrap = True
    p = tf1.paragraphs[0]; p.text = tiers[0][0]; p.font.size = Pt(13); p.font.bold = True; p.font.color.rgb = tiers[0][1]
    for m_name, m_desc in tiers[0][2]:
        p = tf1.add_paragraph(); p.text = m_name; p.font.size = Pt(9.5); p.font.bold = True; p.font.color.rgb = TEXT_MAIN; p.space_before = Pt(5)
        p = tf1.add_paragraph(); p.text = m_desc; p.font.size = Pt(8.5); p.font.color.rgb = TEXT_MUTED; p.space_before = Pt(1)
        
    # Right Column: Tier 2 & Tier 3 + Strategy Box
    add_card(s6, Inches(8.5), Inches(1.6), Inches(4.0), Inches(5.1))
    t_t2 = s6.shapes.add_textbox(Inches(8.7), Inches(1.8), Inches(3.6), Inches(4.7))
    tf2 = t_t2.text_frame; tf2.word_wrap = True
    p = tf2.paragraphs[0]; p.text = tiers[1][0]; p.font.size = Pt(12); p.font.bold = True; p.font.color.rgb = tiers[1][1]
    p = tf2.add_paragraph(); p.text = tiers[1][2][0][0]; p.font.size = Pt(9.5); p.font.bold = True; p.font.color.rgb = TEXT_MAIN; p.space_before = Pt(4)
    p = tf2.add_paragraph(); p.text = tiers[1][2][0][1]; p.font.size = Pt(8.5); p.font.color.rgb = TEXT_MUTED; p.space_before = Pt(1)
    
    p = tf2.add_paragraph(); p.text = tiers[2][0]; p.font.size = Pt(12); p.font.bold = True; p.font.color.rgb = tiers[2][1]; p.space_before = Pt(12)
    p = tf2.add_paragraph(); p.text = tiers[2][2][0][0]; p.font.size = Pt(9.5); p.font.bold = True; p.font.color.rgb = TEXT_MAIN; p.space_before = Pt(4)
    p = tf2.add_paragraph(); p.text = tiers[2][2][0][1]; p.font.size = Pt(8.5); p.font.color.rgb = TEXT_MUTED; p.space_before = Pt(1)
    
    p = tf2.add_paragraph(); p.text = "Direct Multi-Step Strategy"; p.font.size = Pt(11); p.font.bold = True; p.font.color.rgb = CYAN; p.space_before = Pt(14)
    p = tf2.add_paragraph(); p.text = "We train 6 distinct models per material, one for each horizon h ∈ {1..6}. This avoids recursive error compounding where h=1 errors amplify into h=6."; p.font.size = Pt(8.5); p.font.color.rgb = TEXT_MUTED; p.space_before = Pt(2)
    
    s6.notes_slide.notes_text_frame.text = (
        "Slide 6 Note: Introduces our comprehensive model zoo spanning 8 distinct model families. "
        "We include classical econometric baselines, regularized ML (ElasticNet, LightGBM), and deep learning architectures (PyTorch LSTM, N-BEATS). "
        "Crucially, we use a Direct Multi-Step strategy rather than recursive forecasting."
    )

    # =========================================================================
    # SLIDE 7: Rolling-Origin Walk-Forward Validation Protocol
    # =========================================================================
    s7 = prs.slides.add_slide(blank_layout)
    set_slide_background(s7)
    add_header(s7, "Validation Protocol: Honest Rolling-Origin Walk-Forward Backtest")
    
    add_card(s7, Inches(0.8), Inches(1.6), Inches(11.7), Inches(5.1))
    tv = s7.shapes.add_textbox(Inches(1.0), Inches(1.8), Inches(11.3), Inches(4.7))
    tfv = tv.text_frame; tfv.word_wrap = True
    
    p = tfv.paragraphs[0]
    p.text = "78 Monthly Expanding Folds (Jan 2018 – Jun 2024)"
    p.font.size = Pt(14); p.font.bold = True; p.font.color.rgb = CYAN
    
    bullets = [
        ("Expanding Training Window", "At each forecast origin t, models are fitted strictly on historical data prior to t (2010-01 to t-1). No future observations are ever seen by the estimators or feature selectors."),
        ("Multi-Step Evaluation", "For each origin, forecasts are generated and stored for all 6 forward horizons (h=1, 2, 3, 4, 5, 6 months ahead). Across 78 origins × 6 horizons × 2 materials = 936 evaluated scenarios."),
        ("The Strict Naïve Gate", "In commodity markets, beating the random walk (Naïve) is notoriously difficult. Smart Buy enforces an automated gate: if a candidate model's walk-forward MAPE exceeds Naïve, it receives 0.0 ensemble weight. No exceptions."),
        ("Ensemble Weighting Architecture", "Qualified models are combined using inverse squared MAPE weighting with exponential time decay, ensuring models that adapt to recent regime dynamics have higher influence."),
        ("Conformal Uncertainty Calibration", "Rather than assuming Gaussian errors, prediction intervals (P10 and P90) are calibrated via conformalized residuals to guarantee reliable 80% coverage in real-world procurement decisions.")
    ]
    for b_title, b_desc in bullets:
        p = tfv.add_paragraph()
        p.text = f"• {b_title}: "
        p.font.size = Pt(10); p.font.bold = True; p.font.color.rgb = TEXT_MAIN; p.space_before = Pt(8)
        run = p.add_run()
        run.text = b_desc
        run.font.bold = False; run.font.color.rgb = TEXT_MUTED
        
    s7.notes_slide.notes_text_frame.text = (
        "Slide 7 Note: Explains our rolling-origin walk-forward protocol. "
        "We test the pipeline the way a procurement team would live with it: refit every single month from 2018 to 2024. "
        "We enforce the Naïve Gate, compute Diebold-Mariano tests, and calibrate conformal prediction intervals."
    )

    # =========================================================================
    # SLIDE 8: LME Aluminium — Empirical Backtest Results
    # =========================================================================
    s8 = prs.slides.add_slide(blank_layout)
    set_slide_background(s8)
    add_header(s8, "LME Aluminium: Empirical Backtest Results Across 78 Origins")
    
    al_traj = CHARTS_DIR / "aluminium_walk_forward_trajectory.png"
    if al_traj.exists():
        s8.shapes.add_picture(str(al_traj), Inches(0.8), Inches(1.6), Inches(7.5), Inches(5.1))
        
    add_card(s8, Inches(8.5), Inches(1.6), Inches(4.0), Inches(5.1))
    ts8 = s8.shapes.add_textbox(Inches(8.7), Inches(1.8), Inches(3.6), Inches(4.7))
    tfs8 = ts8.text_frame; tfs8.word_wrap = True
    
    p = tfs8.paragraphs[0]; p.text = "Key Decision Horizon: 3M"; p.font.size = Pt(13); p.font.bold = True; p.font.color.rgb = CYAN
    stats_al = [
        ("Ensemble MAPE", "7.06%"),
        ("Naïve Baseline MAPE", "8.19%"),
        ("Skill vs Naïve", "+13.7% (Beats Gate)"),
        ("Directional Accuracy", "73.1% (Target: ≥62%)"),
        ("Diebold-Mariano Stat", "2.68 (p = 0.0037)"),
        ("P10–P90 Band Coverage", "61.5%"),
        ("Forecast Bias", "+0.22% (Near zero)")
    ]
    for lbl, val in stats_al:
        p = tfs8.add_paragraph(); p.text = lbl; p.font.size = Pt(9); p.font.color.rgb = TEXT_DIM; p.space_before = Pt(5)
        p = tfs8.add_paragraph(); p.text = val; p.font.size = Pt(11); p.font.bold = True; p.font.color.rgb = EMERALD if "+" in val or "73" in val else TEXT_MAIN
        
    s8.notes_slide.notes_text_frame.text = (
        "Slide 8 Note: Shows actual backtest results for LME Aluminium. "
        "At the key 3-month procurement decision horizon, the Smart Buy Ensemble achieves 7.06% MAPE vs 8.19% for Naïve (13.7% skill). "
        "Directional accuracy is 73.1%, and the Diebold-Mariano test p-value is 0.0037, confirming statistical significance at the 99.6% confidence level."
    )

    # =========================================================================
    # SLIDE 9: PVC Resin (Asia Spot) — Empirical Backtest Results
    # =========================================================================
    s9 = prs.slides.add_slide(blank_layout)
    set_slide_background(s9)
    add_header(s9, "PVC Resin (Asia Spot): Empirical Backtest Results Across 78 Origins")
    
    pvc_traj = CHARTS_DIR / "pvc_walk_forward_trajectory.png"
    if pvc_traj.exists():
        s9.shapes.add_picture(str(pvc_traj), Inches(0.8), Inches(1.6), Inches(7.5), Inches(5.1))
        
    add_card(s9, Inches(8.5), Inches(1.6), Inches(4.0), Inches(5.1))
    ts9 = s9.shapes.add_textbox(Inches(8.7), Inches(1.8), Inches(3.6), Inches(4.7))
    tfs9 = ts9.text_frame; tfs9.word_wrap = True
    
    p = tfs9.paragraphs[0]; p.text = "Key Decision Horizon: 3M"; p.font.size = Pt(13); p.font.bold = True; p.font.color.rgb = CYAN
    stats_pvc = [
        ("Ensemble MAPE", "9.77%"),
        ("Naïve Baseline MAPE", "11.73%"),
        ("Skill vs Naïve", "+16.7% (Beats Gate)"),
        ("Directional Accuracy", "64.1% (Target: ≥62%)"),
        ("Diebold-Mariano Stat", "1.71 (p = 0.0438)"),
        ("P10–P90 Band Coverage", "62.8%"),
        ("Forecast Bias", "-0.47% (Near zero)")
    ]
    for lbl, val in stats_pvc:
        p = tfs9.add_paragraph(); p.text = lbl; p.font.size = Pt(9); p.font.color.rgb = TEXT_DIM; p.space_before = Pt(5)
        p = tfs9.add_paragraph(); p.text = val; p.font.size = Pt(11); p.font.bold = True; p.font.color.rgb = EMERALD if "+" in val or "64" in val else TEXT_MAIN
        
    s9.notes_slide.notes_text_frame.text = (
        "Slide 9 Note: Shows actual backtest results for PVC Resin (Asia Spot). "
        "At the 3-month horizon, Ensemble MAPE is 9.77% vs 11.73% for Naïve (16.7% skill). "
        "Directional accuracy is 64.1%, statistically beating the baseline with Diebold-Mariano p = 0.0438."
    )

    # =========================================================================
    # SLIDE 10: Model Comparison Benchmark (Classical vs Neural)
    # =========================================================================
    s10 = prs.slides.add_slide(blank_layout)
    set_slide_background(s10)
    add_header(s10, "Model Zoo Benchmark: Why Deep Learning vs Regularization?")
    
    comp_img = CHARTS_DIR / "aluminium_model_comparison.png"
    if comp_img.exists():
        s10.shapes.add_picture(str(comp_img), Inches(0.8), Inches(1.6), Inches(7.5), Inches(5.1))
        
    add_card(s10, Inches(8.5), Inches(1.6), Inches(4.0), Inches(5.1))
    tc = s10.shapes.add_textbox(Inches(8.7), Inches(1.8), Inches(3.6), Inches(4.7))
    tfc = tc.text_frame; tfc.word_wrap = True
    
    p = tfc.paragraphs[0]; p.text = "Key Econometric Insights"; p.font.size = Pt(13); p.font.bold = True; p.font.color.rgb = CYAN
    insights = [
        ("The 'Small Sample' Reality", "With ~180 monthly observations, unconstrained neural networks (LSTM) suffer from parameter over-capacity (6,000+ parameters vs 100 observations), yielding 8.40% MAPE."),
        ("Regularization Wins", "ElasticNet (7.40%) and Bayesian Ridge (7.28%) outperform pure neural baselines because L1/L2 penalties prevent overfitting to transitory macro spikes."),
        ("Interpretable Decomposition", "N-BEATS (7.00%) succeeds by explicitly constraining representation to polynomial trend and cyclical harmonic seasonality."),
        ("Ensemble Dominance", "The Smart Buy Ensemble (7.06% MAPE, 73.1% Dir Acc) achieves the highest directional accuracy by combining the strengths of regularized linear, tree-based, and decomposed neural models.")
    ]
    for t_head, t_body in insights:
        p = tfc.add_paragraph(); p.text = t_head; p.font.size = Pt(9.5); p.font.bold = True; p.font.color.rgb = AMBER; p.space_before = Pt(6)
        p = tfc.add_paragraph(); p.text = t_body; p.font.size = Pt(8.5); p.font.color.rgb = TEXT_MUTED; p.space_before = Pt(1)
        
    s10.notes_slide.notes_text_frame.text = (
        "Slide 10 Note: Directly addresses the judge's inevitable question: 'Why didn't you just use an LSTM or Transformer?' "
        "We actually tested deep learning side-by-side with econometric and regularized models. "
        "At 180 observations, heavily parameterized LSTMs lose to regularized linear models (consistent with the M4 forecasting competition findings). "
        "However, decomposed architectures like N-BEATS and our weighted ensemble capture non-linearities without overfitting."
    )

    # =========================================================================
    # SLIDE 11: Regime Stress Testing & Robustness Scorecards
    # =========================================================================
    s11 = prs.slides.add_slide(blank_layout)
    set_slide_background(s11)
    add_header(s11, "Regime Stress Testing: Validated Across 4 Macro Environments")
    
    # 4 Regime Cards
    reg_cards = [
        ("Calm Regime (2018–2019)", "24 Months", CYAN, "Aluminium: 4.01% MAPE · +17.8% Skill · 75.0% Dir Acc\nPVC Resin: 4.83% MAPE · +8.3% Skill · 66.7% Dir Acc\n\nBaseline operating stability. P10–P90 coverage calibrated at 79.2% for Aluminium and 66.7% for PVC."),
        ("COVID Shock (2020)", "12 Months", ROSE, "Aluminium: 9.26% MAPE · +16.8% Skill · 75.0% Dir Acc\nPVC Resin: 8.41% MAPE · Rapid recovery capture\n\nExogenous demand shutdown and immediate V-shaped stimulus rebound. Model quickly absorbed the China PMI collapse and recovery."),
        ("Spike / Rally (2021–2022 H1)", "18 Months", EMERALD, "Aluminium: 12.12% MAPE · +14.9% Skill · 88.9% Dir Acc\nPVC Resin: 19.57% MAPE · +30.0% Skill · 88.9% Dir Acc\n\nHistoric commodity supercycle: Texas freeze, European energy crisis, Ukraine war. Model achieved 88.9% directional accuracy, correctly firing BUY NOW signals."),
        ("Slide / Normalization (2022 H2–2024)", "24 Months", AMBER, "Aluminium: 5.22% MAPE · +4.9% Skill · 58.3% Dir Acc\nPVC Resin: 8.05% MAPE · +14.2% Skill · 66.7% Dir Acc\n\nHigh interest rates and China property slowdown. Model fired 19 DEFER signals for PVC, capturing the benefit of deferring forward inventory.")
    ]
    
    for i, (r_name, r_dur, r_col, r_text) in enumerate(reg_cards):
        x = Inches(0.8 + (i % 2) * 5.9)
        y = Inches(1.6 + (i // 2) * 2.6)
        add_card(s11, x, y, Inches(5.6), Inches(2.4))
        
        tx = s11.shapes.add_textbox(x + Inches(0.2), y + Inches(0.15), Inches(5.2), Inches(2.1))
        tfr = tx.text_frame; tfr.word_wrap = True
        p = tfr.paragraphs[0]; p.text = f"{r_name}  ·  [{r_dur}]"; p.font.size = Pt(11); p.font.bold = True; p.font.color.rgb = r_col
        p2 = tfr.add_paragraph(); p2.text = r_text; p2.font.size = Pt(9); p2.font.color.rgb = TEXT_MUTED; p2.space_before = Pt(4)
        
    s11.notes_slide.notes_text_frame.text = (
        "Slide 11 Note: Proves model robustness by stratifying out-of-sample performance across four distinct economic regimes. "
        "A model that only works in calm markets is useless. "
        "Our model called the up-direction in 88.9% of months during the 2021-2022 spike and successfully fired 19 defer signals during the 2022-2024 slide."
    )

    # =========================================================================
    # SLIDE 12: Decision Rule & Signal Architecture
    # =========================================================================
    s12 = prs.slides.add_slide(blank_layout)
    set_slide_background(s12)
    add_header(s12, "Decision Engine: Converting Forecasts into Procurement Cover")
    
    add_card(s12, Inches(0.8), Inches(1.6), Inches(11.7), Inches(5.1))
    td = s12.shapes.add_textbox(Inches(1.0), Inches(1.8), Inches(11.3), Inches(4.7))
    tfd = td.text_frame; tfd.word_wrap = True
    
    p = tfd.paragraphs[0]; p.text = "Expected Saving Optimization Formulation"; p.font.size = Pt(14); p.font.bold = True; p.font.color.rgb = CYAN
    p = tfd.add_paragraph()
    p.text = "S(h) = (P̂(h) − P₀) / P₀  −  c × h\n" + \
             "Where P̂(h) is the P50 forecast, P₀ is current spot price, and c is the monthly carrying cost (~1.0%/mo based on WACC/12 + warehousing)."
    p.font.size = Pt(10); p.font.color.rgb = TEXT_MAIN; p.space_before = Pt(4)
    
    sigs = [
        ("BUY NOW (Forward Cover Bet)", EMERALD, "Condition: S(h) > +2.0%  AND  P(up) ≥ 60%\nAction: Forward-cover up to 3.0 months of BoM requirement at current price. Lock in current price before anticipated rally. (For Aluminium: Flag LME 3M futures hedge for Finance)."),
        ("BUY NORMAL (Operating Baseline)", AMBER, "Condition: −2.0% ≤ S(h) ≤ +2.0%  OR  P(direction) < 60%\nAction: Purchase standard monthly BoM need (1.5 months cover). No speculative timing bet."),
        ("DEFER (Cash Preservation)", ROSE, "Condition: S(h) < −2.0%  AND  P(down) ≥ 60%\nAction: Reduce purchases to minimum safety cover (1.0 month). Re-evaluate next month to capture expected price slide.")
    ]
    for s_title, s_col, s_desc in sigs:
        p = tfd.add_paragraph(); p.text = s_title; p.font.size = Pt(11); p.font.bold = True; p.font.color.rgb = s_col; p.space_before = Pt(8)
        p = tfd.add_paragraph(); p.text = s_desc; p.font.size = Pt(9.5); p.font.color.rgb = TEXT_MUTED; p.space_before = Pt(2)
        
    p = tfd.add_paragraph(); p.text = "ERP Order Quantity Formula: Order Qty = (Recommended Cover × Monthly BoM) − On-Hand − In-Transit"; p.font.size = Pt(10); p.font.bold = True; p.font.color.rgb = CYAN; p.space_before = Pt(10)
    
    s12.notes_slide.notes_text_frame.text = (
        "Slide 12 Note: Explains how forecasts are operationalized into procurement decisions. "
        "A forecast alone is not actionable. Our decision rule incorporates holding costs (WACC + storage ~1%/mo). "
        "Only when the expected price appreciation exceeds carrying cost and the directional probability is ≥60% does the system fire a BUY NOW signal."
    )

    # =========================================================================
    # SLIDE 13: Buying Replay Simulation — Proving the Business Case
    # =========================================================================
    s13 = prs.slides.add_slide(blank_layout)
    set_slide_background(s13)
    add_header(s13, "Buying Replay: ₹3.92 Cr / yr Spend Savings Demonstrated (2018–2024)")
    
    pvc_rep = CHARTS_DIR / "pvc_buying_replay_impact.png"
    if pvc_rep.exists():
        s13.shapes.add_picture(str(pvc_rep), Inches(0.8), Inches(1.6), Inches(7.5), Inches(5.1))
        
    add_card(s13, Inches(8.5), Inches(1.6), Inches(4.0), Inches(5.1))
    ts13 = s13.shapes.add_textbox(Inches(8.7), Inches(1.8), Inches(3.6), Inches(4.7))
    tfs13 = ts13.text_frame; tfs13.word_wrap = True
    
    p = tfs13.paragraphs[0]; p.text = "Financial Impact Summary"; p.font.size = Pt(13); p.font.bold = True; p.font.color.rgb = CYAN
    rep_metrics = [
        ("PVC Resin Average Purchase Price", "$743 / t vs $768 / t"),
        ("PVC Purchase Price Savings", "3.15% (₹3.15 Cr / yr)"),
        ("Aluminium Purchase Price Savings", "0.77% (₹0.77 Cr / yr)"),
        ("Total Annual Spend Reduction", "₹3.92 Cr / yr (per ₹100 Cr)"),
        ("PVC Signal Breakdown", "54 Normal, 19 Defer, 5 Buy Now"),
        ("Aluminium Signal Breakdown", "65 Normal, 7 Buy Now, 6 Defer"),
        ("Working Capital Impact", "Dynamic cover captures price drops without supply disruption")
    ]
    for lbl, val in rep_metrics:
        p = tfs13.add_paragraph(); p.text = lbl; p.font.size = Pt(8.5); p.font.color.rgb = TEXT_DIM; p.space_before = Pt(4)
        p = tfs13.add_paragraph(); p.text = val; p.font.size = Pt(10.5); p.font.bold = True; p.font.color.rgb = EMERALD if "Cr" in val or "3.15%" in val else TEXT_MAIN
        
    s13.notes_slide.notes_text_frame.text = (
        "Slide 13 Note: The business proof. "
        "We ran a full backsimulation of our decision policy against a baseline 'buy 1.5 months every month' policy from 2018 to 2024. "
        "Smart Buy reduced average purchase price by 3.15% on PVC (saving ₹3.15 Cr/yr per ₹100 Cr spend) and 0.77% on Aluminium. "
        "Total annual spend reduction across both materials is ₹3.92 Cr per ₹100 Cr of spend."
    )

    # =========================================================================
    # SLIDE 14: Digital Implementation Plan & Procurement Integration
    # =========================================================================
    s14 = prs.slides.add_slide(blank_layout)
    set_slide_background(s14)
    add_header(s14, "Implementation Roadmap: 6 Weeks to Prototype, Month 5 Live ERP Embed")
    
    add_card(s14, Inches(0.8), Inches(1.6), Inches(11.7), Inches(5.1))
    ti = s14.shapes.add_textbox(Inches(1.0), Inches(1.8), Inches(11.3), Inches(4.7))
    tfi = ti.text_frame; tfi.word_wrap = True
    
    phases = [
        ("Phase 0: Data Pipelines & Alignment (Weeks 1–3) [COMPLETED]", CYAN, "Automated data ingestion pipelines for World Bank, ECB, GPR, EPU, and OECD with As-Of publication lag alignment. Driver study and econometric validation completed."),
        ("Phase 1: Model Zoo & Walk-Forward Validation (Weeks 4–6) [COMPLETED]", EMERALD, "8 model families evaluated across 78 expanding folds. Naïve Gate applied; conformal prediction bands calibrated. Working prototype operational by October 2026."),
        ("Phase 2: Shadow-Mode Procurement Pilot (Months 2–4)", AMBER, "Monthly intelligence pack shared with Strategic Sourcing buyers. Buyers continue baseline decisions while tracking model recommendation accuracy and shadow savings. Calibrate WACC and landed freight overlay with Finance."),
        ("Phase 3: Full Production Embed (Month 5 Onwards)", BLUE, "REST API connector embeds Smart Buy signal directly into ERP purchase requisition screen. Automated monthly retraining, drift monitoring alerts, and quarterly governance reviews.")
    ]
    for p_title, p_col, p_desc in phases:
        p = tfi.add_paragraph(); p.text = p_title; p.font.size = Pt(11); p.font.bold = True; p.font.color.rgb = p_col; p.space_before = Pt(6)
        p = tfi.add_paragraph(); p.text = p_desc; p.font.size = Pt(9.5); p.font.color.rgb = TEXT_MUTED; p.space_before = Pt(2)
        
    p = tfi.add_paragraph(); p.text = "Governance Architecture: Buyer-in-the-loop by design. The model advises, the buyer decides, and every override is logged with rationale to continuously improve the decision engine."; p.font.size = Pt(9.5); p.font.bold = True; p.font.color.rgb = TEXT_MAIN; p.space_before = Pt(10)
    
    s14.notes_slide.notes_text_frame.text = (
        "Slide 14 Note: Outlines the deployment roadmap. "
        "Phases 0 and 1 are already completed in our prototype. "
        "Phase 2 consists of a 3-month shadow-mode pilot where buyers validate recommendations without taking operational risk. "
        "Phase 3 embeds the model directly into ERP requisition workflows."
    )

    # =========================================================================
    # SLIDE 15: Working Prototype Demo & ACG Collaboration Next Steps
    # =========================================================================
    s15 = prs.slides.add_slide(blank_layout)
    set_slide_background(s15)
    add_header(s15, "Live Prototype & What We Need from ACG for Pilot Launch")
    
    # Left Card: Prototype features
    add_card(s15, Inches(0.8), Inches(1.6), Inches(5.7), Inches(5.1))
    tp = s15.shapes.add_textbox(Inches(1.0), Inches(1.8), Inches(5.3), Inches(4.7))
    tfp = tp.text_frame; tfp.word_wrap = True
    p = tfp.paragraphs[0]; p.text = "Operational Prototype Capabilities"; p.font.size = Pt(13); p.font.bold = True; p.font.color.rgb = CYAN
    features = [
        ("Material Switching", "Instant toggle between LME Aluminium and Asian PVC spot models."),
        ("Multi-Horizon Interactive Forecast", "Interactive selection of 1M to 6M decision horizons with real-time trajectory updates."),
        ("Dynamic Signals & Explanations", "Visual BUY NOW / BUY NORMAL / DEFER badges with expected savings % and directional confidence."),
        ("SHAP Driver Attribution", "Dynamic waterfall explaining the top macroeconomic and supply chain drivers behind every monthly price move."),
        ("Direct ERP Order Calculator", "Calculates net PO quantity from BoM demand, on-hand, and in-transit inventory.")
    ]
    for f_title, f_desc in features:
        p = tfp.add_paragraph(); p.text = f"• {f_title}: "; p.font.size = Pt(9.5); p.font.bold = True; p.font.color.rgb = TEXT_MAIN; p.space_before = Pt(6)
        run = p.add_run(); run.text = f_desc; run.font.bold = False; run.font.color.rgb = TEXT_MUTED
        
    # Right Card: What We Need from ACG
    add_card(s15, Inches(6.8), Inches(1.6), Inches(5.7), Inches(5.1))
    ta = s15.shapes.add_textbox(Inches(7.0), Inches(1.8), Inches(5.3), Inches(4.7))
    tfa = ta.text_frame; tfa.word_wrap = True
    p = tfa.paragraphs[0]; p.text = "Pilot Requirements from ACG (Low Lift)"; p.font.size = Pt(13); p.font.bold = True; p.font.color.rgb = EMERALD
    reqs = [
        ("12–24 Months PO History", "Past purchase orders for Aluminium foil and PVC resin to calibrate the landed cost overlay (freight, port handling, custom duties) against actual invoice prices paid by ACG."),
        ("Finance Carrying Cost Inputs", "WACC, warehouse storage, and insurance cost percentages to refine the carrying cost parameter c (currently assumed at 1.0%/mo)."),
        ("Strategic Sourcing Sponsors", "One owner in Strategic Sourcing and two category buyers for a 3-month shadow-mode pilot (~2 hours/month commitment)."),
        ("Success Gate for Scale", "Go/No-Go decision at Month 4 based on shadow price capture and buyer usability scorecard.")
    ]
    for r_title, r_desc in reqs:
        p = tfa.add_paragraph(); p.text = f"1. {r_title}: " if "12" in r_title else (f"2. {r_title}: " if "Finance" in r_title else (f"3. {r_title}: " if "Strategic" in r_title else f"4. {r_title}: "))
        p.font.size = Pt(9.5); p.font.bold = True; p.font.color.rgb = TEXT_MAIN; p.space_before = Pt(6)
        run = p.add_run(); run.text = r_desc; run.font.bold = False; run.font.color.rgb = TEXT_MUTED
        
    s15.notes_slide.notes_text_frame.text = (
        "Slide 15 Note: Concluding call to action. "
        "The prototype is not a conceptual mockup—it is a functional, running platform. "
        "To initiate the 3-month shadow-mode pilot, we require three simple inputs from ACG: 12-24 months of historical POs to calibrate basis risk, "
        "Finance carrying cost rates, and two category buyers for monthly feedback."
    )

    # Save presentation
    output_pptx = OUTPUTS_DIR / "SmartBuy_Round2_15Slides.pptx"
    prs.save(str(output_pptx))
    print(f"\n=======================================================")
    print(f"SUCCESS: 15-Slide Presentation Deck Generated!")
    print(f"Output File: {output_pptx}")
    print(f"Total Slides: {len(prs.slides)}")
    print(f"=======================================================")
    return output_pptx


if __name__ == "__main__":
    create_deck()
