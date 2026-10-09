"""
Global panel: every World Bank Pink Sheet commodity plus the BLS PPI series.

Why: 180 monthly points per material is too few to train a flexible model.
Price dynamics (momentum, mean reversion, volatility clustering) are shared
across commodities, so a single model trained on ~70 series sees ~25,000 rows.
This is how the M4/M5 forecasting competitions were won.

Only price-history features are used here (no exogenous drivers), so the
panel is a different "view" from the local driver models; that is what makes
it a useful ensemble member.

Availability: Pink Sheet values for month t are usable at origin t (lag 0).
FRED/BLS values are treated as usable one month later (lag 1) for training
rows, which is conservative for PVC and correct for aluminium.
"""
from __future__ import annotations

from functools import lru_cache

import numpy as np
import pandas as pd

from .data import CFG, raw_panel, pinksheet_prices

H = CFG["backtest"]["horizons"]

GROUPS = {
    "energy": ["Crude oil", "Coal", "Natural gas", "Liquefied"],
    "metal": ["Aluminum", "Copper", "Lead", "Tin", "Nickel", "Zinc", "Iron ore", "Gold", "Platinum", "Silver"],
    "fert": ["Phosphate", "DAP", "TSP", "Urea", "Potassium"],
}
FRED_IN_PANEL = ["ppi_plastic_resins", "ppi_organic_chem", "ppi_primary_al"]


def _group(name: str) -> int:
    for i, (g, keys) in enumerate(GROUPS.items()):
        if any(name.startswith(k) for k in keys):
            return i
    return 3  # agriculture & other


@lru_cache(maxsize=1)
def panel_series() -> dict[str, tuple[pd.Series, int, int]]:
    """name -> (price series, group code, availability lag)"""
    ps = pinksheet_prices()
    ps = ps[ps.index >= "1990-01-01"]
    out = {}
    for c in ps.columns:
        s = ps[c].dropna()
        s = s[s > 0]
        if len(s) < 180 or s.nunique() < 50:
            continue
        name = "aluminium" if c == "Aluminum" else c
        out[name] = (s, _group(c), 0)
    raw = raw_panel()
    for c in FRED_IN_PANEL:
        out[c] = (raw[c].dropna(), 4, 1)
    return out


def _series_features(s: pd.Series) -> pd.DataFrame:
    lp = np.log(s)
    r1 = lp.diff()
    f = pd.DataFrame(index=s.index)
    for k in (1, 2, 3, 6, 12):
        f[f"ret_{k}"] = lp - lp.shift(k)
    for w in (3, 6, 12):
        f[f"ma_{w}"] = s / s.rolling(w).mean()
    f["vol_6"] = r1.rolling(6).std()
    f["vol_12"] = r1.rolling(12).std()
    f["vol_60"] = r1.rolling(60, min_periods=24).std()
    f["z_12"] = (s - s.rolling(12).mean()) / s.rolling(12).std()
    f["z_36"] = (s - s.rolling(36).mean()) / s.rolling(36).std()
    f["range_pos_36"] = (s - s.rolling(36).min()) / (s.rolling(36).max() - s.rolling(36).min())
    f["acc"] = r1 - r1.shift(1)
    f["month"] = s.index.month
    for h in H:
        f[f"y_h{h}"] = lp.shift(-h) - lp
    return f


@lru_cache(maxsize=1)
def panel_frame() -> pd.DataFrame:
    frames = []
    for name, (s, g, lag) in panel_series().items():
        f = _series_features(s)
        f["series"] = name
        f["group"] = g
        f["avail_lag"] = lag
        f["date"] = f.index
        frames.append(f.reset_index(drop=True))
    p = pd.concat(frames, ignore_index=True).replace([np.inf, -np.inf], np.nan)
    return p


PANEL_FEATURES = ["ret_1", "ret_2", "ret_3", "ret_6", "ret_12", "ma_3", "ma_6", "ma_12",
                  "vol_6", "vol_12", "vol_60", "z_12", "z_36", "range_pos_36", "acc",
                  "month", "group"]


def training_rows(p: pd.DataFrame, origin: pd.Timestamp, h: int) -> pd.DataFrame:
    """Rows whose h-step outcome was already published at `origin` (the embargo)."""
    cutoff = origin - pd.DateOffset(months=h)
    ok = p["date"] <= cutoff - pd.to_timedelta(0, "D")
    ok &= ~((p["avail_lag"] == 1) & (p["date"] > cutoff - pd.DateOffset(months=1)))
    return p[ok & p[f"y_h{h}"].notna()]


if __name__ == "__main__":
    p = panel_frame()
    print(p.shape, p.series.nunique(), "series")
    print(p.groupby("group").series.nunique())
