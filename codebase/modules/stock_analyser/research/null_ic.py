"""IC-only null + power tools (seconds, not 30-minute hierarchy runs).

1. perm_null(): shuffle the TARGET across symbols *within each date* (keeps every date's cross-section,
   the date-level market component and the score untouched) and recompute mean IC and NW-t.
   Gives the empirical threshold a real score must beat -> use as the stage-1 / alpha-gate cutoff.
2. power_ic(): "with n_sym names and n_indep independent periods, what IC can I even detect?"
   Replaces guesswork about whether a gate is too strict or the data too thin.
"""
from __future__ import annotations

import numpy as np
import pandas as pd

from .horizon_ic import newey_west_t


def _wide(df, col):
    return df.pivot(index="date", columns="symbol", values=col)


def _rowrank(a: np.ndarray) -> np.ndarray:
    return a.argsort(axis=1).argsort(axis=1).astype(float)


def _ic_rows(rs: np.ndarray, rt: np.ndarray) -> np.ndarray:
    rs = rs - rs.mean(axis=1, keepdims=True)
    rt = rt - rt.mean(axis=1, keepdims=True)
    return (rs * rt).sum(1) / np.sqrt((rs**2).sum(1) * (rt**2).sum(1))


def perm_null(scored: pd.DataFrame, lag: int = 1, n_perm: int = 1000, seed: int = 0, score="score", target="fwd", block: int = 1):
    """scored: long df ['date','symbol',score,target] (OOS scores only).  Complete-case symbols are used.

    block=1  : independent shuffle per date (valid only when target windows do not overlap, i.e. h=1).
    block=h  : ONE random symbol permutation is applied to every run of h consecutive dates, so the overlap
               autocorrelation of the h-day target (and of the IC series) survives under the null.  Without this,
               the null t-distribution is too narrow and long-horizon results look significant.  Use block=h and lag=h+entry_lag-1."""
    S, T = _wide(scored, score), _wide(scored, target)
    keep = S.columns[S.notna().all() & T.notna().all()]
    S, T = S[keep].to_numpy(), T[keep].to_numpy()
    rs, rt = _rowrank(S), _rowrank(T)
    real_ic = _ic_rows(rs, rt)
    real_mean, real_t = real_ic.mean(), newey_west_t(real_ic, lag)
    rng = np.random.default_rng(seed)
    means, ts = np.empty(n_perm), np.empty(n_perm)
    nd, nsym = rt.shape
    for b in range(n_perm):
        if block <= 1:
            rp = rng.permuted(rt, axis=1)
        else:
            rp = np.empty_like(rt)
            for a in range(0, nd, block):
                rp[a : a + block] = rt[a : a + block][:, rng.permutation(nsym)]
        ic = _ic_rows(rs, rp)
        means[b], ts[b] = ic.mean(), newey_west_t(ic, lag)
    return dict(
        n_sym=len(keep),
        n_dates=len(real_ic),
        real_ic=real_mean,
        real_t=real_t,
        p_mean=float((np.sum(means >= real_mean) + 1) / (n_perm + 1)),
        null_ic_q95=float(np.quantile(means, 0.95)),
        null_ic_q99=float(np.quantile(means, 0.99)),
        null_t_q95=float(np.nanquantile(ts, 0.95)),
        null_t_q99=float(np.nanquantile(ts, 0.99)),
    )


def power_ic(n_sym: int, n_indep: int, ics=(0.01, 0.02, 0.03, 0.05), t_thr: float = 2.0, n_sim: int = 400, seed: int = 0):
    """Detection probability of a true cross-sectional IC given breadth and independent periods."""
    rng = np.random.default_rng(seed)
    out = {}
    for ic in ics:
        hit = 0
        for _ in range(n_sim):
            z = rng.standard_normal((n_indep, n_sym))
            y = ic * z + np.sqrt(1 - ic**2) * rng.standard_normal((n_indep, n_sym))
            r = _ic_rows(_rowrank(z), _rowrank(y))
            hit += (r.mean() / (r.std(ddof=1) / np.sqrt(n_indep))) > t_thr
        out[ic] = hit / n_sim
    return pd.Series(out, name=f"power(t>{t_thr}) n_sym={n_sym}, n_indep={n_indep}")
