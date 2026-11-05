"""Approval inbox + risk tiers + one autonomy charter (STR-05).

Founder attention is the bottleneck, so every queued action states how much
attention it deserves:

  tier 1  notify     agent proceeds, human sees it afterwards
  tier 2  single     one human approval, 24h SLA
  tier 3  dual       two distinct humans, 4h SLA (money, refunds, first sends)

Two invariants are enforced here rather than described in a doc:
- the requester can never be the approver (separation of duties)
- tier 3 needs two *distinct* humans, so one tired click cannot move money

Pure functions over dicts; persistence stays in `ledger`/audit.
"""
from __future__ import annotations

from datetime import datetime, timedelta, timezone
from typing import Any, Dict, Iterable, List, Optional

TIERS: Dict[int, Dict[str, Any]] = {
    1: {"name": "notify", "approvers": 0, "sla_hours": 0},
    2: {"name": "single", "approvers": 1, "sla_hours": 24},
    3: {"name": "dual", "approvers": 2, "sla_hours": 4},
}

# Money above this (paise) always reaches the top tier.
LIVE_AMOUNT_PAISE = 5_000_000  # ₹50,000
REFUND_AMOUNT_PAISE = 100_000  # ₹1,000

CHARTER = {
    "may_act_alone": [
        "research.record", "prospect.score", "outreach.draft",
        "deliverable.assemble", "kernel.write",
    ],
    "needs_one_human": [
        "outreach.send.first", "deliverable.export", "contract.stage",
        "money.cap_change", "worker.payout_under_5000",
    ],
    "needs_two_humans": [
        "money.live", "money.kill_switch", "ledger.refund",
        "contract.execute", "money.payout_over_5000", "policy.change",
    ],
    "never_automatic": [
        "money.provider_credentials", "customer.data_export",
        "legal.commitment", "price.commitment",
    ],
}

# action -> tier; first match wins, so order matters.
_RULES: List[tuple] = [
    ("money.live", 3), ("money.kill_switch", 3), ("ledger.refund", 3),
    ("contract.execute", 3), ("policy.change", 3),
    ("outreach.send.repeat", 1), ("outreach.send.first", 2),
    ("deliverable.export", 2), ("contract.stage", 2),
    ("research.record", 1), ("prospect.score", 1), ("outreach.draft", 1),
    ("deliverable.assemble", 1),
]


def classify(item: Dict[str, Any]) -> Dict[str, Any]:
    """Action dict -> tier + how many humans + deadline. Unknown = tier 2."""
    action = str(item.get("action") or "")
    amount = int(item.get("amount_paise") or 0)
    for prefix, tier in _RULES:
        if action == prefix or action.startswith(prefix + "."):
            break
    else:
        tier = 3 if action in CHARTER["needs_two_humans"] else 2
    if action in CHARTER["never_automatic"]:
        tier = 3
    if amount >= LIVE_AMOUNT_PAISE:
        tier = 3
    elif action.startswith("ledger.refund") and amount >= REFUND_AMOUNT_PAISE:
        tier = 3
    spec = TIERS[tier]
    return {"tier": tier, "tier_name": spec["name"],
            "approvers_required": spec["approvers"],
            "sla_hours": spec["sla_hours"],
            "charter": "never_automatic" if action in CHARTER["never_automatic"]
                       else "tiered"}


def enqueue(item: Dict[str, Any], now: Optional[datetime] = None) -> Dict[str, Any]:
    """Add the classification + deadline to an inbox item."""
    now = now or datetime.now(timezone.utc)
    c = classify(item)
    created = item.get("created_at") or now.isoformat()
    try:
        base = datetime.fromisoformat(str(created))
        if base.tzinfo is None:
            base = base.replace(tzinfo=timezone.utc)
    except ValueError:
        base = now
    return {**item, **c, "requested_by": item.get("requested_by") or "agent",
            "status": item.get("status") or "pending",
            "created_at": created,
            "due_at": (base + timedelta(hours=c["sla_hours"])).isoformat(),
            "approvals": list(item.get("approvals") or [])}


def inbox(items: Iterable[Dict[str, Any]],
          now: Optional[datetime] = None) -> Dict[str, Any]:
    """Highest risk first, then oldest — the founder reads top-down."""
    now = now or datetime.now(timezone.utc)
    queued = [enqueue(i, now) for i in items if not i.get("status")
              or i.get("status") == "pending"]
    for i in queued:
        i["overdue"] = _overdue(i, now)
    queued.sort(key=lambda i: (-i["tier"], i["created_at"]))
    return {
        "items": queued,
        "counts": {t: sum(1 for i in queued if i["tier"] == t) for t in TIERS},
        "overdue": sum(1 for i in queued if i["overdue"]),
        "waiting_on_human": sum(1 for i in queued if i["approvers_required"] > 0),
    }


def decide(item: Dict[str, Any], actor: str, decision: str = "approve",
           reason: str = "") -> Dict[str, Any]:
    """Apply one decision. Refuses self-approval and under-signed tier 3."""
    action = str(item.get("action") or "")
    tier = int((classify(item).get("tier") if item.get("tier") is None
                else item["tier"]))
    if decision not in ("approve", "reject"):
        return {**item, "error": "decision must be approve or reject"}
    if not actor:
        return {**item, "error": "actor is required"}
    if actor == (item.get("requested_by") or "agent"):
        return {**item, "error": "requester cannot approve their own action"}
    if decision == "reject":
        return {**item, "status": "rejected", "decided_by": actor,
                "reason": reason, "approvals": item.get("approvals") or []}

    approvals = list(item.get("approvals") or [])
    if actor not in approvals:
        approvals.append(actor)
    need = TIERS[tier]["approvers"]
    if len(approvals) < need:
        return {**item, "tier": tier, "status": "pending",
                "approvals": approvals,
                "remaining": need - len(approvals),
                "reason": reason or "awaiting a second approver"}
    return {**item, "tier": tier, "status": "approved",
            "approvals": approvals, "decided_by": actor, "reason": reason}


def _overdue(item: Dict[str, Any], now: datetime) -> bool:
    try:
        due = datetime.fromisoformat(str(item["due_at"]))
    except (KeyError, ValueError):
        return False
    if due.tzinfo is None:
        due = due.replace(tzinfo=timezone.utc)
    return now > due and item.get("status") == "pending"


def charter() -> Dict[str, Any]:
    """Machine-readable autonomy contract (also dumped into docs)."""
    return {"tiers": TIERS, "charter": CHARTER,
            "live_amount_paise": LIVE_AMOUNT_PAISE,
            "refund_amount_paise": REFUND_AMOUNT_PAISE,
            "invariants": [
                "requester != approver",
                "tier 3 requires two distinct humans",
                "unknown action defaults to tier 2, never tier 1",
                "amount >= LIVE_AMOUNT_PAISE escalates to tier 3",
            ]}
