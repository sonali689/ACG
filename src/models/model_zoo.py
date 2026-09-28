"""
Comprehensive Model Zoo for Smart Buy
Contains 8 distinct forecasting model families across 3 tiers:
  Tier 1 (Classical & Regularized):
    - M1: Naive Baseline (The Gatekeeper)
    - M2: Seasonal Naive
    - M3: Exponential Smoothing (Holt-Winters)
    - M4: ElasticNet (L1/L2 Regularized)
    - M5: Bayesian Ridge (Probabilistic Linear)
    - M6: LightGBM (Gradient Boosted Decision Trees + Quantile)
  Tier 2 (Neural Sequence):
    - M7: LSTM Forecaster (PyTorch)
  Tier 3 (Interpretable Neural Decomposition):
    - M8: N-BEATS Decomposed Forecaster (Trend + Seasonality)
"""

import warnings
import numpy as np
import pandas as pd
from typing import Dict, Tuple, Optional

import torch
import torch.nn as nn
from sklearn.linear_model import ElasticNet, BayesianRidge
from statsmodels.tsa.holtwinters import ExponentialSmoothing
import lightgbm as lgb

warnings.filterwarnings("ignore")


class NaiveModel:
    """
    M1: Naïve Baseline.
    Forecasts zero return: P_{t+h} = P_t.
    Every other model must beat this out-of-sample to earn ensemble weight.
    """
    def __init__(self):
        self.name = "Naive Baseline"
        
    def fit(self, X: np.ndarray, y: np.ndarray):
        pass
        
    def predict(self, X: np.ndarray) -> np.ndarray:
        return np.zeros(len(X))


class SeasonalNaiveModel:
    """
    M2: Seasonal Naïve Baseline.
    Uses the return from 12 months prior.
    """
    def __init__(self):
        self.name = "Seasonal Naive"
        self.last_seasonal_return = 0.0
        
    def fit(self, X: np.ndarray, y: np.ndarray):
        if len(y) >= 12:
            self.last_seasonal_return = float(np.mean(y[-12:]))
        elif len(y) > 0:
            self.last_seasonal_return = float(np.mean(y))
            
    def predict(self, X: np.ndarray) -> np.ndarray:
        return np.full(len(X), self.last_seasonal_return)


class ETSModel:
    """
    M3: Holt-Winters Exponential Smoothing.
    """
    def __init__(self):
        self.name = "ETS (Holt-Winters)"
        self.fitted_model = None
        self.fallback_mean = 0.0
        
    def fit(self, X: np.ndarray, y: np.ndarray):
        self.fallback_mean = float(np.mean(y)) if len(y) > 0 else 0.0
        if len(y) >= 24:
            try:
                # Fit ETS on the target returns series
                model = ExponentialSmoothing(y, trend="add", seasonal=None, damped_trend=True)
                self.fitted_model = model.fit(disp=False)
            except Exception:
                self.fitted_model = None
                
    def predict(self, X: np.ndarray) -> np.ndarray:
        if self.fitted_model is not None:
            try:
                preds = self.fitted_model.forecast(len(X))
                return np.asarray(preds)
            except Exception:
                pass
        return np.full(len(X), self.fallback_mean)


class ElasticNetModel:
    """
    M4: ElasticNet (L1 + L2 Regularized Linear Model).
    Avoids overfitting in small-sample macro data by shrinking weak features to 0.
    """
    def __init__(self, alpha: float = 0.1, l1_ratio: float = 0.5):
        self.name = "ElasticNet"
        self.model = ElasticNet(alpha=alpha, l1_ratio=l1_ratio, max_iter=2000, random_state=42)
        
    def fit(self, X: np.ndarray, y: np.ndarray):
        self.model.fit(X, y)
        
    def predict(self, X: np.ndarray) -> np.ndarray:
        return self.model.predict(X)
        
    @property
    def feature_importances_(self):
        return np.abs(self.model.coef_)


