"""Domain models: Instrument, EquityBar, OptionBar. Stdlib only."""
from __future__ import annotations
from dataclasses import dataclass, field, asdict
from typing import Any, Dict, Optional


@dataclass
class Instrument:
    instrument_id: str
    symbol: str
    exchange: str = "NSE"
    asset_type: str = "EQUITY"  # EQUITY | OPTION | FUTURE | INDEX
    underlying: str = ""
    lot_size: int = 1
    expiry: str = ""
    strike: float = 0.0
    right: str = ""  # CE | PE | ""
    active_from: str = ""
    active_to: str = ""
    meta: Dict[str, Any] = field(default_factory=dict)

    def to_row(self) -> tuple:
        import json
        return (self.instrument_id, self.symbol, self.exchange, self.asset_type,
                self.underlying, self.lot_size, self.expiry, self.strike,
                self.right, self.active_from, self.active_to, json.dumps(self.meta))

    @staticmethod
    def equity(symbol: str, exchange: str = "NSE") -> "Instrument":
        return Instrument(instrument_id=f"{exchange}:{symbol}", symbol=symbol, exchange=exchange)


@dataclass
class EquityBar:
    instrument_id: str
    ts: str  # ISO sortable
    timeframe: str
    open: float
    high: float
    low: float
    close: float
    volume: float
    source: str = "synthetic"

    def to_row(self) -> tuple:
        return (self.instrument_id, self.ts, self.timeframe, self.open, self.high,
                self.low, self.close, self.volume, self.source)


@dataclass
class OptionBar:
    instrument_id: str
    ts: str
    timeframe: str
    underlying: str = ""
    expiry: str = ""
    strike: float = 0.0
    right: str = ""
    ltp: float = 0.0
    bid: float = 0.0
    ask: float = 0.0
    volume: float = 0.0
    oi: float = 0.0
    oi_change: float = 0.0
    iv: float = 0.0
    delta: float = 0.0
    gamma: float = 0.0
    theta: float = 0.0
    vega: float = 0.0
    source: str = "live"

    def to_row(self) -> tuple:
        return (self.instrument_id, self.ts, self.timeframe, self.underlying,
                self.expiry, self.strike, self.right, self.ltp, self.bid, self.ask,
                self.volume, self.oi, self.oi_change, self.iv, self.delta,
                self.gamma, self.theta, self.vega, self.source)


def asdict_any(o: Any) -> Dict[str, Any]:
    return asdict(o)
