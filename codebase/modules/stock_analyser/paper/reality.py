"""Paper reality check (stdlib): BACKTEST → OOS → PAPER → PAPER_REVALIDATED.

Compares live paper ledger against backtest expectation (avg net/trade,
trade rate, costs) and reports deviations. Large deviations are simulator
miscalibration feedback (slippage, fills, costs), not just a scale verdict.
"""
from __future__ import annotations
from typing import Any, Dict


def check(expected: Dict[str, Any], actual: Dict[str, Any],
          cfg: Dict[str, Any] | None = None) -> Dict[str, Any]:
    cfg = cfg or {}
    tol = float(cfg.get("paper_dev_tol", 0.5))
    exp_net = float(expected.get("avg_net_per_trade") or 0)
    act_net = float(actual.get("avg_net_per_trade") or 0)
    exp_n = int(expected.get("n") or 0)
    act_n = int(actual.get("closed") or 0)
    dev_net = ((act_net - exp_net) / abs(exp_net)) if exp_net else 0.0
    dev_rate = ((act_n - exp_n) / exp_n) if exp_n else 0.0
    exp_cost = float(expected.get("total_costs") or 0)
    act_cost = float(actual.get("total_costs") or actual.get("total_net") or 0)
    verdict = ("REVALIDATED" if abs(dev_net) <= tol and act_net > 0
               else "DEGRADED" if act_net > 0 else "REJECTED")
    return {"expected_net": round(exp_net, 2), "actual_net": round(act_net, 2),
            "dev_net": round(dev_net, 3), "expected_n": exp_n, "actual_n": act_n,
            "dev_rate": round(dev_rate, 3),
            "verdict": verdict, "tol": tol,
            "calibration_note": ("within tolerance" if verdict == "REVALIDATED"
                                 else "check slippage/fills/costs calibration")}


def check_strategy(strategy: str, expected: Dict[str, Any],
                   db_path: str | None = None) -> Dict[str, Any]:
    from .trader import report
    from ..config import load_capital
    actual = report(strategy, db_path=db_path)
    out = check(expected, {"avg_net_per_trade": actual.get("avg_net_per_trade"),
                           "closed": actual.get("closed")}, load_capital())
    out.update({"strategy": strategy, "open": actual.get("open"),
                "pending": actual.get("pending")})
    return out
