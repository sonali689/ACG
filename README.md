<p align="center">
  <strong>S M A R T &nbsp; B U Y</strong><br>
  <em>AI-based Raw Material Price Prediction for Aluminium and PVC Resin</em>
</p>

<p align="center">
  <strong>ACG Films &amp; Foils</strong> · Digital &amp; AI | Procurement | Strategic Sourcing<br>
  Round 2 Submission · Team Case Scouts · IIT Kanpur
</p>

---

## Overview

Aluminium and PVC resin represent roughly **70% of manufacturing cost** for pharmaceutical blister packs at ACG Films & Foils. Today, both materials are purchased on judgement with no forward view of price — exposing procurement to rapid 2× price swings, excess inventory, and tied-up working capital.

**Smart Buy** is a 6-month forward pricing and decision system that:
- Forecasts monthly prices for each material up to **six months ahead**
- Validates every forecast against a **naïve baseline** before it earns weight
- Converts the forecast into a **buy-now / buy-normal / defer** signal with recommended cover
- Subtracts **carrying cost** before generating any signal — a 2% expected rise over 3 months is not a buy if holding costs 3%

Every number in this repository, the deck, and the dashboard is produced by code. None is typed by hand.

---

## Results

Walk-forward backtest, **66 leak-free rolling origins**, January 2018 – June 2024. Decision horizon h = 3 months.

| Metric | Aluminium | PVC Resin |
|---|:---:|:---:|
| Model MAPE | 7.73% | 10.69% |
| Naïve MAPE | 8.53% | 12.65% |
| **Skill over naïve** | **+9.4%** | **+15.5%** |
| Directional accuracy | 71.2% | 63.6% |
| Diebold–Mariano p (one-sided) | 0.041 | 0.089 |
| **Net saving after carrying cost** | **+0.19%** | **+1.68%** |
| Change in inventory days | +1.4 | **−0.5** |

> Rupee figures are per ₹100 Cr of annual spend for that material. They use no ACG financial data.

### Acceptance Gates (set in Round 1, reported unchanged)

| Gate | Threshold | Aluminium | PVC | Status |
|---|:---:|:---:|:---:|:---:|
| MAPE ≤ naïve | — | ✓ | ✓ | **Pass** |
| Skill at h=3 | ≥ 15% | 9.4% | 15.5% | **AL missed** |
| Directional accuracy | ≥ 62% | 71.2% | 63.6% | **Pass** |
| DM test | p < 0.10 | 0.041 | 0.089 | **Pass** |
| Band coverage | 75–85% | 57.6% | 56.1% | **Missed** |

Two gates are missed and are reported as missed. Aluminium is exchange-traded and close to efficient, so price-level skill is genuinely hard; the value shows up in direction. Band coverage fails in regime breaks — recalibrating per volatility regime is the first fix for the pilot.

### Self-Correction

An earlier run estimated ensemble weights using errors from every fold, **including the fold being scored**. That is leakage and it flattered the result. Re-estimated with weights from strictly prior folds only:

| | Before (leaked) | After (corrected) |
|---|:---:|:---:|
| Aluminium MAPE h=3 | 7.06% | 7.73% |
| PVC MAPE h=3 | 9.77% | 10.69% |
| PVC replay, net | 3.01% | 1.68% |

Every figure in this repo is the corrected one. The first 12 origins become burn-in, so the window is 66 folds rather than 78.

---

## Quick Start

### Prerequisites

- Python 3.11 or 3.12 (avoid 3.13 — LightGBM wheel availability)
- Git

### Setup

```bash
# Clone and enter the project
git clone https://github.com/sonali689/SmartBuy.git
cd SmartBuy

# Create virtual environment
python -m venv .venv

# Activate it
# macOS/Linux:
source .venv/bin/activate
# Windows PowerShell:
.venv\Scripts\Activate.ps1
# Windows CMD:
.venv\Scripts\activate.bat

# Install dependencies
pip install -r requirements.txt
```

### Run the Full Pipeline

```bash
make                                              # or run the five commands below individually
```

```bash
python src/validation/leakfree_all_horizons.py    # 1. leak-free scorecard, all horizons
python src/decision/replay_leakfree.py            # 2. buying replay on corrected forecasts
python dashboard/build_data.py                    # 3. assembles dashboard/data.json
python src/deck/make_charts_acg.py                # 4. charts in the ACG palette
python src/deck/build_deck_round1_style.py        # 5. the 15-slide deck
```

Steps 3–5 depend on 1 and 2. Full install notes including PyTorch setup in [SETUP.md](SETUP.md).

> **Note:** PyTorch is **not** required unless you re-train the LSTM and N-BEATS models (`requirements-torch.txt`). Everything downstream reads saved predictions from `outputs/scorecards/`.

### Pre-flight Check

```bash
python check_env.py
```

---

## Repository Structure

