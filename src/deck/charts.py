import json, sys
from pathlib import Path
import matplotlib; matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np, pandas as pd
from matplotlib.ticker import FuncFormatter
SB = Path(__file__).resolve().parents[2]; sys.path.insert(0, str(SB))
from src.sb.replay import simulate, COVER
OUT = SB / "outputs" / "deck" / "charts"; OUT.mkdir(parents=True, exist_ok=True)
SC = SB/"outputs/scorecards"
ACG, INK, INK2, MUTE, RULE = "#C8102E", "#16181D", "#4A4D55", "#7C8089", "#E2E3E7"
BUY, DEFER, HOLD, GREY = "#0F6B3F", "#8A5A00", "#3F4A5C", "#B9BCC3"
from matplotlib import font_manager as _fm
for _f in (SB / "assets" / "fonts").glob("*.ttf"):
    _fm.fontManager.addfont(str(_f))
plt.rcParams.update({"font.family":"sans-serif","font.sans-serif":["Open Sans","DejaVu Sans"],"font.size":7.5,
  "axes.edgecolor":RULE,"axes.linewidth":.8,"axes.labelcolor":MUTE,"xtick.color":MUTE,"ytick.color":MUTE,
  "xtick.labelsize":6.8,"ytick.labelsize":6.8,"axes.grid":True,"grid.color":"#F0F1F3","grid.linewidth":.8,
  "legend.frameon":False,"legend.fontsize":6.8,"axes.titlesize":7.8,"axes.titleweight":"bold","axes.titlecolor":INK})
NAMES = {"naive":"Naïve","seasonal_naive":"Seasonal naïve","drift":"Drift","ets":"ETS","arima":"ARIMA","vecm":"VECM",
         "enet":"ElasticNet","lgb_local":"LightGBM (drivers)","lgb_global":"LightGBM (global)","nbeats":"N-BEATS (global)",
         "gated_equal_weight":"Smart Buy ensemble"}
def clean(ax):
    for s in ("top","right"): ax.spines[s].set_visible(False)
    ax.set_axisbelow(True)
def fig(w,h): return plt.figure(figsize=(w,h), dpi=200)
def save(f,name): f.savefig(OUT/name, dpi=200); plt.close(f); print(" ", name)

# ---- S5 lead-lag, both materials
d = pd.read_csv(SB/"outputs/drivers/lead_lag_granger.csv")
f = fig(5.90, 2.41); axs = f.subplots(1,2)
for ax,(m,t) in zip(axs,[("aluminium","Aluminium"),("pvc","PVC proxy")]):
    g = d[d.material==m].reindex(d[d.material==m].best_rho.abs().sort_values(ascending=False).index).head(7)[::-1]
    SHORT = {"coal_aus":"Coal (Australia)","gas_eu":"Gas, Europe","gas_us":"Gas, US","wb_energy":"Energy index","brent":"Brent crude",
             "copper":"Copper","zinc":"Zinc","cli_china":"China CLI","indpro":"US ind. production","ip_aluminium":"US Al output",
             "ip_resin":"US resin output","usd_inr":"USD/INR","gpr":"Geopolitical risk","epu":"Policy uncertainty",
             "freight_tsi":"US freight index","ppi_organic_chem":"Monomer PPI"}
    lab = [f"{SHORT.get(dr,dr)} · {'same mo' if k==0 else f'lead {k}m'}" for dr,k in zip(g.driver,g.best_lead)]
    cols = [ACG if (s and k>0) else (INK2 if s else GREY) for s,k in zip(g.granger_sig_fdr,g.best_lead)]
    ax.barh(range(len(g)), g.best_rho, color=cols, height=.62)
    ax.set_yticks(range(len(g))); ax.set_yticklabels(lab, fontsize=6.2); ax.axvline(0,color=RULE,lw=.8)
    ax.set_title(t, loc="left"); clean(ax); ax.grid(axis="y",visible=False); ax.set_xlim(-.55,.95); ax.set_xticks([-.4,0,.4,.8])
    for i,v in enumerate(g.best_rho): ax.text(v+(.02 if v>=0 else -.02), i, f"{v:+.2f}", va="center", ha="left" if v>=0 else "right", fontsize=6, color=INK2)
