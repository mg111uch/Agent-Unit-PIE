"""Cost model: realistic Indian-equity drag by default (STT/stamp/exchange/SEBI,
slippage + square-root impact), flat-Rs fallback via `cost_basis: flat`.

`realistic_breakdown` estimates true roundtrip drag for honest reporting;
`book_cost` is the execution path (engine + paper, same model): full round-trip
equivalent, callers halve per leg. Stress via mult (validation sets
`cost_stress_mult`, default 2x). `sized_frac` adds optional ATR vol-targeting
(off when target<=0).
"""
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


def book_cost(notional: float, flat: float = 0.0, fee_bps: float = 0.0,
               slippage_bps: float = 0.0, cfg=None, mult: float = 1.0) -> float:
    """Execution cost, full round-trip equivalent (callers halve per leg).
    `cost_basis: realistic` (default) = honest drag x mult; flat = legacy Rs."""
    cfg = cfg or {}
    if cfg.get("cost_basis", "realistic") == "realistic":
        return realistic_breakdown(notional, cfg)["total"] * float(mult or 1.0)
    return trade_cost(notional, flat, fee_bps, slippage_bps) * float(mult or 1.0)


def realistic_breakdown(notional: float, cfg=None) -> dict:
    """Honest roundtrip estimate (Rs). Delivery tariff (Zerodha/NSE 2026):
    STT 0.1% buy AND sell, stamp 0.015% buy-side, exchange ~0.00322%/side,
    SEBI Rs10/crore, DP ~Rs15.34/scrip on sell, + slippage and square-root
    impact (assumed). All knobs via capital.yaml."""
    cfg = cfg or {}
    n = abs(float(notional))
    # delivery STT is 0.1%/side, BOTH sides (20bps round-trip)
    stt = n * float(cfg.get("cost_stt_bps", 20.0)) / 10000.0
    stamp = n * float(cfg.get("cost_stamp_bps", 1.5)) / 10000.0
    exch = n * float(cfg.get("cost_exch_bps", 0.65)) / 10000.0
    sebi = n * float(cfg.get("cost_sebi_bps", 0.01)) / 10000.0
    slip = n * float(cfg.get("cost_slip_bps", 5.0)) / 10000.0
    impact = n * float(cfg.get("cost_impact_bps", 8.0)) / 10000.0 * (0.5 + 0.5 * (n / 1e7) ** 0.5)
    dp = float(cfg.get("cost_dp_flat", 15.0)) if n > 0 else 0.0
    total = stt + stamp + exch + sebi + slip + impact + dp
    return {"stt": round(stt, 2), "stamp": round(stamp, 2), "exchange": round(exch, 2),
            "sebi": round(sebi, 2), "slippage": round(slip, 2),
            "impact": round(impact, 2), "dp": round(dp, 2), "total": round(total, 2)}


def floor_qty(raw: float) -> int:
    """NSE cash equities: whole shares only — always round down, never up."""
    import math
    try:
        return max(0, int(math.floor(float(raw) + 1e-9)))
    except Exception:
        return 0


def sized_frac(base_frac: float, atr: float | None, price: float | None, cfg=None) -> float:
    """ATR vol-target: scale base_frac by target/(atr/price), clamped. Off when target<=0."""
    cfg = cfg or {}
    target = float(cfg.get("sizing_vol_target", 0) or 0)
    if target <= 0 or not atr or not price or price <= 0:
        return float(base_frac)
    vol = atr / price
    if vol <= 0:
        return float(base_frac)
    k = target / vol
    lo, hi = float(cfg.get("sizing_min_k", 0.25)), float(cfg.get("sizing_max_k", 2.0))
    return float(base_frac * max(lo, min(hi, k)))


def stressed_costs(fee_bps: float, slip_bps: float, mult: float = 2.0) -> tuple:
    return fee_bps * mult, slip_bps * mult
