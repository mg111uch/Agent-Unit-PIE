"""Live recorder: NSE chain/quote -> normalize -> market.db. Stdlib only.

Restart-safe (INSERT OR IGNORE), dup-safe (shared snapshot ts), market-hours
guard (IST Mon-Fri 09:15-15:30). Reuses UpstoxStub.record_options/equity path.
"""
from __future__ import annotations
import json
import time
import urllib.request
from datetime import datetime, timedelta, timezone
from typing import Any, Dict, List
from .nse_session import NseSession, UA
from .providers import UpstoxStub

IST = timezone(timedelta(hours=5, minutes=30))
INDEX_SYMBOLS = ("NIFTY", "BANKNIFTY")
YAHOO_MAP = {"NIFTY": "^NSEI", "BANKNIFTY": "^NSEBANK"}


def market_open(now: datetime | None = None) -> bool:
    t = (now or datetime.now(IST)).astimezone(IST)
    if t.weekday() > 4:
        return False
    mins = t.hour * 60 + t.minute
    return 9 * 60 + 15 <= mins <= 15 * 60 + 30


def snapshot_ts() -> str:
    return datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M")


def chain_to_option_rows(doc: Dict[str, Any], ts: str) -> List[Dict[str, Any]]:
    """NSE chain JSON -> UpstoxStub option dicts (front expiry only)."""
    recs = doc.get("records", {})
    expiries = recs.get("expiryDates", [])
    if not expiries:
        return []
    front = expiries[0]
    under = recs.get("underlyingValue")
    out = []
    for row in recs.get("data", []):
        if row.get("expiryDate") != front:
            continue
        strike = row.get("strikePrice")
        for right in ("CE", "PE"):
            leg = row.get(right) or {}
            if not leg:
                continue
            iid = f"NSE:{under or '?'}:{front}:{strike}:{right}"
            out.append({"instrument_id": iid, "ts": ts, "underlying": str(under or ""),
                        "expiry": front, "strike": float(strike or 0),
                        "right": right, "ltp": round(float(leg.get("lastPrice") or 0), 2),
                        "bid": round(float(leg.get("bidprice") or 0), 2),
                        "ask": round(float(leg.get("askPrice") or 0), 2),
                        "volume": float(leg.get("totalTradedVolume") or 0),
                        "oi": float(leg.get("openInterest") or 0),
                        "oi_change": float(leg.get("changeinOpenInterest") or 0),
                        "iv": round(float(leg.get("impliedVolatility") or 0), 2),
                        "delta": 0.0, "gamma": 0.0, "theta": 0.0, "vega": 0.0})
    return out


def quote_to_equity_row(symbol: str, doc: Dict[str, Any], ts: str) -> Dict[str, Any] | None:
    try:
        p = doc["priceInfo"]
        return {"instrument_id": f"NSE:{symbol}", "ts": ts,
                "open": float(p["open"]), "high": float(p["intraDayHighLow"]["max"] or p["high"]),
                "low": float(p["intraDayHighLow"]["min"] or p["low"]),
                "close": float(p["lastPrice"]), "volume": float(doc.get("preOpenMarket", {})
                .get("totalTradedVolume", 0) or 0)}
    except (KeyError, TypeError, ValueError):
        return None


def yahoo_bars(symbol: str, interval: str = "15m", rng: str = "1d",
               timeout: int = 20, adjusted: bool = False) -> List[Dict[str, Any]]:
    """Yahoo chart API (no key): NSE equity/index OHLC. No options chain.

    adjusted=True scales OHLC by adjclose/close (daily bars) so splits and
    dividends don't appear as fake jumps in backtests.
    """
    ysym = YAHOO_MAP.get(symbol, symbol if symbol.endswith(".NS") else symbol + ".NS")
    url = (f"https://query1.finance.yahoo.com/v8/finance/chart/{ysym}"
           f"?interval={interval}&range={rng}&events=div%2Csplit")
    req = urllib.request.Request(url, headers={"User-Agent": UA})
    with urllib.request.urlopen(req, timeout=timeout) as resp:
        doc = json.loads(resp.read().decode("utf-8"))
    res = (doc.get("chart", {}) or {}).get("result") or []
    if not res:
        raise ValueError(f"yahoo: no data for {symbol}")
    r0 = res[0]
    q = (r0.get("indicators", {}).get("quote") or [{}])[0]
    adj = (r0.get("indicators", {}).get("adjclose") or [{}])[0].get("adjclose") or []
    out = []
    for i, epoch in enumerate(r0.get("timestamp") or []):
        try:
            o, h, lo, c = q["open"][i], q["high"][i], q["low"][i], q["close"][i]
            if o is None or c is None:
                continue
            if adjusted and i < len(adj) and adj[i] and c:
                f = adj[i] / c  # scale whole candle, keep shape
                o, h, lo, c = o * f, (h or o) * f, (lo or o) * f, adj[i]
            ts = datetime.fromtimestamp(epoch, timezone.utc).strftime("%Y-%m-%dT%H:%M")
            o, h, lo, c = round(o, 2), round(h or o, 2), round(lo or o, 2), round(c, 2)  # paise
            out.append({"instrument_id": f"NSE:{symbol}", "ts": ts,
                        "open": float(o), "high": float(h), "low": float(lo),
                        "close": float(c), "volume": float((q.get("volume") or [0])[i] or 0)})
        except (TypeError, IndexError):
            continue
    return out