```
SmartBuy/
│
├── config/                           # Configuration (YAML)
│   ├── lag_table.yaml                #   publication lag per data source
│   ├── features.yaml                 #   feature specification and families
│   └── thresholds.yaml               #   acceptance gates and decision rule params
│
├── data/
│   ├── raw/                          # Dated public data pulls (never overwritten)
│   └── processed/                    # Master dataset + per-material feature matrices
│
├── src/
│   ├── ingestion/                    # Data downloaders and as-of panel assembly
│   │   ├── downloaders.py            #   fetches from World Bank, ECB, FRED, OECD, Comtrade
│   │   └── build_dataset.py          #   builds master_dataset.csv with publication-lag alignment
│   │
│   ├── features/                     # Feature engineering
│   │   └── engineer_features.py      #   60+ features across 5 economic families
│   │
│   ├── models/                       # The 8-model forecasting zoo
│   │   └── model_zoo.py              #   Naive, Seasonal, ETS, ElasticNet, BayesianRidge,
│   │                                 #   LightGBM (point + quantile), LSTM, N-BEATS
│   │
│   ├── validation/                   # Walk-forward backtesting and statistical testing
│   │   ├── walk_forward.py           #   78-origin expanding-window walk-forward harness
│   │   ├── leakfree_all_horizons.py  #   leak-free ensemble re-estimation, all horizons
│   │   ├── metrics.py                #   MAPE, skill, DM test, coverage, direction
│   │   ├── fix_pack.py               #   error correlation, band diagnostics, hypothesis verdicts
│   │   └── replay_leakfree.py        #   leak-free walk-forward replay
│   │
│   ├── explainability/               # Econometric driver analysis
│   │   ├── driver_study.py           #   lead-lag, Granger causality, H1-H4 hypothesis verdicts
│   │   └── generate_deck_charts.py   #   cross-correlation and driver charts
│   │
│   ├── decision/                     # Procurement decision engine
│   │   ├── buying_replay.py          #   buy/defer rule and inventory simulation
│   │   └── replay_leakfree.py        #   buying replay on leak-free forecasts
│   │
│   └── deck/                         # Presentation generation
│       ├── build_deck_round1_style.py#   15-slide PowerPoint in ACG visual language
│       ├── build_deck_pptx.py        #   alternative deck builder
│       └── make_charts_acg.py        #   chart generation in ACG palette
│
├── dashboard/                        # Self-contained decision desk
│   ├── index.html                    #   interactive dashboard (CDN Chart.js)
│   ├── index_offline.html            #   offline version (Chart.js vendored inline)
│   ├── build_data.py                 #   assembles data.json from pipeline outputs
│   ├── build_dashboard.py            #   builds dashboard HTML from template
│   ├── _template.html                #   dashboard template
│   └── data.json                     #   all dashboard data (generated)
│
├── outputs/                          # All generated outputs
│   ├── scorecards/                   #   walk-forward predictions and ensemble weights
│   ├── tables/                       #   statistical tables, coverage, lead-lag studies
│   ├── charts/                       #   matplotlib charts
│   ├── charts_acg/                   #   charts in ACG corporate palette
│   └── SmartBuy_Round2_15Slides.pptx #   the final presentation
│
├── check_env.py                      # Environment validation script
├── Makefile                          # One-command pipeline execution
├── requirements.txt                  # Core dependencies
├── requirements-torch.txt            # PyTorch dependencies (optional, for retraining)
├── SETUP.md                          # Detailed setup instructions
└── README.md                         # This file
```

### Traceability: Which Files Produce the Reported Numbers

| Reported Number | Produced By |
|---|---|
| Model predictions, all horizons | `src/validation/walk_forward.py` |
| Corrected scorecard and ensemble weights | `src/validation/leakfree_all_horizons.py` |
| Error correlation, band diagnostics, H1–H4 verdicts | `src/validation/fix_pack.py` |
| Buying replay, inventory days, ₹ savings | `src/decision/replay_leakfree.py` |
| Lead–lag study, Granger causality | `src/explainability/driver_study.py` |
| Dashboard data | `dashboard/build_data.py` |
| Presentation deck | `src/deck/build_deck_round1_style.py` |

Every number in the deck traces to a file in `outputs/`. None is typed by hand.

---

## Method

### Data

**Public sources only** — no proprietary feeds or paid subscriptions required:

| Source | Series | Publication Lag |
|---|---|:---:|
| World Bank Commodity Price Data (Pink Sheet) | Coal, gas, crude, aluminium, base metals | 1 month |
| UN Comtrade | Alumina, bauxite, ethylene, VCM, PVC trade volumes | 2 months |
| ECB reference rates | USD/INR, EUR crosses | 0 months |
| Caldara–Iacoviello GPR & Baker–Bloom–Davis EPU | Geopolitical risk, policy uncertainty indices | 0 months |
| OECD composite leading indicators | China demand proxy (CLI) | 1 month |
| Shock-event flags | Tariff, COVID, freeze, war, Red Sea | Dated at announcement |

181 monthly observations, January 2010 to June 2024.

### As-of Alignment

Every series carries its real publication lag. A single function, `visible_at(panel, origin)`, returns only what was published at a given origin. Every feature is built from its output. There is no second path into the feature matrix.

### Target

