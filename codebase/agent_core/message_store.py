from __future__ import annotations

import hashlib
import json
import os
import sqlite3
import threading
import time
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Optional, List

from agent_core.secrets_redactor import redact

# Stored tool results are bounded (head + sha256 + length). The full text is
# never needed for the LLM (it sees truncated/compacted payloads); a tool can be
# re-invoked to refetch verbatim output on demand.
_STORED_RESULT_MAX = 4000


def _bound_result(text: str) -> dict:
    """Return a bounded {head, _digest, _len} triple for a long result string."""
    t = text if isinstance(text, str) else str(text)
    if len(t) <= _STORED_RESULT_MAX:
        return {"result": t}
    digest = hashlib.sha256(t.encode("utf-8", errors="replace")).hexdigest()[:16]
    return {
        "result": t[:_STORED_RESULT_MAX] + f"…[truncated {len(t) - _STORED_RESULT_MAX} chars]",
        "_digest": digest,
        "_len": len(t),
    }


def _redact_nested(value: Any) -> Any:
    """Redact secrets inside a nested structure, preserving its shape."""
    if isinstance(value, dict):
        return {k: _redact_nested(v) for k, v in value.items()}
    if isinstance(value, list):
        return [_redact_nested(v) for v in value]
    if isinstance(value, str):
        return redact(value)
    return value

_AGENT_DIR = Path(__file__).resolve().parent
_CODEBASE_DIR = _AGENT_DIR.parent
_PROJECT_ROOT = _CODEBASE_DIR.parent
DB_PATH = str(_PROJECT_ROOT / "data" / "logs" / "agent_sessions.db")


