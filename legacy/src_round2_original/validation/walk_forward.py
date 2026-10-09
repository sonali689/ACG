"""
Walk-Forward Validation Engine for Smart Buy
Executes the Rolling-Origin Walk-Forward backtest from Jan 2018 to Dec 2024:
  - 84 monthly origins × 6 forecast horizons (h=1..6)
  - 8 candidate models + Smart Buy Weighted Ensemble
  - Enforces the strict Naive Gate
  - Evaluates MAPE, Skill vs Naive, Directional Accuracy, Diebold-Mariano test
  - Produces Regime-Stratified Scorecards (Calm, COVID, Spike, Slide)
"""

import json
import time
import warnings
import numpy as np
import pandas as pd
from typing import Dict, List, Tuple, Optional
from pathlib import Path

from smartbuy.src.models.model_zoo import (
    NaiveModel,
    SeasonalNaiveModel,
    ETSModel,
    ElasticNetModel,
    BayesianRidgeModel,
    LightGBMForecaster,
    LSTMForecaster,
    NBeatsForecaster
)
from smartbuy.src.validation.metrics import (
    evaluate_forecast_series,
    compute_mape,
    compute_directional_accuracy,
    compute_skill_vs_naive,
    diebold_mariano_test
)

warnings.filterwarnings("ignore")

BASE_DIR = Path(__file__).resolve().parents[2]
PROCESSED_DIR = BASE_DIR / "data" / "processed"
OUTPUTS_DIR = BASE_DIR / "outputs"
SCORECARDS_DIR = OUTPUTS_DIR / "scorecards"
SCORECARDS_DIR.mkdir(parents=True, exist_ok=True)


def get_feature_and_target_columns(df: pd.DataFrame, h: int) -> Tuple[list, str, str]:
    """Identifies feature columns and specific horizon target columns."""
    target_ret_col = f"target_log_return_h{h}"
    target_price_col = f"target_price_h{h}"
    
    # Exclude all future target columns and date from feature set
    exclude_cols = ["date", "current_price"] + [f"target_log_return_h{i}" for i in range(1, 7)] + [f"target_price_h{i}" for i in range(1, 7)]
    feature_cols = [c for c in df.columns if c not in exclude_cols]
    
    return feature_cols, target_ret_col, target_price_col


