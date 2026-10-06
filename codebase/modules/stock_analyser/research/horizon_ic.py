"""Horizon scan: does ANY holding horizon clear costs once the model is RETRAINED for that horizon?

Why this exists
---------------
A model trained on a 5-day label and then scored against 20/60-day returns is evaluated out of
distribution; its IC at long horizons is a loading on whatever the 5d score happens to correlate with,
not a test of "is there a long-horizon edge".  Also, daily IC series built from h-day forward returns
overlap by h-1 days, so the Newey-West lag must be >= h-1 (a lag-5 t-stat at h=60 is inflated ~3x).

Interface (generic; adapt `panel` from ml/dataset.py in ~5 lines)
------------------------------------------------------------------
panel : long DataFrame with columns ['date','symbol','close', *feats]  (feats already point-in-time)
Returns one row per horizon.  Pure numpy/pandas/scipy; no sklearn needed.
"""
from __future__ import annotations

import numpy as np
import pandas as pd
from scipy.special import ndtri


# ---------------------------------------------------------------- helpers
def rank_gauss_by_date(df: pd.DataFrame, cols, by: str = "date") -> pd.DataFrame:
    """Per-date rank -> N(0,1) scores (NaN preserved)."""
    out = df.copy()
    g = out.groupby(by)
    for c in cols:
        r = g[c].rank(method="average")
        n = g[c].transform("count")
        out[c] = ndtri((r - 0.5) / n)
    return out


def newey_west_t(x, lag: int) -> float:
    """t-stat of mean(x) with Bartlett-kernel HAC variance."""
    x = np.asarray(x, float)
    x = x[~np.isnan(x)]
    n = len(x)
    if n < 10:
        return float("nan")
    lag = int(min(max(lag, 0), n - 2))
    u = x - x.mean()
    s = (u @ u) / n
    for k in range(1, lag + 1):
        w = 1.0 - k / (lag + 1.0)
        s += 2.0 * w * (u[k:] @ u[:-k]) / n
    return float(x.mean() / np.sqrt(max(s, 1e-18) / n))


def daily_rank_ic(df: pd.DataFrame, score: str, target: str) -> pd.Series:
    """Spearman IC per date (vectorised via per-date ranks)."""
    d = df[["date", score, target]].dropna()
    rs = d.groupby("date")[score].rank()
    rt = d.groupby("date")[target].rank()
    d = d.assign(_rs=rs, _rt=rt)
    g = d.groupby("date")
    cov = g.apply(lambda x: np.cov(x["_rs"], x["_rt"])[0, 1])
    sd = g["_rs"].std() * g["_rt"].std()
    return (cov / sd).dropna()


def ridge_scorer(lam: float = 100.0):
    """scorer(X_tr, y_tr, grp_tr, X_te) -> scores.  Closed-form ridge on rank-gauss inputs."""

    def f(X_tr, y_tr, grp_tr, X_te):
        X = np.nan_to_num(X_tr)
        y = np.nan_to_num(y_tr)
        A = X.T @ X + lam * len(X) / 1000.0 * np.eye(X.shape[1])
        beta = np.linalg.solve(A, X.T @ y)
        return np.nan_to_num(X_te) @ beta

    return f


# ---------------------------------------------------------------- core
def _forward_return(panel: pd.DataFrame, h: int, entry_lag: int) -> pd.Series:
    g = panel.groupby("symbol")["close"]
    return g.shift(-(h + entry_lag)) / g.shift(-entry_lag) - 1.0


