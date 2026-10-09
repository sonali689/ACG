# What changed from Round 2 to v2, and why

The original Round 2 code, outputs, dashboard and configs are preserved unchanged in `legacy/`.

## A. Problems found in the Round 2 pipeline

| # | Problem | Evidence | Fix in v2 |
|---|---|---|---|
| 1 | **PVC price was simulated.** `pvc_asia_spot` = formula of Brent and coal × hand-typed shock multipliers (×1.35, ×1.62, ×1.25, ×0.88), clipped at $620; 47 of 180 months sat exactly at $620. | `legacy/src_round2_original/ingestion/build_dataset.py`, `build_pvc_market_model()` | Target is a real series: BLS PPI plastic resins & materials (WPU066). |
| 2 | **Ethylene, naphtha, VCM, freight "BDI", LME stocks, China PVC exports, alumina, bauxite were formulas**, several computed from the target itself. | corr(exports, PVC lagged 2m) = 1.000; corr(LME stocks, aluminium) = −1.000 | Removed. Only published series are used. `test_no_synthetic_series` fails if any feature is a copy of the target. |
| 3 | **Look-ahead leak in training.** At origin T every row before T was used, but rows T−1…T−h+1 carry h-month labels built from prices after T. | Re-running with an embargo turned +8% skill into −6% at h=3 and +31% into −2% at h=6, while h=1 (where no leak is possible) was unchanged. | Embargo: training rows need target date ≤ origin. Asserted in the backtest and checked by `test_future_perturbation_local_models`, which fails on the Round 2 logic. |
| 4 | The "leak-free" ensemble weights still used folds whose outcome was not yet known (origin < T instead of origin ≤ T−h). | `leakfree_all_horizons.py` | Weights and conformal scores use only realised forecasts (origin ≤ T−h). |
| 5 | "N-BEATS" was a plain 3-layer MLP with no polynomial/Fourier basis. | `model_zoo.py`, `NBeatsForecaster` | Real interpretable N-BEATS (trend + seasonality stacks, doubly residual), trained globally on 74 series. |
| 6 | No conformal calibration existed, although the deck and dashboard said so. Raw coverage was relabelled "calibrated", and a "NEAR PASS" category was invented. | `fix_pack.py` | Normalised split-conformal around the headline forecast, scaled by GARCH(1,1) volatility. Calibrated and uncalibrated coverage are both reported. |
| 7 | No SHAP, no in-fold feature selection, no hyper-parameter tuning, although all were claimed. | `walk_forward.py` | SHAP via LightGBM TreeSHAP. ElasticNet with in-fold top-15 selection and time-series CV with an h-month gap. N-BEATS early stopping on an in-fold validation slice. |
| 8 | "Seasonal naïve" was the mean of the last 12 returns (a drift model). | `model_zoo.py` | A real seasonal naïve plus a separate drift model. |
| 9 | LSTM fed a repeated copy of the current row at prediction time instead of real history. | `LSTMForecaster.predict` | LSTM dropped. The global N-BEATS and LightGBM cover the neural/ML tier properly. |
| 10 | "PMI" was the OECD China CLI (level ~100), and a "PMI > 50" feature was always 1. "China coal" was Australian coal. | `build_dataset.py`, `engineer_features.py` | Named accurately everywhere. |
| 11 | Shock flags had hindsight end dates (e.g., "freeze" until Nov 2021). | `apply_as_of_lags()` | Replaced by data-driven shock indicators that use only past data. |
| 12 | `bfill()` on features pulled later values into earlier rows. | `engineer_features.py` | No back-fill anywhere. Forward-fill of at most 6 months, after lagging. |
| 13 | Replay bought at the price just observed, and did not value leftover stock. | `replay_leakfree.py` | Executes at next month's price, values ending inventory, and adds a permutation test and a perfect-foresight bound. |
| 14 | Deck/dashboard claims contradicted outputs: N-BEATS "carries most weight" (12.7% for Al), LSTM "excluded" (8–38% weight), H4 "ρ = +0.89" (not in any output), working-capital signs reversed, 66/78/84-month counts mixed. | Round 2 deck vs `legacy/outputs_round2_original` | Dashboard text is generated from the outputs. See `DECK_UPDATE.md` for the deck. |
| 15 | The Makefile re-used saved predictions, and feature files post-dated the predictions, so results could not be reproduced. | file timestamps | `make` rebuilds everything from `data/raw`. |

## B. Choices made during the v2 build (disclosed)

1. **N-BEATS early stopping.** Without it, N-BEATS overfit: out-of-sample skill fell as training continued. This was found by
   checking the 2015–17 warm-up years only, which are never scored. Early stopping on the last 12 months of each training set
   was added before the full backtest.
2. **N-BEATS patience (stop after 400 steps without validation improvement).** Added for run time, before the N-BEATS backtest.
   The best checkpoint is still the one kept.
3. **Diebold–Mariano variance guard (added after seeing results).** On the 15-point holdout at h=5 the autocorrelation correction
   drove the variance to about zero and printed p = 0.0000 for a +0.5% skill. If the corrected variance falls below 10% of the plain
   variance, the plain variance is now used. This is a bug fix. It changed 8 holdout cells, every one of which had read exactly 0 or 1 before, and no development-window cell.
4. **Stale-input warning (added after seeing results).** The live PVC note cited Brent as a driver, but Brent data ends Dec 2024.
   The forecast now lists every driver whose data is more than 3 months old.

5. **Official N-BEATS predictions replaced by a verified re-run.** The first N-BEATS run (kept in
   `legacy/nbeats_first_run_superseded.csv`) could not be reproduced; two later independent runs were
   bit-identical, so they are the submitted results. Effect: PVC 1-month skill +20.7% → +21.4%, PVC replay
   +0.45% → +0.41% (timing p 0.002 → 0.003). No conclusion changed. The N-BEATS-alone significance claim was
   dropped because it did not hold in both runs.

Nothing else in `config/pipeline.yaml` or the model settings was changed after results were seen.

## C. Not done, and why

- **Futures curve** (aluminium): no free source was available. This is the top roadmap item.
- **Chronos** foundation model: code is written (`src/sb/chronos_local.py`, `make chronos`) but was not run, because PyTorch and
  Hugging Face were unavailable in the build environment.
- **Data refresh:** the World Bank file ends Dec 2024. Network access was not available, so see `SETUP.md`.
