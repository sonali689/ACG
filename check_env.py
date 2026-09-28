"""Pre-flight check. Run from ACG/smartbuy:  python check_env.py

Verifies you are in the right folder, on a supported Python, with the packages
and input files the pipeline needs. Reports everything wrong at once rather
than failing on the first problem.
"""
import importlib
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
ok = True


def check(label, passed, hint=""):
    global ok
    print(f"  [{'OK ' if passed else 'XX '}] {label}" + ("" if passed else f"\n         -> {hint}"))
    ok = ok and passed


print(f"\nSmart Buy pre-flight\n  folder: {HERE}\n  python: {sys.version.split()[0]}\n")

print("Python version")
check("3.9 to 3.12", (3, 9) <= sys.version_info[:2] <= (3, 12),
      "LightGBM wheels lag on 3.13. Install 3.11 or 3.12 and rebuild the venv.")

print("\nVirtual environment")
check("running inside a venv", sys.prefix != sys.base_prefix,
      "Activate it:  .venv\\Scripts\\Activate.ps1  (Windows)  /  source .venv/bin/activate")

print("\nFolder layout")
for p in ["src/validation", "src/decision", "src/deck", "dashboard", "outputs/scorecards"]:
    check(p, (HERE / p).is_dir(),
          "You are in the wrong folder. Open the one that CONTAINS src/, not ACG/.")

print("\nPackages")
for mod, pkg in [("pandas", "pandas"), ("numpy", "numpy"), ("scipy", "scipy"),
                 ("matplotlib", "matplotlib"), ("pptx", "python-pptx"),
                 ("sklearn", "scikit-learn"), ("statsmodels", "statsmodels"),
                 ("lightgbm", "lightgbm"), ("yaml", "PyYAML")]:
    try:
        importlib.import_module(mod)
        check(pkg, True)
    except ImportError:
        check(pkg, False, f"pip install -r requirements.txt   (missing: {pkg})")

print("\nScripts in place")
for p in ["src/validation/leakfree_all_horizons.py", "src/decision/replay_leakfree.py",
          "src/deck/make_charts_acg.py", "src/deck/build_deck_round1_style.py",
          "dashboard/build_data.py", "dashboard/build_dashboard.py",
          "dashboard/_template.html", "dashboard/vendor/chart.umd.js"]:
    check(p, (HERE / p).exists(), "Copy it from the smartbuy_src bundle.")

print("\nInput data")
for m in ["aluminium", "pvc"]:
    f = f"outputs/scorecards/{m}_walk_forward_predictions.csv"
    check(f, (HERE / f).exists(),
          "Run src/validation/walk_forward.py first, or restore it from the zip.")

print("\nDeck fonts (optional, affects appearance only)")
try:
    from matplotlib import font_manager
    fams = {f.name for f in font_manager.fontManager.ttflist}
    for f in ["Poppins", "IBM Plex Sans"]:
        print(f"  [{'OK ' if f in fams else '-- '}] {f}"
              + ("" if f in fams else "   fonts.google.com — install, then restart PowerPoint"))
except Exception:
    print("  [-- ] could not read font list")

print("\n" + ("All checks passed. Run:  make   (or the six commands in SETUP.md)"
              if ok else "Fix the XX lines above, then re-run this script."))
sys.exit(0 if ok else 1)
