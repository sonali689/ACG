.PHONY: all clean check
all:
	python src/validation/leakfree_all_horizons.py
	python src/decision/replay_leakfree.py
	python dashboard/build_data.py
	python dashboard/build_dashboard.py
	python src/deck/make_charts_acg.py
	python src/deck/build_deck_round1_style.py

check:
	python check_env.py

clean:
	rm -rf outputs/charts_acg dashboard/data.json dashboard/index.html dashboard/index_offline.html
