"""Live CMP: NSE quote first, Yahoo 1m fallback. Stdlib only, cached, never writes bars."""
from __future__ import annotations
import time
from datetime import datetime, timezone
from typing import Any, Dict, List

_CACHE: Dict[str, Dict[str, Any]] = {}
_TTL = 60.0


def _now() -> str:
    return datetime.now(timezone.utc).isoformat()


def _nse_cmp(symbol: str, timeout: int = 15) -> Dict[str, Any] | None:
    try:
        from .nse_session import NseSession
        doc = NseSession(min_interval=0).quote_equity(symbol)
        px = float((doc.get("priceInfo") or {}).get("lastPrice") or 0)
        if px > 0:
            return {"px": round(px, 2), "ts": _now(), "source": "nse"}
    except Exception:
        pass
    return None


def _yahoo_cmp(symbol: str) -> Dict[str, Any] | None:
    try:
        from .recorder import yahoo_bars
        bars = yahoo_bars(symbol, "1m", "1d")
        if bars:
            return {"px": round(float(bars[-1]["close"]), 2), "ts": _now(), "source": "yahoo-1m"}
    except Exception:
        pass
    return None


def get_cmp(symbol: str, max_age_s: float = _TTL) -> Dict[str, Any] | None:
    """Fresh-ish CMP or None (offline/tests). Cached 60s to respect NSE throttle."""
    hit = _CACHE.get(symbol)
    if hit and time.time() - hit.get("_t", 0) < max_age_s:
        return {k: v for k, v in hit.items() if not k.startswith("_")}
    q = _nse_cmp(symbol) or _yahoo_cmp(symbol)
    if q:
        _CACHE[symbol] = dict(q, _t=time.time())
    return q


def get_cmps(symbols: List[str]) -> Dict[str, Dict[str, Any]]:
    out = {}
    for s in symbols:
        try:
            q = get_cmp(s)
            if q:
                out[s] = q
        except Exception:
            continue
    return out


def clear_cache() -> None:
    _CACHE.clear()


LIVE_SCHEMA = """
CREATE TABLE IF NOT EXISTS live_prices(
 symbol TEXT PRIMARY KEY, px REAL, ts TEXT, source TEXT);
"""


def save_cmps(cmps: Dict[str, Dict[str, Any]], db_path: str | None = None) -> int:
    """Persist last-fetched CMPs so portfolio shows them without refetch."""
    from .store import connect
    con = connect(db_path)
    try:
        con.executescript(LIVE_SCHEMA)
        rows = [(s, float(q.get("px", 0)), str(q.get("ts", "")),
                 str(q.get("source", "?"))) for s, q in cmps.items() if q.get("px", 0) > 0]
        con.executemany("INSERT OR REPLACE INTO live_prices VALUES(?,?,?,?)", rows)
        con.commit()
        return len(rows)
    finally:
        con.close()


def load_cmps(symbols: List[str], db_path: str | None = None) -> Dict[str, Dict[str, Any]]:
    """Last persisted CMPs (no network). Empty when never fetched."""
    from .store import connect
    con = connect(db_path)
    try:
        try:
            con.execute("SELECT symbol FROM live_prices LIMIT 1")
        except Exception:
            return {}
        want = set(symbols)
        out = {}
        for sym, px, ts, src in con.execute("SELECT symbol,px,ts,source FROM live_prices"):
            if sym in want and px and px > 0:
                out[sym] = {"px": float(px), "ts": ts, "source": f"{src}+cache"}
        return out
    finally:
        con.close()