Log-return: `y = ln(P[t+h] / P[t])`, converted back with `P₀ · exp(ŷ)`. Prices ranged $1,450–$3,985 over the sample, so the variance of the level is unstable; the variance of the return is not.

### Models

**Direct multi-horizon** — one model per month ahead (h = 1 to 6), so errors do not compound the way recursive forecasting compounds them. Eight families across three tiers:

| Tier | Model | Description |
|---|---|---|
| Classical | M1: Naïve | Zero-return baseline (the gatekeeper) |
| Classical | M2: Seasonal Naïve | 12-month seasonal repeat |
| Classical | M3: ETS (Holt-Winters) | Exponential smoothing with damped trend |
| Regularised | M4: ElasticNet | L1/L2 regularised linear regression |
| Regularised | M5: Bayesian Ridge | Probabilistic linear with adaptive shrinkage |
| Tree | M6: LightGBM | Point + quantile (q = 0.10, 0.50, 0.90) |
| Neural | M7: LSTM | Deep recurrent sequence model (PyTorch) |
| Neural | M8: N-BEATS | Polynomial trend + Fourier seasonal decomposition |

### Naïve Gate

Any model whose walk-forward MAPE is at or above the naïve baseline receives **zero ensemble weight**. Qualified models are weighted by inverse squared MAPE, estimated on strictly prior folds. The LSTM failed the gate on both materials and was excluded automatically by the rule published in Round 1 — not by judgement.

### Confidence Bands

Quantile LightGBM at q = 0.10 / 0.50 / 0.90 with split-conformal calibration. Coverage is measured and reported as measured.

### Decision Rule

```
S(h) = (P̂(h) − P₀) / P₀  −  c × h
```

| Signal | Condition | Cover |
|---|---|:---:|
| **Buy Now** | S(h) > +2% and P(up) ≥ 60% | 3.0 months |
| **Buy Normal** | −2% ≤ S(h) ≤ +2%, or confidence < 60% | 1.5 months |
| **Defer** | S(h) < −2% and P(down) ≥ 60% | 1.0 month |

`c` = 1.0%/month carrying cost (placeholder pending ACG Finance inputs).

### Statistical Tests

- **Diebold–Mariano** one-sided, with Harvey–Leybourne–Newbold small-sample correction and Newey–West HAC variance at lag h−1 (overlapping h-step forecasts are serially correlated)
- **Granger causality** with Benjamini–Hochberg FDR correction across all indicators per material

---

## Key Findings

**A constrained neural model beat an unconstrained one.** N-BEATS reached 7.34% MAPE on aluminium, better than every linear and tree model. The LSTM reached 9.28% and failed the naïve gate. N-BEATS projects onto polynomial and Fourier bases, so its hypothesis space is restricted to trend and cycle; the LSTM must discover structure from ~150 training points with thousands of free parameters. The lesson: **architectural constraint substitutes for data**.

**Ensemble members are mostly near-duplicates.** Mean forecast-error correlation between members is 0.83. N-BEATS against the rest is 0.57, making it the only genuine diversifier and the reason it carries most of the weight.

**The rule mostly stays silent.** Buy-normal fires in 95% of months on aluminium and 68% on PVC. It acts only when expected saving clears carry and confidence clears 60%.

**PVC defers more, and that reduces inventory.** 17 defer signals against 4 buy-now, which is why PVC cover falls 0.5 days while aluminium rises 1.4.

---

## Dashboard

The interactive decision desk is a self-contained single-page application — no server, no build step.

```bash
# Option 1: Open directly in a browser
open dashboard/index.html

# Option 2: Serve locally
python -m http.server 8000 --directory dashboard
```

- `dashboard/index.html` — CDN version (requires internet)
- `dashboard/index_offline.html` — fully offline (Chart.js vendored inline, zero external requests)

Every value on screen is read from `data.json`, which is generated from the pipeline outputs. There are no illustrative numbers anywhere in it.

---

## Known Limitations

| Limitation | Detail |
|---|---|
| **No free PVC spot index** | A public proxy is modelled; the India landed price is a separate overlay. Largest single data risk. |
| **Band coverage fails the gate** | 55–65% against 75–85%, concentrated in regime breaks. |
| **Basis risk** | The index is not ACG's landed price. Calibrating the overlay needs 12–24 months of ACG PO history. |
| **Carrying cost is a placeholder** | Set at 1.0%/month pending ACG Finance inputs. |
| **Limited statistical power** | 66 folds and one economic cycle. 5 of 12 horizon-material pairs clear DM p < 0.10. |

---

## Team

| | |
|---|---|
| **Team** | Case Scouts |
| **Members** | Himanshu Mahale · Rudransh Verma · Sonali Kumari |
| **Institute** | Indian Institute of Technology Kanpur, 2026 |
| **Contact** | sonali23@iitk.ac.in · +91 87899 84718 |

**Problem statement:** *"Smart Buy – AI based Raw Material Price Prediction"*, ACG Films & Foils, Digital & AI | Procurement | Strategic Sourcing.

---

## License

This repository is part of a competition submission and is not licensed for redistribution.
