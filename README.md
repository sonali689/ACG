# Smart Buy v2: AI-based raw material price prediction for aluminium and PVC resin

ACG Films & Foils · Digital & AI | Procurement | Strategic Sourcing · Team Case Scouts, IIT Kanpur

Smart Buy forecasts aluminium and PVC resin prices one to six months ahead from public data, scores every
forecast against the naïve "no change" baseline in a leak-free walk-forward test, and turns the forecast into a
buy-now / buy-normal / defer signal net of carrying cost.

**Version 2 is a rebuild of the Round 2 pipeline after an internal audit.** The audit found a simulated PVC price,
drivers derived from the target price, and a look-ahead leak in training. All three are fixed, and an automated
test now proves the leak is gone. See `CHANGES.md` for the full list, and `legacy/` for the original code and outputs.

---

## Results (all numbers produced by `make`; none typed by hand)

Development window: 78 monthly forecast origins, Jan 2018 – Jun 2024. Holdout: origins from Jan 2025, scored once.
Headline forecast = equal-weight average of the models that beat naïve on their own past forecasts (pre-specified).

### Accuracy vs naïve, development window

| Horizon | Aluminium skill | DM p | PVC proxy skill | DM p |
|---|---|---|---|---|
| 1 month | +1.5% | 0.29 | **+21.4%** | **0.0004** |
| 2 months | +3.8% | 0.16 | **+16.0%** | **0.029** |
| 3 months (decision) | +3.9% | 0.14 | +10.0% | 0.12 |
| 4 months | +4.9% | 0.11 | +0.2% | 0.49 |
| 5 months | +4.2% | 0.16 | +1.4% | 0.42 |
| 6 months | +4.4% | 0.13 | +0.5% | 0.47 |

Skill = 1 − MAPE(model)/MAPE(naïve). DM p = one-sided Diebold–Mariano, Newey–West variance, HLN correction.

How to read this:

- **Aluminium.** The models are a few percent better than naïve at every horizon, but never significantly so. That is
  the expected result for an exchange-traded metal whose price already reflects public information.
- **PVC proxy.** The skill is real and significant at one and two months, then fades. Part of the reason is that the proxy is
  a producer price index, which moves more slowly than a spot price, so its next step is partly predictable.
- **PVC holdout (2025–26, 14–19 origins).** The ensemble does not beat naïve (−14% at 3 months). The driver data in `data/raw`
  stops in Dec 2024, so the driver models were running without inputs for most of the holdout. Refresh the data and re-run
  before drawing conclusions.
- **Best single model.** The real N-BEATS (global, trend + seasonality stacks) is the best single model on both materials
  at 3 months in every training run. Its exact skill varies between training runs, so no significance claim is made for it alone.

### Uncertainty bands (target 75–85% coverage of an 80% band)

| | h=1 | h=2 | h=3 | h=4 | h=5 | h=6 |
|---|---|---|---|---|---|---|
| Aluminium, calibrated | 78.2 | 73.1 | 71.8 | 71.8 | 71.8 | 70.5 |
| Aluminium, uncalibrated | 76.9 | 65.4 | 65.4 | 64.1 | 60.3 | 57.7 |
| PVC, calibrated | 76.9 | 74.4 | 71.8 | 67.9 | 66.7 | 67.9 |
| PVC holdout, calibrated | 78.9 | 77.8 | 76.5 | 81.2 | 73.3 | 78.6 |

Round 2 reported 55–65% coverage while claiming a conformal step that did not exist. That step is now real, and it lifts
coverage to 66–78%. Coverage is still a few points short at longer horizons and in shocks (50% in COVID for aluminium).

### Buying replay (decision rule unchanged from Round 1, h = 3)

