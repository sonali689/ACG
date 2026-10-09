"""
Data layer for Smart Buy v2.

Two rules:
  1. Only REAL published series. No formulas, no hand-typed multipliers,
     nothing derived from a target price and then used to "predict" it.
  2. Publication lags are applied in exactly one place: `visible_panel()`.
     Every feature is built from its output.

raw_panel()      -> monthly panel indexed by the month each value REFERS to
visible_panel(m) -> the same panel shifted so that row t only contains what a
                    buyer of material m could have seen on that material's
                    forecast day for month t
"""
from __future__ import annotations

from functools import lru_cache
from pathlib import Path

import numpy as np
import pandas as pd
import yaml

BASE = Path(__file__).resolve().parents[2]
RAW = BASE / "data" / "raw"
CFG = yaml.safe_load((BASE / "config" / "pipeline.yaml").read_text())

# column -> (lag group, human label, source)
SERIES = {
    # World Bank Pink Sheet, monthly averages of public market quotes
    "aluminium":        ("pinksheet", "LME aluminium (US$/t)",          "World Bank Pink Sheet"),
    "brent":            ("pinksheet", "Brent crude (US$/bbl)",          "World Bank Pink Sheet"),
    "coal_aus":         ("pinksheet", "Australian thermal coal (US$/t)", "World Bank Pink Sheet"),
    "gas_us":           ("pinksheet", "US natural gas (US$/mmbtu)",     "World Bank Pink Sheet"),
    "gas_eu":           ("pinksheet", "Europe natural gas (US$/mmbtu)", "World Bank Pink Sheet"),
    "copper":           ("pinksheet", "LME copper (US$/t)",             "World Bank Pink Sheet"),
    "zinc":             ("pinksheet", "LME zinc (US$/t)",               "World Bank Pink Sheet"),
    "nickel":           ("pinksheet", "LME nickel (US$/t)",             "World Bank Pink Sheet"),
    "wb_energy":        ("wb_index",  "WB energy price index",          "World Bank Pink Sheet"),
    "wb_basemetals":    ("wb_index",  "WB base metals index",           "World Bank Pink Sheet"),
    # Exchange rate
    "usd_inr":          ("usd_inr",   "USD/INR",                        "ECB reference rates"),
    # Risk indices
    "gpr":              ("gpr",       "Geopolitical Risk index",        "Caldara & Iacoviello"),
    "epu":              ("epu",       "Global Economic Policy Uncertainty", "Baker, Bloom & Davis"),
    # Demand
    "cli_china":        ("cli",       "OECD China leading indicator",   "OECD"),
    # US statistics via FRED
    "ppi_plastic_resins": ("fred_ppi", "PPI plastic resins & materials (WPU066)", "BLS via FRED"),
    "ppi_organic_chem":   ("fred_ppi", "PPI basic organic chemicals (WPU0613)",   "BLS via FRED"),
    "ppi_primary_al":     ("fred_ppi", "PPI primary aluminium (WPU102501)",       "BLS via FRED"),
    "ip_resin":         ("fred_ip",   "US industrial production: resins (IPG3252N)", "Federal Reserve via FRED"),
    "ip_aluminium":     ("fred_ip",   "US industrial production: alumina & aluminium (IPG3313N)", "Federal Reserve via FRED"),
    "indpro":           ("fred_ip",   "US industrial production, total (INDPRO)", "Federal Reserve via FRED"),
    "freight_tsi":      ("freight_tsi", "US freight transportation services index (TSIFRGHT)", "BTS via FRED"),
}

PINK_COLS = {
    "Aluminum": "aluminium", "Crude oil, Brent": "brent", "Coal, Australian": "coal_aus",
    "Natural gas, US": "gas_us", "Natural gas, Europe": "gas_eu", "Copper": "copper",
    "Zinc": "zinc", "Nickel": "nickel",
}
FRED_FILES = {
    "fred_wpu066.csv": "ppi_plastic_resins", "fred_wpu0613.csv": "ppi_organic_chem",
    "fred_wpu102501.csv": "ppi_primary_al", "fred_ipg3252n.csv": "ip_resin",
    "fred_ipg3313n.csv": "ip_aluminium", "fred_indpro.csv": "indpro",
    "fred_tsifrght.csv": "freight_tsi",
}


def _month(s) -> pd.Series:
    return pd.to_datetime(s).dt.to_period("M").dt.to_timestamp()


@lru_cache(maxsize=1)
def pinksheet_prices() -> pd.DataFrame:
    """Every commodity in the World Bank Pink Sheet (used by the global model too)."""
    d = pd.read_excel(RAW / "wb_cmo_monthly.xlsx", "Monthly Prices", header=None)
    names = [str(x).strip() for x in d.iloc[4].values]
    body = d.iloc[6:].copy()
    body.columns = names
    body = body.rename(columns={names[0]: "period"})
    body["date"] = pd.to_datetime(body["period"].astype(str).str.replace("M", "-"),
                                  format="%Y-%m", errors="coerce")
    body = body.dropna(subset=["date"]).set_index("date").drop(columns="period")
    body = body.apply(pd.to_numeric, errors="coerce")
    return body.sort_index()


