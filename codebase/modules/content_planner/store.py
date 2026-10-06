"""content_planner store — SQLite only. DB lives in <root>/data/planner.db"""
from __future__ import annotations
import sqlite3
from datetime import datetime, timedelta
from pathlib import Path

DB_PATH = Path(__file__).resolve().parents[3] / "data" / "planner.db"
PAGE = 5  # rows rendered per section; rest arrive on scroll
MAX_PAGE = 50
TS = "%Y-%m-%d %H:%M"


def now() -> str:
    return datetime.now().strftime(TS)


def conn():
    DB_PATH.parent.mkdir(parents=True, exist_ok=True)
    c = sqlite3.connect(str(DB_PATH))
    c.row_factory = sqlite3.Row
    c.execute("PRAGMA foreign_keys=ON")
    return c


def init_db():
    with conn() as c:
        c.execute("""CREATE TABLE IF NOT EXISTS topics(
          id INTEGER PRIMARY KEY, name TEXT UNIQUE NOT NULL)""")
        # no pos column: order comes from created_at
        c.execute("""CREATE TABLE IF NOT EXISTS items(
          id INTEGER PRIMARY KEY, topic_id INTEGER NOT NULL REFERENCES topics(id) ON DELETE CASCADE,
          body TEXT NOT NULL, status TEXT NOT NULL CHECK(status IN ('planned','done')),
          created_at TEXT NOT NULL DEFAULT '')""")
        cols = [r["name"] for r in c.execute("PRAGMA table_info(items)")]
        if "created_at" not in cols:  # migrate: old rows keep '' -> treated as oldest
            c.execute("ALTER TABLE items ADD COLUMN created_at TEXT NOT NULL DEFAULT ''")


def list_topics():
    with conn() as c:
        return [dict(r) for r in c.execute("SELECT * FROM topics ORDER BY id")]


def create_topic(name: str) -> int:
    with conn() as c:
        cur = c.execute("INSERT INTO topics(name) VALUES(?)", (name.strip(),))
        return cur.lastrowid


def rename_topic(tid: int, name: str):
    with conn() as c:
        c.execute("UPDATE topics SET name=? WHERE id=?", (name.strip(), tid))


def delete_topic(tid: int):
    with conn() as c:
        c.execute("DELETE FROM topics WHERE id=?", (tid,))


def count_items(topic_id: int, status: str) -> int:
    with conn() as c:
        return c.execute("SELECT COUNT(*) FROM items WHERE topic_id=? AND status=?",
                          (topic_id, status)).fetchone()[0]


def get_items(topic_id: int, status: str, offset: int = 0, limit: int | None = None):
    """Newest first by created_at; id breaks ties and keeps paging stable."""
    sql = "SELECT * FROM items WHERE topic_id=? AND status=? ORDER BY created_at DESC, id DESC"
    args: tuple = (topic_id, status)
    if limit is not None:
        sql += " LIMIT ? OFFSET ?"
        args += (limit, max(0, offset))
    with conn() as c:
        return [dict(r) for r in c.execute(sql, args)]


def items_page(topic_id: int, status: str, offset: int = 0, limit: int = PAGE) -> dict:
    """One lazy-load slice: items + how many exist overall."""
    limit = max(1, min(int(limit), MAX_PAGE))
    offset = max(0, int(offset))
    items = get_items(topic_id, status, offset, limit)
    return {"items": items, "offset": offset, "limit": limit,
            "total": count_items(topic_id, status)}


def add_item(topic_id: int, body: str, status: str = "planned") -> int:
    with conn() as c:
        cur = c.execute("INSERT INTO items(topic_id,body,status,created_at) VALUES(?,?,?,?)",
                        (topic_id, body.strip(), status, now()))
        return cur.lastrowid


def last_item(topic_id: int, status: str | None = None):
    """Newest item of a topic (optionally of one section) by created_at, id as tiebreak."""
    sql, args = "SELECT * FROM items WHERE topic_id=?", [topic_id]
    if status:
        sql, args = sql + " AND status=?", [*args, status]
    with conn() as c:
        r = c.execute(sql + " ORDER BY created_at DESC, id DESC LIMIT 1", args).fetchone()
        return dict(r) if r else None


def edit_item(iid: int, body: str):
    with conn() as c:
        c.execute("UPDATE items SET body=? WHERE id=?", (body.strip(), iid))


def delete_item(iid: int):
    with conn() as c:
        c.execute("DELETE FROM items WHERE id=?", (iid,))


def move_item(iid: int, to_status: str):
    """Flip a listing between sections. Display order is created_at, so nothing else to do."""
    if to_status not in ("planned", "done"):
        return
    with conn() as c:
        c.execute("UPDATE items SET status=? WHERE id=?", (to_status, iid))


def backfill_created_at(step_minutes: int = 1) -> int:
    """Stamp blank created_at from the DB file mtime, oldest id = oldest stamp.

    Idempotent: only touches rows with an empty timestamp. mtime is read before
    any write, so the newest row lands on the DB's last-write time.
    """
    base = datetime.fromtimestamp(DB_PATH.stat().st_mtime)
    with conn() as c:
        ids = [r["id"] for r in c.execute(
            "SELECT id FROM items WHERE created_at='' ORDER BY id")]
        n = len(ids)
        for i, iid in enumerate(ids):
            c.execute("UPDATE items SET created_at=? WHERE id=?",
                      ((base - timedelta(minutes=(n - 1 - i) * step_minutes)).strftime(TS), iid))
    return n


def full_state(rows_for: set | None = None) -> dict:
    """Item rows ship only for topics in rows_for (None = every topic, for /api/state)."""
    init_db()
    out = {"page": PAGE, "topics": []}
    for t in list_topics():
        tid = t["id"]
        done = last_item(tid, "done")
        want = rows_for is None or tid in rows_for
        out["topics"].append({
            "id": tid, "name": t["name"],
            "planned": get_items(tid, "planned", 0, PAGE) if want else [],
            "planned_total": count_items(tid, "planned"),
            "done": get_items(tid, "done", 0, PAGE) if want else [],
            "done_total": count_items(tid, "done"),
            "last_done_at": (done or {}).get("created_at", ""),
            "last_done_id": (done or {}).get("id", 0),
            "latest_done": False,
        })
    win = max(out["topics"], key=lambda t: (t["last_done_at"], t["last_done_id"]), default=None)
    if win and win["done_total"]:
        win["latest_done"] = True   # exactly one topic carries the dot
    return out