| | Aluminium | PVC proxy (dev) | PVC proxy (holdout) |
|---|---|---|---|
| Months | 78 | 78 | 17 |
| Signals (now / normal / defer) | 2 / 72 / 4 | 5 / 59 / 14 | 1 / 14 / 2 |
| Net saving after carry | −0.19% | **+0.41%** | −0.08% |
| Better than random timing? (permutation p) | 0.83 (no) | **0.003 (yes)** | 0.44 (no) |
| Perfect-foresight ceiling | +2.93% | +1.31% | +1.67% |
| Inventory days vs baseline | +0.6 | +0.6 | +0.9 |

Per ₹100 Cr of annual PVC spend, +0.41% is about ₹0.41 Cr a year, with 0.6 more days of inventory. This is a backtest on a
US index, not on ACG's purchases. The pilot exists to measure the real number.

### Driver study (real series, 2000–2024, Granger at a fixed 3-month lag, FDR-corrected)

- **Aluminium.** The strongest relationships are same-month (copper ρ = +0.68, zinc +0.63, energy +0.46). They explain price moves
  but cannot forecast them. Two drivers survive FDR as leading indicators: the **OECD China leading indicator** (leads by about
  2 months, q = 0.02) and copper (q = 0.07).
- **PVC proxy.** **Brent crude leads by 1 month** (ρ = +0.41, q < 0.001). The China leading indicator, US gas, the energy index and
  USD/INR are also significant.
- **Hypotheses.** H1 (coal, LME stocks → aluminium): coal not supported, and LME stocks cannot be tested because no free data exists.
  H2 (feedstock → PVC): partial, with Brent supported and the monomer PPI proxy not. H3 (activity leads): supported for the China CLI
  on both materials. H4 (FX → landed price): mechanical one-for-one pass-through, but FX explains only about 1% of aluminium's
  monthly rupee-price variance and about 36% for the PVC index.

---

## How it works

```
data/raw (public files)
  └─ src/sb/data.py         real series only; publication lags applied in one place (visible_panel)
      └─ src/sb/features.py trailing-window features; data-driven shock indicators
          └─ src/sb/backtest.py   walk-forward, EMBARGO: train only on rows whose outcome was published
                ├─ statistical: naïve, seasonal naïve, drift, ETS, ARIMA, VECM, GARCH volatility
                ├─ local ML with drivers: ElasticNet (in-fold selection + tuning), LightGBM
                └─ global ML on 74 commodity series: LightGBM + classifier, N-BEATS (JAX)
          └─ src/sb/combine.py    naïve gate, ensembles, conformal bands, DM tests, dev vs holdout
          └─ src/sb/replay.py     buying replay, permutation test, perfect-foresight bound
          └─ src/sb/drivers.py    lead-lag, Granger, FDR, H1–H4 verdicts
          └─ src/sb/forecast_now.py  live forecast, SHAP attribution, buyer note, stale-data warnings
dashboard/                  single-file decision desk built from outputs/
tests/test_leakage.py       future-perturbation test: scramble all post-origin data, forecasts must not change
```

Every design choice was fixed in `config/pipeline.yaml` before the first backtest.

## Run it

```bash
pip install -r requirements.txt
python check_env.py
python run_all.py   # tests -> backtest -> scoring -> dashboard -> decks (see SETUP.md)
```

Open `dashboard/index_offline.html`. **Before presenting, refresh `data/raw`** (see `SETUP.md`). The World Bank file ends in Dec 2024.

## Known limitations

- **PVC target is a US producer price index** (BLS WPU066), not an Asian spot price. No free long-history Asian PVC series exists.
  It is a real, published proxy, and the overlay to ACG's landed price must be calibrated on ACG purchase orders.
- **Data vintage.** FRED series are final, revised values, not what was published at the time. Using ALFRED vintages would remove this.
- **Holdout** exists only for PVC, and it ran with stale driver inputs. Refreshing the data fixes both issues.
- **Futures prices** (the market's own forecast for aluminium) are not used because no free source was available. This is the first roadmap item.
- **Chronos** (foundation model) is wired in (`python -m src.sb.chronos_local`, see SETUP.md) but was not run during development.
- **Carrying cost** of 1%/month is a placeholder pending ACG Finance.
