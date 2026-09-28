"""
Smart Buy Decision Engine & Buying Replay Simulator
Implements:
  1. Horizon-weighted expected saving calculation:
     S(h) = (P_hat(h) - P_0) / P_0 - c * h
  2. Procurement Signals: BUY NOW, BUY NORMAL, DEFER
  3. Continuous Buying Replay Simulation across 2018-2024 vs Baseline Policy:
     - Tracks Average Purchase Price ($/t)
     - Spend Savings (%)
     - RM Inventory Days & Working Capital Impact (per Rs 100 Cr spend)
"""

import numpy as np
import pandas as pd
from pathlib import Path
from typing import Dict, List, Tuple

BASE_DIR = Path(__file__).resolve().parents[2]
SCORECARDS_DIR = BASE_DIR / "outputs" / "scorecards"
OUTPUTS_DIR = BASE_DIR / "outputs"


class SmartBuyDecisionEngine:
    def __init__(self,
                 monthly_carrying_cost: float = 0.010,  # 1.0% per month
                 buy_threshold: float = 0.02,          # +2.0%
                 defer_threshold: float = -0.02,       # -2.0%
                 min_direction_prob: float = 0.60):    # 60%
        self.c = monthly_carrying_cost
        self.buy_thresh = buy_threshold
        self.defer_thresh = defer_threshold
        self.min_prob = min_direction_prob

    def evaluate_signal(self, current_price: float, pred_price_3m: float, p_up: float) -> Tuple[str, float, float]:
        """
        Evaluates decision rule at the 3-month decision horizon (h=3).
        Returns (signal, expected_saving_pct, recommended_cover_months).
        """
        # Expected saving over 3 months after carrying cost
        price_change_pct = (pred_price_3m - current_price) / current_price
        expected_saving = price_change_pct - (self.c * 3.0)
        
        if expected_saving > self.buy_thresh and p_up >= self.min_prob:
            signal = "BUY NOW"
            rec_cover = 3.0  # Max forward cover
        elif expected_saving < self.defer_thresh and (1.0 - p_up) >= self.min_prob:
            signal = "DEFER"
            rec_cover = 1.0  # Minimum safety cover
        else:
            signal = "BUY NORMAL"
            rec_cover = 1.5  # Standard operating cover
            
        return signal, round(expected_saving * 100.0, 2), rec_cover