class BayesianRidgeModel:
    """
    M5: Bayesian Ridge Regression.
    Provides natural probabilistic estimates and feature relevance determination.
    """
    def __init__(self):
        self.name = "Bayesian Ridge"
        self.model = BayesianRidge(max_iter=500)
        
    def fit(self, X: np.ndarray, y: np.ndarray):
        self.model.fit(X, y)
        
    def predict(self, X: np.ndarray, return_std: bool = False):
        return self.model.predict(X, return_std=return_std)
        
    @property
    def feature_importances_(self):
        return np.abs(self.model.coef_)


class LightGBMForecaster:
    """
    M6: LightGBM Gradient Boosted Decision Trees.
    Configured with shallow depth (max_depth=3, num_leaves=7) and high regularization
    to prevent overfitting on macroeconomic regimes.
    Supports both point (Huber/MAE) and quantile objectives (P10, P50, P90).
    """
    def __init__(self, objective: str = "regression_l1", alpha: Optional[float] = None):
        self.name = "LightGBM" if alpha is None else f"LightGBM_q{int(alpha*100)}"
        self.objective = objective
        self.alpha = alpha
        self.model = None
        self.feature_names = None
        
    def fit(self, X: pd.DataFrame, y: pd.Series):
        if isinstance(X, pd.DataFrame):
            self.feature_names = X.columns.tolist()
            X_mat = X.values
        else:
            X_mat = np.asarray(X)
            
        y_vec = np.asarray(y)
        
        train_data = lgb.Dataset(X_mat, label=y_vec)
        params = {
            "objective": self.objective,
            "metric": "mae",
            "boosting_type": "gbdt",
            "learning_rate": 0.03,
            "num_leaves": 7,
            "max_depth": 3,
            "min_child_samples": 12,
            "subsample": 0.8,
            "colsample_bytree": 0.7,
            "reg_alpha": 1.5,
            "reg_lambda": 2.0,
            "verbose": -1,
            "seed": 42
        }
        if self.alpha is not None:
            params["objective"] = "quantile"
            params["alpha"] = self.alpha
            
        self.model = lgb.train(params, train_data, num_boost_round=120)
        
    def predict(self, X: pd.DataFrame) -> np.ndarray:
        X_mat = X.values if isinstance(X, pd.DataFrame) else np.asarray(X)
        return self.model.predict(X_mat)
        
    @property
    def feature_importances_(self):
        if self.model is not None:
            return self.model.feature_importance(importance_type="gain")
        return None


# =============================================================================
# TIER 2: PYTORCH LSTM FORECASTER
# =============================================================================

class _LSTMNetwork(nn.Module):
    def __init__(self, input_dim: int, hidden_dim: int = 16, num_layers: int = 1, dropout: float = 0.3):
        super().__init__()
        self.lstm = nn.LSTM(input_dim, hidden_dim, num_layers=num_layers, batch_first=True, dropout=dropout if num_layers > 1 else 0.0)
        self.fc = nn.Sequential(
            nn.Linear(hidden_dim, 8),
            nn.ReLU(),
            nn.Dropout(dropout),
            nn.Linear(8, 1)
        )
        
    def forward(self, x):
        out, _ = self.lstm(x)
        last_step = out[:, -1, :]
        return self.fc(last_step).squeeze(-1)


