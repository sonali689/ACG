# How to run Smart Buy and reproduce the submitted results

## 1. One-time setup

You need **Python 3.12** (3.10–3.12 work; 3.12.3 was used). Open a terminal in the `smartbuy` folder.

**Windows (PowerShell)**
```powershell
py -3.12 -m venv .venv
.venv\Scripts\Activate.ps1          # if blocked: Set-ExecutionPolicy -Scope CurrentUser RemoteSigned
python -m pip install --upgrade pip
pip install -r requirements-lock.txt
python check_env.py                 # every line should say OK, last line: READY
```

**Mac / Linux**
```bash
python3.12 -m venv .venv
source .venv/bin/activate
pip install --upgrade pip
pip install -r requirements-lock.txt
python check_env.py
```

`requirements-lock.txt` pins the exact versions that produced the submitted numbers. `requirements.txt`
allows newer versions; results may then differ slightly in the last decimal (mostly N-BEATS).

## 2. Reproduce everything (same commands on every OS)

```
python run_all.py
```

Runs, in order: leakage tests → backtest (statistical, global LightGBM, N-BEATS; about 20–30 min on a
laptop) → driver study → scoring → buying replay → live forecast → dashboard → deck charts → decks →
a check of every number written into the slides. It stops at the first failing step.

Faster options:

| Command | What it does | Time |
|---|---|---|
| `python run_all.py --skip-backtest` | reuses `outputs/predictions/`, redoes everything after it | ~1 min |
| `python run_all.py --decks-only` | rebuilds charts and both decks from existing outputs | ~10 s |
| `python tests/test_leakage.py` | the leakage tests alone | ~10 s |

## Exactly the same numbers?

| Step | Re-run from scratch gives |
|---|---|
| Statistical models, ElasticNet, local and global LightGBM | identical (checked: 0.0 difference) |
| N-BEATS (neural network) | identical on the same processor type (checked: two independent re-runs, 0.0 difference); may differ slightly on a different CPU |
| Everything with `--skip-backtest` | identical to the submitted deck (checked slide by slide) |

The submitted predictions are in `outputs/predictions/`, so `--skip-backtest` reproduces the submission exactly.
On a different kind of processor, retrained N-BEATS forecasts can round differently, which moves some ensemble
numbers in the first decimal (an earlier run on another machine gave PVC 1-month skill +20.7% instead of +21.4%).
The deck builder rewrites every such number from the new outputs automatically, and the last step confirms the
deck matches.

## 3. What you get

| File | What it is |
|---|---|
| `outputs/SmartBuy_Finals_Deck.pptx` | finals deck: 14 slides + appendix A1–A3, set in Open Sans (fonts in `assets/fonts`) |
| `outputs/deck/SmartBuy_Round2_15Slides_v2.pptx` | corrected 15-slide Round 2 deck |
| `dashboard/index_offline.html` | decision dashboard (no internet needed) |
| `outputs/scorecards/*_scorecard.csv` | accuracy vs naïve, every model and horizon |
| `outputs/replay_summary.json` | buying replay, permutation test |
| `outputs/forecast_now.json` | the live forecast and buyer note |
| `outputs/drivers/` | lead–lag study and hypothesis verdicts |

## 4. Checking the numbers on the slides

The last step prints a table: each number written into slide text, its current value from the outputs, and
**OK** or **UPDATE**. Without new data every line says OK. Run it alone with `python src/deck/deck_numbers.py`.

## 5. Refreshing the data (changes the results)

The data in `data/raw` is frozen so results reproduce exactly. To forecast from today, replace the files:
World Bank Pink Sheet monthly prices → `data/raw/wb_cmo_monthly.xlsx`; the FRED series listed in
`check_env.py` via `https://fred.stlouisfed.org/graph/fredgraph.csv?id=<SERIES>` → `data/raw/fred_<series>.csv`;
ECB, GPR, EPU and OECD files likewise. Then run `python run_all.py` and fix every line marked UPDATE.

## 6. Optional: Chronos foundation model

`pip install -r requirements-chronos.txt`, then `python -m src.sb.chronos_local`, then
`python run_all.py --skip-backtest`. Not run during development; check it works first.
