# Smart Buy v2 - full pipeline. `make` rebuilds every number from data/raw.
PY = PYTHONPATH=. python
.PHONY: all test backtest score dashboard chronos clean

all:
	python run_all.py

test:                      ## leakage tests must pass before anything is scored
	$(PY) tests/test_leakage.py

backtest:                  ## ~20 min on a laptop CPU (N-BEATS is most of it)
	$(PY) -m src.sb.backtest local
	$(PY) -m src.sb.backtest global
	$(PY) -m src.sb.backtest nbeats

score:
	$(PY) -m src.sb.drivers
	$(PY) -m src.sb.combine
	$(PY) -m src.sb.replay
	$(PY) -m src.sb.forecast_now

dashboard:
	$(PY) dashboard/build_data.py
	$(PY) dashboard/build_dashboard.py

chronos:                   ## optional, needs torch + internet: then `make score dashboard`
	$(PY) -m src.sb.chronos_local

clean:
	rm -rf outputs/predictions outputs/scorecards outputs/drivers outputs/*.json outputs/*.csv dashboard/data.json dashboard/index*.html
