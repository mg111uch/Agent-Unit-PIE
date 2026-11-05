"""PIE inbox: durable, idempotent consumer for FireFlow outbox events.

FireFlow writes each economic event to its `outbox` table and serves it at
`GET /api/pie/events` (at-least-once, acked with `POST /api/pie/events/ack`).
This module owns the PIE side of that contract (INT-01):

    pull(fetcher) -> stage rows in ff_inbox -> apply() -> kernel_bus

Guarantees
- Delivery is at-least-once; dedup is on the FireFlow event id (PRIMARY KEY).
- Application is idempotent twice over: the ff_inbox state and a kernel
  marker (`external_events/<event_id>`), so replaying an applied event
  publishes nothing and returns `already_applied`.
- Failures are counted; after MAX_ATTEMPTS the row is dead-lettered and can
  be retried explicitly. Nothing here raises into the caller's loop.

Pure stdlib + existing modules. No network: the fetcher is injected.
"""
from __future__ import annotations

import json
import sqlite3
from datetime import datetime, timezone
from typing import Any, Callable, Dict, List, Optional

from modules.economy import ledger

MAX_ATTEMPTS = 3
MARKER_TYPE = "external_events"

SCHEMA = """
CREATE TABLE IF NOT EXISTS ff_inbox(
  event_id TEXT PRIMARY KEY,
  event_type TEXT,
  payload_json TEXT DEFAULT '{}',
  state TEXT NOT NULL DEFAULT 'new'
    CHECK(state IN ('new','applied','ignored','dead')),
  attempts INTEGER NOT NULL DEFAULT 0,
  last_error TEXT NOT NULL DEFAULT '',
  received_at TEXT NOT NULL DEFAULT '',
  applied_at TEXT NOT NULL DEFAULT '');
CREATE INDEX IF NOT EXISTS idx_ff_inbox_state ON ff_inbox(state, received_at);
"""


def _now() -> str:
    return datetime.now(timezone.utc).isoformat(timespec="seconds")


# ---------------------------------------------------------------- markers
class KernelMarkerStore:
    """Production marker store: a tiny kernel generic-memory object per event."""

    def exists(self, event_id: str) -> bool:
        from kernel.memory.memory_engine import memory_engine
        return bool(memory_engine.object_exists(MARKER_TYPE, event_id))

    def mark(self, event_id: str, data: Dict[str, Any]) -> None:
        from kernel.memory.memory_engine import memory_engine
        memory_engine.save_object(MARKER_TYPE, event_id, data)


class MemoryMarkerStore:
    """In-memory marker store for tests (no kernel.db writes)."""

    def __init__(self) -> None:
        self.seen: Dict[str, Dict[str, Any]] = {}

    def exists(self, event_id: str) -> bool:
        return event_id in self.seen

    def mark(self, event_id: str, data: Dict[str, Any]) -> None:
        self.seen[event_id] = data


_marker_store: Any = None


def set_marker_store(store: Any) -> None:
    """Override the marker store (tests). Pass None to restore the default."""
    global _marker_store
    _marker_store = store


def _markers() -> Any:
    return _marker_store if _marker_store is not None else KernelMarkerStore()


# ---------------------------------------------------------------- storage
def ensure_schema(db_path: Optional[str] = None) -> None:
    con = ledger.connect(db_path)
    try:
        con.executescript(SCHEMA)
        con.commit()
    finally:
        con.close()


def _row(con, event_id: str) -> Optional[Dict[str, Any]]:
    con.row_factory = sqlite3.Row
    r = con.execute("SELECT * FROM ff_inbox WHERE event_id=?", (event_id,)).fetchone()
    return dict(r) if r else None


def _stage(con, event: Dict[str, Any]) -> bool:
    """Insert a new inbox row. False when the id was already seen (duplicate)."""
    cur = con.execute(
        "INSERT OR IGNORE INTO ff_inbox(event_id, event_type, payload_json,"
        " state, received_at) VALUES(?,?,?,'new',?)",
        (str(event["id"]), str(event.get("event_type", "")),
         json.dumps(event.get("payload") or {}), _now()))
    return cur.rowcount > 0


def _finish(con, event_id: str, state: str, error: str = "") -> None:
    con.execute(
        "UPDATE ff_inbox SET state=?, last_error=?, applied_at=? WHERE event_id=?",
        (state, error[:500], _now(), event_id))


