"""
Data Downloader Module for Smart Buy
Fetches public commodity prices, macro indicators, energy, and risk metrics.
Handles FRED public endpoints, World Bank, Yahoo Finance, and GPR indices.
"""

import os
import time
import requests
import pandas as pd
import numpy as np
from pathlib import Path
from typing import Dict, List, Optional

RAW_DIR = Path(__file__).resolve().parents[2] / "data" / "raw"
RAW_DIR.mkdir(parents=True, exist_ok=True)

HEADERS = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36"
}


def download_fred_series(series_id: str, col_name: Optional[str] = None) -> pd.DataFrame:
    """
    Downloads time series directly from FRED via public CSV endpoint.
    No API key required.
    """
    col_name = col_name or series_id.lower()
    local_path = RAW_DIR / f"fred_{series_id.lower()}.csv"
    
    url = f"https://fred.stlouisfed.org/graph/fredgraph.csv?id={series_id}"
    print(f"Fetching FRED series: {series_id} -> {col_name}...")
    try:
        resp = requests.get(url, headers=HEADERS, timeout=15)
        if resp.status_code == 200 and len(resp.text) > 100:
            with open(local_path, "w", encoding="utf-8") as f:
                f.write(resp.text)
            df = pd.read_csv(local_path)
            # FRED CSV columns are DATE and series_id
            df["DATE"] = pd.to_datetime(df["DATE"], errors="coerce")
            df = df.dropna(subset=["DATE"])
            df[series_id] = pd.to_numeric(df[series_id], errors="coerce")
            df = df.rename(columns={"DATE": "date", series_id: col_name})
            df = df.dropna(subset=[col_name]).sort_values("date").reset_index(drop=True)
            print(f"  Successfully fetched {len(df)} records for {col_name}")
            return df
        else:
            print(f"  Failed with status {resp.status_code}")
    except Exception as e:
        print(f"  Error downloading {series_id}: {e}")
        if local_path.exists():
            print(f"  Using cached local file: {local_path}")
            df = pd.read_csv(local_path)
            df["DATE"] = pd.to_datetime(df["DATE"], errors="coerce")
            df = df.dropna(subset=["DATE"])
            df[series_id] = pd.to_numeric(df[series_id], errors="coerce")
            df = df.rename(columns={"DATE": "date", series_id: col_name})
            return df.dropna(subset=[col_name]).sort_values("date").reset_index(drop=True)
            
    return pd.DataFrame(columns=["date", col_name])


def download_yfinance_daily(ticker: str, col_name: str, start_date: str = "2005-01-01") -> pd.DataFrame:
    """
    Downloads daily historical series via yfinance and saves raw CSV.
    """
    import yfinance as yf
    local_path = RAW_DIR / f"yf_{ticker.replace('=', '_').replace('^', '')}.csv"
    print(f"Fetching Yahoo Finance daily: {ticker} -> {col_name}...")
    try:
        data = yf.download(ticker, start=start_date, progress=False)
        if not data.empty:
            # Flatten multiindex columns if present
            if isinstance(data.columns, pd.MultiIndex):
                close_series = data["Close"].iloc[:, 0]
            else:
                close_series = data["Close"]
            df = pd.DataFrame({"date": close_series.index, col_name: close_series.values})
            df["date"] = pd.to_datetime(df["date"]).dt.tz_localize(None)
            df[col_name] = pd.to_numeric(df[col_name], errors="coerce")
            df = df.dropna().sort_values("date").reset_index(drop=True)
            df.to_csv(local_path, index=False)
            print(f"  Successfully fetched {len(df)} daily points for {col_name}")
            return df
    except Exception as e:
        print(f"  yfinance download error for {ticker}: {e}")
        if local_path.exists():
            df = pd.read_csv(local_path)
            df["date"] = pd.to_datetime(df["date"])
            return df.sort_values("date").reset_index(drop=True)
            
    return pd.DataFrame(columns=["date", col_name])


def download_gpr_index() -> pd.DataFrame:
    """
    Downloads Geopolitical Risk (GPR) Index from Matteo Iacoviello.
    """
    local_path = RAW_DIR / "gpr_monthly.csv"
    url = "https://www.matteoiacoviello.com/gpr_files/gpr_monthly_recent.csv"
    print("Fetching Geopolitical Risk (GPR) Index...")
    try:
        resp = requests.get(url, headers=HEADERS, timeout=15)
        if resp.status_code == 200:
            with open(local_path, "w", encoding="utf-8") as f:
                f.write(resp.text)
            df = pd.read_csv(local_path)
            # Find month/year column and GPR column
            # Typically columns: month, GPR, GPRT, etc.
            date_col = [c for c in df.columns if "month" in c.lower() or "date" in c.lower()][0]
            gpr_col = [c for c in df.columns if c.upper() == "GPR"][0]
            df["date"] = pd.to_datetime(df[date_col].astype(str), format="%Y%m", errors="coerce")
            if df["date"].isna().all():
                df["date"] = pd.to_datetime(df[date_col], errors="coerce")
            df = df.dropna(subset=["date"])
            df["gpr_index"] = pd.to_numeric(df[gpr_col], errors="coerce")
            df = df[["date", "gpr_index"]].dropna().sort_values("date").reset_index(drop=True)
            print(f"  Successfully fetched {len(df)} GPR records")
            return df
    except Exception as e:
        print(f"  GPR download error: {e}")
        if local_path.exists():
            df = pd.read_csv(local_path)
            return df
            
    return pd.DataFrame(columns=["date", "gpr_index"])
