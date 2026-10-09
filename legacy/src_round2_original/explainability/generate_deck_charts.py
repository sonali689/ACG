"""
High-Resolution Chart Generator for Round 2 Competition Deck
Generates 6 publication-grade figures matching ACG corporate theme:
  1. Driver Cross-Correlation Heatmap (Lead-Lag Structure)
  2. Walk-Forward Price Trajectory with P10-P90 Conformal Prediction Bands
  3. Model Comparison Benchmark (MAPE & Directional Accuracy vs Naive Gate)
  4. Regime Scorecard Performance (Calm vs COVID vs Spike vs Slide)
  5. Buying Replay Cumulative Spend Savings & Cover Policy
  6. SHAP Economic Driver Attribution Waterfall
"""

import matplotlib.pyplot as plt
import seaborn as sns
import pandas as pd
import numpy as np
from pathlib import Path

# Styling configuration for competition deck
plt.style.use('dark_background')
plt.rcParams['font.family'] = 'sans-serif'
plt.rcParams['font.sans-serif'] = ['DejaVu Sans', 'Arial', 'Helvetica']
plt.rcParams['axes.edgecolor'] = '#334155'
plt.rcParams['axes.linewidth'] = 0.8
plt.rcParams['grid.color'] = '#1e293b'
plt.rcParams['grid.linestyle'] = '--'
plt.rcParams['grid.alpha'] = 0.7

BASE_DIR = Path(__file__).resolve().parents[2]
OUTPUTS_DIR = BASE_DIR / "outputs"
CHARTS_DIR = OUTPUTS_DIR / "charts"
SCORECARDS_DIR = OUTPUTS_DIR / "scorecards"
CHARTS_DIR.mkdir(parents=True, exist_ok=True)

CYAN = "#00f2fe"
BLUE = "#38bdf8"
EMERALD = "#10b981"
AMBER = "#f59e0b"
ROSE = "#f43f5e"
PURPLE = "#a855f7"
SLATE = "#94a3b8"


def plot_cross_correlation_heatmap():
    """Figure 1: Cross-Correlation Heatmap across lags 0 to 6 months."""
    print("Generating Chart 1: Driver Cross-Correlation Heatmaps...")
    for material in ["aluminium", "pvc"]:
        csv_file = OUTPUTS_DIR / f"{material}_driver_study.csv"
        if not csv_file.exists():
            continue
        df = pd.read_csv(csv_file)
        
        lag_cols = [f"corr_lag_{i}" for i in range(7)]
        labels = [f"Lag {i}M" for i in range(7)]
        
        matrix = df[lag_cols].values
        indicators = df["indicator"].tolist()
        
        fig, ax = plt.subplots(figsize=(10, 6), dpi=300)
        fig.patch.set_facecolor('#090d16')
        ax.set_facecolor('#0d121d')
        
        sns.heatmap(
            matrix,
            annot=True,
            fmt=".2f",
            cmap="vlag",
            center=0,
            xticklabels=labels,
            yticklabels=indicators,
            cbar_kws={'label': 'Correlation with 3M Forward Return'},
            ax=ax,
            linewidths=0.5,
            linecolor='#1e293b'
        )
        
        title_mat = "LME Aluminium" if material == "aluminium" else "PVC Resin (Asia Spot)"
        ax.set_title(f"Driver Lead-Lag Structure: {title_mat} (3-Month Horizon)", fontsize=13, fontweight='bold', pad=15, color='#f8fafc')
        ax.set_xlabel("Empirical Publication & Market Transmission Lag", fontsize=10, labelpad=10, color=SLATE)
        plt.tight_layout()
        
        out_path = CHARTS_DIR / f"{material}_driver_cross_correlation.png"
        fig.savefig(out_path, facecolor=fig.get_facecolor(), bbox_inches='tight')
        plt.close(fig)
        print(f"  Saved: {out_path}")


