"""Validation pipeline: cost stress -> perturbation -> walk-forward -> locked OOS.

Hard seal: `seal()` snapshots (strategy_hash, cut) before OOS; `run_locked_oos`
refuses if candidate hash != sealed hash. A strategy carrying `meta.oos_seal`
already saw OOS and is REJECTed on re-validation; `mutate()` clears it (new lineage).
"""
from __future__ import annotations
import copy
import hashlib
import json
from typing import Dict, List, Any
from ..strategies.model import Strategy
from ..strategies.genome import mutate
from .engine import run_backtest
from .costs import stressed_costs

MIN_TRADES, MIN_SHARPE, MAX_DD = 20, 0.5, -0.35


def strategy_hash(d: Dict[str, Any]) -> str:
    canon = {k: v for k, v in d.items() if k not in ("name", "meta")}
    return hashlib.sha256(json.dumps(canon, sort_keys=True).encode()).hexdigest()[:16]


def seal(strategy_d: Dict[str, Any], cut: str, oos_frac: float) -> Dict[str, Any]:
    return {"strategy_hash": strategy_hash(strategy_d), "cut": cut, "oos_frac": oos_frac}


def run_locked_oos(strategy: Strategy, oos: Dict[str, List],
                   sealed: Dict[str, Any], start_cash: float = 50000.0) -> Dict[str, Any]:
    if strategy_hash(strategy.to_dict()) != sealed.get("strategy_hash"):
        return {"error": "MUTATED_AFTER_SEAL", "verdict": "REJECT",
                "reason": "strategy mutated after seal; new lineage required"}
    r = run_backtest(strategy, oos, start_cash=start_cash, min_bars=0)
    return {k: r.get(k) for k in ("n", "sharpe", "max_dd", "cagr",
                                  "avg_net_per_trade", "net_profit")}


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
    if (strategy.meta or {}).get("oos_seal"):
        return {"verdict": "REJECT", "reason": "MUTATED_AFTER_SEAL",
                "robustness": 0.0, "seal": (strategy.meta or {})["oos_seal"]}
    if min_bars is None:
        try:
            from ..config import load_capital
            min_bars = int(load_capital().get("min_history_bars", 60) or 60)
        except Exception:
            min_bars = 60
    eligible = {s: bl for s, bl in bars.items() if len(bl) >= min_bars}
    stages: Dict[str, Any] = {"excluded": sorted(set(bars) - set(eligible))}
    train, oos = _split(eligible, 1 - oos_frac)
    dates = sorted({b["ts"] for bl in eligible.values() for b in bl})
    cut = dates[max(5, int(len(dates) * (1 - oos_frac)) - 1)] if dates else ""
    sealed = seal(strategy.to_dict(), cut, oos_frac)
    stages["seal"] = sealed
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
    try:  # honest drag report: realistic roundtrip at representative notional
        from .costs import realistic_breakdown as _real
        from ..config import load_capital as _ccap
        _cc = _ccap()
        _not = start_cash * float(getattr(strategy, "position_frac", 0.1) or 0.1)
        stages["realistic_costs"] = {"per_trade_drag": _real(_not, _cc)["total"],
                                     "notional": round(_not, 2)}
    except Exception:
        pass
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
        wcut = int(len(next(iter(train.values()))) * (0.5 + 0.15 * f))
        sub = {s: bl[:wcut] for s, bl in train.items()}
        wfs.append(run_backtest(strategy, sub, start_cash=start_cash, min_bars=0).get("avg_net_per_trade", 0) or 0)
    stages["walk_forward"] = {"avg_nets": wfs}
    locked = run_locked_oos(strategy, oos, sealed, start_cash=start_cash)
    if locked.get("error") == "MUTATED_AFTER_SEAL":
        locked["reason"] = locked.pop("error")
        stages["locked_oos"] = locked
        stages["verdict"] = "REJECT"
        stages["robustness"] = 0.0
        return stages
    stages["locked_oos"] = locked
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
    if ok:
        try:  # falsification: break it before promoting (passers only, bounded)
            from ..research.falsify import falsify_symbolic
            from ..config import load_capital as _fcap
            fal = falsify_symbolic(strategy, train, base_net, start_cash, _fcap())
            stages["falsification"] = fal
            if not fal.get("survived"):
                stages["verdict"] = "REJECT"
                stages["reason"] = "FALSIFIED"
                ok = False
        except Exception:
            pass
    if ok:
        try:  # P16 liquidity/capacity: untradable size is not a strategy
            from ..research.liquidity import gate as _liqgate
            from ..config import load_capital as _lcap
            liq = _liqgate(eligible, strategy.position_frac, start_cash, _lcap())
            stages["liquidity"] = {k: v for k, v in liq.items() if k != "per_symbol"}
            if not liq["pass"]:
                stages["verdict"] = "REJECT"
                stages["reason"] = "ILLIQUID"
                ok = False
        except Exception:
            pass
    try:
        from ..research.scoring import score as _score
        from ..config import load_capital as _cap
        stages["research_score"] = _score(strategy.to_dict(), stages, _cap())
    except Exception:
        pass
    return stages