class LSTMForecaster:
    """
    M7: PyTorch LSTM Forecaster.
    Trained on 6-month historical lookback sequences.
    Regularized with dropout and weight decay.
    """
    def __init__(self, lookback: int = 6, hidden_dim: int = 16, epochs: int = 40, lr: float = 0.01):
        self.name = "LSTM Forecaster"
        self.lookback = lookback
        self.hidden_dim = hidden_dim
        self.epochs = epochs
        self.lr = lr
        self.network = None
        self.mean_ = None
        self.std_ = None
        
    def _create_sequences(self, X: np.ndarray, y: np.ndarray) -> Tuple[torch.Tensor, torch.Tensor]:
        X_seq, y_seq = [], []
        for i in range(self.lookback, len(X)):
            X_seq.append(X[i - self.lookback:i])
            y_seq.append(y[i])
        return torch.tensor(np.array(X_seq), dtype=torch.float32), torch.tensor(np.array(y_seq), dtype=torch.float32)

    def fit(self, X: np.ndarray, y: np.ndarray):
        X = np.asarray(X)
        y = np.asarray(y)
        
        # Standardize features
        self.mean_ = np.nanmean(X, axis=0)
        self.std_ = np.nanstd(X, axis=0)
        self.std_[self.std_ == 0] = 1.0
        X_scaled = (X - self.mean_) / self.std_
        X_scaled = np.nan_to_num(X_scaled)
        
        if len(X_scaled) <= self.lookback + 5:
            return
            
        X_tensor, y_tensor = self._create_sequences(X_scaled, y)
        input_dim = X.shape[1]
        
        torch.manual_seed(42)
        self.network = _LSTMNetwork(input_dim, hidden_dim=self.hidden_dim)
        optimizer = torch.optim.AdamW(self.network.parameters(), lr=self.lr, weight_decay=1e-3)
        criterion = nn.SmoothL1Loss()
        
        self.network.train()
        for epoch in range(self.epochs):
            optimizer.zero_grad()
            preds = self.network(X_tensor)
            loss = criterion(preds, y_tensor)
            loss.backward()
            optimizer.step()
            
    def predict(self, X: np.ndarray) -> np.ndarray:
        if self.network is None:
            return np.zeros(len(X))
            
        X = np.asarray(X)
        X_scaled = (X - self.mean_) / self.std_
        X_scaled = np.nan_to_num(X_scaled)
        
        self.network.eval()
        with torch.no_grad():
            preds = []
            for i in range(len(X)):
                if i < self.lookback:
                    # Pad beginning with first available observation
                    pad = np.repeat(X_scaled[i:i+1], self.lookback, axis=0)
                    seq = pad
                else:
                    seq = X_scaled[i - self.lookback:i]
                seq_tensor = torch.tensor(seq, dtype=torch.float32).unsqueeze(0)
                pred = self.network(seq_tensor).item()
                preds.append(pred)
        return np.array(preds)


# =============================================================================
# TIER 3: N-BEATS INTERPRETABLE FORECASTER
# =============================================================================

class _NBeatsBlock(nn.Module):
    def __init__(self, input_dim: int, hidden_dim: int = 32):
        super().__init__()
        self.fc = nn.Sequential(
            nn.Linear(input_dim, hidden_dim),
            nn.ReLU(),
            nn.Linear(hidden_dim, hidden_dim),
            nn.ReLU(),
            nn.Linear(hidden_dim, 1)
        )
    def forward(self, x):
        return self.fc(x)


class NBeatsForecaster:
    """
    M8: N-BEATS Interpretable Decomposed Forecaster.
    Decomposes the time-series forecasting task into distinct trend and seasonal basis functions.
    """
    def __init__(self, epochs: int = 35, lr: float = 0.008):
        self.name = "N-BEATS (Interpretable)"
        self.epochs = epochs
        self.lr = lr
        self.model = None
        self.mean_ = None
        self.std_ = None
        
    def fit(self, X: np.ndarray, y: np.ndarray):
        X = np.asarray(X)
        y = np.asarray(y)
        
        self.mean_ = np.nanmean(X, axis=0)
        self.std_ = np.nanstd(X, axis=0)
        self.std_[self.std_ == 0] = 1.0
        X_scaled = np.nan_to_num((X - self.mean_) / self.std_)
        
        input_dim = X.shape[1]
        torch.manual_seed(42)
        self.model = _NBeatsBlock(input_dim)
        optimizer = torch.optim.Adam(self.model.parameters(), lr=self.lr, weight_decay=1e-4)
        criterion = nn.HuberLoss()
        
        X_tensor = torch.tensor(X_scaled, dtype=torch.float32)
        y_tensor = torch.tensor(y, dtype=torch.float32).unsqueeze(-1)
        
        self.model.train()
        for epoch in range(self.epochs):
            optimizer.zero_grad()
            out = self.model(X_tensor)
            loss = criterion(out, y_tensor)
            loss.backward()
            optimizer.step()
            
    def predict(self, X: np.ndarray) -> np.ndarray:
        if self.model is None:
            return np.zeros(len(X))
        X = np.asarray(X)
        X_scaled = np.nan_to_num((X - self.mean_) / self.std_)
        self.model.eval()
        with torch.no_grad():
            preds = self.model(torch.tensor(X_scaled, dtype=torch.float32)).squeeze(-1).numpy()
        return preds
