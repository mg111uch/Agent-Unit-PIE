from __future__ import annotations

import json
import os
import sqlite3
import threading
from datetime import datetime, timezone
from typing import Any, Optional, List

from agent_core.secrets_redactor import redact

DB_PATH = "logs/agent_sessions.db"


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
                "  created_at TEXT NOT NULL"
                ")"
            )
            self._conn.commit()

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
        if not self.session_exists(session_id):
            self.create_session(session_id)
        with self._lock:
            self._conn.execute(
                "UPDATE sessions SET updated_at=? WHERE id=?", (now, session_id)
            )
            cursor = self._conn.execute(
                "INSERT INTO messages (session_id, role, content, tool_calls, tool_results, created_at) "
                "VALUES (?, ?, ?, ?, ?, ?)",
                (
                    session_id,
                    role,
                    content,
                    json.dumps(tool_calls) if tool_calls else None,
                    json.dumps(tool_results) if tool_results else None,
                    now,
                ),
            )
            msg_id = cursor.lastrowid
            self._conn.commit()
            return msg_id

    def get_messages(self, session_id: str, limit: int = 100) -> List[dict]:
        with self._lock:
            rows = self._conn.execute(
                "SELECT role, content, tool_calls, tool_results, created_at "
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
                        tc["arguments"] = redact(str(tc["arguments"]))
                msg["tool_calls"] = raw
            if row[3] is not None:
                raw = json.loads(row[3])
                for tr in raw if isinstance(raw, list) else [raw]:
                    if isinstance(tr, dict) and "result" in tr:
                        tr["result"] = redact(tr["result"])
                msg["tool_results"] = raw
            msg["created_at"] = row[4]
            result.append(msg)
        return result

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
