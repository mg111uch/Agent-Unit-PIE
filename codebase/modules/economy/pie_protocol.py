"""PIE gateway protocol, in-repo half (IN-4): byte-compatible builders.

Key lists mirror FireFlow `backend/pie/commands.js` exactly. Builders emit
proposal envelopes; parsers validate receipts strictly; receipts convert to
kernel event dicts via the event_adapter pattern (no external calls).
"""
from __future__ import annotations

import uuid
from typing import Any, Dict

PROPOSAL_KEYS = ("proposal_id", "objective", "action", "budget_paise",
                 "risk", "required_capabilities", "expected_outcome",
                 "authorization")
RECEIPT_KEYS = ("proposal_id", "execution_id", "status",
                "actual_cost_paise", "evidence", "result", "economic_delta")
RISKS = ("low", "medium", "high")
RECEIPT_STATUS = ("succeeded", "failed", "partial")


def build_proposal(objective: str, action: str, budget_paise: float,
                   risk: str = "low",
                   required_capabilities: list | None = None,
                   expected_outcome: Dict[str, Any] | None = None,
                   proposal_id: str = "",
                   authorization: str = "agent") -> Dict[str, Any]:
    if risk not in RISKS:
        raise ValueError(f"risk must be one of {RISKS}")
    return {
        "proposal_id": proposal_id or f"prop_{uuid.uuid4().hex[:8]}",
        "objective": objective,
        "action": action,
        "budget_paise": float(budget_paise),
        "risk": risk,
        "required_capabilities": list(required_capabilities or []),
        "expected_outcome": dict(expected_outcome or {}),
        "authorization": authorization,
    }


def parse_receipt(raw: Dict[str, Any]) -> Dict[str, Any]:
    missing = [k for k in RECEIPT_KEYS if raw.get(k) is None]
    if missing:
        raise ValueError(f"receipt missing {missing}")
    if raw["status"] not in RECEIPT_STATUS:
        raise ValueError(f"status must be one of {RECEIPT_STATUS}")
    return {k: raw[k] for k in RECEIPT_KEYS}


def receipt_to_kernel_event(receipt: Dict[str, Any]) -> Dict[str, Any]:
    """Receipt -> kernel event dict (event_adapter pattern)."""
    r = parse_receipt(receipt)
    delta = r["economic_delta"] if isinstance(r["economic_delta"], dict) else {}
    return {
        "event_type": "pie_execution",
        "category": "economic",
        "title": f"pie execution {r['execution_id']} {r['status']}",
        "description": f"proposal {r['proposal_id']} -> {r['status']}",
        "source_unit_id": "fireflow_pie",
        "source_type": "fireflow_shaped",
        "confidence": 0.9,
        "importance": 0.6,
        "tags": ["pie_execution", r["status"]],
        "metadata": {
            "proposal_id": r["proposal_id"],
            "execution_id": r["execution_id"],
            "actual_cost_paise": r["actual_cost_paise"],
            "economic_delta": delta,
        },
    }