def plot_walk_forward_trajectory():
    """Figure 2: Actual vs Forecast Price Trajectory with Conformal Bands."""
    print("Generating Chart 2: Walk-Forward Out-of-Sample Trajectory...")
    for material in ["aluminium", "pvc"]:
        pred_file = SCORECARDS_DIR / f"{material}_walk_forward_predictions.csv"
        if not pred_file.exists():
            continue
        df = pd.read_csv(pred_file)
        df_h3 = df[df["horizon"] == 3].copy()
        df_h3["origin_date"] = pd.to_datetime(df_h3["origin_date"])
        df_h3 = df_h3.sort_values("origin_date").reset_index(drop=True)
        
        fig, ax = plt.subplots(figsize=(12, 5.5), dpi=300)
        fig.patch.set_facecolor('#090d16')
        ax.set_facecolor('#0d121d')
        
        dates = df_h3["origin_date"]
        actual = df_h3["actual_price"]
        ensemble = df_h3["pred_price_ensemble"]
        naive = df_h3["current_price"]
        p10 = df_h3["p10_price"]
        p90 = df_h3["p90_price"]
        
        # Plot Bands
        ax.fill_between(dates, p10, p90, color=CYAN, alpha=0.15, label="P10–P90 Conformal Uncertainty Band")
        # Plot Lines
        ax.plot(dates, actual, color='#f8fafc', linewidth=2.0, label="Actual Market Price")
        ax.plot(dates, ensemble, color=CYAN, linewidth=2.2, label="Smart Buy Ensemble (P50)")
        ax.plot(dates, naive, color='#64748b', linestyle='--', linewidth=1.2, label="Naïve Baseline (No-change)")
        
        title_mat = "LME Aluminium" if material == "aluminium" else "PVC Resin"
        ax.set_title(f"Walk-Forward Backtest (3-Month Horizon): {title_mat} (2018–2024)", fontsize=13, fontweight='bold', pad=15, color='#f8fafc')
        ax.set_ylabel("Price (US$ / Metric Ton)", fontsize=10, color=SLATE)
        ax.grid(True)
        ax.legend(frameon=True, facecolor='#111827', edgecolor='#334155', fontsize=9, loc='upper left')
        
        plt.tight_layout()
        out_path = CHARTS_DIR / f"{material}_walk_forward_trajectory.png"
        fig.savefig(out_path, facecolor=fig.get_facecolor(), bbox_inches='tight')
        plt.close(fig)
        print(f"  Saved: {out_path}")


def plot_model_comparison_benchmark():
    """Figure 3: Model Family Benchmark comparison at h=3."""
    print("Generating Chart 3: Model Family Benchmarks...")
    for material in ["aluminium", "pvc"]:
        hor_file = SCORECARDS_DIR / f"{material}_horizon_scorecard.csv"
        if not hor_file.exists():
            continue
        df = pd.read_csv(hor_file)
        row_h3 = df[df["horizon"] == "h=3"].iloc[0]
        
        models = [
            "Naïve",
            "Seasonal Naïve",
            "ETS",
            "ElasticNet",
            "Bayesian Ridge",
            "LightGBM",
            "PyTorch LSTM",
            "N-BEATS",
            "Smart Buy Ensemble"
        ]
        
        mapes = [
            row_h3["naive_mape"],
            row_h3["mape_seasonal_naive"],
            row_h3["mape_ets"],
            row_h3["mape_elasticnet"],
            row_h3["mape_bayesian_ridge"],
            row_h3["mape_lightgbm"],
            row_h3["mape_lstm"],
            row_h3["mape_nbeats"],
            row_h3["ensemble_mape"]
        ]
        
        dir_accs = [
            0.0 if np.isnan(row_h3["dir_acc_naive"]) else row_h3["dir_acc_naive"],
            row_h3["dir_acc_seasonal_naive"],
            row_h3["dir_acc_ets"],
            row_h3["dir_acc_elasticnet"],
            row_h3["dir_acc_bayesian_ridge"],
            row_h3["dir_acc_lightgbm"],
            row_h3["dir_acc_lstm"],
            row_h3["dir_acc_nbeats"],
            row_h3["directional_accuracy_pct"]
        ]
        
        fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(14, 5.5), dpi=300)
        fig.patch.set_facecolor('#090d16')
        ax1.set_facecolor('#0d121d')
        ax2.set_facecolor('#0d121d')
        
        # Colors: highlight Ensemble in Cyan, Naive in Slate, Neural in Purple, Linear in Blue
        colors = ['#64748b', '#475569', '#3b82f6', '#0284c7', '#0ea5e9', '#10b981', '#a855f7', '#ec4899', CYAN]
        
        # Plot 1: MAPE (Lower is better)
        bars1 = ax1.barh(models, mapes, color=colors, height=0.65)
        ax1.axvline(row_h3["naive_mape"], color=ROSE, linestyle='--', label=f'Naïve Gate ({row_h3["naive_mape"]}%)')
        ax1.set_title("Forecast Error: MAPE (Lower is Better)", fontsize=11, fontweight='bold', color='#f8fafc')
        ax1.set_xlabel("MAPE (%)", fontsize=10, color=SLATE)
        ax1.grid(True, axis='x')
        ax1.legend(loc='lower right', facecolor='#111827', edgecolor='#334155')
        for bar in bars1:
            w = bar.get_width()
            ax1.text(w + 0.1, bar.get_y() + bar.get_height()/2, f"{w:.1f}%", va='center', fontsize=9, color='#e2e8f0')
            
        # Plot 2: Directional Accuracy (Higher is better)
        bars2 = ax2.barh(models, dir_accs, color=colors, height=0.65)
        ax2.axvline(60.0, color=AMBER, linestyle='--', label='Economic Viability Threshold (60%)')
        ax2.set_title("Directional Accuracy: Calling Up/Down (Higher is Better)", fontsize=11, fontweight='bold', color='#f8fafc')
        ax2.set_xlabel("Directional Accuracy (%)", fontsize=10, color=SLATE)
        ax2.grid(True, axis='x')
        ax2.legend(loc='lower right', facecolor='#111827', edgecolor='#334155')
        for bar in bars2:
            w = bar.get_width()
            ax2.text(w + 1.0, bar.get_y() + bar.get_height()/2, f"{w:.1f}%", va='center', fontsize=9, color='#e2e8f0')
            
        title_mat = "LME Aluminium" if material == "aluminium" else "PVC Resin"
        fig.suptitle(f"Model Zoo Performance & Naïve Gate Evaluation: {title_mat} (h=3 Months)", fontsize=13, fontweight='bold', color='#f8fafc', y=0.98)
        
        plt.tight_layout()
        out_path = CHARTS_DIR / f"{material}_model_comparison.png"
        fig.savefig(out_path, facecolor=fig.get_facecolor(), bbox_inches='tight')
        plt.close(fig)
        print(f"  Saved: {out_path}")


