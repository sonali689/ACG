"""Regenerate every deck chart in the ACG Round 1 palette.

White paper, ACG red #C8102E, near-black ink, thin grey rules. No dark theme,
no gradients. Output is 200 dpi PNG sized for the slide slots.
"""
import json
from pathlib import Path

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
from matplotlib.ticker import FuncFormatter

BASE = Path(__file__).resolve().parents[2]
OUT = BASE / "outputs/charts_acg"
OUT.mkdir(parents=True, exist_ok=True)

ACG, INK, MUTE, RULE = "#C8102E", "#16181D", "#7C8089", "#E2E3E7"
BUY, DEFER, HOLD = "#0F6B3F", "#8A5A00", "#3F4A5C"

plt.rcParams.update({
    "font.family": "sans-serif",
    "font.sans-serif": ["Poppins", "DejaVu Sans"],
    "font.size": 8.5, "axes.edgecolor": RULE, "axes.linewidth": .8,
    "axes.labelcolor": MUTE, "xtick.color": MUTE, "ytick.color": MUTE,
    "xtick.labelsize": 7.5, "ytick.labelsize": 7.5,
    "axes.grid": True, "grid.color": "#F0F1F3", "grid.linewidth": .8,
    "figure.facecolor": "white", "axes.facecolor": "white",
    "legend.frameon": False, "legend.fontsize": 7.5,
    "savefig.facecolor": "white", "savefig.bbox": "tight", "savefig.pad_inches": .12,
})


def clean(ax, money=True):
    for s in ("top", "right"):
        ax.spines[s].set_visible(False)
    ax.spines["left"].set_color(RULE); ax.spines["bottom"].set_color(RULE)
    if money:
        ax.yaxis.set_major_formatter(FuncFormatter(lambda v, _: f"${v:,.0f}"))
    ax.set_axisbelow(True)


def save(fig, name):
    p = OUT / name
    fig.savefig(p, dpi=200)
    plt.close(fig)
    print("  ", name)


D = json.loads((BASE / "dashboard/data.json").read_text())