# ---------------------------------------------------------------- apply
def apply(event_id: str, db_path: Optional[str] = None) -> Dict[str, Any]:
    """Apply one staged event. Never raises for an event-level failure."""
    ensure_schema(db_path)
    con = ledger.connect(db_path)
    try:
        row = _row(con, event_id)
        if not row:
            return {"event_id": event_id, "state": "missing"}
        if row["state"] in ("applied", "ignored"):
            return {"event_id": event_id, "state": row["state"],
                    "already_applied": True}
        markers = _markers()
        if markers.exists(event_id):
            _finish(con, event_id, "applied")
            con.commit()
            return {"event_id": event_id, "state": "applied",
                    "already_applied": True}
        etype = row["event_type"]
        payload = json.loads(row["payload_json"] or "{}")
        try:
            marker = _dispatch(etype, payload)
        except Exception as e:  # noqa: BLE001 - recorded, not raised
            attempts = int(row["attempts"]) + 1
            state = "dead" if attempts >= MAX_ATTEMPTS else "new"
            con.execute(
                "UPDATE ff_inbox SET attempts=?, state=?, last_error=? WHERE event_id=?",
                (attempts, state, str(e)[:500], event_id))
            con.commit()
            return {"event_id": event_id, "state": state,
                    "attempts": attempts, "error": str(e)}
        if marker == "ignored":
            _finish(con, event_id, "ignored")
            con.commit()
            return {"event_id": event_id, "state": "ignored"}
        markers.mark(event_id, {"event_type": etype, "applied_at": _now(),
                                **marker})
        con.execute("UPDATE ff_inbox SET attempts=0, last_error='' WHERE event_id=?",
                    (event_id,))
        _finish(con, event_id, "applied")
        con.commit()
        return {"event_id": event_id, "state": "applied", **marker}
    finally:
        con.close()


def _dispatch(event_type: str, payload: Dict[str, Any]) -> Any:
    """Event type -> kernel write. Unknown types are ignored, not guessed."""
    if event_type == "payment_settled":
        from modules.economy.event_adapter import publish_payment_settled
        return publish_payment_settled(payload)
    return "ignored"


# ---------------------------------------------------------------- pull / replay
def pull(fetcher: Callable[..., Dict[str, Any]],
         since: Optional[str] = None, limit: int = 100,
         db_path: Optional[str] = None) -> Dict[str, Any]:
    """Fetch -> stage -> apply. `fetcher(since=..., limit=...)` returns
    {"events": [{id, event_type, payload, created_at}], count}."""
    ensure_schema(db_path)
    batch = fetcher(since=since, limit=limit) or {}
    events: List[Dict[str, Any]] = list(batch.get("events") or [])
    con = ledger.connect(db_path)
    fresh: List[str] = []
    dupes = 0
    try:
        for ev in events:
            if not ev.get("id"):
                continue
            if _stage(con, ev):
                fresh.append(str(ev["id"]))
            else:
                dupes += 1
        con.commit()
        # Retry anything still unattempted/retryable, not only this batch:
        # failed events must be able to reach the dead-letter cap.
        con.row_factory = sqlite3.Row
        pending = [r["event_id"] for r in con.execute(
            "SELECT event_id FROM ff_inbox WHERE state='new'"
            " ORDER BY received_at").fetchall()]
    finally:
        con.close()
    applied, ignored, failed = [], [], []
    for eid in pending:
        state = apply(eid, db_path).get("state")
        if state == "applied":
            applied.append(eid)
        elif state == "ignored":
            ignored.append(eid)
        else:
            failed.append(eid)
    return {"received": len(events), "duplicates": dupes,
            "staged": len(fresh), "applied": len(applied),
            "ignored": len(ignored), "dead": len(failed),
            "applied_ids": applied}


def replay(event_id: str, db_path: Optional[str] = None) -> Dict[str, Any]:
    """Re-run an already applied event. Must change nothing."""
    con = ledger.connect(db_path)
    try:
        row = _row(con, event_id)
        if not row:
            return {"event_id": event_id, "state": "missing"}
        con.execute("UPDATE ff_inbox SET state='new', last_error='' WHERE event_id=?",
                    (event_id,))
        con.commit()
    finally:
        con.close()
    return apply(event_id, db_path)


def dlq_list(db_path: Optional[str] = None) -> List[Dict[str, Any]]:
    con = ledger.connect(db_path)
    try:
        con.row_factory = sqlite3.Row
        return [dict(r) for r in con.execute(
            "SELECT * FROM ff_inbox WHERE state='dead' ORDER BY received_at").fetchall()]
    finally:
        con.close()


def dlq_retry(db_path: Optional[str] = None) -> Dict[str, Any]:
    out = {"retried": 0, "applied": 0}
    for row in dlq_list(db_path):
        con = ledger.connect(db_path)
        try:
            con.execute("UPDATE ff_inbox SET state='new', attempts=0 WHERE event_id=?",
                        (row["event_id"],))
            con.commit()
        finally:
            con.close()
        out["retried"] += 1
        if apply(row["event_id"], db_path).get("state") == "applied":
            out["applied"] += 1
    return out


def stats(db_path: Optional[str] = None) -> Dict[str, int]:
    ensure_schema(db_path)
    con = ledger.connect(db_path)
    try:
        out = {"new": 0, "applied": 0, "ignored": 0, "dead": 0}
        for r in con.execute("SELECT state, COUNT(*) FROM ff_inbox GROUP BY state"):
            out[str(r[0])] = int(r[1])
        return out
    finally:
        con.close()
