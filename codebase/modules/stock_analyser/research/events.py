"""Event-study harness for low-turnover information signals (insider purchases, bulk/block deals, results...).

Why event signals: with ~46bps round trip a trade must pay >~1%.  Events are sparse and, where they work, pay over
weeks -- the opposite of daily technical ML (~20bps gross per hold).

events : DataFrame ['symbol','date'] (+ optional 'side' in {+1,-1}).  `date` = day the information became PUBLIC to a
         trader (see research.event_prep.event_date_from_disclosure).  Entry is at the close `entry_lag` sessions later.
close  : wide DataFrame (index=date, columns=symbol) of ADJUSTED prices (see event_prep.adj_price_wide -- raw bhavcopy
         closes are NOT split/bonus adjusted and will fabricate -50% "events").
tradable : optional wide bool DataFrame; events whose entry cell is False (circuit lock, T2T, suspended...) are dropped.

Inference
  * excess = stock return - equal-weight universe return over the same window.
  * placebo_k>0: for every event draw k random entry dates for the SAME symbol (outside +-(h+5) of any event on it) and
    subtract their mean excess.  This removes stock-specific drift / small-cap trend / selection of persistently
    rising names -- the usual way insider-buy "alpha" is manufactured.  Report excess_vs_placebo as the headline.
  * everything is averaged within calendar month, then t-tested across months (events in one market episode are
    not independent).
"""
from __future__ import annotations

import numpy as np
import pandas as pd


def event_study(events, close, horizons=(5, 20, 40, 60), entry_lag=1, cost_bps=46.0, min_events=30,
                placebo_k=0, tradable=None, seed=0):
    close = close.sort_index()
    idx, cols = close.index, close.columns
    C = close.to_numpy(float)
    col_ix = {c: i for i, c in enumerate(cols)}
    T = None if tradable is None else tradable.reindex(index=idx, columns=cols).fillna(False).to_numpy(bool)
    ev = events.copy()
    ev["date"] = pd.to_datetime(ev["date"])
    if "side" not in ev:
        ev["side"] = 1
    ev = ev[ev["symbol"].isin(col_ix)].copy()
    ev["i0"] = idx.searchsorted(ev["date"].values, side="left") + entry_lag
    ev["j"] = ev["symbol"].map(col_ix)
    rng = np.random.default_rng(seed)
    by_sym = ev.groupby("j")["i0"].apply(np.array).to_dict()
    rows = []
    for h in horizons:
        out = []
        for r in ev.itertuples():
            i0, i1, j = r.i0, r.i0 + h, r.j
            if i1 >= len(idx) or i0 < 0:
                continue
            if T is not None and not T[i0, j]:
                continue
            p0, p1 = C[i0, j], C[i1, j]
            if not (np.isfinite(p0) and np.isfinite(p1)) or p0 <= 0:
                continue
            ex = (p1 / p0 - 1.0) - np.nanmean(C[i1] / C[i0] - 1.0)
            pl = np.nan
            if placebo_k > 0:
                bad = by_sym[j]
                pool = [k for k in rng.integers(0, len(idx) - h - 1, size=placebo_k * 6)
                        if np.all(np.abs(bad - k) > h + 5) and np.isfinite(C[k, j]) and np.isfinite(C[k + h, j]) and C[k, j] > 0][:placebo_k]
                if len(pool) >= max(1, placebo_k // 2):
                    pl = np.mean([(C[k + h, j] / C[k, j] - 1.0) - np.nanmean(C[k + h] / C[k] - 1.0) for k in pool])
            out.append((idx[i0], r.side * ex, r.side * pl if np.isfinite(pl) else np.nan))
        if len(out) < min_events:
            rows.append(dict(h=h, n=len(out)))
            continue
        x = pd.DataFrame(out, columns=["d", "ex", "pl"])
        per = x["d"].dt.to_period("M")

        def mt(s):
            m = s.groupby(per).mean().dropna()
            return (m.mean() / (m.std(ddof=1) / np.sqrt(len(m)))) if len(m) > 2 else np.nan, len(m)

        t_raw, nm = mt(x["ex"])
        row = dict(h=h, n=len(x), n_months=nm, mean_excess_bps=1e4 * x["ex"].mean(), median_excess_bps=1e4 * x["ex"].median(),
                   hit_rate=float((x["ex"] > 0).mean()), t_month_clustered=float(t_raw), net_bps=1e4 * x["ex"].mean() - cost_bps)
        if placebo_k > 0:
            d = (x["ex"] - x["pl"]).dropna()
            tp, _ = mt((x["ex"] - x["pl"]))
            row.update(placebo_bps=1e4 * x["pl"].mean(), excess_vs_placebo_bps=1e4 * d.mean(), t_vs_placebo=float(tp),
                       net_vs_placebo_bps=1e4 * d.mean() - cost_bps)
        rows.append(row)
    return pd.DataFrame(rows).set_index("h")
