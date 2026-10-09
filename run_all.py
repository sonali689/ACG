"""Run the whole Smart Buy pipeline, in order, on any OS (no `make` needed).

    python run_all.py                    # everything: tests, backtest (~20-30 min), scoring, dashboard, decks
    python run_all.py --skip-backtest    # reuse outputs/predictions (minutes): scoring, dashboard, decks
    python run_all.py --decks-only       # rebuild charts and both decks from existing outputs
"""
import subprocess
import sys
import time
from pathlib import Path

ROOT = Path(__file__).resolve().parent
PY = sys.executable
args = set(sys.argv[1:])

STEPS = [
    ("Leakage tests",                     ["tests/test_leakage.py"]),
    ("Backtest: statistical + local",     ["-m", "src.sb.backtest", "local"]),
    ("Backtest: global LightGBM",         ["-m", "src.sb.backtest", "global"]),
    ("Backtest: N-BEATS",                 ["-m", "src.sb.backtest", "nbeats"]),
    ("Driver study",                      ["-m", "src.sb.drivers"]),
    ("Scoring and ensembles",             ["-m", "src.sb.combine"]),
    ("Buying replay",                     ["-m", "src.sb.replay"]),
    ("Live forecast",                     ["-m", "src.sb.forecast_now"]),
    ("Dashboard data",                    ["dashboard/build_data.py"]),
    ("Dashboard HTML",                    ["dashboard/build_dashboard.py"]),
    ("Deck charts",                       ["src/deck/charts.py"]),
    ("Deck v2 (15 slides)",               ["src/deck/edit_deck.py"]),
    ("Deck restructure",                  ["src/deck/restructure.py"]),
    ("Finals deck (10 + appendix)",       ["src/deck/edit_finals.py"]),
    ("Numbers to check in the deck",      ["src/deck/deck_numbers.py"]),
]
if "--skip-backtest" in args:
    STEPS = [s for s in STEPS if not s[0].startswith("Backtest")]
if "--decks-only" in args:
    STEPS = STEPS[-5:]

env = {**__import__("os").environ, "PYTHONPATH": str(ROOT), "PYTHONIOENCODING": "utf-8"}
(ROOT / "outputs" / "deck").mkdir(parents=True, exist_ok=True)
for name, cmd in STEPS:
    t = time.time()
    print(f"\n=== {name} ===", flush=True)
    r = subprocess.run([PY, *cmd], cwd=ROOT, env=env)
    if r.returncode != 0:
        sys.exit(f"\nSTOPPED: '{name}' failed (exit {r.returncode}). Nothing after it was run.")
    print(f"--- done in {time.time() - t:.0f}s", flush=True)
print("\nALL DONE. Finals deck: outputs/SmartBuy_Finals_Deck.pptx  |  Dashboard: dashboard/index_offline.html")
