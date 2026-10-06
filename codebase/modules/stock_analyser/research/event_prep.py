"""Event data hygiene: the three places event studies on Indian data usually go wrong.

1. adj_price_wide(): raw bhavcopy CLOSE is not adjusted for splits/bonuses.  The same file's PREV_CLOSE on an ex-date
   is the exchange's adjusted base price, so chaining close/prev_close gives an adjusted return series that is
   continuous across corporate actions and across suspension gaps (the next print is relative to the last traded
   price).  VERIFY on a few known splits/bonuses in your data before trusting it (see artifact_days()).
2. event_date_from_disclosure(): the date information became tradable = the exchange disclosure timestamp, not the
   trade date; after-close or non-trading-day timestamps roll to the next session.  (Insider/PIT filings can be
   disclosed up to ~2 trading days after the trade.)
3. net_bulk_deals(): a bulk-deal row is one leg; the same client buying and selling the same day is an intraday
   round trip, not a view.  Net by (symbol, date, client) and keep only directional clients.
"""
from __future__ import annotations

import numpy as np
import pandas as pd


def adj_price_wide(bhav: pd.DataFrame, artifact_thresh: float = 0.35) -> pd.DataFrame:
    b = bhav.dropna(subset=["close", "prev_close"]).sort_values(["symbol", "date"]).copy()
    b = b[(b["close"] > 0) & (b["prev_close"] > 0)]
    b["ret"] = b["close"] / b["prev_close"] - 1.0
    # VERIFIED 10/04 on bhav_copy.db: PREV_CLOSE is NOT rebased on ex-dates
    # (209 clean 1:2/3/4/5/10 splits + ~400 more action-like days out of 622
    # |ret|>35% flags). Chaining raw would fabricate -50..-90% "returns", so the
    # action day contributes 0 and windows spanning it read ex-action returns.
    bad = b["ret"].abs() > artifact_thresh
    b["px"] = b.groupby("symbol")["ret"].transform(
        lambda s: 100.0 * (1.0 + s.mask(s.abs() > artifact_thresh).fillna(0.0)).cumprod())
    b.loc[bad, "px"] = np.nan
    return b.pivot(index="date", columns="symbol", values="px").sort_index().ffill()


def artifact_days(bhav: pd.DataFrame, thresh: float = 0.35) -> pd.DataFrame:
    """Days where |close/prev_close-1| is huge even after exchange adjustment -> inspect (illiquid relistings,
    unadjusted actions, circuit-limit-free listings).  Drop or review these before an event study."""
    r = (bhav["close"] / bhav["prev_close"] - 1.0).abs()
    return bhav.loc[r > thresh, ["symbol", "date", "close", "prev_close"]].assign(abs_ret=r[r > thresh])


def event_date_from_disclosure(ts: pd.Series, trading_days: pd.DatetimeIndex, cutoff: str = "15:30") -> pd.Series:
    ts = pd.to_datetime(ts)
    td = pd.DatetimeIndex(trading_days).sort_values()
    day = ts.dt.normalize()
    after = ts.dt.strftime("%H:%M") > cutoff
    day = day.where(~after, day + pd.Timedelta(days=1))
    pos = td.searchsorted(day.values, side="left")
    pos = np.minimum(pos, len(td) - 1)
    return pd.Series(td[pos], index=ts.index)


def net_bulk_deals(deals: pd.DataFrame, min_directional: float = 0.5) -> pd.DataFrame:
    """deals: ['symbol','date','client','side' in BUY/SELL,'qty'] -> events ['symbol','date','side','net_qty','client']"""
    d = deals.copy()
    d["sq"] = np.where(d["side"].str.upper().str.startswith("B"), 1.0, -1.0) * d["qty"]
    g = d.groupby(["symbol", "date", "client"]).agg(net_qty=("sq", "sum"), gross=("qty", "sum")).reset_index()
    g = g[(g["net_qty"].abs() / g["gross"]) >= min_directional]
    g["side"] = np.sign(g["net_qty"]).astype(int)
    return g[["symbol", "date", "side", "net_qty", "client"]]
