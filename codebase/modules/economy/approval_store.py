"""SQLite-backed approval inbox (STR-05) shared by the CLI and the UI.

Decision rules stay in `approvals` (pure functions); this module only stores
the queue and re-reads it, so the terminal and the web queue cannot drift.
"""
from __future__ import annotations

import hashlib
import json
from datetime import datetime, timezone
from typing import Any, Dict, List, Optional

from sqlite3 import Row

from modules.economy import approvals, ledger



def _connect():
    con = ledger.connect()
    con.row_factory = Row
    return con

_COLS = ("item_id", "action", "title", "payload_json", "tier", "status",
         "requested_by", "approvals_json", "amount_paise", "created_at",
         "due_at", "decided_by", "reason")


def _now() -> str:
    return datetime.now(timezone.utc).isoformat()


def _new_id(item: Dict[str, Any]) -> str:
    blob = "|".join(str(item.get(k, "")) for k in
                    ("action", "title", "requested_by", "created_at"))
    return "apv_" + hashlib.sha1(f"{blob}|{_now()}".encode()).hexdigest()[:12]


def _row(r) -> Dict[str, Any]:
    d = dict(r)
    for key in ("payload_json",):
        d[key] = json.loads(d.get(key) or "{}")
    d["approvals"] = json.loads(d.pop("approvals_json", "[]") or "[]")
    d["payload"] = d.pop("payload_json", {})
    d["item_id"] = d.get("item_id")
    return d


def save(item: Dict[str, Any]) -> Dict[str, Any]:
    """Upsert one queued action; classification is applied once."""
    queued = approvals.enqueue(item)
    item_id = item.get("item_id") or _new_id(queued)
    queued["item_id"] = item_id
    con = _connect()
    try:
        con.executescript(ledger.SCHEMA)
        con.execute(
            f"INSERT OR REPLACE INTO approvals({','.join(_COLS)}) "
            f"VALUES({','.join('?' for _ in _COLS)})",
            (item_id, queued.get("action"), queued.get("title", ""),
             json.dumps(queued.get("payload") or {}), int(queued["tier"]),
             queued.get("status", "pending"),
             queued.get("requested_by", "agent"),
             json.dumps(queued.get("approvals") or []),
             int(queued.get("amount_paise") or 0),
             queued.get("created_at", _now()), queued.get("due_at", ""),
             queued.get("decided_by", ""), queued.get("reason", "")))
        con.commit()
    finally:
        con.close()
    return queued


def get(item_id: str) -> Optional[Dict[str, Any]]:
    con = _connect()
    try:
        con.executescript(ledger.SCHEMA)
        r = con.execute("SELECT * FROM approvals WHERE item_id=?",
                        (item_id,)).fetchone()
        return _row(r) if r else None
    finally:
        con.close()


def list_items(status: Optional[str] = "pending",
               limit: int = 100) -> List[Dict[str, Any]]:
    con = _connect()
    try:
        con.executescript(ledger.SCHEMA)
        q = "SELECT * FROM approvals"
        args: tuple = ()
        if status:
            q += " WHERE status=?"
            args = (status,)
        q += " ORDER BY tier DESC, created_at ASC LIMIT ?"
        return [_row(r) for r in con.execute(q, (*args, int(limit)))]
    finally:
        con.close()


def counts() -> Dict[str, int]:
    con = _connect()
    try:
        con.executescript(ledger.SCHEMA)
        rows = con.execute(
            "SELECT status, COUNT(*) n FROM approvals GROUP BY status").fetchall()
        return {r["status"]: r["n"] for r in rows}
    finally:
        con.close()


def decide(item_id: str, actor: str, decision: str = "approve",
           reason: str = "") -> Dict[str, Any]:
    item = get(item_id)
    if not item:
        return {"error": f"unknown approval {item_id}"}
    flat = {**item, "payload": item.get("payload") or {}}
    decided = approvals.decide(flat, actor, decision, reason)
    if decided.get("error"):
        return decided
    con = _connect()
    try:
        con.executescript(ledger.SCHEMA)
        con.execute(
            "UPDATE approvals SET status=?, approvals_json=?, decided_by=?, "
            "tier=?, reason=? WHERE item_id=?",
            (decided.get("status"), json.dumps(decided.get("approvals") or []),
             decided.get("decided_by") or actor, int(decided.get("tier") or 2),
             decided.get("reason", ""), item_id))
        con.commit()
    finally:
        con.close()
    out = get(item_id) or decided
    if out.get("status") == "pending":
        out["remaining"] = max(0, int(out.get("approvers_required") or
                                       approvals.TIERS[int(out.get("tier") or 2)]["approvers"])
                               - len(out.get("approvals") or []))
    return out
