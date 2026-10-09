"""
Feature engineering for Smart Buy v2.

Every feature at row t is a function of visible_panel(material) rows <= t only:
trailing windows, no centring, no back-fill. Targets are the realised
log-returns ln(P[t+h] / P[t]) and are never used as features.

Shock events are data-driven and dated when they become visible (a large move
in the material's own price, or a geopolitical-risk spike against its own
3-year history), instead of hand-dated flags whose end dates need hindsight.
"""
from __future__ import annotations

import numpy as np
import pandas as pd

from .data import CFG, raw_panel, visible_panel

H = CFG["backtest"]["horizons"]


def _lr(s, k):
    return np.log(s / s.shift(k))


def _z(s, w):
    m = s.rolling(w, min_periods=max(6, w // 2)).mean()
    sd = s.rolling(w, min_periods=max(6, w // 2)).std()
    return (s - m) / sd.replace(0, np.nan)


def _common(v: pd.DataFrame, P: pd.Series) -> dict:
    f = {}
    r1 = _lr(P, 1)
    for k in (1, 3, 6, 12):
        f[f"own_ret_{k}m"] = _lr(P, k)
    for w in (3, 6, 12):
        f[f"own_ma_ratio_{w}m"] = P / P.rolling(w).mean()
    f["own_vol_6m"] = r1.rolling(6).std()
    f["own_vol_12m"] = r1.rolling(12).std()
    f["own_z_12m"] = _z(P, 12)
    f["own_z_36m"] = _z(P, 36)
    # data-driven shock: this month's move against the last 3 years of moves
    f["shock_own_move"] = (r1.abs() / r1.rolling(36, min_periods=18).std().shift(1))
    f["fx_ret_1m"] = _lr(v.usd_inr, 1)
    f["fx_ret_3m"] = _lr(v.usd_inr, 3)
    f["gpr_z_36m"] = _z(v.gpr, 36)
    f["gpr_ret_3m"] = _lr(v.gpr, 3)
    f["shock_gpr_spike"] = (f["gpr_z_36m"] > 2).astype(float).where(f["gpr_z_36m"].notna())
    f["epu_z_36m"] = _z(v.epu, 36)
    f["epu_diff_3m"] = v.epu - v.epu.shift(3)
    f["cli_china_diff_1m"] = v.cli_china - v.cli_china.shift(1)
    f["cli_china_diff_3m"] = v.cli_china - v.cli_china.shift(3)
    f["cli_china_level"] = v.cli_china
    f["indpro_ret_3m"] = _lr(v.indpro, 3)
    f["freight_tsi_ret_3m"] = _lr(v.freight_tsi, 3)
    f["brent_ret_1m"] = _lr(v.brent, 1)
    f["brent_ret_3m"] = _lr(v.brent, 3)
    f["energy_idx_ret_3m"] = _lr(v.wb_energy, 3)
    m = v.index.month
    f["month_sin"] = pd.Series(np.sin(2 * np.pi * m / 12), index=v.index)
    f["month_cos"] = pd.Series(np.cos(2 * np.pi * m / 12), index=v.index)
    return f


def build_features(material: str, raw: pd.DataFrame | None = None) -> pd.DataFrame:
    raw = raw_panel() if raw is None else raw
    v = visible_panel(material, raw)
    tgt = CFG["materials"][material]["target"]
    P = v[tgt]
    f = _common(v, P)

    if material == "aluminium":
        f["coal_ret_1m"] = _lr(v.coal_aus, 1)
        f["coal_ret_3m"] = _lr(v.coal_aus, 3)
        f["gas_eu_ret_3m"] = _lr(v.gas_eu, 3)
        f["copper_ret_3m"] = _lr(v.copper, 3)
        f["copper_ret_6m"] = _lr(v.copper, 6)
        f["zinc_ret_3m"] = _lr(v.zinc, 3)
        f["nickel_ret_3m"] = _lr(v.nickel, 3)
        f["basemetals_idx_ret_3m"] = _lr(v.wb_basemetals, 3)
        f["al_vs_copper_z36"] = _z(np.log(P) - np.log(v.copper), 36)
        f["al_vs_coal_z36"] = _z(np.log(P) - np.log(v.coal_aus), 36)
        f["ppi_primary_al_ret_3m"] = _lr(v.ppi_primary_al, 3)
        f["ip_aluminium_ret_3m"] = _lr(v.ip_aluminium, 3)
    else:
        f["brent_ret_6m"] = _lr(v.brent, 6)
        f["monomer_ppi_ret_1m"] = _lr(v.ppi_organic_chem, 1)
        f["monomer_ppi_ret_3m"] = _lr(v.ppi_organic_chem, 3)
        f["gas_us_ret_3m"] = _lr(v.gas_us, 3)
        f["resin_vs_monomer_z36"] = _z(np.log(P) - np.log(v.ppi_organic_chem), 36)
        f["resin_vs_brent_z36"] = _z(np.log(P) - np.log(v.brent), 36)
        f["ip_resin_ret_3m"] = _lr(v.ip_resin, 3)

    X = pd.DataFrame(f, index=v.index)
    X = X.replace([np.inf, -np.inf], np.nan)

    out = X.copy()
    out["price"] = P
    true_P = raw[tgt]
    for h in H:
        out[f"y_h{h}"] = np.log(true_P.shift(-h) / true_P)
    out["material"] = material
    return out


def feature_columns(df: pd.DataFrame) -> list[str]:
    return [c for c in df.columns
            if c not in ("price", "material") and not c.startswith("y_h")]


if __name__ == "__main__":
    for m in ("aluminium", "pvc"):
        d = build_features(m)
        fc = feature_columns(d)
        print(m, d.shape, len(fc), "features")
        print(d.loc["2018-01-01":"2018-03-01", fc[:6] + ["price", "y_h3"]])
