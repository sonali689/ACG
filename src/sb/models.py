"""
Model zoo v2. Every function takes data that is ALREADY restricted to what was
visible at the origin, and returns forecasts of the h-month log-return.

Univariate / statistical (fit once per origin, all horizons):
  naive           P[t+h] = P[t]                              (the gatekeeper)
  seasonal_naive  repeat last year's h-month move              (real seasonal naive)
  drift           average monthly move over the last 5 years x h
  ets             damped-trend exponential smoothing on log price
  arima           ARIMA on log price, order picked by AIC from a small set
  vecm            vector error-correction on the material and its cost drivers
                  (Johansen rank test; falls back to a VAR in differences)
  garch_sigma     GARCH(1,1) h-month volatility (used for bands, not a point forecast)

Local ML with drivers (fit per origin and horizon, embargoed):
  enet            ElasticNet with in-fold feature selection (top 15) and in-fold
                  hyper-parameter search (time-series CV with an h-month gap)
  lgb_local       LightGBM, shallow and heavily regularised, fixed settings

Global ML on ~74 commodity series (see panel.py):
  lgb_global      LightGBM regression on price-history features
  lgb_global_clf  LightGBM classifier for P(price higher in h months)
  nbeats          interpretable N-BEATS, see nbeats_jax.py
"""
from __future__ import annotations

import warnings

import lightgbm as lgb
import numpy as np
import pandas as pd
from sklearn.feature_selection import SelectKBest, f_regression
from sklearn.impute import SimpleImputer
from sklearn.linear_model import ElasticNetCV
from sklearn.model_selection import TimeSeriesSplit
from sklearn.pipeline import Pipeline
from sklearn.preprocessing import StandardScaler

warnings.filterwarnings("ignore")
HZ = 6


# --------------------------------------------------------------------------- #
# Univariate / statistical
# --------------------------------------------------------------------------- #
def seasonal_naive(lp: pd.Series) -> np.ndarray:
    """lp: visible log price up to and including the origin."""
    v = lp.values
    out = []
    for h in range(1, HZ + 1):
        if len(v) < 13:
            out.append(0.0)
        else:
            out.append(v[-13 + h] - v[-13])
    return np.array(out)


def drift(lp: pd.Series, window=60) -> np.ndarray:
    r = lp.diff().dropna().values[-window:]
    mu = r.mean() if len(r) else 0.0
    return mu * np.arange(1, HZ + 1)


def ets(lp: pd.Series) -> np.ndarray:
    from statsmodels.tsa.holtwinters import ExponentialSmoothing
    try:
        m = ExponentialSmoothing(lp.values, trend="add", damped_trend=True).fit()
        return m.forecast(HZ) - lp.values[-1]
    except Exception:
        return np.full(HZ, np.nan)


def arima(lp: pd.Series) -> np.ndarray:
    from statsmodels.tsa.arima.model import ARIMA
    best, best_aic = None, np.inf
    for order in [(1, 1, 0), (0, 1, 1), (1, 1, 1), (2, 1, 0)]:
        try:
            r = ARIMA(lp.values, order=order).fit()
            if r.aic < best_aic:
                best, best_aic = r, r.aic
        except Exception:
            continue
    if best is None:
        return np.full(HZ, np.nan)
    return best.forecast(HZ) - lp.values[-1]


def vecm(logs: pd.DataFrame, target: str, k_ar_diff=2) -> tuple[np.ndarray, int]:
    """logs: visible log levels of [target, drivers...], last N months, no gaps."""
    from statsmodels.tsa.vector_ar.vecm import VECM, select_coint_rank
    from statsmodels.tsa.api import VAR
    d = logs.dropna(axis=1, how="any")
    if target not in d.columns or d.shape[1] < 2:
        return np.full(HZ, np.nan), -1
    cols = [target] + [c for c in d.columns if c != target]
    d = d[cols]
    try:
        rank = select_coint_rank(d.values, det_order=0, k_ar_diff=k_ar_diff,
                                 method="trace", signif=0.05).rank
        rank = min(rank, d.shape[1] - 1)
        if rank >= 1:
            res = VECM(d.values, k_ar_diff=k_ar_diff, coint_rank=rank, deterministic="co").fit()
            f = res.predict(steps=HZ)[:, 0]
            return f - d.values[-1, 0], rank
        dd = np.diff(d.values, axis=0)
        res = VAR(dd).fit(k_ar_diff)
        f = res.forecast(dd[-k_ar_diff:], steps=HZ)[:, 0]
        return np.cumsum(f), 0
    except Exception:
        return np.full(HZ, np.nan), -1


