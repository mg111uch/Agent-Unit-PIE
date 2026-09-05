"""Multi-objective ResearchScore (stdlib): robust value, not max Sharpe.

score = economic + stability + robustness - drawdown - complexity - overfit
All terms bounded; weights overridable via capital.yaml (score_* keys).
"""
from __future__ import annotations
import math
from typing import Any, Dict


def _clamp(x: float, lo: float = -1.0, hi: float = 1.0) -> float:
    return max(lo, min(hi, x))


def complexity_of(strategy_d: Dict[str, Any]) -> int:
    from .alpha_screen import expr_nodes
    fam = (strategy_d.get("meta", {}) or {}).get("family", "sym")
    if fam == "ml":
        m = strategy_d.get("meta", {}) or {}
        return len(m.get("features", [])) + int(m.get("max_depth", 3))
    n = expr_nodes(strategy_d.get("entry", {}))
    return n + len(strategy_d.get("features", {}))


def score(strategy_d: Dict[str, Any], stages: Dict[str, Any],
          cfg: Dict[str, Any] | None = None) -> Dict[str, Any]:
    cfg = cfg or {}
    w_eco = float(cfg.get("score_w_eco", 1.0))
    w_stab = float(cfg.get("score_w_stab", 1.0))
    w_rob = float(cfg.get("score_w_rob", 1.0))
    w_dd = float(cfg.get("score_w_dd", 1.0))
    w_cx = float(cfg.get("score_w_cx", 0.02))
    w_of = float(cfg.get("score_w_of", 0.5))
    bt, oos = stages.get("backtest") or {}, stages.get("locked_oos") or {}
    pert = stages.get("perturbation") or {}
    wf = stages.get("walk_forward") or {}
    stress = stages.get("cost_stress") or {}
    oos_net = float(oos.get("avg_net_per_trade") or 0)
    base_net = float(bt.get("avg_net_per_trade") or 0)
    # economic: per-trade edge scaled, capped; needs both train+oos positive
    eco = _clamp(oos_net / 100.0) + 0.5 * _clamp(base_net / 100.0)
    if oos_net <= 0 or base_net <= 0:
        eco -= 1.0
    # stability: perturbation share positive + walk-forward share positive
    pavgs = pert.get("avg_nets") or []
    wavgs = wf.get("avg_nets") or []
    pfrac = sum(1 for x in pavgs if (x or 0) > 0) / len(pavgs) if pavgs else 0.0
    wfrac = sum(1 for x in wavgs if (x or 0) > 0) / len(wavgs) if wavgs else 0.0
    stab = 0.5 * pfrac + 0.5 * wfrac
    # robustness: existing 0..1 + stress survival bonus
    rob = float(stages.get("robustness") or 0)
    if (stress.get("avg_net_per_trade") or 0) > 0:
        rob += 0.25
    # trade sufficiency with diminishing returns (log), penalty when thin
    n = int(oos.get("n") or 0) + int(bt.get("n") or 0)
    suff = math.log1p(max(0, n)) / math.log1p(200)
    if n < 25:
        suff -= 0.5
    # drawdown penalty from OOS leg
    dd = abs(float(oos.get("max_dd") or 0))
    # overfit gap: train far above OOS suggests curve-fit
    gap = max(0.0, _clamp(base_net / 100.0) - _clamp(oos_net / 100.0))
    cx = complexity_of(strategy_d)
    # realistic-cost drag: honest roundtrip vs the flat charged in-sim
    drag = float(((stages.get("realistic_costs") or {}).get("per_trade_drag")) or 0)
    total = (w_eco * (eco + suff) + w_stab * stab + w_rob * min(1.25, rob)
             - w_dd * dd * 2 - w_cx * cx - w_of * gap - w_eco * _clamp(drag / 100.0))
    bd = {"eco": round(eco + suff, 3), "stab": round(stab, 3),
          "rob": round(min(1.25, rob), 3), "dd": round(dd, 4),
          "cx": cx, "gap": round(gap, 3), "n": n, "drag": round(drag, 2)}
    return {"score": round(total, 3), "breakdown": bd}
