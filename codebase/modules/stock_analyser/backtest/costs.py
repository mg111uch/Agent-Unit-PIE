"""Cost model: flat Rs per round-trip (default, from capital.yaml) or bps fallback."""
from __future__ import annotations


def roundtrip_cost(notional: float, fee_bps: float = 5.0, slippage_bps: float = 5.0) -> float:
    bps = max(0.0, fee_bps) + max(0.0, slippage_bps)
    return abs(notional) * bps / 10000.0


def trade_cost(notional: float, flat: float = 0.0, fee_bps: float = 0.0,
               slippage_bps: float = 0.0) -> float:
    """Flat Rs per round-trip when flat>0 (e.g. 60 = Rs30 each way, taxes in)."""
    if flat > 0:
        return float(flat)
    return roundtrip_cost(notional, fee_bps, slippage_bps)


def stressed_costs(fee_bps: float, slip_bps: float, mult: float = 2.0) -> tuple:
    return fee_bps * mult, slip_bps * mult
