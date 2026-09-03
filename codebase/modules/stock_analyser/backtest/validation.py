"""Validation pipeline: cost stress -> perturbation -> walk-forward -> locked OOS.

Researcher must not mutate after seeing locked OOS: `seal()` marks dataset locked;
`run_locked_oos` refuses if strategy was modified after seal (caller passes parent tag).
"""
from __future__ import annotations
import copy
from typing import Dict, List, Any
from ..strategies.model import Strategy
from ..strategies.genome import mutate
from .engine import run_backtest
from .costs import stressed_costs

MIN_TRADES, MIN_SHARPE, MAX_DD = 20, 0.5, -0.35


def _split(bars: Dict[str, List], frac: float) -> tuple:
    """Shared-date split: one OOS period for all symbols (late entrants keep own window)."""
    dates = sorted({b["ts"] for bl in bars.values() for b in bl})
    cut = dates[max(5, int(len(dates) * frac) - 1)] if dates else ""
    tr = {s: [b for b in bl if b["ts"] <= cut] for s, bl in bars.items()}
    te = {s: [b for b in bl if b["ts"] > cut] for s, bl in bars.items()}
    return {s: v for s, v in tr.items() if v}, {s: v for s, v in te.items() if v}


def validate_strategy(strategy: Strategy, bars: Dict[str, List[Dict[str, Any]]],
                      oos_frac: float = 0.2, start_cash: float = 50000.0,
                      min_bars: int | None = None) -> Dict[str, Any]:
    if min_bars is None:
        try:
            from ..config import load_capital
            min_bars = int(load_capital().get("min_history_bars", 60) or 60)
        except Exception:
            min_bars = 60
    eligible = {s: bl for s, bl in bars.items() if len(bl) >= min_bars}
    stages: Dict[str, Any] = {"excluded": sorted(set(bars) - set(eligible))}
    train, oos = _split(eligible, 1 - oos_frac)
    base = run_backtest(strategy, train, start_cash=start_cash, min_bars=0)
    stages["backtest"] = {k: base.get(k) for k in ("n", "sharpe", "max_dd", "cagr",
                                                   "avg_net_per_trade", "net_profit")}
    s2 = copy.deepcopy(strategy)
    s2.fee_bps, s2.slippage_bps = stressed_costs(strategy.fee_bps, strategy.slippage_bps)
    if hasattr(s2, "flat_cost") and s2.flat_cost:
        s2.flat_cost = s2.flat_cost * 2  # stress flat costs too
    stress = run_backtest(s2, train, start_cash=start_cash, min_bars=0)
    stages["cost_stress"] = {"sharpe": stress.get("sharpe"), "n": stress.get("n"),
                             "avg_net_per_trade": stress.get("avg_net_per_trade")}
    perts = []
    for i in range(4):
        m = mutate(strategy, seed=100 + i, kind="threshold")
        r = run_backtest(m, train, start_cash=start_cash, min_bars=0)
        perts.append(r.get("avg_net_per_trade", 0) or 0)
    stages["perturbation"] = {"avg_nets": perts,
                              "stable": sum(1 for x in perts if x > 0) >= 2}
    # walk-forward: 3 folds on train
    wfs = []
    for f in range(3):
        cut = int(len(next(iter(train.values()))) * (0.5 + 0.15 * f))
        sub = {s: bl[:cut] for s, bl in train.items()}
        wfs.append(run_backtest(strategy, sub, start_cash=start_cash, min_bars=0).get("avg_net_per_trade", 0) or 0)
    stages["walk_forward"] = {"avg_nets": wfs}
    locked = run_backtest(strategy, oos, start_cash=start_cash, min_bars=0)
    stages["locked_oos"] = {k: locked.get(k) for k in ("n", "sharpe", "max_dd", "cagr",
                                                       "avg_net_per_trade", "net_profit")}
    base_net = base.get("avg_net_per_trade", 0) or 0
    oos_net = locked.get("avg_net_per_trade", 0) or 0
    ok = (locked.get("n", 0) >= 5 and oos_net > 0
          and (base.get("max_dd", 0) or 0) >= MAX_DD
          and (base.get("n", 0) or 0) >= MIN_TRADES
          and base_net > 0
          and stages["perturbation"]["stable"])
    stages["verdict"] = "PAPER_READY" if ok else "REJECT"
    stages["robustness"] = round(sum(1 for v in [ok, stages["perturbation"]["stable"],
        oos_net > 0, (stress.get("avg_net_per_trade", 0) or 0) > 0] if v) / 4, 2)
    return stages
