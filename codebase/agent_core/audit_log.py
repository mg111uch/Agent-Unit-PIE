from __future__ import annotations

import json
import os
import sqlite3
import threading
import hashlib
from datetime import datetime, timezone
from typing import Optional

AUDIT_DB_PATH = "logs/agent_audit.db"


class AuditLog:
    def __init__(self, db_path: str = AUDIT_DB_PATH):
        self._db_path = db_path
        self._lock = threading.Lock()
        os.makedirs(os.path.dirname(db_path) or ".", exist_ok=True)
        self._conn = sqlite3.connect(db_path, check_same_thread=False)
        self._conn.execute("PRAGMA journal_mode=WAL")
        self._init_db()

    def _init_db(self):
        with self._lock:
            self._conn.execute(
                "CREATE TABLE IF NOT EXISTS audit_log ("
                "  id INTEGER PRIMARY KEY AUTOINCREMENT,"
                "  user_id TEXT NOT NULL,"
                "  tool TEXT NOT NULL,"
                "  input_hash TEXT,"
                "  status TEXT NOT NULL,"
                "  created_at TEXT NOT NULL"
                ")"
            )
            self._conn.commit()

    def log(
        self,
        user_id: str,
        tool: str,
        input_data: str = "",
        status: str = "ok",
    ):
        now = datetime.now(timezone.utc).isoformat()
        input_hash = hashlib.sha256(input_data.encode("utf-8")).hexdigest()[:16] if input_data else None
        with self._lock:
            self._conn.execute(
                "INSERT INTO audit_log (user_id, tool, input_hash, status, created_at) "
                "VALUES (?, ?, ?, ?, ?)",
                (user_id, tool, input_hash, status, now),
            )
            self._conn.commit()

    def query(self, limit: int = 100, offset: int = 0) -> list[dict]:
        with self._lock:
            rows = self._conn.execute(
                "SELECT user_id, tool, input_hash, status, created_at "
                "FROM audit_log ORDER BY id DESC LIMIT ? OFFSET ?",
                (limit, offset),
            ).fetchall()
        return [
            {
                "user_id": r[0],
                "tool": r[1],
                "input_hash": r[2],
                "status": r[3],
                "created_at": r[4],
            }
            for r in rows
        ]

    def close(self):
        self._conn.close()
