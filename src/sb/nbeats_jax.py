"""
N-BEATS, interpretable configuration (Oreshkin, Carpov, Chapados & Bengio, ICLR 2020),
implemented in JAX so it runs on a laptop CPU without PyTorch.

Architecture (N-BEATS-I):
  * Trend stack: 3 blocks sharing weights. Each block maps the input window
    through 4 fully-connected ReLU layers to polynomial coefficients
    (degree 2), then projects them onto a polynomial basis for both the
    backcast (reconstructing the input) and the forecast.
  * Seasonality stack: 3 blocks sharing weights, same idea with a Fourier
    basis at annual harmonics.
  * Doubly residual: each block removes what it explained from the input
    (x <- x - backcast) and adds its forecast to the running total.

Trained GLOBALLY on windows from ~74 commodity series (see panel.py) because
a single 180-point series is far too short for any neural network.

Input  : last L=24 monthly log prices, minus the last one (so the input ends at 0)
Output : log-returns for h = 1..6 (direct, all horizons at once)
Loss   : mean absolute error
"""
from __future__ import annotations

import numpy as np
import jax
import jax.numpy as jnp
import optax

L, HZ = 24, 6
HIDDEN, LAYERS, BLOCKS = 128, 4, 3
POLY_DEG, HARMONICS = 2, 3


def _bases():
    tb = (np.arange(L) - (L - 1)) / HZ          # backcast time, ending at 0
    tf = np.arange(1, HZ + 1) / HZ              # forecast time
    trend_b = np.stack([tb ** p for p in range(POLY_DEG + 1)])
    trend_f = np.stack([tf ** p for p in range(POLY_DEG + 1)])
    mb = np.arange(L) - (L - 1)
    mf = np.arange(1, HZ + 1)
    sb, sf = [np.ones(L)], [np.ones(HZ)]
    for k in range(1, HARMONICS + 1):
        for fn in (np.cos, np.sin):
            sb.append(fn(2 * np.pi * k * mb / 12))
            sf.append(fn(2 * np.pi * k * mf / 12))
    return (jnp.array(trend_b), jnp.array(trend_f),
            jnp.array(np.stack(sb)), jnp.array(np.stack(sf)))


TB, TF, SB, SF = _bases()


def _init_block(key, n_theta):
    keys = jax.random.split(key, LAYERS + 2)
    p, d_in = {}, L
    for i in range(LAYERS):
        scale = np.sqrt(2.0 / d_in)
        p[f"W{i}"] = jax.random.normal(keys[i], (d_in, HIDDEN)) * scale
        p[f"b{i}"] = jnp.zeros(HIDDEN)
        d_in = HIDDEN
    p["Wb"] = jax.random.normal(keys[-2], (HIDDEN, n_theta)) * 0.01
    p["Wf"] = jax.random.normal(keys[-1], (HIDDEN, n_theta)) * 0.01
    return p


def init_params(seed: int):
    k1, k2 = jax.random.split(jax.random.PRNGKey(seed))
    return {"trend": _init_block(k1, TB.shape[0]), "season": _init_block(k2, SB.shape[0])}


def _block(p, x, Bb, Bf):
    h = x
    for i in range(LAYERS):
        h = jax.nn.relu(h @ p[f"W{i}"] + p[f"b{i}"])
    return (h @ p["Wb"]) @ Bb, (h @ p["Wf"]) @ Bf


def forward(params, x):
    fc = jnp.zeros((x.shape[0], HZ))
    for _ in range(BLOCKS):
        b, f = _block(params["trend"], x, TB, TF)
        x, fc = x - b, fc + f
    for _ in range(BLOCKS):
        b, f = _block(params["season"], x, SB, SF)
        x, fc = x - b, fc + f
    return fc


def _loss(params, x, y):
    return jnp.mean(jnp.abs(forward(params, x) - y))


def make_windows(series_list, cutoffs):
    """series_list: list of 1-D log-price arrays.
    cutoffs: index of the last month whose value may appear as a forecast END.
    Returns X, Y and, for each window, how many months before the cutoff it ends
    (used to carve out the validation slice)."""
    X, Y, age = [], [], []
    for lp, last_ok in zip(series_list, cutoffs):
        for e in range(L + HZ - 1, last_ok + 1):      # e = index of last forecast month
            w = lp[e - HZ - L + 1: e + 1]
            if np.isnan(w).any():
                continue
            anchor = w[L - 1]
            X.append(w[:L] - anchor)
            Y.append(w[L:] - anchor)
            age.append(last_ok - e)
    return np.asarray(X, np.float32), np.asarray(Y, np.float32), np.asarray(age)


def fit(X, Y, age=None, seed=0, max_steps=1500, eval_every=50, val_months=12, patience=400,
        batch=1024, lr=1e-3):
    """Adam on MAE with EARLY STOPPING: windows ending in the last `val_months`
    before the cutoff are held out; training stops at the step with the best
    validation MAE. Validation windows are older than the forecast origin,
    so this is in-fold tuning, not peeking."""
    if age is not None:
        va = age < val_months
        Xv, Yv = jnp.asarray(X[va]), jnp.asarray(Y[va])
        X, Y = X[~va], Y[~va]
    params = init_params(seed)
    opt = optax.chain(optax.clip_by_global_norm(1.0), optax.adam(lr))
    state = opt.init(params)

    @jax.jit
    def step(params, state, xb, yb):
        loss, g = jax.value_and_grad(_loss)(params, xb, yb)
        upd, state = opt.update(g, state, params)
        return optax.apply_updates(params, upd), state, loss

    rng = np.random.default_rng(seed)
    Xj, Yj = jnp.asarray(X), jnp.asarray(Y)
    n = len(X)
    best, best_loss, best_i = params, np.inf, 0
    for i in range(1, max_steps + 1):
        idx = rng.integers(0, n, size=min(batch, n))
        params, state, _ = step(params, state, Xj[idx], Yj[idx])
        if age is not None and i % eval_every == 0:
            vl = float(_loss_j(params, Xv, Yv))
            if vl < best_loss:
                best, best_loss, best_i = params, vl, i
            elif i - best_i >= patience:          # no improvement for `patience` steps
                break
    return best if age is not None else params


_fwd = jax.jit(forward)
_loss_j = jax.jit(_loss)


def predict(params_list, x_window):
    """x_window: last L log prices. Returns median over the seed ensemble of h=1..6 log-returns."""
    x = (x_window - x_window[-1])[None, :].astype(np.float32)
    preds = np.stack([np.asarray(_fwd(p, jnp.asarray(x)))[0] for p in params_list])
    return np.median(preds, axis=0)