def horizon_scan(
    panel: pd.DataFrame,
    feats,
    horizons=(5, 10, 20, 40, 60),
    scorer=None,
    refit_every: int = 21,
    min_train_dates: int = 252,
    entry_lag: int = 1,
    top_n: int = 5,
    top_frac: float = 0.2,
    cost_bps: float = 46.0,
    return_scored: bool = False,
):
    """Purged expanding-window scan.  For horizon h the model is trained ONLY on dates d <= t0 - (h+entry_lag)
    (label fully realised before the refit origin t0) and scores the next `refit_every` dates.

    Reports per horizon:
      ic_mean, t_nw_h (lag=h+entry_lag-1), n_indep (= n_dates/h), t_nonoverlap (every h-th date, plain t)
      long_top_n_bps / long_q_bps : mean (top bucket fwd ret - universe mean) in bps per hold
      net_top_n_bps               : long_top_n_bps - cost_bps   (cost_bps = round trip at your notional)
      be_ic                       : IC needed for net==0 at top_n (cost / (sigma_xs * z_sel)), a decision number

    CAUTION: even a horizon-matched Newey-West t is optimistic when n_indep (= n_dates/h) is below ~15
    (HAC variance is biased down in small samples; a pure-noise panel gives |t|~2 at h=60 with 8 blocks).
    Judge long horizons with return_scored=True -> research.null_ic.perm_null(block=h), not with t_nw_h alone.
    """
    scorer = scorer or ridge_scorer()
    feats = list(feats)
    panel = panel.sort_values(["symbol", "date"]).reset_index(drop=True)
    panel = rank_gauss_by_date(panel, feats)
    dates = np.sort(panel["date"].unique())
    rows, scored_by_h = [], {}
    for h in horizons:
        lag_label = h + entry_lag
        d = panel.copy()
        d["fwd"] = _forward_return(d, h, entry_lag)
        d["y"] = rank_gauss_by_date(d[["date", "fwd"]].assign(y=d["fwd"]), ["y"])["y"]
        d["score"] = np.nan
        for i0 in range(min_train_dates, len(dates) - 1, refit_every):
            t0 = dates[i0]
            tr_cut = dates[max(i0 - lag_label, 0)]
            te_dates = dates[i0 : i0 + refit_every]
            tr = d[(d["date"] <= tr_cut) & d["y"].notna()]
            te_mask = d["date"].isin(te_dates)
            if len(tr) < 1000 or not te_mask.any():
                continue
            grp = pd.factorize(tr["date"], sort=True)[0]  # chronological date codes
            d.loc[te_mask, "score"] = scorer(tr[feats].to_numpy(), tr["y"].to_numpy(), grp, d.loc[te_mask, feats].to_numpy())
        ev = d.dropna(subset=["score", "fwd"])
        if ev["date"].nunique() < 30:
            rows.append(dict(h=h, n_dates=ev["date"].nunique()))
            continue
        scored_by_h[h] = ev[["date", "symbol", "score", "fwd"]]
        ic = daily_rank_ic(ev, "score", "fwd")
        sel = ev.copy()
        sel["rk"] = sel.groupby("date")["score"].rank(ascending=False, method="first")
        sel["n"] = sel.groupby("date")["score"].transform("count")
        mu = sel.groupby("date")["fwd"].mean()
        topn = sel[sel["rk"] <= top_n].groupby("date")["fwd"].mean() - mu
        topq = sel[sel["rk"] <= sel["n"] * top_frac].groupby("date")["fwd"].mean() - mu
        sig = sel.groupby("date")["fwd"].std().mean()
        z_sel = 2.3 if top_n <= 5 else 1.9
        nl = h + entry_lag - 1
        rows.append(
            dict(
                h=h,
                n_dates=len(ic),
                n_indep=round(len(ic) / h, 1),
                ic_mean=ic.mean(),
                t_nw_h=newey_west_t(ic.values, nl),
                t_naive_lag1=newey_west_t(ic.values, 1),
                t_nonoverlap=float(ic.iloc[::h].mean() / (ic.iloc[::h].std() / np.sqrt(max(len(ic.iloc[::h]), 2)))),
                long_top_n_bps=1e4 * topn.mean(),
                t_top_n=newey_west_t(topn.values, nl),
                long_q_bps=1e4 * topq.mean(),
                net_top_n_bps=1e4 * topn.mean() - cost_bps,
                sigma_xs_bps=1e4 * sig,
                be_ic=(cost_bps / 1e4) / (sig * z_sel),
            )
        )
    out = pd.DataFrame(rows).set_index("h")
    return (out, scored_by_h) if return_scored else out