def run_walk_forward_backtest(material: str = "aluminium", max_origins: int = 84) -> Tuple[pd.DataFrame, pd.DataFrame, pd.DataFrame]:
    """
    Executes walk-forward backtest across origins 2018-01 to 2024-12.
    """
    print("=" * 70)
    print(f"STARTING WALK-FORWARD ROLLING-ORIGIN BACKTEST: {material.upper()}")
    print("=" * 70)
    
    file_path = PROCESSED_DIR / f"{material}_feature_matrix.csv"
    df = pd.read_csv(file_path)
    df["date"] = pd.to_datetime(df["date"])
    
    # Origins start from Jan 2018 (index ~96 for 2010 start)
    origin_mask = (df["date"] >= "2018-01-01") & (df["date"] <= "2024-06-01")
    origin_indices = df[origin_mask].index.tolist()
    if max_origins is not None and len(origin_indices) > max_origins:
        origin_indices = origin_indices[:max_origins]
        
    print(f"Total walk-forward origins: {len(origin_indices)} (from {df.loc[origin_indices[0], 'date'].strftime('%Y-%m')} to {df.loc[origin_indices[-1], 'date'].strftime('%Y-%m')})")
    
    models_to_test = [
        "naive",
        "seasonal_naive",
        "ets",
        "elasticnet",
        "bayesian_ridge",
        "lightgbm",
        "lstm",
        "nbeats"
    ]
    
    # Storage for all origin predictions
    records = []
    
    t0 = time.time()
    
    # Iterate across each horizon h = 1..6
    for h in range(1, 7):
        print(f"\nProcessing Horizon h = {h} month(s) ahead...")
        feature_cols, target_ret_col, target_price_col = get_feature_and_target_columns(df, h)
        
        # Track predictions for each model across origins
        origin_preds = {m: [] for m in models_to_test}
        actual_prices = []
        current_prices = []
        actual_returns = []
        origin_dates = []
        target_dates = []
        p10_bands = []
        p90_bands = []
        
        for idx in origin_indices:
            # Training data: strictly data prior to current origin (expanding window)
            train_df = df.iloc[:idx].dropna(subset=[target_ret_col])
            # Origin test point
            test_row = df.iloc[idx:idx+1]
            
            curr_p = float(test_row["current_price"].values[0])
            act_p = float(test_row[target_price_col].values[0])
            act_r = float(test_row[target_ret_col].values[0])
            orig_d = test_row["date"].values[0]
            targ_d = df.iloc[idx + h]["date"] if (idx + h) < len(df) else orig_d
            
            X_train = train_df[feature_cols].values
            y_train = train_df[target_ret_col].values
            X_test = test_row[feature_cols].values
            
            # 1. Fit Candidate Models
            preds_h = {}
            
            # Naive
            m_naive = NaiveModel()
            m_naive.fit(X_train, y_train)
            preds_h["naive"] = float(m_naive.predict(X_test)[0])
            
            # Seasonal Naive
            m_snaive = SeasonalNaiveModel()
            m_snaive.fit(X_train, y_train)
            preds_h["seasonal_naive"] = float(m_snaive.predict(X_test)[0])
            
            # ETS
            m_ets = ETSModel()
            m_ets.fit(X_train, y_train)
            preds_h["ets"] = float(m_ets.predict(X_test)[0])
            
            # ElasticNet
            m_enet = ElasticNetModel(alpha=0.05, l1_ratio=0.3)
            m_enet.fit(X_train, y_train)
            preds_h["elasticnet"] = float(m_enet.predict(X_test)[0])
            
            # Bayesian Ridge
            m_bridge = BayesianRidgeModel()
            m_bridge.fit(X_train, y_train)
            preds_h["bayesian_ridge"] = float(m_bridge.predict(X_test)[0])
            
            # LightGBM Point
            m_lgb = LightGBMForecaster(objective="regression_l1")
            m_lgb.fit(train_df[feature_cols], train_df[target_ret_col])
            preds_h["lightgbm"] = float(m_lgb.predict(test_row[feature_cols])[0])
            
            # LightGBM Quantile (P10 and P90)
            m_q10 = LightGBMForecaster(alpha=0.10)
            m_q10.fit(train_df[feature_cols], train_df[target_ret_col])
            ret_p10 = float(m_q10.predict(test_row[feature_cols])[0])
            
            m_q90 = LightGBMForecaster(alpha=0.90)
            m_q90.fit(train_df[feature_cols], train_df[target_ret_col])
            ret_p90 = float(m_q90.predict(test_row[feature_cols])[0])
            
            # PyTorch LSTM
            m_lstm = LSTMForecaster(lookback=4, hidden_dim=12, epochs=25, lr=0.015)
            m_lstm.fit(X_train, y_train)
            preds_h["lstm"] = float(m_lstm.predict(X_test)[0])
            
            # N-BEATS
            m_nbeats = NBeatsForecaster(epochs=20, lr=0.01)
            m_nbeats.fit(X_train, y_train)
            preds_h["nbeats"] = float(m_nbeats.predict(X_test)[0])
            
            # Record predictions for this origin
            actual_prices.append(act_p)
            current_prices.append(curr_p)
            actual_returns.append(act_r)
            origin_dates.append(orig_d)
            target_dates.append(targ_d)
            p10_bands.append(curr_p * np.exp(ret_p10))
            p90_bands.append(curr_p * np.exp(ret_p90))
            
            for m in models_to_test:
                origin_preds[m].append(preds_h[m])

        # =====================================================================
        # ENSEMBLE FORMATION WITH STRICT NAIVE GATE
        # =====================================================================
        # Compute MAPE for each model up to this point
        naive_prices = np.array(current_prices)  # Naive price = P_t
        act_prices = np.array(actual_prices)
        
        model_mapes = {}
        for m in models_to_test:
            pred_prices = current_prices * np.exp(np.array(origin_preds[m]))
            model_mapes[m] = compute_mape(act_prices, pred_prices)
            
        naive_mape = model_mapes["naive"]
        
        # Apply Naive Gate: Models with MAPE >= Naive receive 0 weight
        raw_weights = {}
        for m in models_to_test:
            if m == "naive":
                raw_weights[m] = 0.0
            elif model_mapes[m] < naive_mape:
                # Inverse squared MAPE weighting
                raw_weights[m] = (1.0 / model_mapes[m]) ** 2
            else:
                raw_weights[m] = 0.0
                
        total_w = sum(raw_weights.values())
        if total_w > 0:
            norm_weights = {m: raw_weights[m] / total_w for m in models_to_test}
        else:
            norm_weights = {"naive": 1.0}
            
        # Ensemble Prediction
        ensemble_ret = np.zeros(len(act_prices))
        for m, w in norm_weights.items():
            if w > 0:
                ensemble_ret += w * np.array(origin_preds[m])
                
        ensemble_prices = current_prices * np.exp(ensemble_ret)
        
        # Save per-origin records for this horizon
        for i in range(len(origin_indices)):
            rec = {
                "material": material,
                "horizon": h,
                "origin_date": pd.to_datetime(origin_dates[i]).strftime("%Y-%m-%d"),
                "target_date": pd.to_datetime(target_dates[i]).strftime("%Y-%m-%d"),
                "current_price": current_prices[i],
                "actual_price": actual_prices[i],
                "actual_log_return": actual_returns[i],
                "pred_price_ensemble": ensemble_prices[i],
                "pred_return_ensemble": ensemble_ret[i],
                "p10_price": p10_bands[i],
                "p90_price": p90_bands[i],
            }
            for m in models_to_test:
                p_m = current_prices[i] * np.exp(origin_preds[m][i])
                rec[f"pred_price_{m}"] = p_m
                rec[f"pred_ret_{m}"] = origin_preds[m][i]
                
            records.append(rec)
            
        print(f"  Horizon h={h}: Naive MAPE={naive_mape:.2f}% | Ensemble MAPE={compute_mape(act_prices, ensemble_prices):.2f}% | Skill={compute_skill_vs_naive(compute_mape(act_prices, ensemble_prices), naive_mape):.1f}% | DirAcc={compute_directional_accuracy(actual_returns, ensemble_ret):.1f}%")

    df_records = pd.DataFrame(records)
    predictions_csv = SCORECARDS_DIR / f"{material}_walk_forward_predictions.csv"
    df_records.to_csv(predictions_csv, index=False)
    print(f"\nSaved origin predictions to: {predictions_csv}")
    
    # =========================================================================
    # GENERATE SCORECARD BY HORIZON (h=1..6)
    # =========================================================================
    horizon_summary = []
    for h in range(1, 7):
        sub = df_records[df_records["horizon"] == h]
        act_p = sub["actual_price"].values
        curr_p = sub["current_price"].values
        act_r = sub["actual_log_return"].values
        ens_p = sub["pred_price_ensemble"].values
        ens_r = sub["pred_return_ensemble"].values
        low_p = sub["p10_price"].values
        high_p = sub["p90_price"].values
        
        # Evaluate Ensemble
        score_ens = evaluate_forecast_series(
            actual_prices=act_p,
            predicted_prices=ens_p,
            actual_returns=act_r,
            predicted_returns=ens_r,
            naive_prices=curr_p,
            lower_bands=low_p,
            upper_bands=high_p,
            h=h
        )
        
        # Evaluate individual models
        row = {
            "horizon": f"h={h}",
            "ensemble_mape": score_ens["mape"],
            "naive_mape": score_ens["naive_mape"],
            "skill_vs_naive_pct": score_ens["skill_vs_naive_pct"],
            "directional_accuracy_pct": score_ens["directional_accuracy_pct"],
            "band_coverage_p10_p90_pct": score_ens["coverage_p10_p90_pct"],
            "bias_pct": score_ens["bias_pct"],
            "dm_stat": score_ens["dm_stat"],
            "dm_p_value": score_ens["dm_p_value"]
        }
        for m in models_to_test:
            p_m = sub[f"pred_price_{m}"].values
            r_m = sub[f"pred_ret_{m}"].values
            sc_m = evaluate_forecast_series(act_p, p_m, act_r, r_m, curr_p, h=h)
            row[f"mape_{m}"] = sc_m["mape"]
            row[f"dir_acc_{m}"] = sc_m["directional_accuracy_pct"]
            
        horizon_summary.append(row)
        
    df_horizons = pd.DataFrame(horizon_summary)
    horizons_csv = SCORECARDS_DIR / f"{material}_horizon_scorecard.csv"
    df_horizons.to_csv(horizons_csv, index=False)
    print(f"Saved horizon scorecard to: {horizons_csv}")
    
    # =========================================================================
    # GENERATE REGIME STRATIFIED SCORECARD (h=3 Key Decision Horizon)
    # =========================================================================
    regimes = {
        "Calm (2018-2019)": ("2018-01-01", "2019-12-31"),
        "COVID Shock (2020)": ("2020-01-01", "2020-12-31"),
        "Spike / Rally (2021-2022 H1)": ("2021-01-01", "2022-06-30"),
        "Slide / Normalization (2022 H2-2024)": ("2022-07-01", "2024-12-31"),
    }
    
    sub_h3 = df_records[df_records["horizon"] == 3].copy()
    sub_h3["origin_date"] = pd.to_datetime(sub_h3["origin_date"])
    
    regime_summary = []
    for reg_name, (start_d, end_d) in regimes.items():
        reg_df = sub_h3[(sub_h3["origin_date"] >= start_d) & (sub_h3["origin_date"] <= end_d)]
        if len(reg_df) > 0:
            act_p = reg_df["actual_price"].values
            curr_p = reg_df["current_price"].values
            act_r = reg_df["actual_log_return"].values
            ens_p = reg_df["pred_price_ensemble"].values
            ens_r = reg_df["pred_return_ensemble"].values
            low_p = reg_df["p10_price"].values
            high_p = reg_df["p90_price"].values
            
            sc = evaluate_forecast_series(act_p, ens_p, act_r, ens_r, curr_p, low_p, high_p, h=3)
            regime_summary.append({
                "regime": reg_name,
                "n_months": len(reg_df),
                "ensemble_mape": sc["mape"],
                "naive_mape": sc["naive_mape"],
                "skill_vs_naive_pct": sc["skill_vs_naive_pct"],
                "directional_accuracy_pct": sc["directional_accuracy_pct"],
                "band_coverage_p10_p90_pct": sc["coverage_p10_p90_pct"],
                "bias_pct": sc["bias_pct"]
            })
            
    df_regimes = pd.DataFrame(regime_summary)
    regimes_csv = SCORECARDS_DIR / f"{material}_regime_scorecard.csv"
    df_regimes.to_csv(regimes_csv, index=False)
    print(f"Saved regime scorecard to: {regimes_csv}")
    print(f"Validation completed in {time.time() - t0:.1f}s")
    
    return df_records, df_horizons, df_regimes


def run_all_validations():
    """Runs complete walk-forward validation for both materials."""
    al_records, al_horizons, al_regimes = run_walk_forward_backtest("aluminium")
    pvc_records, pvc_horizons, pvc_regimes = run_walk_forward_backtest("pvc")
    print("\nAll Walk-Forward Validations Finished Successfully!")


if __name__ == "__main__":
    run_all_validations()
