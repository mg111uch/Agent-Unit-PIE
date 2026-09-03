"""Strategy object — formal representation, no arbitrary Python."""
from __future__ import annotations
from dataclasses import dataclass, field, asdict
from typing import Any, Dict, List
from ..features.algebra import validate_expr

TIMEFRAMES = ("1D", "15m", "5m", "1m")


@dataclass
class Strategy:
    name: str
    universe: str = "MY_RESEARCH_UNIVERSE"
    timeframe: str = "1D"
    features: Dict[str, Any] = field(default_factory=dict)
    entry: Dict[str, Any] = field(default_factory=dict)
    stop_atr: float = 2.0
    take_atr: float = 4.0
    max_hold: int = 10
    position_frac: float = 0.1
    max_positions: int = 5
    fee_bps: float = 5.0
    slippage_bps: float = 5.0
    flat_cost: float = 0.0  # Rs per round-trip; 0 = use capital.yaml flat cost
    atr_n: int = 14
    meta: Dict[str, Any] = field(default_factory=dict)

    def validate(self) -> str | None:
        if self.timeframe not in TIMEFRAMES:
            return f"bad timeframe {self.timeframe}"
        if not self.entry:
            return "entry required"
        e = validate_expr(self.entry)
        if e:
            return f"entry: {e}"
        for k, v in self.features.items():
            e = validate_expr(v)
            if e:
                return f"feature {k}: {e}"
        if not (0 < self.position_frac <= 1):
            return "position_frac in (0,1]"
        if self.flat_cost < 0:
            return "flat_cost >= 0"
        if self.max_hold < 1 or self.atr_n < 2:
            return "bad hold/atr"
        return None

    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)


def strategy_from_dict(d: Dict[str, Any]) -> Strategy:
    s = Strategy(name=d.get("name", "unnamed"), universe=d.get("universe", "MY_RESEARCH_UNIVERSE"),
                 timeframe=d.get("timeframe", "1D"), features=d.get("features", {}),
                 entry=d.get("entry", {}), stop_atr=float(d.get("stop_atr", 2.0)),
                 take_atr=float(d.get("take_atr", 4.0)), max_hold=int(d.get("max_hold", 10)),
                 position_frac=float(d.get("position_frac", 0.1)),
                 max_positions=int(d.get("max_positions", 5)),
                 fee_bps=float(d.get("fee_bps", 5.0)),
                 slippage_bps=float(d.get("slippage_bps", 5.0)),
                 flat_cost=float(d.get("flat_cost", 0.0)),
                 atr_n=int(d.get("atr_n", 14)), meta=d.get("meta", {}))
    err = s.validate()
    if err:
        raise ValueError(err)
    return s


def default_long_volume_breakout(universe: str = "MY_RESEARCH_UNIVERSE") -> Strategy:
    # NOTE: rolling refs are lag(...,1) — comparing against a window that
    # includes the current bar can never fire (and would peek by construction).
    hi20 = {"op": "lag", "args": [
        {"op": "rolling_max", "args": [{"field": "close"}, {"const": 20}]}, {"const": 1}]}
    vol20 = {"op": "lag", "args": [
        {"op": "rolling_mean", "args": [{"field": "volume"}, {"const": 20}]}, {"const": 1}]}
    entry = {"op": "and", "args": [
        {"op": "gt", "args": [{"field": "close"}, hi20]},
        {"op": "gt", "args": [{"op": "ratio", "args": [
            {"field": "volume"}, vol20]}, {"const": 2.0}]}]}
    return strategy_from_dict({"name": "volume_breakout_pullback", "universe": universe,
                               "timeframe": "1D", "entry": entry})