def _pinksheet_indices() -> pd.DataFrame:
    d = pd.read_excel(RAW / "wb_cmo_monthly.xlsx", "Monthly Indices", header=None)
    body = d.iloc[9:]
    dates = pd.to_datetime(body.iloc[:, 0].astype(str).str.replace("M", "-"),
                           format="%Y-%m", errors="coerce")
    out = pd.DataFrame({"wb_energy": pd.to_numeric(body.iloc[:, 2], errors="coerce").values,
                        "wb_basemetals": pd.to_numeric(body.iloc[:, 15], errors="coerce").values},
                       index=dates.values)
    return out[out.index.notna()].sort_index()


def _ecb_usdinr() -> pd.Series:
    inr = pd.read_csv(RAW / "ecb_inr_eur.csv")[["TIME_PERIOD", "OBS_VALUE"]]
    usd = pd.read_csv(RAW / "ecb_usd_eur.csv")[["TIME_PERIOD", "OBS_VALUE"]]
    fx = inr.merge(usd, on="TIME_PERIOD", suffixes=("_inr", "_usd"))
    s = pd.to_numeric(fx.OBS_VALUE_inr) / pd.to_numeric(fx.OBS_VALUE_usd)
    s.index = pd.to_datetime(fx.TIME_PERIOD + "-01")
    return s.rename("usd_inr").sort_index()


def _gpr() -> pd.Series:
    g = pd.read_excel(RAW / "data_gpr_export.xls")
    s = pd.to_numeric(g["GPR"], errors="coerce")
    s.index = _month(g["month"])
    return s.dropna().rename("gpr")


def _epu() -> pd.Series:
    e = pd.read_excel(RAW / "Global_Policy_Uncertainty_Data.xlsx").dropna(subset=["Year", "Month"])
    e = e[pd.to_numeric(e.Year, errors="coerce").notna()]
    idx = pd.to_datetime(e.Year.astype(int).astype(str) + "-" + e.Month.astype(int).astype(str) + "-01")
    return pd.Series(pd.to_numeric(e.GEPU_current, errors="coerce").values, index=idx).dropna().rename("epu")


def _cli() -> pd.Series:
    c = pd.read_csv(RAW / "oecd_china_cli.csv")
    s = pd.Series(pd.to_numeric(c.OBS_VALUE, errors="coerce").values,
                  index=pd.to_datetime(c.TIME_PERIOD + "-01"))
    return s.dropna().sort_index().rename("cli_china")


def _fred() -> pd.DataFrame:
    cols = []
    for f, name in FRED_FILES.items():
        x = pd.read_csv(RAW / f)
        s = pd.Series(pd.to_numeric(x.iloc[:, 1], errors="coerce").values, index=_month(x.iloc[:, 0]))
        cols.append(s.groupby(level=0).mean().rename(name))
    return pd.concat(cols, axis=1, sort=True)


@lru_cache(maxsize=1)
def raw_panel() -> pd.DataFrame:
    """Monthly panel, indexed by the month each value refers to. No lags, no fills."""
    ps = pinksheet_prices()[list(PINK_COLS)].rename(columns=PINK_COLS)
    parts = [ps, _pinksheet_indices(), _ecb_usdinr(), _gpr(), _epu(), _cli(), _fred()]
    df = pd.concat(parts, axis=1, sort=True).sort_index()
    df = df[df.index >= "1995-01-01"]
    df.index.name = "date"
    return df[list(SERIES)]


def last_observed(material: str) -> pd.Timestamp:
    """Last month for which the target price has been published."""
    return raw_panel()[CFG["materials"][material]["target"]].dropna().index.max()


def visible_panel(material: str, raw: pd.DataFrame | None = None) -> pd.DataFrame:
    """Row t = what a buyer of `material` could see on the forecast day for month t.

    Each series is shifted forward by its publication lag. After shifting,
    gaps are forward-filled (carrying the last published value forward is what
    a buyer would actually do). Nothing is ever back-filled.
    """
    raw = raw_panel() if raw is None else raw
    lags = CFG["lags"][material]
    out = {}
    for col, (group, _, _) in SERIES.items():
        out[col] = raw[col].shift(lags[group])
    vis = pd.DataFrame(out, index=raw.index)
    # forward-fill a stale series for at most 6 months, then leave it missing
    vis = vis.ffill(limit=6)
    # the target itself is never filled: no observation = no forecast origin
    tgt = CFG["materials"][material]["target"]
    vis[tgt] = raw[tgt].shift(CFG["lags"][material][SERIES[tgt][0]])
    return vis


if __name__ == "__main__":
    p = raw_panel()
    print(p.shape, p.index.min().date(), p.index.max().date())
    for c in p.columns:
        s = p[c].dropna()
        print(f"  {c:20s} {s.index.min().date()} -> {s.index.max().date()}  n={len(s)}")
    for m in ("aluminium", "pvc"):
        print(m, "last observed target month:", last_observed(m).date())
