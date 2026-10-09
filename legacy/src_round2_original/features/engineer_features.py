"""
Feature Engineering Engine for Smart Buy
Constructs 60+ engineered features across 5 distinct economic families:
  1. Price Dynamics (multi-scale returns, MAs, volatility, z-scores, momentum crossovers)
  2. Feedstock & Cost-Push (energy, monomer spreads, cost-to-price ratios)
  3. Macro & Demand (China industrial activity, FX momentum, maritime freight)
  4. Supply & Inventory (LME stock drawdowns, cross-metal spillovers)
  5. Risk & Calendar (Geopolitical Risk, Economic Uncertainty, Shock flags, cyclical seasonality)

Creates multi-horizon targets y_h1 through y_h6 (log-returns).
"""

import numpy as np
import pandas as pd
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parents[2]
PROCESSED_DIR = BASE_DIR / "data" / "processed"


def build_material_features(df_master: pd.DataFrame, material: str = "aluminium") -> pd.DataFrame:
    """
    Builds the full feature matrix and direct multi-step target variables
    for a given raw material ('aluminium' or 'pvc').
    """
    print(f"Engineering features for {material.upper()}...")
    df = df_master.copy()
    df["date"] = pd.to_datetime(df["date"])
    df = df.sort_values("date").reset_index(drop=True)
    
    target_price_col = "lme_aluminium" if material == "aluminium" else "pvc_asia_spot"
    P = df[target_price_col]
    
    feat = pd.DataFrame({"date": df["date"]})
    feat["current_price"] = P
    
    # =========================================================================
    # MULTI-HORIZON TARGETS: y_t(h) = ln(P_{t+h} / P_t) for h in 1..6
    # =========================================================================
    for h in range(1, 7):
        feat[f"target_log_return_h{h}"] = np.log(P.shift(-h) / P)
        feat[f"target_price_h{h}"] = P.shift(-h)

    # =========================================================================
    # FAMILY 1: PRICE DYNAMICS
    # =========================================================================
    feat["price_log_ret_1m"] = np.log(P / P.shift(1))
    feat["price_log_ret_3m"] = np.log(P / P.shift(3))
    feat["price_log_ret_6m"] = np.log(P / P.shift(6))
    feat["price_log_ret_12m"] = np.log(P / P.shift(12))
    
    # Moving Average Ratios (mean-reversion indicators)
    feat["price_ma_ratio_3m"] = P / P.rolling(3).mean()
    feat["price_ma_ratio_6m"] = P / P.rolling(6).mean()
    feat["price_ma_ratio_12m"] = P / P.rolling(12).mean()
    
    # Volatilities & Z-Score
    feat["price_volatility_6m"] = feat["price_log_ret_1m"].rolling(6).std()
    feat["price_volatility_12m"] = feat["price_log_ret_1m"].rolling(12).std()
    ma12 = P.rolling(12).mean()
    std12 = P.rolling(12).std()
    feat["price_z_score_12m"] = (P - ma12) / std12.replace(0, np.nan)
    
    # Momentum crossover: MA(3) vs MA(12)
    feat["price_mom_crossover"] = np.sign(P.rolling(3).mean() - ma12)
    
    # Intra-month / short momentum proxy
    feat["price_acceleration_3m"] = feat["price_log_ret_1m"] - feat["price_log_ret_1m"].shift(2)

    # =========================================================================
    # FAMILY 2: FEEDSTOCK & COST-PUSH
    # =========================================================================
    if material == "aluminium":
        coal = df["china_coal_price"]
        alumina = df["alumina_price"]
        bauxite = df["bauxite_price"]
        gas_eu = df["natural_gas_europe"]
        
        feat["coal_log_ret_1m"] = np.log(coal / coal.shift(1))
        feat["coal_log_ret_3m"] = np.log(coal / coal.shift(3))
        feat["coal_log_ret_6m"] = np.log(coal / coal.shift(6))
        
        feat["alumina_log_ret_1m"] = np.log(alumina / alumina.shift(1))
        feat["alumina_log_ret_3m"] = np.log(alumina / alumina.shift(3))
        
        feat["bauxite_log_ret_3m"] = np.log(bauxite / bauxite.shift(3))
        
        # Cost-to-Price Spreads & Ratios
        feat["coal_to_lme_ratio"] = coal / P
        feat["alumina_to_lme_ratio"] = alumina / P
        feat["energy_smelting_pressure"] = (0.5 * (coal / coal.rolling(12).mean()) + 
                                            0.5 * (gas_eu / gas_eu.rolling(12).mean()))
        
        # Real Empirical Feedstock & Smelting Benchmarks
        if "ppi_primary_aluminum" in df.columns:
            feat["ppi_primary_aluminum_ret_3m"] = np.log(df["ppi_primary_aluminum"] / df["ppi_primary_aluminum"].shift(3))
        if "ip_aluminum_mfg" in df.columns:
            feat["ip_aluminum_diff_3m"] = df["ip_aluminum_mfg"] - df["ip_aluminum_mfg"].shift(3)
        if "wb_index_energy" in df.columns:
            feat["wb_energy_index_ret_3m"] = np.log(df["wb_index_energy"] / df["wb_index_energy"].shift(3))
        if "wb_index_basemetals" in df.columns:
            feat["wb_basemetals_index_ret_3m"] = np.log(df["wb_index_basemetals"] / df["wb_index_basemetals"].shift(3))
    else:  # PVC Resin
        naphtha = df["naphtha_price"]
        ethylene = df["ethylene_price"]
        vcm = df["vcm_price"]
        brent = df["crude_brent"]
        
        feat["ethylene_log_ret_1m"] = np.log(ethylene / ethylene.shift(1))
        feat["ethylene_log_ret_3m"] = np.log(ethylene / ethylene.shift(3))
        feat["ethylene_log_ret_6m"] = np.log(ethylene / ethylene.shift(6))
        
        feat["naphtha_log_ret_3m"] = np.log(naphtha / naphtha.shift(3))
        feat["crude_brent_log_ret_3m"] = np.log(brent / brent.shift(3))
        
        # Chemical Margins & Conversion Ratios
        feat["ethylene_to_pvc_ratio"] = ethylene / P
        feat["naphtha_to_ethylene_ratio"] = naphtha / ethylene
        feat["cracker_spread"] = ethylene - 1.25 * naphtha
        feat["pvc_monomer_margin"] = P - (0.46 * ethylene + 0.54 * vcm)
        
        # Real Empirical Resin & Monomer BLS/Fed Benchmarks
        if "ppi_plastic_resins" in df.columns:
            feat["ppi_resin_ret_3m"] = np.log(df["ppi_plastic_resins"] / df["ppi_plastic_resins"].shift(3))
        if "ppi_organic_chemicals" in df.columns:
            feat["ppi_monomer_ret_3m"] = np.log(df["ppi_organic_chemicals"] / df["ppi_organic_chemicals"].shift(3))
        if "ip_resin_mfg" in df.columns:
            feat["ip_resin_diff_3m"] = df["ip_resin_mfg"] - df["ip_resin_mfg"].shift(3)

    # =========================================================================
    # FAMILY 3: MACRO & DEMAND
    # =========================================================================
    pmi = df["pmi_china_mfg"]
    feat["pmi_china_level"] = pmi
    feat["pmi_china_diff_1m"] = pmi - pmi.shift(1)
    feat["pmi_china_diff_3m"] = pmi - pmi.shift(3)
    feat["pmi_china_expansion"] = (pmi > 50.0).astype(int)
    
    fx = df["usd_inr"]
    feat["usd_inr_level"] = fx
    feat["usd_inr_log_ret_1m"] = np.log(fx / fx.shift(1))
    feat["usd_inr_log_ret_3m"] = np.log(fx / fx.shift(3))
    feat["usd_inr_log_ret_12m"] = np.log(fx / fx.shift(12))
    feat["usd_inr_ma_ratio_6m"] = fx / fx.rolling(6).mean()
    
    bdi = df["freight_bdi"]
    feat["freight_bdi_log_ret_3m"] = np.log(bdi / bdi.shift(3))
    feat["freight_bdi_z_score_12m"] = (bdi - bdi.rolling(12).mean()) / bdi.rolling(12).std()
    
    # Real Freight & Total Industrial Production
    if "freight_tsi" in df.columns:
        feat["freight_tsi_ret_3m"] = np.log(df["freight_tsi"] / df["freight_tsi"].shift(3))
    if "indpro_macro" in df.columns:
        feat["indpro_macro_diff_3m"] = df["indpro_macro"] - df["indpro_macro"].shift(3)

    # =========================================================================
    # FAMILY 4: SUPPLY & INVENTORY
    # =========================================================================
    if material == "aluminium":
        stocks = df["lme_stocks_aluminium"]
        feat["lme_stocks_level"] = stocks
        feat["lme_stocks_log_ret_1m"] = np.log(stocks / stocks.shift(1))
        feat["lme_stocks_log_ret_3m"] = np.log(stocks / stocks.shift(3))
        feat["lme_stocks_log_ret_6m"] = np.log(stocks / stocks.shift(6))
        feat["lme_stocks_z_score_12m"] = (stocks - stocks.rolling(12).mean()) / stocks.rolling(12).std()
        
        # Cross-Commodity Base Metals Spillover
        copper = df["metal_copper"]
        zinc = df["metal_zinc"]
        feat["copper_log_ret_3m"] = np.log(copper / copper.shift(3))
        feat["zinc_log_ret_3m"] = np.log(zinc / zinc.shift(3))
        feat["metals_supercycle_signal"] = 0.5 * feat["copper_log_ret_3m"] + 0.5 * feat["zinc_log_ret_3m"]
    else:
        exports = df["un_comtrade_pvc_export"]
        feat["china_pvc_export_log_ret_3m"] = np.log(exports / exports.shift(3))
        feat["china_pvc_export_z_score_12m"] = (exports - exports.rolling(12).mean()) / exports.rolling(12).std()

    # =========================================================================
    # FAMILY 5: RISK, SHOCKS & CALENDAR
    # =========================================================================
    feat["gpr_index_level"] = df["gpr_index"]
    feat["gpr_index_log_ret_3m"] = np.log((df["gpr_index"] + 1) / (df["gpr_index"].shift(3) + 1))
    feat["gpr_threats_level"] = df["gpr_threats"]
    
    feat["epu_index_level"] = df["epu_index"]
    feat["epu_index_diff_3m"] = df["epu_index"] - df["epu_index"].shift(3)
    
    # Explicit Structural Shock Regimes
    feat["shock_flag_tariff"] = df["shock_flag_tariff"]
    feat["shock_flag_covid"] = df["shock_flag_covid"]
    feat["shock_flag_freeze"] = df["shock_flag_freeze"]
    feat["shock_flag_war"] = df["shock_flag_war"]
    feat["shock_flag_redsea"] = df["shock_flag_redsea"]
    
    # Cyclical Seasonality
    feat["month_sin"] = df["month_sin"]
    feat["month_cos"] = df["month_cos"]
    
    # Fill remaining NaNs from rolling windows (first 12 rows)
    feat = feat.bfill().ffill()
    
    print(f"  Generated {feat.shape[1]} columns (features + targets) for {len(feat)} months")
    return feat


def run_feature_engineering():
    """
    Loads master dataset and builds processed feature matrices for both materials.
    """
    master_path = PROCESSED_DIR / "master_dataset.csv"
    if not master_path.exists():
        raise FileNotFoundError(f"Master dataset not found at {master_path}. Run build_dataset first.")
        
    df_master = pd.read_csv(master_path)
    
    # Build Aluminium features
    df_al = build_material_features(df_master, material="aluminium")
    al_out = PROCESSED_DIR / "aluminium_feature_matrix.csv"
    df_al.to_csv(al_out, index=False)
    print(f"Saved Aluminium feature matrix: {al_out} ({df_al.shape})")
    
    # Build PVC features
    df_pvc = build_material_features(df_master, material="pvc")
    pvc_out = PROCESSED_DIR / "pvc_feature_matrix.csv"
    df_pvc.to_csv(pvc_out, index=False)
    print(f"Saved PVC feature matrix: {pvc_out} ({df_pvc.shape})")
    
    print("Feature engineering complete!")


if __name__ == "__main__":
    run_feature_engineering()
