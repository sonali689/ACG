"""
Validation Metrics & Statistical Tests for Smart Buy
Implements:
  - MAPE (Mean Absolute Percentage Error on price levels)
  - RMSE & MAE
  - Directional Accuracy (%)
  - Skill vs Naive (%)
  - Diebold-Mariano (DM) test for predictive superiority
  - Prediction interval coverage & Mean Prediction Interval Width (MPIW)
  - Forecast Bias (%)
"""

import numpy as np
import pandas as pd
from scipy import stats
from typing import Dict, Tuple, Optional


def compute_mape(actual: np.ndarray, predicted: np.ndarray) -> float:
    """Computes MAPE in percentage: mean(|actual - pred| / actual) * 100"""
    actual, predicted = np.asarray(actual), np.asarray(predicted)
    valid = actual > 0
    if not np.any(valid):
        return 0.0
    return float(np.mean(np.abs((actual[valid] - predicted[valid]) / actual[valid])) * 100.0)


def compute_directional_accuracy(actual_ret: np.ndarray, predicted_ret: np.ndarray) -> float:
    """Computes directional accuracy: % of times sign of predicted return matches actual"""
    actual_ret, predicted_ret = np.asarray(actual_ret), np.asarray(predicted_ret)
    correct = np.sign(actual_ret) == np.sign(predicted_ret)
    return float(np.mean(correct) * 100.0) if len(correct) > 0 else 50.0


def compute_skill_vs_naive(model_mape: float, naive_mape: float) -> float:
    """Skill = (1 - MAPE_model / MAPE_naive) * 100"""
    if naive_mape <= 0:
        return 0.0
    return float((1.0 - model_mape / naive_mape) * 100.0)


def compute_forecast_bias(actual: np.ndarray, predicted: np.ndarray) -> float:
    """Mean signed percentage error: mean((predicted - actual) / actual) * 100"""
    actual, predicted = np.asarray(actual), np.asarray(predicted)
    valid = actual > 0
    return float(np.mean((predicted[valid] - actual[valid]) / actual[valid]) * 100.0)


def compute_band_coverage(actual: np.ndarray, lower: np.ndarray, upper: np.ndarray) -> float:
    """Computes fraction of actual prices inside [lower, upper] band in percent"""
    actual, lower, upper = np.asarray(actual), np.asarray(lower), np.asarray(upper)
    inside = (actual >= lower) & (actual <= upper)
    return float(np.mean(inside) * 100.0) if len(actual) > 0 else 0.0


def diebold_mariano_test(actual: np.ndarray, pred_model: np.ndarray, pred_naive: np.ndarray, h: int = 1) -> Tuple[float, float]:
    """
    Performs the Diebold-Mariano test of equal predictive accuracy.
    H0: Model and Naive have equal accuracy.
    H1: Model is significantly more accurate than Naive (one-sided).
    Returns (dm_statistic, p_value).
    """
    e_model = np.abs(actual - pred_model)
    e_naive = np.abs(actual - pred_naive)
    d = e_naive - e_model  # positive when model has lower error
    
    n = len(d)
    if n < 8:
        return 0.0, 1.0
        
    mean_d = np.mean(d)
    # Autocovariance adjustment for multi-step horizon h
    gamma_0 = np.var(d, ddof=1)
    autocov_sum = 0.0
    for lag in range(1, h):
        if lag < n:
            gamma_k = np.cov(d[lag:], d[:-lag])[0, 1]
            autocov_sum += 2.0 * gamma_k
            
    var_d = (gamma_0 + autocov_sum) / n
    if var_d <= 0:
        return 0.0, 1.0
        
    dm_stat = mean_d / np.sqrt(var_d)
    # One-sided p-value (is model superior?)
    p_val = float(1.0 - stats.norm.cdf(dm_stat))
    return round(float(dm_stat), 3), round(float(p_val), 4)


def evaluate_forecast_series(actual_prices: np.ndarray,
                             predicted_prices: np.ndarray,
                             actual_returns: np.ndarray,
                             predicted_returns: np.ndarray,
                             naive_prices: np.ndarray,
                             lower_bands: Optional[np.ndarray] = None,
                             upper_bands: Optional[np.ndarray] = None,
                             h: int = 1) -> dict:
    """
    Comprehensive evaluation scorecard for a model forecast.
    """
    mape = compute_mape(actual_prices, predicted_prices)
    naive_mape = compute_mape(actual_prices, naive_prices)
    skill = compute_skill_vs_naive(mape, naive_mape)
    dir_acc = compute_directional_accuracy(actual_returns, predicted_returns)
    bias = compute_forecast_bias(actual_prices, predicted_prices)
    dm_stat, dm_p = diebold_mariano_test(actual_prices, predicted_prices, naive_prices, h=h)
    
    coverage = compute_band_coverage(actual_prices, lower_bands, upper_bands) if lower_bands is not None else np.nan
    
    return {
        "mape": round(mape, 2),
        "naive_mape": round(naive_mape, 2),
        "skill_vs_naive_pct": round(skill, 2),
        "directional_accuracy_pct": round(dir_acc, 2),
        "bias_pct": round(bias, 2),
        "dm_stat": dm_stat,
        "dm_p_value": dm_p,
        "beats_naive": bool(mape < naive_mape),
        "coverage_p10_p90_pct": round(coverage, 2) if not np.isnan(coverage) else None
    }