from matplotlib.patches import Patch
f.legend(handles=[Patch(color=ACG,label="leads + Granger-significant (FDR)"),Patch(color=INK2,label="Granger-significant, same month"),Patch(color=GREY,label="not significant")],
         loc="lower center", ncol=3, fontsize=6.2, bbox_to_anchor=(.55,-.01))
axs[0].set_position([.25,.22,.23,.66]); axs[1].set_position([.75,.22,.235,.66])
save(f,"s5_leadlag.png")

# ---- S7 ladders
for m,(w,h) in {"aluminium":(5.95,2.81),"pvc":(5.85,2.76)}.items():
    s = pd.read_csv(SC/f"{m}_scorecard.csv"); s = s[(s.window=="development")&(s.h==3)&s.mape.notna()]
    s = s[s.model.isin(NAMES)].sort_values("mape", ascending=False)
    wt = pd.read_csv(SC/f"{m}_weights.csv"); w3 = wt[wt.h==3].iloc[0]
    nm = s[s.model=="naive"].mape.iloc[0]
    f = fig(w,h); ax = f.add_subplot(111)
    cols = [ACG if r=="gated_equal_weight" else (INK if r=="naive" else (GREY if w3.get(r,0)==0 else HOLD)) for r in s.model]
    ax.barh(range(len(s)), s.mape, color=cols, height=.66)
    ax.axvline(nm, color=INK, lw=.9, ls=(0,(3,2))); ax.text(nm, len(s)-.3, " naïve", fontsize=6.3, color=INK, va="bottom")
    ax.set_yticks(range(len(s))); ax.set_yticklabels([NAMES[r] for r in s.model], fontsize=6.6)
    for i,(v,sk,r) in enumerate(zip(s.mape,s.skill_pct,s.model)):
        wtxt = "" if r in ("naive","gated_equal_weight") else (f"  ·  weight {w3.get(r,0):.0f}%" if w3.get(r,0)>0 else "  ·  gated out")
        ax.text(max(v, nm)+(max(s.mape)-min(s.mape))*.03, i, f"{v:.2f}%  ({sk:+.1f}%){wtxt}", va="center", fontsize=6, color=INK2)
    ax.set_xlim(min(s.mape)*.9, max(s.mape)*1.32); ax.xaxis.set_major_formatter(FuncFormatter(lambda v,_: f"{v:.0f}%"))
    clean(ax); ax.grid(axis="y", visible=False); ax.set_xlabel("MAPE at 3 months, 78 origins (lower is better)", fontsize=6.5)
    f.subplots_adjust(left=.22,right=.98,top=.97,bottom=.15); save(f,f"s7_ladder_{m}.png")

# ---- S8 heatmap PVC
e = pd.read_csv(SC/"pvc_error_corr_h3.csv", index_col=0); lab=[NAMES[c].replace(" (global)","\n(global)").replace(" (drivers)","\n(drivers)") for c in e.columns]
f = fig(3.27,3.35); ax = f.add_subplot(111)
from matplotlib.colors import LinearSegmentedColormap
cm = LinearSegmentedColormap.from_list("acg", ["#FFFFFF","#F6C9D1",ACG])
ax.imshow(e.values, cmap=cm, vmin=.3, vmax=1)
ax.set_xticks(range(len(e))); ax.set_yticks(range(len(e))); ax.set_xticklabels(lab, rotation=90, fontsize=5.2); ax.set_yticklabels(lab, fontsize=5.2)
for i in range(len(e)):
    for j in range(len(e)):
        ax.text(j,i,f"{e.values[i,j]:.2f}",ha="center",va="center",fontsize=4.6,color="white" if e.values[i,j]>.8 else INK)
ax.grid(False); [s.set_visible(False) for s in ax.spines.values()]
f.subplots_adjust(left=.25,right=.99,top=.99,bottom=.24); save(f,"s8_errcorr_pvc.png")

