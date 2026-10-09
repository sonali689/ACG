"""
Leakage tests. Run:  python -m pytest tests -q   (or: python tests/test_leakage.py)

The core idea is a FUTURE-PERTURBATION test: take the raw data, scramble every
value dated after the forecast origin T, rebuild everything, and check that
every forecast made at T is bit-for-bit identical. If any feature, training
label, scaler or model can see the future, the forecast changes and the test
fails. This is the test the Round 2 code would have failed.
"""
from __future__ import annotations

import sys
from pathlib import Path

import numpy as np
import pandas as pd

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from src.sb import models as M                                      # noqa: E402
from src.sb.backtest import VECM_VARS, embargoed                    # noqa: E402
from src.sb.data import CFG, raw_panel, visible_panel                # noqa: E402
from src.sb.features import build_features, feature_columns         # noqa: E402
from src.sb.panel import _series_features, panel_frame, training_rows  # noqa: E402

ORIGINS = [pd.Timestamp("2019-06-01"), pd.Timestamp("2022-03-01")]


def _scramble_after(raw: pd.DataFrame, T: pd.Timestamp, seed=0) -> pd.DataFrame:
    rng = np.random.default_rng(seed)
    r = raw.copy()
    fut = r.index > T
    r.loc[fut] = r.loc[fut] * rng.uniform(0.3, 3.0, size=r.loc[fut].shape)
    return r


def _forecasts_at(material, T, raw):
    tgt = CFG["materials"][material]["target"]
    feats = build_features(material, raw)
    fc = feature_columns(feats)
    vis = visible_panel(material, raw)
    lp = np.log(vis[tgt][:T]).dropna().iloc[-CFG["backtest"]["history_months_stat"]:]
    out = {"features": feats.loc[T, fc].values.astype(float),
           "seasonal_naive": M.seasonal_naive(lp), "drift": M.drift(lp),
           "ets": M.ets(lp), "arima": M.arima(lp),
           "vecm": M.vecm(np.log(vis.loc[:T, VECM_VARS[material]].iloc[-120:]), tgt)[0],
           "garch": M.garch_sigma(lp)[0]}
    for h in (1, 3, 6):
        tr = embargoed(feats, T, h)
        out[f"enet_h{h}"] = M.enet(tr[fc], tr[f"y_h{h}"], feats.loc[[T], fc], h)[0]
        out[f"lgb_h{h}"] = M.lgb_local(tr[fc], tr[f"y_h{h}"], feats.loc[[T], fc])[0]
    return out


def test_future_perturbation_local_models():
    raw = raw_panel()
    for material in ("aluminium", "pvc"):
        for T in ORIGINS:
            a = _forecasts_at(material, T, raw)
            b = _forecasts_at(material, T, _scramble_after(raw, T))
            for k in a:
                assert np.allclose(np.nan_to_num(a[k]), np.nan_to_num(b[k]), atol=1e-10), \
                    f"LEAK: {material} {k} at {T.date()} changed when the future was scrambled"


def test_embargo_rule():
    feats = build_features("aluminium")
    for T in ORIGINS:
        for h in (1, 2, 3, 6):
            tr = embargoed(feats, T, h)
            assert (tr.index + pd.DateOffset(months=h)).max() <= T


def test_global_panel_features_and_rows():
    s = panel_frame()
    raw_al = raw_panel()["aluminium"].dropna()
    for T in ORIGINS:
        pert = raw_al.copy()
        pert[pert.index > T] *= 2.5
        a = _series_features(raw_al).drop(columns=[c for c in _series_features(raw_al) if c.startswith("y_h")])
        b = _series_features(pert).drop(columns=[c for c in _series_features(pert) if c.startswith("y_h")])
        assert np.allclose(a.loc[:T].fillna(0).values, b.loc[:T].fillna(0).values), "LEAK in panel features"
        for h in (1, 3, 6):
            tr = training_rows(s, T, h)
            assert (tr["date"] + pd.DateOffset(months=h) <= T).all(), "EMBARGO violated in global panel"


def test_no_synthetic_series():
    """Every series must come from a file in data/raw, and no feature may be a
    deterministic copy of the target (|corr| of levels > 0.999)."""
    raw = raw_panel()
    for material in ("aluminium", "pvc"):
        tgt = CFG["materials"][material]["target"]
        feats = build_features(material)
        for c in feature_columns(feats):
            for k in range(0, 4):
                x = feats[c]
                y = feats["price"].shift(k)
                ok = x.notna() & y.notna()
                if ok.sum() > 30 and x[ok].std() > 0:
                    assert abs(np.corrcoef(x[ok], y[ok])[0, 1]) < 0.999, f"{c} is a copy of the target"


def test_backtest_outputs_respect_embargo():
    p = Path(__file__).resolve().parents[1] / "outputs" / "predictions"
    for m in ("aluminium", "pvc"):
        f = p / f"{m}_local.csv"
        if f.exists():
            d = pd.read_csv(f, parse_dates=["origin", "max_train_target_date"])
            assert (d.max_train_target_date <= d.origin).all()


if __name__ == "__main__":
    for name, fn in list(globals().items()):
        if name.startswith("test_"):
            fn()
            print(f"PASS  {name}")
