"""Cost model: flat Rs per round-trip (default, from capital.yaml) or bps fallback.

`realistic_breakdown` estimates true Indian-equity roundtrip drag (STT, stamp,
exchange/SEBI, slippage + square-root impact) for honest reporting; the flat
path stays the default execution cost so ledger history remains comparable.
`sized_frac` adds optional ATR vol-targeting (off when target<=0).
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


def realistic_breakdown(notional: float, cfg=None) -> dict:
    """Honest roundtrip estimate (Rs). Square-root impact; all knobs via capital.yaml."""
    cfg = cfg or {}
    n = abs(float(notional))
    stt = n * float(cfg.get("cost_stt_bps", 2.5)) / 10000.0
    stamp = n * float(cfg.get("cost_stamp_bps", 0.3)) / 10000.0
    exch = n * float(cfg.get("cost_exch_bps", 0.35)) / 10000.0
    sebi = n * float(cfg.get("cost_sebi_bps", 0.02)) / 10000.0
    slip = n * float(cfg.get("cost_slip_bps", 5.0)) / 10000.0
    impact = n * float(cfg.get("cost_impact_bps", 8.0)) / 10000.0 * (0.5 + 0.5 * (n / 1e7) ** 0.5)
    total = stt + stamp + exch + sebi + slip + impact
    return {"stt": round(stt, 2), "stamp": round(stamp, 2), "exchange": round(exch, 2),
            "sebi": round(sebi, 2), "slippage": round(slip, 2),
            "impact": round(impact, 2), "total": round(total, 2)}


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