# ---- S9a skill by horizon
f = fig(6.40,2.10); ax = f.add_subplot(111)
gates = [10,12,15,12,10,10]; x = np.arange(1,7)
for k,(m,c,lbl) in enumerate([("aluminium",HOLD,"Aluminium"),("pvc",ACG,"PVC proxy")]):
    s = pd.read_csv(SC/f"{m}_scorecard.csv"); s = s[(s.window=="development")&(s.model=="gated_equal_weight")].sort_values("h")
    sig = s.dm_p_one_sided < .10
    bars = ax.bar(x+(k-.5)*.36, s.skill_pct, width=.34, color=[c if q else "white" for q in sig], edgecolor=c, lw=1, label=lbl)
    for xi,v,q in zip(x+(k-.5)*.36, s.skill_pct, s.dm_p_one_sided):
        ax.text(xi, v+(.6 if v>=0 else -1.8), f"{v:+.1f}%", ha="center", fontsize=5.8, color=INK2)
ax.step(np.r_[.5,x+.5], np.r_[gates[0],gates], where="pre", color=MUTE, lw=.9, ls=(0,(3,2)), label="Round 1 skill gate")
ax.axhline(0,color=RULE,lw=.8); ax.set_xticks(x); ax.set_xticklabels([f"{h} mo" for h in x]); ax.set_ylim(-3,25)
ax.yaxis.set_major_formatter(FuncFormatter(lambda v,_: f"{v:.0f}%")); clean(ax); ax.grid(axis="x",visible=False)
ax.legend(loc="upper right", ncol=3); ax.text(.995,.70,"filled = significant (DM p < 0.10)   outline = not significant", transform=ax.transAxes, ha="right", fontsize=5.8, color=MUTE)
ax.set_ylabel("skill vs naïve", fontsize=6.5); f.subplots_adjust(left=.08,right=.99,top=.97,bottom=.13); save(f,"s9_skill_by_h.png")

# ---- S9b PVC backtest
c = pd.read_csv(SC/"pvc_combined.csv", parse_dates=["origin"]); b = c[(c.h==3)&c.y.notna()&(c.origin>="2018-01-01")].sort_values("origin")
t = b.origin + pd.DateOffset(months=3)
f = fig(5.35,2.05); ax = f.add_subplot(111)
ax.fill_between(t, b.p0*np.exp(b.lo_conf), b.p0*np.exp(b.hi_conf), color=ACG, alpha=.10, lw=0, label="80% band")
ax.plot(t, b.p0*np.exp(b.y), color=INK, lw=1.3, label="realised")
ax.plot(t, b.p0*np.exp(b.f_gated_equal_weight), color=ACG, lw=1.1, label="forecast made 3 months earlier")
ax.axvspan(pd.Timestamp("2025-04-01"), t.max(), color="#F1F1F3", zorder=0); ax.text(pd.Timestamp("2025-05-01"), ax.get_ylim()[1]*.97 if False else (b.p0*np.exp(b.hi_conf)).max()*.98, "holdout", fontsize=6, color=MUTE, va="top")
clean(ax); ax.legend(loc="upper left", ncol=3); ax.set_ylabel("index (1982=100)", fontsize=6.3)
f.subplots_adjust(left=.09,right=.99,top=.97,bottom=.11); save(f,"s9_backtest_pvc.png")

# ---- S11 coverage
for m,(w,h) in {"aluminium":(5.50,2.20),"pvc":(5.50,2.05)}.items():
    bd = pd.read_csv(SC/f"{m}_bands.csv")
    f = fig(w,h); ax = f.add_subplot(111)
    ax.axhspan(75,85,color="#EEF6F1",zorder=0); ax.text(6.55,80,"gate\n75–85%",fontsize=5.8,color=BUY,va="center")
    series = [("development","gauss","uncalibrated",GREY),("development","conf","calibrated (conformal × GARCH)",ACG)]
    if m=="pvc": series.append(("holdout","conf","calibrated, 2025–26 holdout",INK))
    n = len(series); wd = .8/n
    for k,(win,band,lbl,col) in enumerate(series):
        g = bd[(bd.window==win)&(bd.band==band)].sort_values("h")
        xs = g.h + (k-(n-1)/2)*wd
        ax.bar(xs, g.coverage_pct, width=wd*.92, color=col, label=lbl)
        for xi,v in zip(xs,g.coverage_pct): ax.text(xi, v+1, f"{v:.0f}", ha="center", fontsize=5.4, color=INK2)
    ax.set_ylim(40,102); ax.set_xticks(range(1,7)); ax.set_xticklabels([f"{h} mo" for h in range(1,7)]); ax.set_xlim(.5,7.1)
    ax.yaxis.set_major_formatter(FuncFormatter(lambda v,_: f"{v:.0f}%")); clean(ax); ax.grid(axis="x",visible=False)
    ax.legend(loc="upper left", ncol=3, fontsize=6); f.subplots_adjust(left=.08,right=.99,top=.97,bottom=.12); save(f,f"s11_cov_{m}.png")

