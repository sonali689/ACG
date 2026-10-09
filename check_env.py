"""Pre-flight check for Smart Buy v2: python version, packages, raw data files."""
import importlib, sys
from pathlib import Path

ok = True
print(f"Python {sys.version.split()[0]}", "OK" if sys.version_info >= (3, 10) else "-> need 3.10+")
for pkg in ["pandas", "numpy", "scipy", "sklearn", "statsmodels", "lightgbm", "arch", "jax", "optax",
            "openpyxl", "xlrd", "yaml"]:
    try:
        m = importlib.import_module(pkg)
        print(f"  {pkg:12s} {getattr(m, '__version__', '')}")
    except ImportError:
        ok = False
        print(f"  {pkg:12s} MISSING  (pip install -r requirements.txt)")
raw = Path(__file__).parent / "data" / "raw"
need = ["wb_cmo_monthly.xlsx", "ecb_inr_eur.csv", "ecb_usd_eur.csv", "data_gpr_export.xls",
        "Global_Policy_Uncertainty_Data.xlsx", "oecd_china_cli.csv", "fred_wpu066.csv",
        "fred_wpu0613.csv", "fred_wpu102501.csv", "fred_ipg3252n.csv", "fred_ipg3313n.csv",
        "fred_indpro.csv", "fred_tsifrght.csv"]
for f in need:
    e = (raw / f).exists()
    ok &= e
    print(f"  data/raw/{f:38s} {'OK' if e else 'MISSING'}")
print("\nREADY: run `make`" if ok else "\nFix the items above first.")