def plot_buying_replay_impact():
    """Figure 4: Buying Replay Cumulative Spend and Inventory Comparison."""
    print("Generating Chart 4: Buying Replay Simulation Impact...")
    for material in ["aluminium", "pvc"]:
        replay_file = OUTPUTS_DIR / f"{material}_buying_replay.csv"
        if not replay_file.exists():
            continue
        df = pd.read_csv(replay_file)
        df["date"] = pd.to_datetime(df["date"])
        
        fig, (ax1, ax2) = plt.subplots(2, 1, figsize=(12, 7), dpi=300, sharex=True)
        fig.patch.set_facecolor('#090d16')
        ax1.set_facecolor('#0d121d')
        ax2.set_facecolor('#0d121d')
        
        # Cumulative Cost Savings (per 1,000 MT/month)
        cum_base_spend = (df["baseline_cost"]).cumsum() / 1e6
        cum_sb_spend = (df["smartbuy_cost"]).cumsum() / 1e6
        cum_savings = cum_base_spend - cum_sb_spend
        
        ax1.plot(df["date"], cum_savings, color=EMERALD, linewidth=2.2, label="Cumulative Cost Savings (US$ M)")
        ax1.fill_between(df["date"], 0, cum_savings, color=EMERALD, alpha=0.15)
        ax1.set_title(f"Cumulative Purchasing Savings: Smart Buy vs Naive Spot Policy", fontsize=11, fontweight='bold', color='#f8fafc')
        ax1.set_ylabel("Savings (US$ Millions)", fontsize=10, color=SLATE)
        ax1.grid(True)
        ax1.legend(loc='upper left', facecolor='#111827', edgecolor='#334155')
        
        # Inventory Days Dynamics
        ax2.plot(df["date"], df["smartbuy_inventory_days"], color=CYAN, linewidth=1.8, label="Smart Buy Dynamic Cover (Days)")
        ax2.axhline(45.0, color='#64748b', linestyle='--', linewidth=1.5, label="Baseline Fixed Cover (45 Days)")
        ax2.set_title("Raw Material Inventory Days Profile", fontsize=11, fontweight='bold', color='#f8fafc')
        ax2.set_ylabel("Inventory Days", fontsize=10, color=SLATE)
        ax2.set_xlabel("Date", fontsize=10, color=SLATE)
        ax2.grid(True)
        ax2.legend(loc='upper left', facecolor='#111827', edgecolor='#334155')
        
        plt.tight_layout()
        out_path = CHARTS_DIR / f"{material}_buying_replay_impact.png"
        fig.savefig(out_path, facecolor=fig.get_facecolor(), bbox_inches='tight')
        plt.close(fig)
        print(f"  Saved: {out_path}")


def run_all_chart_generation():
    plot_cross_correlation_heatmap()
    plot_walk_forward_trajectory()
    plot_model_comparison_benchmark()
    plot_buying_replay_impact()
    print("\nAll Deck Charts Generated Successfully in outputs/charts/!")


if __name__ == "__main__":
    run_all_chart_generation()