# ---- S12 PVC cumulative replay
r = pd.read_csv(SB/"outputs/replay_signals.csv", parse_dates=["origin"]); r = r[(r.material=="pvc")&(r.window=="development")].sort_values("origin")
cum = []
for i in range(1,len(r)+1):
    px = r.exec_px.values[:i]
    base = simulate([COVER["BUY NORMAL"]]*i, px, px[-1]); sb = simulate([COVER[s] for s in r.signal.values[:i]], px, px[-1])
    cum.append(100*(1-sb["cost_per_unit"]/base["cost_per_unit"]))
f = fig(5.65,2.75); ax = f.add_subplot(211); ax2 = f.add_subplot(212, sharex=ax)
ax.fill_between(r.origin, 0, cum, color=BUY, alpha=.12, lw=0); ax.plot(r.origin, cum, color=BUY, lw=1.4)
ax.axhline(0,color=RULE,lw=.8); ax.yaxis.set_major_formatter(FuncFormatter(lambda v,_: f"{v:+.1f}%")); clean(ax)
ax.set_ylabel("cumulative net\nsaving", fontsize=6.2); ax.text(r.origin.iloc[-1], cum[-1], f" {cum[-1]:+.2f}%", fontsize=6.5, color=BUY, va="center")
ax2.plot(r.origin, r.exec_px, color=INK, lw=1)
for sg,col in [("BUY NOW",BUY),("DEFER",DEFER)]:
    k = r.signal==sg; ax2.scatter(r.origin[k], r.exec_px[k], s=14, color=col, zorder=3, label=sg.title())
clean(ax2); ax2.set_ylabel("PVC proxy\n(purchase price)", fontsize=6.2); ax2.legend(loc="upper left", ncol=2)
plt.setp(ax.get_xticklabels(), visible=False); f.subplots_adjust(left=.14,right=.92,top=.97,bottom=.09,hspace=.12); save(f,"s12_replay_pvc.png")

# ---- S13 live forecast fans
D = json.loads((SB/"dashboard/data.json").read_text())
f = fig(5.75,4.31); axs = f.subplots(2,1)
for ax,m in zip(axs,["aluminium","pvc"]):
    s = D["materials"][m]["series"]; L = s["labels"]; xi = np.arange(len(L))
    p10 = np.array([np.nan if v is None else v for v in s["p10"]]); p90 = np.array([np.nan if v is None else v for v in s["p90"]])
    ax.fill_between(xi, p10, p90, color=ACG, alpha=.12, lw=0)
    ax.plot(xi, [np.nan if v is None else v for v in s["actual"]], color=INK, lw=1.3, label="actual")
    ax.plot(xi, [np.nan if v is None else v for v in s["p50"]], color=ACG, lw=1.4, ls=(0,(4,2)), label="forecast P50 (80% band)")
    ax.plot(xi, [np.nan if v is None else v for v in s["naive"]], color=MUTE, lw=.9, ls=(0,(1,2)), label="naïve")
    mm = D["materials"][m]; h3 = mm["horizons"]["3"]
    nm = "LME aluminium, US$/t" if m=="aluminium" else "PVC proxy, US PPI resins (index)"
    ax.set_title(f"{nm}  ·  as of {mm['origin']}  ·  3-month signal: {h3['signal']}, P(up) {h3['p_up']:.0f}%", loc="left", fontsize=6.6)
    ax.set_xticks(xi[::6]); ax.set_xticklabels(L[::6]); clean(ax); ax.legend(loc="upper center" if m=="aluminium" else "upper left", ncol=3, fontsize=5.8)
    if m=="aluminium": ax.yaxis.set_major_formatter(FuncFormatter(lambda v,_: f"${v:,.0f}"))
f.subplots_adjust(left=.1,right=.99,top=.95,bottom=.06,hspace=.32); save(f,"s13_live_forecast.png")