def run_buying_replay(material: str = "aluminium", monthly_bom_tonnes: float = 1000.0) -> Tuple[pd.DataFrame, dict]:
    """
    Simulates monthly procurement execution across all walk-forward test origins (2018-2024).
    Compares Smart Buy dynamic cover vs Baseline fixed 1.5-month cover.
    """
    print(f"\nRunning Buying Replay Simulation for {material.upper()} (2018-2024)...")
    preds_file = SCORECARDS_DIR / f"{material}_walk_forward_predictions.csv"
    if not preds_file.exists():
        raise FileNotFoundError(f"Walk-forward predictions not found at {preds_file}. Run walk_forward first.")
        
    df_preds = pd.read_csv(preds_file)
    # Focus on h=3 decision horizon predictions
    df_h3 = df_preds[df_preds["horizon"] == 3].sort_values("origin_date").reset_index(drop=True)
    
    engine = SmartBuyDecisionEngine()
    
    # State tracking
    sb_inventory = 1.5 * monthly_bom_tonnes
    base_inventory = 1.5 * monthly_bom_tonnes
    
    sb_total_spend = 0.0
    sb_total_tonnes = 0.0
    base_total_spend = 0.0
    base_total_tonnes = 0.0
    
    records = []
    
    for i, row in df_h3.iterrows():
        date_str = row["origin_date"]
        curr_p = float(row["current_price"])
        pred_p = float(row["pred_price_ensemble"])
        pred_ret = float(row["pred_return_ensemble"])
        
        # P(up) estimate: probability that return > 0 from ensemble log return
        p_up = 1.0 / (1.0 + np.exp(-12.0 * pred_ret))  # calibrated sigmoid
        
        # Generate Signal
        signal, exp_saving, rec_cover = engine.evaluate_signal(curr_p, pred_p, p_up)
        
        # Smart Buy Order Execution
        # Order quantity = recommended_cover * BoM - current_inventory + monthly_consumption
        sb_target_inventory = rec_cover * monthly_bom_tonnes
        sb_order_qty = max(0.5 * monthly_bom_tonnes, sb_target_inventory - sb_inventory + monthly_bom_tonnes)
        sb_cost = sb_order_qty * curr_p
        sb_total_spend += sb_cost
        sb_total_tonnes += sb_order_qty
        sb_inventory = sb_inventory + sb_order_qty - monthly_bom_tonnes
        sb_days = (sb_inventory / monthly_bom_tonnes) * 30.0
        
        # Baseline Order Execution (Fixed 1.5 months cover every month)
        base_order_qty = monthly_bom_tonnes
        base_cost = base_order_qty * curr_p
        base_total_spend += base_cost
        base_total_tonnes += base_order_qty
        base_days = 45.0  # 1.5 months = 45 days
        
        records.append({
            "date": date_str,
            "material": material,
            "current_price": curr_p,
            "pred_price_3m": pred_p,
            "p_up": round(p_up, 3),
            "expected_saving_pct": exp_saving,
            "signal": signal,
            "recommended_cover_months": rec_cover,
            "smartbuy_order_qty": sb_order_qty,
            "smartbuy_cost": sb_cost,
            "smartbuy_inventory_days": round(sb_days, 1),
            "baseline_order_qty": base_order_qty,
            "baseline_cost": base_cost,
            "baseline_inventory_days": base_days
        })
        
    df_replay = pd.DataFrame(records)
    
    # Financial Impact Metrics
    avg_sb_price = sb_total_spend / sb_total_tonnes
    avg_base_price = base_total_spend / base_total_tonnes
    price_saving_pct = ((avg_base_price - avg_sb_price) / avg_base_price) * 100.0
    
    avg_sb_days = df_replay["smartbuy_inventory_days"].mean()
    days_reduced = 45.0 - avg_sb_days
    
    # Per Rs 100 Cr Spend Scaling
    annual_spend_cr = 100.0
    p_saving_cr = (price_saving_pct / 100.0) * annual_spend_cr
    wc_released_cr = (days_reduced / 365.0) * annual_spend_cr
    
    summary = {
        "material": material,
        "n_months": len(df_replay),
        "avg_baseline_price_usd": round(avg_base_price, 2),
        "avg_smartbuy_price_usd": round(avg_sb_price, 2),
        "price_saving_pct": round(price_saving_pct, 2),
        "avg_inventory_days_smartbuy": round(avg_sb_days, 1),
        "inventory_days_reduced": round(days_reduced, 1),
        "saving_per_100cr_spend": round(p_saving_cr, 2),
        "working_capital_released_per_100cr": round(wc_released_cr, 2),
        "signal_distribution": df_replay["signal"].value_counts().to_dict()
    }
    
    replay_csv = OUTPUTS_DIR / f"{material}_buying_replay.csv"
    df_replay.to_csv(replay_csv, index=False)
    
    summary_json = OUTPUTS_DIR / f"{material}_replay_summary.json"
    import json
    with open(summary_json, "w") as f:
        json.dump(summary, f, indent=2)
        
    print(f"  Saved Buying Replay to: {replay_csv}")
    print(f"  Avg Baseline Price: ${avg_base_price:.2f}/t")
    print(f"  Avg Smart Buy Price: ${avg_sb_price:.2f}/t  (Savings: {price_saving_pct:.2f}%)")
    print(f"  Average RM Inventory Days: {avg_sb_days:.1f} days (Reduced by: {days_reduced:.1f} days)")
    print(f"  Direct Spend Savings per Rs 100 Cr: Rs {p_saving_cr:.2f} Cr / year")
    print(f"  Working Capital Released per Rs 100 Cr: Rs {wc_released_cr:.2f} Cr")
    print(f"  Signal distribution: {summary['signal_distribution']}")
    
    return df_replay, summary


def run_all_buying_replays():
    run_buying_replay("aluminium")
    run_buying_replay("pvc")
    print("\nAll Buying Replays Completed Successfully!")


if __name__ == "__main__":
    run_all_buying_replays()
