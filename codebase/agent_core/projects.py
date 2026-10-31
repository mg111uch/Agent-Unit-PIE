"""Registry of extra project roots shown in the file tree.

Persistence lives in the existing SQLite database (single store) — no JSON file.
"""

from __future__ import annotations

import os
import sqlite3
import threading
import time

from agent_core.message_store import DB_PATH


class ProjectRegistry:
    def __init__(self, db_path: str = DB_PATH):
        self._lock = threading.Lock()
        os.makedirs(os.path.dirname(db_path) or ".", exist_ok=True)
        self._conn = sqlite3.connect(db_path, check_same_thread=False)
        self._conn.execute("PRAGMA journal_mode=WAL")
        self._conn.execute(
            "CREATE TABLE IF NOT EXISTS projects ("
            "  id INTEGER PRIMARY KEY AUTOINCREMENT,"
            "  path TEXT NOT NULL UNIQUE,"
            "  name TEXT NOT NULL,"
            "  created_at REAL NOT NULL"
            ")"
        )
        self._conn.commit()

    def list(self) -> list[dict]:
        with self._lock:
            rows = self._conn.execute(
                "SELECT id, path, name FROM projects ORDER BY name COLLATE NOCASE"
            ).fetchall()
        return [{"id": str(r[0]), "path": r[1], "name": r[2]} for r in rows]

    def get(self, project_id: str) -> dict | None:
        with self._lock:
            row = self._conn.execute(
                "SELECT id, path, name FROM projects WHERE id = ?", (project_id,)
            ).fetchone()
        return {"id": str(row[0]), "path": row[1], "name": row[2]} if row else None

    def add(self, path: str) -> dict:
        real = os.path.realpath(os.path.expanduser(path.strip()))
        if not os.path.isdir(real):
            raise ValueError(f"Not an existing directory: {path}")
        name = os.path.basename(os.path.normpath(real)) or real
        with self._lock:
            try:
                cur = self._conn.execute(
                    "INSERT INTO projects (path, name, created_at) VALUES (?, ?, ?)",
                    (real, name, time.time()),
                )
                self._conn.commit()
            except sqlite3.IntegrityError:
                row = self._conn.execute(
                    "SELECT id, path, name FROM projects WHERE path = ?", (real,)
                ).fetchone()
                return {"id": str(row[0]), "path": row[1], "name": row[2], "exists": True}
        return {"id": str(cur.lastrowid), "path": real, "name": name}

    def remove(self, project_id: str) -> dict | None:
        item = self.get(project_id)
        if not item:
            return None
        with self._lock:
            self._conn.execute("DELETE FROM projects WHERE id = ?", (project_id,))
            self._conn.commit()
        return item


registry = ProjectRegistry()
