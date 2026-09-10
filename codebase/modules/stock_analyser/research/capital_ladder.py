"""Capital-ladder probe: flat Rs/trade punishes small capital linearly.

A candidate with positive gross edge but negative net at research capital
may clear costs at a higher rung. For REJECTs killed by costs on one leg
(NEG_IS/NEG_OOS with gross>0), estimate breakeven from the flat-cost line
and confirm with ONE backtest at the suggested rung (same signals/leg).
Verdict stays REJECT; suggestion lands in meta for the report.
Ladder from capital.yaml: research_min/max_capital stepped by scale_step.
"""
from __future__ import annotations
from typing import Any, Dict, List


def ladder(cfg: Dict[str, Any] | None = None) -> List[int]:
    cfg = cfg or {}
    lo = int(cfg.get("research_min_capital", 25000))
    hi = int(cfg.get("research_max_capital", 100000))
    step = int(cfg.get("scale_step", 25000) or 25000)
    return list(range(lo, hi + 1, step)) or [lo]


def estimate_breakeven(net_profit: float, n: int, c0: float, flat: float,
                       steps: List[int]) -> int | None:
    """Cheapest rung where gross−flat*n > 0. None when gross<=0 or beyond cap."""
    gross = (net_profit or 0) + flat * (n or 0)
    if gross <= 0 or not n or (net_profit or 0) > 0:
        return None  # unfixable by capital, or already profitable: no suggestion
    c_star = flat * n * c0 / gross
    for s in steps:
        if s + 1e-9 >= c_star and s > c0:
            return s  # confirmation backtest settles the boundary
    return None


def suggest_and_confirm(strategy_d: Dict[str, Any], stages: Dict[str, Any],
                        bars: Dict[str, List], is_ml: bool,
                        start_cash: float, cfg: Dict[str, Any] | None = None) -> Dict[str, Any]:
    cfg = cfg or {}
    leg = {"NEG_IS": "backtest", "NEG_OOS": "locked_oos"}.get(stages.get("reason") or "")
    if not leg:
        return {}
    m = stages.get(leg) or {}
    n = int(m.get("n") or 0)
    flat = float(cfg.get("flat_cost_per_roundtrip", 60) or 60)
    c_star = estimate_breakeven(m.get("net_profit") or 0, n, start_cash, flat, ladder(cfg))
    if not c_star:
        return {}
    r = _leg_backtest(strategy_d, bars, is_ml, leg, stages, c_star)
    out = {"suggested_min_capital": c_star, "leg": leg,
           "confirm_n": r.get("n"), "confirm_avg": r.get("avg_net_per_trade"),
           "confirmed": bool((r.get("avg_net_per_trade") or 0) > 0 and (r.get("n") or 0) >= 5)}
    return out


def _leg_backtest(strategy_d: Dict[str, Any], bars: Dict[str, List], is_ml: bool,
                  leg: str, stages: Dict[str, Any], cash: float) -> Dict[str, Any]:
    if is_ml:
        from ..ml.strategies import ml_signals, ml_exits
        from ..backtest.engine import run_backtest
        b = stages.get("bounds") or {}
        if leg == "backtest":
            sub = {s: [x for x in bl if x["ts"] <= b.get("val_end", "")] for s, bl in bars.items()}
            live = b.get("val_start", "")
        else:
            sub, live = bars, (stages.get("locked_oos") or {}).get("from", "")
        return run_backtest(ml_exits(strategy_d), {s: v for s, v in sub.items() if v},
                            start_cash=cash, min_bars=0,
                            signals=ml_signals(strategy_d, {s: v for s, v in sub.items() if v},
                                               live_from=live))
    from ..backtest.engine import run_backtest
    from ..strategies.model import strategy_from_dict
    cut = stages.get("cut") or (stages.get("seal") or {}).get("cut", "")
    sub = {s: [x for x in bl if (x["ts"] <= cut if leg == "backtest" else x["ts"] > cut)]
           for s, bl in bars.items()}
    return run_backtest(strategy_from_dict(strategy_d),
                        {s: v for s, v in sub.items() if v}, start_cash=cash, min_bars=0)