class MessageStore:
    def __init__(self, db_path: str = DB_PATH):
        self._db_path = db_path
        self._lock = threading.Lock()
        os.makedirs(os.path.dirname(db_path) or ".", exist_ok=True)
        self._conn = sqlite3.connect(db_path, check_same_thread=False)
        self._conn.execute("PRAGMA journal_mode=WAL")
        self._conn.execute("PRAGMA foreign_keys=ON")
        self._init_db()

    def _init_db(self):
        with self._lock:
            self._conn.execute(
                "CREATE TABLE IF NOT EXISTS sessions ("
                "  id TEXT PRIMARY KEY,"
                "  created_at TEXT NOT NULL,"
                "  updated_at TEXT NOT NULL"
                ")"
            )
            self._conn.execute(
                "CREATE TABLE IF NOT EXISTS messages ("
                "  id INTEGER PRIMARY KEY AUTOINCREMENT,"
                "  session_id TEXT NOT NULL REFERENCES sessions(id) ON DELETE CASCADE,"
                "  role TEXT NOT NULL,"
                "  content TEXT,"
                "  tool_calls TEXT,"
                "  tool_results TEXT,"
                "  created_at TEXT NOT NULL,"
                "  ts REAL"
                ")"
            )
            self._conn.commit()
            try:
                self._conn.execute("ALTER TABLE messages ADD COLUMN ts REAL")
                self._conn.commit()
            except sqlite3.OperationalError:
                pass  # column already exists

    def create_session(self, session_id: str) -> dict:
        now = datetime.now(timezone.utc).isoformat()
        with self._lock:
            self._conn.execute(
                "INSERT OR IGNORE INTO sessions (id, created_at, updated_at) VALUES (?, ?, ?)",
                (session_id, now, now),
            )
            self._conn.commit()
        return {"id": session_id, "created_at": now, "updated_at": now}

    def session_exists(self, session_id: str) -> bool:
        with self._lock:
            row = self._conn.execute(
                "SELECT 1 FROM sessions WHERE id=?", (session_id,)
            ).fetchone()
            return row is not None

    def add_message(
        self,
        session_id: str,
        role: str,
        content: Optional[str] = None,
        tool_calls: Optional[List[dict]] = None,
        tool_results: Optional[List[dict]] = None,
    ) -> int:
        now = datetime.now(timezone.utc).isoformat()
        ts = time.time()
        if not self.session_exists(session_id):
            self.create_session(session_id)
        bounded_results = None
        if tool_results:
            bounded_results = []
            for tr in tool_results:
                tr = dict(tr)
                res = tr.get("result")
                if isinstance(res, str):
                    tr.update(_bound_result(res))
                bounded_results.append(tr)
        with self._lock:
            self._conn.execute(
                "UPDATE sessions SET updated_at=? WHERE id=?", (now, session_id)
            )
            cursor = self._conn.execute(
                "INSERT INTO messages (session_id, role, content, tool_calls, tool_results, created_at, ts) "
                "VALUES (?, ?, ?, ?, ?, ?, ?)",
                (
                    session_id,
                    role,
                    content,
                    json.dumps(tool_calls) if tool_calls else None,
                    json.dumps(bounded_results) if bounded_results else None,
                    now,
                    ts,
                ),
            )
            msg_id = cursor.lastrowid
            self._conn.commit()
            return msg_id

    def get_messages(self, session_id: str, limit: int = 100) -> List[dict]:
        with self._lock:
            rows = self._conn.execute(
                "SELECT role, content, tool_calls, tool_results, created_at, ts "
                "FROM messages WHERE session_id=? ORDER BY id ASC LIMIT ?",
                (session_id, limit),
            ).fetchall()
        result = []
        for row in rows:
            msg = {"role": row[0]}
            if row[1] is not None:
                msg["content"] = redact(row[1])
            if row[2] is not None:
                raw = json.loads(row[2])
                for tc in raw if isinstance(raw, list) else [raw]:
                    if isinstance(tc, dict) and "arguments" in tc:
                        tc["arguments"] = _redact_nested(tc["arguments"])
                msg["tool_calls"] = raw
            if row[3] is not None:
                raw = json.loads(row[3])
                for tr in raw if isinstance(raw, list) else [raw]:
                    if isinstance(tr, dict) and "result" in tr:
                        tr["result"] = redact(tr["result"])
                msg["tool_results"] = raw
            msg["created_at"] = row[4]
            msg["ts"] = row[5]
            result.append(msg)
        return result

    def turn_timings(self, session_id: str) -> List[dict]:
        """Per-turn wall-clock analytics from stored message timestamps.

        Each turn starts at a user message. llm_ms_est = time until the first
        model output (assistant/tool activity) after the user message;
        tool_span_ms = first model output -> last tool result. Rows written
        before the ts column existed have ts=None and are skipped.
        """
        rows = self.get_messages(session_id, limit=10000)
        turns: List[dict] = []
        cur: Optional[dict] = None
        for m in rows:
            if m["role"] == "user":
                cur = {"user_ts": m["ts"], "llm_ms_est": None,
                       "first_activity_ts": None, "last_tool_result_ts": None,
                       "tool_span_ms": None, "steps": 0}
                turns.append(cur)
                continue
            if cur is None or m["ts"] is None:
                continue
            if cur["first_activity_ts"] is None:
                cur["first_activity_ts"] = m["ts"]
            if m.get("tool_results"):
                cur["steps"] = max(cur["steps"], len(m["tool_results"]))
                cur["last_tool_result_ts"] = m["ts"]
        for t in turns:
            if t["user_ts"] is not None and t["first_activity_ts"] is not None:
                t["llm_ms_est"] = (t["first_activity_ts"] - t["user_ts"]) * 1000
            if t["first_activity_ts"] is not None and t["last_tool_result_ts"] is not None:
                t["tool_span_ms"] = (t["last_tool_result_ts"] - t["first_activity_ts"]) * 1000
            for k in ("first_activity_ts", "last_tool_result_ts"):
                t.pop(k, None)
        return turns

    def delete_session(self, session_id: str):
        with self._lock:
            self._conn.execute(
                "DELETE FROM messages WHERE session_id=?", (session_id,)
            )
            self._conn.execute("DELETE FROM sessions WHERE id=?", (session_id,))
            self._conn.commit()

    def count_messages(self, session_id: str) -> int:
        with self._lock:
            row = self._conn.execute(
                "SELECT COUNT(*) FROM messages WHERE session_id=?", (session_id,)
            ).fetchone()
            return row[0] if row else 0

    def delete_old_messages(self, session_id: str, keep_last: int = 30):
        with self._lock:
            self._conn.execute(
                "DELETE FROM messages WHERE session_id=? AND id NOT IN "
                "(SELECT id FROM messages WHERE session_id=? ORDER BY id DESC LIMIT ?)",
                (session_id, session_id, keep_last),
            )
            self._conn.commit()

    def get_all_sessions(self) -> List[dict]:
        with self._lock:
            rows = self._conn.execute(
                "SELECT id, created_at, updated_at FROM sessions ORDER BY updated_at DESC"
            ).fetchall()
            return [
                {"id": r[0], "created_at": r[1], "updated_at": r[2]} for r in rows
            ]

    def close(self):
        self._conn.close()
