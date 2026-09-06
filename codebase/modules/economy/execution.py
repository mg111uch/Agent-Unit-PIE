"""Phase 5 execution_engine: action->outcome pipeline over economy modules.

run_experiment scores + challenges + stages (no money, no sim).
record_outcome_tx approves (human gate), posts the profit/loss delta vs
the staged estimate, and optionally mirrors to a twin timeline.
No sim runs, no kernel imports, no new tables (transactions status +
desc memos only).
"""
from __future__ import annotations
from typing import Any, Dict, Optional
from . import capital
from . import challenge as _CH
from . import ledger
from . import scoring as _SC
from . import twin_bridge as _TB


def run_experiment(opp_id: str, actor_caps: Any = None,
                   db_path: Optional[str] = None) -> Dict[str, Any]:
    """Score + challenge + stage startup_cost. Moves no money, runs no sim."""
    opp = ledger.get_opportunity(opp_id, db_path)
    if not opp:
        raise ValueError(f"unknown opportunity '{opp_id}'")
    s = _SC.score_opportunity(opp, actor_caps or {})
    ch = _CH.challenge(opp_id, db_path)
    actor = (dict(actor_caps or {}).get("actor_id", None)
             if isinstance(actor_caps, dict) else None) or capital.EXT
    staged = capital.propose_action(f"experiment:{opp_id}",
                                    float(opp.get("startup_cost", 0) or 0),
                                    actor, db_path)
    return {"opp_id": opp_id, "score": s["score"], "breakdown": s["breakdown"],
            "verdict": s["verdict"], "challenge": ch,
            "staged_tx": staged["tx_id"]}


def record_outcome_tx(tx_id: str, actual_revenue: float, actual_cost: float,
                      human_approved: bool = False, twin: Any = None,
                      branch_row: Optional[Dict[str, Any]] = None,
                      db_path: Optional[str] = None) -> Dict[str, Any]:
    """Approve staged tx (gate), post delta vs staged estimate, mirror to twin.

    Booked on approve: -staged. Actual net: revenue-cost.
    Delta = actual net + staged (0 -> no adjustment tx)."""
    row = capital.approve_action(tx_id, human_approved, db_path)
    actor = row.get("sender", capital.EXT)
    staged = float(row.get("amount", 0) or 0)
    rev, cost = round(float(actual_revenue), 2), round(float(actual_cost), 2)
    profit = round(rev - cost, 2)
    delta = round(profit + staged, 2)
    adj = None
    if delta > 0:
        adj = capital.earn(delta, actor, f"outcome:{tx_id} rev/cost vs estimate", db_path)
    elif delta < 0:
        adj = capital.spend(-delta, actor, f"outcome:{tx_id} rev/cost vs estimate", db_path)
    updated = False
    if twin is not None:
        brow = branch_row or {"name": f"experiment:{tx_id}", "welfare": profit,
                              "pass": profit >= 0, "fiscal": cost, "society": {}}
        _TB.record_outcome(twin, brow, f"outcome of {tx_id}")
        updated = True
    return {"profit": profit, "adjustment_tx": adj,
            "ledger_balance": capital.balance(actor, db_path),
            "twin_updated": updated}


def close_experiment(db_path: Optional[str] = None) -> Dict[str, Any]:
    """Queue check: how many staged proposals are still open."""
    return {"open_count": len(capital.list_proposed(db_path))}