for key in ("aluminium", "pvc"):
    m = D["materials"][key]
    short = m["short"]

    # 1 --- backtest trajectory: forecast vs realised at h=3 -----------------
    b = m["backtest"]
    x = pd.to_datetime(b["labels"])
    fig, ax = plt.subplots(figsize=(7.6, 2.9))
    ax.fill_between(x, b["p10"], b["p90"], color=ACG, alpha=.10, lw=0,
                    label="P10–P90 band")
    ax.plot(x, b["actual"], color=INK, lw=1.7, label="Realised price")
    ax.plot(x, b["pred"], color=ACG, lw=1.6, label="Forecast, made 3 months earlier")
    clean(ax)
    ax.legend(loc="upper left", ncol=3, bbox_to_anchor=(0, 1.13))
    ax.set_ylabel("US$ / tonne", fontsize=7.5)
    save(fig, f"{key}_backtest.png")

    # 2 --- model ladder ----------------------------------------------------
    lad = sorted(m["ladder"], key=lambda r: -r["mape"])
    names = [r["model"] for r in lad]
    vals = [r["mape"] for r in lad]
    cols = [ACG if r["is_ensemble"] else (INK if r["model"] == "N-BEATS" else "#C9CBD1")
            for r in lad]
    naive = next(r["mape"] for r in lad if r["model"] == "Naive")
    fig, ax = plt.subplots(figsize=(6.4, 3.1))
    ax.barh(names, vals, color=cols, height=.64)
    ax.axvline(naive, color=MUTE, ls="--", lw=1)
    ax.text(naive, len(names) - .3, "  naïve gate", color=MUTE, fontsize=7.5, va="center")
    for i, v in enumerate(vals):
        ax.text(v + max(vals) * .012, i, f"{v:.2f}%", va="center",
                fontsize=7.5, color=INK)
    clean(ax, money=False)
    ax.set_xlabel("MAPE at h = 3, lower is better", fontsize=7.5)
    ax.set_xlim(0, max(vals) * 1.16)
    ax.grid(axis="y", visible=False)
    save(fig, f"{key}_ladder.png")

    # 3 --- skill and direction by horizon ----------------------------------
    sc = m["scorecard"]
    h = [r["h"] for r in sc]
    fig, ax = plt.subplots(figsize=(6.4, 2.6))
    ax.bar([i - .19 for i in h], [r["skill"] for r in sc], width=.38,
           color=ACG, label="Skill vs naïve (%)")
    ax2 = ax.twinx()
    ax2.plot(h, [r["dir"] for r in sc], color=INK, lw=1.6, marker="o",
             ms=4, label="Directional accuracy (%)")
    ax2.axhline(50, color=MUTE, ls=":", lw=1)
    ax2.set_ylim(35, 95); ax2.grid(False)
    ax2.spines["top"].set_visible(False)
    ax2.tick_params(colors=MUTE, labelsize=7.5)
    clean(ax, money=False)
    ax.set_xlabel("months ahead", fontsize=7.5)
    ax.set_xticks(h)
    l1, lb1 = ax.get_legend_handles_labels(); l2, lb2 = ax2.get_legend_handles_labels()
    ax.legend(l1 + l2, lb1 + lb2, loc="upper left", ncol=2, bbox_to_anchor=(0, 1.16))
    save(fig, f"{key}_skill.png")

    # 4 --- lead-lag drivers ------------------------------------------------
    drv = m["drivers"][:8][::-1]
    fig, ax = plt.subplots(figsize=(6.4, 3.0))
    nm = [d["name"][:34] for d in drv]
    rho = [d["rho"] for d in drv]
    ax.barh(nm, rho, color=[BUY if r > 0 else ACG for r in rho], height=.62)
    for i, d in enumerate(drv):
        off = .012 if d["rho"] > 0 else -.012
        ax.text(d["rho"] + off, i, f"lag {d['lead']}m",
                va="center", ha="left" if d["rho"] > 0 else "right",
                fontsize=7, color=MUTE)
    ax.axvline(0, color=INK, lw=.9)
    clean(ax, money=False)
    ax.set_xlabel("peak cross-correlation of log-returns, signed", fontsize=7.5)
    ax.grid(axis="y", visible=False)
    ax.set_xlim(min(rho) * 1.55, max(rho) * 1.55)
    save(fig, f"{key}_drivers.png")

    # 5 --- band coverage vs gate -------------------------------------------
    bd = m["bands"]
    hh = [int(r["h"].replace("h=", "")) for r in bd]
    cov = [r["cov"] for r in bd]
    fig, ax = plt.subplots(figsize=(5.4, 2.4))
    ax.axhspan(75, 85, color=BUY, alpha=.12, lw=0)
    ax.bar(hh, cov, color=[BUY if 75 <= c <= 85 else ACG for c in cov], width=.55)
    for i, c in zip(hh, cov):
        ax.text(i, c + 1.4, f"{c:.0f}%", ha="center", fontsize=7.5, color=INK)
    ax.text(6.35, 80, "gate\n75–85%", fontsize=7, color=BUY, va="center")
    clean(ax, money=False)
    ax.set_ylim(0, 100); ax.set_xticks(hh)
    ax.set_xlabel("months ahead", fontsize=7.5)
    ax.set_ylabel("P10–P90 coverage", fontsize=7.5)
    save(fig, f"{key}_bands.png")

    # 6 --- buying replay ---------------------------------------------------
    r = m["replay"]; c = r["curve"]
    xx = pd.to_datetime(c["labels"])
    fig, (axa, axb) = plt.subplots(2, 1, figsize=(7.6, 3.3), sharex=True,
                                   gridspec_kw={"height_ratios": [2.4, 1]})
    axa.plot(xx, c["cum"], color=BUY, lw=1.9)
    axa.fill_between(xx, 0, c["cum"], color=BUY, alpha=.12, lw=0)
    axa.axhline(0, color=MUTE, lw=.9)
    axa.yaxis.set_major_formatter(FuncFormatter(lambda v, _: f"{v:+.1f}%"))
    for s in ("top", "right"):
        axa.spines[s].set_visible(False)
    axa.set_ylabel("cumulative saving\nvs buying monthly", fontsize=7.5)
    axa.set_title(f"{short} — {r['gross_pct']:+.2f}% gross, "
                  f"{r['net_pct']:+.2f}% net of carry, over {r['months']} months",
                  fontsize=8.5, color=INK, loc="left", pad=8)

    colmap = {"BUY NOW": BUY, "DEFER": DEFER, "BUY NORMAL": "#D8DAE0"}
    axb.bar(xx, [1] * len(xx), width=24,
            color=[colmap[s] for s in c["signal"]])
    axb.set_yticks([]); axb.grid(False)
    for s in ("top", "right", "left"):
        axb.spines[s].set_visible(False)
    axb.set_ylabel("signal", fontsize=7.5)
    handles = [plt.Rectangle((0, 0), 1, 1, color=v) for v in colmap.values()]
    axb.legend(handles, colmap.keys(), ncol=3, loc="lower left",
               bbox_to_anchor=(0, -1.25), fontsize=7.5)
    save(fig, f"{key}_replay.png")

# 7 --- error correlation heatmap (aluminium, explains the ensemble) --------
ec = pd.read_csv(BASE / "outputs/tables/error_corr_PVC_h3.csv", index_col=0)
lbl = ["Naive", "Seas.naive", "ETS", "ElasticNet", "BayesRidge", "LightGBM",
       "LSTM", "N-BEATS"]
fig, ax = plt.subplots(figsize=(4.6, 4.0))
im = ax.imshow(ec.values, cmap="Reds", vmin=0.3, vmax=1.0)
ax.set_xticks(range(len(lbl))); ax.set_xticklabels(lbl, rotation=45, ha="right")
ax.set_yticks(range(len(lbl))); ax.set_yticklabels(lbl)
for i in range(len(lbl)):
    for j in range(len(lbl)):
        v = ec.values[i, j]
        ax.text(j, i, f"{v:.2f}", ha="center", va="center", fontsize=6.4,
                color="white" if v > .8 else INK)
ax.grid(False)
ax.set_title("Forecast-error correlation, PVC h=3", fontsize=8.5, color=INK,
             loc="left", pad=8)
save(fig, "error_corr_pvc.png")

print(f"\ncharts -> {OUT}")
