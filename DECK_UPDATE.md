# Updating the Round 2 deck to match v2

The 15-slide deck (`legacy/outputs_round2_original/SmartBuy_Round2_15Slides.pptx`) reports numbers that v2 no longer supports.
Below, each slide lists what to remove and what to put in its place. All replacement numbers come from `outputs/`.

**Suggested story:** *"We audited our own Round 2 pipeline, found three serious flaws, fixed them, and built a test that proves
the leak is gone. Under honest validation, aluminium is near-efficient, while the PVC proxy shows significant 1–2 month skill and
a buy/defer rule that beats random timing (p = 0.002). The bands are now calibrated. The system says 'buy normal' when it doesn't know."*
Owning the correction is far stronger in front of judges than being caught.

| Slide | Remove | Replace with |
|---|---|---|
| 1 Title | "₹1.68 Cr PVC saving", "71% aluminium direction", "−0.5 d" | PVC replay **+0.45% net, beats random timing p = 0.002** (≈ ₹0.45 Cr per ₹100 Cr, −0.2 inventory days). PVC **+20.7% skill at 1 month (p = 0.0004)**. Bands calibrated: 64–78% coverage, up from 55–65%. |
| 2 Problem | "9.4% / 12.9% skill, DM p = 0.0409 / 0.082", "+1.68% net on PVC" | h=3 skill: Al +3.7% (p 0.16), PVC +10.3% (p 0.11). PVC h=1 +20.7%, h=2 +15.9% (both significant). Replay as above. |
| 3–4 Drivers & data | "PVC spot proxy", UN Comtrade, ethylene/VCM proxies, LME stocks, "181 obs", "60+ features" | Targets: World Bank LME aluminium; **BLS PPI plastic resins (WPU066) as PVC proxy**. Sources: World Bank, BLS/Fed via FRED, ECB, GPR, EPU, OECD. **No simulated series**: say plainly that Round 2's PVC price was simulated and is replaced. 41 aluminium / 36 PVC features. Lag table: `config/pipeline.yaml`. |
| 5 Driver study | All H1–H4 verdicts, "copper leads by 6 months", "China exports ρ = 0.39", "ρ = +0.89" | `outputs/drivers/hypotheses.json`: H1 coal not supported, LME stocks not testable; H2 partial (Brent leads PVC by 1 month, q < 0.001); H3 China CLI leads both by ~2 months (supported); H4 mechanical pass-through, but FX is ~1% of Al rupee-price variance and ~36% for PVC. Aluminium's strong links (copper 0.68) are same-month. |
| 6 Solution | "78 folds", "Eight model families", PyTorch | Embargoed walk-forward; 10 models in three tiers (statistical incl. VECM; local ML with drivers; **global ML on 74 commodity series**: LightGBM + N-BEATS in JAX); naïve gate; conformal + GARCH bands. |
| 7 Model zoo | "LSTM excluded itself", "N-BEATS projects onto bases… architectural constraint substitutes for data" (it was an MLP) | Model ladder from the dashboard. **Real N-BEATS is the best single model on both materials** (Al +6.5%, PVC +10.0% p = 0.035 at h=3). It works because it is trained globally on 74 series with early stopping: *pooling data substitutes for data*. |
| 8 Explainability | Hand-written driver note, "attribution on out-of-fold predictions", error corr 0.79/0.56 | Generated note from `outputs/forecast_now.json`; TreeSHAP bars; mean member error correlation 0.87 (Al) / 0.84 (PVC), with seasonal naïve, ElasticNet and VECM the most independent. |
| 9 Validation | "Skill and direction rise with horizon", regime table | **Remove that claim; it was the leak's fingerprint.** New regime table from `outputs/scorecards/*_regimes.csv`. Add the future-perturbation test: scramble all post-origin data, forecasts do not change; the Round 2 logic fails this test. |
| 10 Results vs gates | Whole table and "correction we made" box | Table from `outputs/scorecards/*_scorecard.csv` (dev + holdout). The "correction" box becomes the audit (`CHANGES.md` A1–A3). |
| 11 Bands | 55–65% table, "conformal applied but too tight" | Calibrated vs uncalibrated coverage (README table). The conformal step now exists and lifts coverage by up to 13 points. Still short in shocks. |
| 12 Replay | All numbers, "84/78 months", WC signs | `outputs/replay_summary.json`: Al −0.31% (p 0.97: no timing value), PVC +0.45% (p 0.002), PVC holdout −0.08%. Add the perfect-foresight ceiling (Al 2.9%, PVC 1.3%). Execution at next month's price. |
| 13 Dashboard | Old screenshot | New screenshot of `dashboard/index.html` (stale-data banner visible until data is refreshed; refresh first). |
| 14 Implementation | (mostly fine) | Keep the 90-day shadow pilot and kill switches. Add "data refresh + ALFRED vintages" to weeks 1–2. Accuracy gate: "MAPE ≤ naïve" is realistic; a "≥1% net saving" gate is above what the backtest supports, so use "beats random timing". |
| 15 Risks & roadmap | "Global drivers account for ~85–90% of variance" (unsourced) | Add risks: PVC proxy is a US index; holdout is short and ran on stale drivers. Roadmap: futures curve for aluminium first, then Chronos, an Asian PVC price feed, and ACG PO calibration. |

Before presenting: refresh `data/raw`, run `make`, and re-read every number on the slides from `outputs/`.