def garch_sigma(lp: pd.Series, lam=0.94) -> tuple[np.ndarray, str]:
    """Std-dev of the cumulative h-month log-return, h = 1..6."""
    r = lp.diff().dropna().values
    try:
        from arch import arch_model
        am = arch_model(100 * r, mean="Constant", vol="GARCH", p=1, q=1, dist="normal")
        res = am.fit(disp="off", show_warning=False)
        var = res.forecast(horizon=HZ, reindex=False).variance.values[-1] / 1e4
        if np.all(np.isfinite(var)) and np.all(var > 0):
            return np.sqrt(np.cumsum(var)), "garch"
    except Exception:
        pass
    w = lam ** np.arange(len(r))[::-1]
    s2 = np.sum(w * (r - r.mean()) ** 2) / w.sum()
    return np.sqrt(s2 * np.arange(1, HZ + 1)), "ewma"


# --------------------------------------------------------------------------- #
# Local ML with drivers
# --------------------------------------------------------------------------- #
def enet(Xtr, ytr, Xte, h) -> tuple[float, list[str]]:
    k = min(15, Xtr.shape[1])
    pipe = Pipeline([
        ("impute", SimpleImputer(strategy="median")),
        ("scale", StandardScaler()),
        ("select", SelectKBest(f_regression, k=k)),
        ("model", ElasticNetCV(l1_ratio=[0.1, 0.5, 0.9], n_alphas=30,
                               cv=TimeSeriesSplit(n_splits=4, gap=h), max_iter=5000)),
    ])
    # drop columns that are entirely missing in the training slice
    keep = Xtr.notna().any().values
    pipe.fit(Xtr.loc[:, keep], ytr)
    names = np.array(Xtr.columns[keep])[pipe.named_steps["select"].get_support()]
    return float(pipe.predict(Xte.loc[:, keep])[0]), list(names)


LGB_LOCAL = dict(objective="regression_l1", learning_rate=0.03, num_leaves=7, max_depth=3,
                 min_data_in_leaf=12, feature_fraction=0.7, bagging_fraction=0.8, bagging_freq=1,
                 lambda_l1=1.5, lambda_l2=2.0, verbose=-1, seed=42, num_threads=1)


def lgb_local(Xtr, ytr, Xte, rounds=120):
    b = lgb.train(LGB_LOCAL, lgb.Dataset(Xtr.values, ytr.values), rounds)
    return float(b.predict(Xte.values)[0]), b


# --------------------------------------------------------------------------- #
# Global ML
# --------------------------------------------------------------------------- #
LGB_GLOBAL = dict(learning_rate=0.05, num_leaves=15, min_data_in_leaf=100,
                  feature_fraction=0.8, bagging_fraction=0.8, bagging_freq=1,
                  lambda_l2=5.0, verbose=-1, seed=42, num_threads=1)


def lgb_global_fit(X, y, rounds=250):
    reg = lgb.train({**LGB_GLOBAL, "objective": "regression_l1"},
                    lgb.Dataset(X.values, y.values, categorical_feature=[X.columns.get_loc("group")]),
                    rounds)
    clf = lgb.train({**LGB_GLOBAL, "objective": "binary"},
                    lgb.Dataset(X.values, (y.values > 0).astype(int),
                                categorical_feature=[X.columns.get_loc("group")]),
                    rounds)
    return reg, clf