def fetch_daily_history(symbols: List[str], span: str = "1y",
                        timeframe: str = "1D", db_path: str | None = None) -> Dict[str, Any]:
    """One-time (+ nightly-refreshable) daily backfill, split-adjusted close."""
    from .providers import UpstoxStub
    stub, per, total = UpstoxStub(), {}, 0
    for s in symbols:
        try:
            bars = yahoo_bars(s, "1d", span, adjusted=True)
            for b in bars:
                b["source"] = "yahoo-adj"
            n = stub.record(bars, timeframe, db_path)
            per[s], total = len(bars), total + n
            time.sleep(2)
        except Exception as e:
            per[s] = f"error: {str(e)[:80]}"
            time.sleep(2)
    return {"span": span, "timeframe": timeframe, "new_rows": total, "per_symbol": per}


class Recorder:
    def _yahoo_range(self, symbol: str) -> str:
        """1d backfill when no recent bars, else 1h top-up (cheap at NIFTY-200 scale)."""
        try:
            from .store import max_ts
            last = max_ts(f"NSE:{symbol}", self.timeframe, self.db_path)
            if not last:
                return "1d"
            age_min = (datetime.now(timezone.utc) -
                       datetime.strptime(last, "%Y-%m-%dT%H:%M").replace(tzinfo=timezone.utc)
                       ).total_seconds() / 60
            return "1d" if age_min > 65 else "1h"
        except Exception:
            return "1d"
    def __init__(self, index_symbols=INDEX_SYMBOLS, equity_symbols=(),
                 timeframe: str = "15m", db_path: str | None = None,
                 poll_s: int = 180, min_interval: float = 20.0):
        self.index_symbols = tuple(index_symbols)
        self.equity_symbols = tuple(equity_symbols)
        self.timeframe = timeframe
        self.db_path = db_path
        self.poll_s = poll_s
        self.sess = NseSession(min_interval=min_interval)
        self.stub = UpstoxStub()

    def run_once(self) -> Dict[str, Any]:
        """One snapshot cycle. NSE first; Yahoo fallback for equities/indices."""
        ts, opts, eqs, sources = snapshot_ts(), [], [], []
        try:
            for s in self.index_symbols:
                opts += chain_to_option_rows(self.sess.chain_indices(s), ts)
            for s in self.equity_symbols:
                try:
                    r = quote_to_equity_row(s, self.sess.quote_equity(s), ts)
                    if r:
                        eqs.append(r)
                except Exception:
                    continue
            if opts or eqs:
                sources.append("nse")
        except Exception as e:
            sources.append(f"nse_fail:{str(e)[:60]}")
        if not eqs:  # Yahoo fallback (OHLC only, no options)
            iv = "15m" if self.timeframe == "15m" else "1d"
            for s in list(self.index_symbols) + list(self.equity_symbols):
                try:
                    rng = self._yahoo_range(s)
                    bars = yahoo_bars(s, iv, rng)
                    if not bars and rng != "1d":
                        bars = yahoo_bars(s, iv, "1d")  # 1h empty e.g. post-close
                    eqs += bars
                    time.sleep(2)
                except Exception:
                    continue
            if eqs:
                sources.append("yahoo")
        nse_ok = "nse" in sources
        for r in opts:
            r["source"] = "nse"
        for r in eqs:
            r.setdefault("source", "nse" if nse_ok else "yahoo")
        n_opt = self.stub.record_options(opts, self.timeframe, self.db_path) if opts else 0
        n_eq = self.stub.record(eqs, self.timeframe, self.db_path) if eqs else 0
        return {"ts": ts, "option_rows": n_opt, "equity_rows": n_eq, "sources": sources,
                "symbols": list(self.index_symbols) + list(self.equity_symbols)}

    def loop(self, max_cycles: int = 0) -> Dict[str, Any]:
        """Poll during market hours until max_cycles (0 = until close)."""
        done, cycles = [], 0
        while market_open():
            try:
                done.append(self.run_once())
            except Exception as e:
                done.append({"error": str(e)[:150]})
            cycles += 1
            if max_cycles and cycles >= max_cycles:
                break
            time.sleep(self.poll_s)
        return {"cycles": cycles, "snapshots": done}
