"""Magic-link customer portal (REV-07): proposal -> accept -> invoice.

The token is the only credential a customer has, so only its SHA-256 hash is
stored and the raw token is returned once at creation. Payment is deliberately
NOT taken here: the first pilot uses the no-escrow path (bank/UPI invoice),
and an authenticated operator records the payment, which writes one ledger
transaction and flips the proposal to `paid`.
"""
from __future__ import annotations

import hashlib
import json
import secrets
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, Optional

from sqlite3 import Row

from modules.economy import ledger
from paths import DATA_ROOT, PIE_ROOT

PAYMENT_INSTRUCTIONS = ("Pay by bank/UPI against the invoice number. "
                        "No card or bank credentials are collected by this page.")



def _connect():
    con = ledger.connect()
    con.row_factory = Row
    return con

_COLS = ("proposal_id", "token_hash", "customer", "title", "price",
         "currency", "status", "deliverable_path", "request_json",
         "created_at", "accepted_at", "accepted_by", "invoice_id",
         "paid_at", "payment_ref")


def _now() -> str:
    return datetime.now(timezone.utc).isoformat()


def _hash(token: str) -> str:
    return hashlib.sha256(str(token).encode()).hexdigest()


def _row(r) -> Dict[str, Any]:
    d = dict(r)
    d["request"] = json.loads(d.pop("request_json", "{}") or "{}")
    d.pop("token_hash", None)
    return d


def create(customer: str, title: str, price: float,
           deliverable_path: str = "", request: Optional[Dict[str, Any]] = None,
           currency: str = "INR") -> Dict[str, Any]:
    if not customer.strip() or not title.strip():
        return {"error": "customer and title are required"}
    if float(price) <= 0:
        return {"error": "price must be positive"}
    token = secrets.token_urlsafe(24)
    pid = "prop_" + _hash(token)[:12]
    con = _connect()
    try:
        con.executescript(ledger.SCHEMA)
        con.execute(
            f"INSERT INTO proposals({','.join(_COLS)}) "
            f"VALUES({','.join('?' for _ in _COLS)})",
            (pid, _hash(token), customer, title, float(price), currency,
             "sent", deliverable_path or "", json.dumps(request or {}),
             _now(), "", "", "", "", ""))
        con.commit()
    finally:
        con.close()
    proposal = get(token) or {}
    return {"ok": True, "token": token,
            "accept_url": f"/portal/{token}", "proposal": proposal}


def get(token: str) -> Optional[Dict[str, Any]]:
    if not token:
        return None
    con = _connect()
    try:
        con.executescript(ledger.SCHEMA)
        r = con.execute("SELECT * FROM proposals WHERE token_hash=?",
                        (_hash(token),)).fetchone()
        return _row(r) if r else None
    finally:
        con.close()


def get_by_id(proposal_id: str) -> Optional[Dict[str, Any]]:
    con = _connect()
    try:
        con.executescript(ledger.SCHEMA)
        r = con.execute("SELECT * FROM proposals WHERE proposal_id=?",
                        (proposal_id,)).fetchone()
        return _row(r) if r else None
    finally:
        con.close()


def list_all(limit: int = 100) -> list:
    con = _connect()
    try:
        con.executescript(ledger.SCHEMA)
        rows = con.execute("SELECT * FROM proposals ORDER BY created_at DESC "
                           "LIMIT ?", (int(limit),)).fetchall()
        return [_row(r) for r in rows]
    finally:
        con.close()


def accept(token: str, actor: str = "customer",
           instructions: str = PAYMENT_INSTRUCTIONS) -> Dict[str, Any]:
    """Idempotent: a second accept returns the same invoice."""
    proposal = get(token)
    if not proposal:
        return {"error": "unknown or expired link"}
    if proposal["status"] in ("accepted", "paid", "delivered"):
        return {"ok": True, "already": True,
                "proposal": {**proposal, "payment_instructions": instructions}}
    if proposal["status"] != "sent":
        return {"error": f"proposal is {proposal['status']}, cannot accept"}
    invoice = proposal.get("invoice_id") or (
        "INV-" + datetime.now(timezone.utc).strftime("%Y%m%d") + "-"
        + proposal["proposal_id"].split("_")[-1])
    con = _connect()
    try:
        con.executescript(ledger.SCHEMA)
        con.execute(
            "UPDATE proposals SET status='accepted', accepted_at=?, "
            "accepted_by=?, invoice_id=? WHERE proposal_id=?",
            (_now(), actor, invoice, proposal["proposal_id"]))
        con.commit()
    finally:
        con.close()
    return {"ok": True, "already": False,
            "proposal": {**get(token), "payment_instructions": instructions}}


def mark_paid(proposal_id: str, reference: str, actor: str = "human") -> Dict[str, Any]:
    """Operator confirms an external payment; writes exactly one ledger tx."""
    proposal = get_by_id(proposal_id)
    if not proposal:
        return {"error": "unknown proposal"}
    if proposal["status"] == "paid":
        return {"ok": True, "already": True, "proposal": proposal}
    if proposal["status"] not in ("accepted", "delivered"):
        return {"error": f"proposal is {proposal['status']}; accept it first"}
    tx_id = "portal:" + proposal_id
    from modules.economy.agent_identity import Actor
    ledger.record_tx({
        "tx_id": tx_id, "from": proposal["customer"], "to": "pie",
        "amount": float(proposal["price"]), "kind": "payment",
        "ts": _now(),
    }, actor=Actor(actor_id=actor, actor_type="human"))
    con = _connect()
    try:
        con.executescript(ledger.SCHEMA)
        con.execute(
            "UPDATE proposals SET status='paid', paid_at=?, payment_ref=? "
            "WHERE proposal_id=?", (_now(), reference or tx_id, proposal_id))
        con.commit()
    finally:
        con.close()
    return {"ok": True, "already": False, "tx_id": tx_id,
            "proposal": get_by_id(proposal_id)}


def _allowed_roots() -> list:
    return [(DATA_ROOT / "deliverables").resolve(),
            (PIE_ROOT / "deliverables").resolve()]


def deliverable(token: str) -> Optional[Path]:
    """Resolve a deliverable inside an allowed root; None if missing/unsafe."""
    proposal = get(token)
    if not proposal or not proposal.get("deliverable_path"):
        return None
    p = Path(proposal["deliverable_path"]).expanduser()
    if not p.is_absolute():
        p = PIE_ROOT / p
    try:
        p = p.resolve()
    except OSError:
        return None
    if not any(p == root or root in p.parents for root in _allowed_roots()):
        return None
    return p if p.is_file() else None
