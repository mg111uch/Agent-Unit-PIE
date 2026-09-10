"""Sector/market-relative context for ML panel. Trailing-only, no peek.

Benchmarks live in market.db as index bars (NIFTY + 6 sectorals from the
daily backfill). bench_map() precomputes trailing returns per date so
symbol_frame() can emit stock-minus-benchmark features causally.
Missing data -> {} and callers fall back to 0.0 (synthetic/tests safe).
"""
from __future__ import annotations
from typing import Dict, List

MARKET_SYMBOL = "NIFTY"
SECTOR_SYMBOLS = ("NIFTY_AUTO", "NIFTY_IT", "NIFTY_PHARMA",
                  "NIFTY_FMCG", "NIFTY_METAL", "NIFTY_ENERGY")


def _closes(symbol: str, timeframe: str, db_path: str | None) -> Dict[str, float]:
    try:
        from ..data.store import query_equity
        out = {}
        for b in query_equity(f"NSE:{symbol}", timeframe, db_path=db_path):
            if b.get("close"):
                out[b["ts"]] = float(b["close"])
        return out
    except Exception:
        return {}


def _rets(closes: Dict[str, float]) -> Dict[str, Dict[int, float]]:
    ds = sorted(closes)
    per: Dict[str, Dict[int, float]] = {}
    for i, d in enumerate(ds):
        r = {}
        for n in (5, 20, 60):
            if i >= n and closes[ds[i - n]]:
                r[n] = closes[d] / closes[ds[i - n]] - 1
        per[d] = r
    return per


def bench_map(db_path: str | None = None, timeframe: str = "1D") -> Dict[str, dict]:
    """ts -> {mkt_5, mkt_20, sec_20, sec_disp_20}. Empty when no index bars."""
    mkt = _rets(_closes(MARKET_SYMBOL, timeframe, db_path))
    secs = [_rets(_closes(s, timeframe, db_path)) for s in SECTOR_SYMBOLS]
    out: Dict[str, dict] = {}
    for ts, mr in mkt.items():
        sr = [s.get(ts, {}) for s in secs]
        s20 = [r.get(20, 0.0) for r in sr if 20 in r]
        if 20 not in mr or not s20:
            continue
        out[ts] = {"mkt_5": mr.get(5, 0.0), "mkt_20": mr[20],
                   "sec_20": sum(s20) / len(s20),
                   "sec_disp_20": max(s20) - min(s20)}
    return out
