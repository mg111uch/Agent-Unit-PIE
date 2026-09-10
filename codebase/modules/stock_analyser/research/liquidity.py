"""Liquidity & capacity gate (stdlib): before PAPER_READY.

Per symbol: ADV20 (mean shares/day), spread proxy (mean daily range/close),
position estimate from start_cash * position_frac at last close, participation
= est_shares / ADV. REJECT when participation >= threshold, ADV below minimum,
or price below minimum — a backtest that buys an untradable quantity is not
a strategy. Thresholds via capital.yaml `liq_*` keys; lenient defaults.
"""
from __future__ import annotations
from typing import Any, Dict, List


def symbol_liquidity(bl: List[Dict], notional: float,
                     cfg: Dict[str, Any] | None = None) -> Dict[str, Any]:
    cfg = cfg or {}
    win = max(5, int(cfg.get("liq_adv_window", 20)))
    tail = bl[-win:] if len(bl) >= win else bl
    vols = [float(b.get("volume") or 0) for b in tail]
    adv = sum(vols) / len(vols) if vols else 0.0
    px = float(bl[-1].get("close") or 0)
    spreads = [(float(b.get("high") or 0) - float(b.get("low") or 0)) / px
               for b in tail if px > 0]
    spread = sum(spreads) / len(spreads) if spreads else 1.0
    shares = notional / px if px > 0 else float("inf")
    part = (shares / adv) if adv > 0 else 1.0
    return {"adv": round(adv, 1), "price": round(px, 2),
            "spread": round(spread, 4), "est_shares": round(shares, 1),
            "participation": round(part, 4)}


def tradable_filter(bars: Dict[str, List[Dict]], notional: float,
                    cfg: Dict[str, Any] | None = None) -> tuple:
    """Pre-research universe filter: drop sub-min-ADV symbols no size can trade.

    Fixes the whole-universe gate blocking every candidate; per-candidate
    participation discipline stays in gate(). Returns (kept, dropped)."""
    cfg = cfg or {}
    _min = float(cfg.get("liq_min_adv", 50000))
    drop = sorted(s for s, bl in bars.items()
                  if symbol_liquidity(bl, notional, cfg)["adv"] < _min)
    return {s: bl for s, bl in bars.items() if s not in drop}, drop


def gate(bars: Dict[str, List[Dict]], position_frac: float, start_cash: float,
         cfg: Dict[str, Any] | None = None) -> Dict[str, Any]:
    max_part = float(cfg.get("liq_max_participation", 0.05))
    min_adv = float(cfg.get("liq_min_adv", 50000))
    min_px = float(cfg.get("liq_min_price", 10.0))
    max_spread = float(cfg.get("liq_max_spread", 0.08))
    notional = float(start_cash) * float(position_frac or 0.1)
    per, bad = {}, []
    for s in sorted(bars):
        if len(bars[s]) < 10:
            bad.append((s, "short"))
            continue
        m = symbol_liquidity(bars[s], notional, cfg)
        per[s] = m
        if m["participation"] >= max_part:
            bad.append((s, f"participation {m['participation']:.1%}"))
        elif m["adv"] < min_adv:
            bad.append((s, f"ADV {m['adv']:.0f}"))
        elif m["price"] < min_px:
            bad.append((s, f"price Rs{m['price']:.0f}"))
        elif m["spread"] > max_spread:
            bad.append((s, f"spread {m['spread']:.1%}"))
    worst = max(([m["participation"] for m in per.values()] or [0.0]))
    return {"pass": not bad, "worst_participation": round(worst, 4),
            "excluded": bad, "per_symbol": per, "notional": round(notional, 2)}
