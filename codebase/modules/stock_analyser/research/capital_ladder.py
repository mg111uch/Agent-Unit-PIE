"""Capital-ladder probe: costs punish small capital; drag scales with notional.

A candidate with positive gross edge but negative net at research capital
may clear costs at a higher rung (bps drag dilutes, DP flat dilutes). For
REJECTs killed by costs on one leg (NEG_IS/NEG_OOS with gross>0), estimate
breakeven from the realistic-drag line and confirm with ONE backtest at the
suggested rung (same signals/leg). Verdict stays REJECT; suggestion lands
in meta for the report. Ladder from capital.yaml: research_min/max_capital
stepped by scale_step.
"""
from __future__ import annotations
from typing import Any, Dict, List


def ladder(cfg: Dict[str, Any] | None = None) -> List[int]:
    cfg = cfg or {}
    lo = int(cfg.get("research_min_capital", 25000))
    hi = int(cfg.get("research_max_capital", 100000))
    step = int(cfg.get("scale_step", 25000) or 25000)
    return list(range(lo, hi + 1, step)) or [lo]


def estimate_breakeven(net_profit: float, total_costs: float, n: int, c0: float,
                       frac: float, cfg: Dict[str, Any] | None,
                       steps: List[int]) -> int | None:
    """Cheapest rung where scaled gross beats realistic drag. Gross scales
    with capital (returns fixed, notionals scale); drag dilutes (bps part
    linear, DP flat fixed). None when gross<=0, already profitable, or
    beyond cap. Confirmation backtest settles the boundary."""
    from ..backtest.costs import realistic_breakdown as _real
    gross = (net_profit or 0) + (total_costs or 0)
    if gross <= 0 or not n or (net_profit or 0) > 0:
        return None  # unfixable by capital, or already profitable: no suggestion
    for s in steps:
        if s <= c0:
            continue
        drag = _real(frac * s, cfg)["total"]
        if gross * s / c0 - drag * n > 0:
            return s
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
    frac = float(strategy_d.get("position_frac")
                 or (strategy_d.get("meta") or {}).get("position_frac", 0.2) or 0.2)
    c_star = estimate_breakeven(m.get("net_profit") or 0, m.get("total_costs") or 0,
                                n, start_cash, frac, cfg, ladder(cfg))
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
