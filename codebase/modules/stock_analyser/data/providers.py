"""Providers: Historical/CSV/synthetic + Upstox live stub. Stdlib only."""
from __future__ import annotations
import csv
import random
from pathlib import Path
from typing import Dict, List, Any
from .models import EquityBar, Instrument
from .store import upsert_equity_bars, upsert_instruments, upsert_option_bars


def synthetic_bars(symbol: str, n: int = 120, start: int = 0, seed: int = 7,
                   timeframe: str = "1D", exchange: str = "NSE") -> List[EquityBar]:
    rng = random.Random(seed + hash(symbol) % 1000)
    px, out = 100.0 + rng.random() * 50, []
    iid = f"{exchange}:{symbol}"
    for i in range(n):
        drift = rng.gauss(0.0008, 0.018)
        o = px
        c = max(1.0, o * (1 + drift))
        h = max(o, c) * (1 + abs(rng.gauss(0, 0.004)))
        lo = min(o, c) * (1 - abs(rng.gauss(0, 0.004)))
        v = int(1e5 * (1 + abs(rng.gauss(0, 1))) * (1.6 if abs(drift) > 0.025 else 1.0))
        ts = f"{start + i:010d}"
        out.append(EquityBar(iid, ts, timeframe, round(o, 2), round(h, 2),
                             round(lo, 2), round(c, 2), float(v)))
        px = c
    return out


class SyntheticProvider:
    name = "synthetic"

    def fetch(self, symbols: List[str], n: int = 120, timeframe: str = "1D",
              seed: int = 7, db_path: str | None = None, persist: bool = False) -> Dict[str, List[Dict[str, Any]]]:
        data: Dict[str, List[Dict[str, Any]]] = {}
        for s in symbols:
            bars = synthetic_bars(s, n=n, seed=seed, timeframe=timeframe)
            if persist:
                upsert_instruments([Instrument.equity(s).to_row()], db_path)
                upsert_equity_bars([b.to_row() for b in bars], db_path)
            data[s] = [b.__dict__ for b in bars]
        return data


class CsvProvider:
    """CSV columns: symbol,ts,open,high,low,close,volume[,timeframe]."""
    name = "csv"

    def ingest(self, path: str, db_path: str | None = None) -> int:
        rows, seen = [], set()
        with open(path, newline="") as f:
            for r in csv.DictReader(f):
                sym = r["symbol"].strip()
                tf = r.get("timeframe", "1D").strip() or "1D"
                iid = f"NSE:{sym}"
                if sym not in seen:
                    upsert_instruments([Instrument.equity(sym).to_row()], db_path)
                    seen.add(sym)
                rows.append((iid, r["ts"], tf, float(r["open"]), float(r["high"]),
                             float(r["low"]), float(r["close"]), float(r["volume"]), "csv"))
        return upsert_equity_bars(rows, db_path)


class UpstoxStub:
    """Live adapter stub: normalize -> validate -> upsert. Restart-safe (INSERT OR IGNORE)."""
    name = "upstox"

    REQUIRED_EQ = ("instrument_id", "ts", "open", "high", "low", "close")

    def normalize_equity(self, raw: Dict[str, Any], timeframe: str = "15m",
                           source: str = "upstox") -> tuple | None:
        try:
            for k in self.REQUIRED_EQ:
                if k not in raw:
                    return None
            o, h, lo, c = (float(raw["open"]), float(raw["high"]),
                            float(raw["low"]), float(raw["close"]))
            if not (h >= max(o, c) and lo <= min(o, c) and o > 0 and c > 0):
                return None
            o, h, lo, c = round(o, 2), round(h, 2), round(lo, 2), round(c, 2)  # paise
            return (str(raw["instrument_id"]), str(raw["ts"]), timeframe, o, h, lo, c,
                    float(raw.get("volume", 0)), raw.get("source", source))
        except (ValueError, TypeError):
            return None

    def record(self, raws: List[Dict[str, Any]], timeframe: str = "15m",
               db_path: str | None = None, source: str = "upstox") -> int:
        rows = [r for r in (self.normalize_equity(x, timeframe, source) for x in raws) if r]
        if not rows:
            return 0
        return upsert_equity_bars(rows, db_path)

    def record_options(self, raws: List[Dict[str, Any]], timeframe: str = "15m",
                       db_path: str | None = None, source: str = "upstox") -> int:
        rows = []
        for r in raws:
            try:
                if "instrument_id" not in r or "ts" not in r:
                    continue
                rows.append((r["instrument_id"], r["ts"], timeframe, r.get("underlying", ""),
                             r.get("expiry", ""), float(r.get("strike", 0)), r.get("right", ""),
                             round(float(r.get("ltp", 0)), 2), round(float(r.get("bid", 0)), 2),
                             round(float(r.get("ask", 0)), 2),
                             float(r.get("volume", 0)), float(r.get("oi", 0)),
                             float(r.get("oi_change", 0)), round(float(r.get("iv", 0)), 2),
                             float(r.get("delta", 0)), float(r.get("gamma", 0)),
                             float(r.get("theta", 0)), float(r.get("vega", 0)),
                             r.get("source", source)))
            except (ValueError, TypeError):
                continue
        return upsert_option_bars(rows, db_path) if rows else 0
