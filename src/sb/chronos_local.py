"""
Chronos-Bolt (Amazon) zero-shot forecasts, plugged into the same walk-forward.

RUN THIS ON YOUR OWN MACHINE. It needs PyTorch and downloads model weights from
Hugging Face, neither of which was available where the rest of this pipeline
was built, so THIS FILE IS UNTESTED. If the chronos API has changed, check
https://github.com/amazon-science/chronos-forecasting for the current call.

    pip install chronos-forecasting torch
    python -m src.sb.chronos_local
    python -m src.sb.combine        # picks up outputs/predictions/chronos.csv automatically

Chronos sees only the price history up to each origin (no exogenous drivers),
so there is nothing for it to leak beyond the series itself. It still has to
pass the same naive gate as every other model to earn weight.

One caution to state in the deck: a foundation model's pre-training corpus may
include public commodity series that overlap the backtest period. Zero-shot
results on historical windows can therefore be optimistic; the 2025-26 holdout
is the cleaner test.
"""
from __future__ import annotations

import numpy as np
import pandas as pd

from .backtest import OUT, origins_for
from .data import CFG, visible_panel

MODEL = "amazon/chronos-bolt-small"
CONTEXT = 120


def run():
    import torch
    from chronos import BaseChronosPipeline

    pipe = BaseChronosPipeline.from_pretrained(MODEL, device_map="cpu", torch_dtype=torch.float32)
    recs = []
    for m in ("aluminium", "pvc"):
        s = visible_panel(m)[CFG["materials"][m]["target"]]
        for T in origins_for(m):
            hist = s[:T].dropna().values[-CONTEXT:]
            q, mean = pipe.predict_quantiles(context=torch.tensor(hist, dtype=torch.float32),
                                             prediction_length=6, quantile_levels=[0.1, 0.5, 0.9])
            med = q[0, :, 1].numpy()
            for j, h in enumerate(range(1, 7)):
                recs.append({"material": m, "origin": T, "h": h,
                             "f_chronos": float(np.log(med[j] / hist[-1]))})
        print(f"chronos {m}: {len(origins_for(m))} origins")
    pd.DataFrame(recs).to_csv(OUT / "chronos.csv", index=False)


if __name__ == "__main__":
    run()
