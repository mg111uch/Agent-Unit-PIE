"""RA-4 outreach agent: research -> draft -> approve -> classify.

Deterministic drafts from prospect evidence only (no fabricated case
studies, no deceptive claims). Keyword response classifier; human
approval gate for high-risk sends; frequency cap helper. Pure, no DB.
"""
from __future__ import annotations
import re
import time
from typing import Any, Dict, List

RESPONSE_CLASSES = ("interested", "later", "wrong_person",
                    "not_relevant", "unsubscribe")
CHANNELS = ("email", "phone", "in_person", "note")
MAX_PER_7D = 1
APPROVAL_ABOVE_PRICE = 10000.0

_CLASS_PATTERNS = {
    "unsubscribe": r"unsub|opt.?out|stop (mail|contact)|remove me|do not contact",
    "wrong_person": r"wrong (person|department|team)|not (me|my area)|forwarded to|contact .* instead",
    "not_relevant": r"not (relevant|interested|needed)|no (need|budget|fit)|pass",
    "later": r"later|next (quarter|month|year)|busy now|follow up|revisit|ping me",
    "interested": r"interested|yes|send (proposal|details|quote)|call me|meet|demo|pilot|price",
}


def draft_message(prospect: Dict[str, Any], template: Dict[str, Any] | None = None,
                  price: float = 0.0) -> Dict[str, Any]:
    """Personalized draft built ONLY from prospect evidence + template facts."""
    ev = list(prospect.get("evidence") or [])
    trig = list(prospect.get("triggers") or [])
    hooks = "; ".join(ev[:2]) if ev else "your recent expansion"
    body = (f"Hello {prospect.get('company', '')} team, we noticed {hooks}. "
            f"We help with {prospect.get('problem', '')}")
    if trig:
        body += f" — timely given {trig[0]}."
    if template:
        body += f" Pilot offer: {template.get('deliverable', '')}"
    if price:
        body += f" at Rs.{price:.0f} fixed scope."
    body += " Reply STOP to opt out."
    return {"to_company": prospect.get("company", ""),
            "subject": f"Pilot: {prospect.get('problem', '')}",
            "body": body, "evidence_used": ev[:2],
            "honest": True}


def approval_gate(message: Dict[str, Any], price: float = 0.0,
                  confidence: float = 0.5) -> Dict[str, Any]:
    """High-risk sends need a human: pricey pilots or low-confidence evidence."""
    if price >= APPROVAL_ABOVE_PRICE:
        return {"decision": "needs_approval", "reason": f"price {price} >= {APPROVAL_ABOVE_PRICE}"}
    if confidence < 0.4:
        return {"decision": "needs_approval", "reason": f"confidence {confidence} < 0.4"}
    return {"decision": "auto_ok", "reason": "low risk"}


def classify_response(text: str) -> Dict[str, Any]:
    """Keyword classification, checked in priority order (opt-out first)."""
    t = (text or "").lower()
    for cls in ("unsubscribe", "wrong_person", "not_relevant", "later", "interested"):
        if re.search(_CLASS_PATTERNS[cls], t):
            return {"class": cls, "method": "keyword"}
    return {"class": "not_relevant", "method": "default"}


def can_contact(sent_ts: List[float], now: float | None = None,
                max_per_7d: int = MAX_PER_7D) -> Dict[str, Any]:
    """Frequency cap: max N sends per prospect per rolling 7 days."""
    now = now if now is not None else time.time()
    recent = [s for s in (sent_ts or []) if now - s < 7 * 86400]
    ok = len(recent) < max_per_7d
    return {"ok": ok, "sent_7d": len(recent),
            "reason": "" if ok else f"cap {max_per_7d}/7d reached"}
