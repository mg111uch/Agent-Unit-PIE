"""Phase 2 debate hook: opportunity -> argu_god-ready claim + attacks.

Read-only against argu_god: imports nothing from it, returns plain dicts
shaped like argu_god nodes ({name, side, premise, confidence}).
"""
from __future__ import annotations
from typing import Any, Dict, List, Optional
from . import ledger


def _premise(o: Dict[str, Any]) -> str:
    return (f"Opportunity '{o['problem']}' for {o['customer']}: price "
            f"{o['price']}, cost {o['cost']} (margin {o['margin']:.0%}), "
            f"startup {o['startup_cost']}, revenue in {o.get('time_to_revenue') or '?'}.")


def challenge(opp_id: str, db_path: Optional[str] = None) -> Dict[str, Any]:
    """Pull opportunity from ledger; return {topic, claim, counters, questions}."""
    o = ledger.get_opportunity(opp_id, db_path)
    if not o:
        raise ValueError(f"unknown opportunity '{opp_id}'")
    claim = {"name": f"Opp: {o['problem']} for {o['customer']}",
             "side": "pro", "premise": _premise(o),
             "confidence": round(0.3 + 0.5 * float(o.get("moonshot_relevance", 0)), 2)}
    tmpl = [("customer", f"Customer '{o['customer']}' will not pay {o['price']}: "
                         "no evidence of budget, urgency, or buying intent."),
            ("rival", f"A rival already serves '{o['problem']}' cheaper or better; "
                      "no stated moat or differentiation."),
            ("cost", f"Unit economics fail: cost {o['cost']} + startup "
                     f"{o['startup_cost']} erase margin {o['margin']:.0%} at scale."),
            ("failure-mode", f"What kills this: revenue slips past "
                             f"'{o.get('time_to_revenue') or '?'}' while startup "
                             "capital burns with zero return.")]
    counters = [{"name": f"Attack ({k}): {o['problem']}", "side": "con",
                 "premise": p, "confidence": 0.6} for k, p in tmpl]
    questions: List[str] = [
        f"Who exactly in '{o['customer']}' pays, and why now?",
        f"Which rival is closest, and what is our edge on cost or speed?",
        f"At what volume does margin {o['margin']:.0%} survive startup {o['startup_cost']}?",
        "What single event kills this, and what is the early warning sign?"]
    return {"topic": f"econ_opp_{opp_id}", "opportunity_id": opp_id,
            "claim": claim, "counters": counters, "questions": questions}
