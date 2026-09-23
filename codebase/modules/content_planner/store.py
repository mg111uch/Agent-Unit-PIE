"""content_planner store — SQLite only. DB lives in <root>/data/planner.db"""
from __future__ import annotations
import sqlite3
from pathlib import Path

DB_PATH = Path(__file__).resolve().parents[3] / "data" / "planner.db"


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
        c.execute("""CREATE TABLE IF NOT EXISTS items(
          id INTEGER PRIMARY KEY, topic_id INTEGER NOT NULL REFERENCES topics(id) ON DELETE CASCADE,
          body TEXT NOT NULL, status TEXT NOT NULL CHECK(status IN ('planned','done')),
          pos INTEGER NOT NULL DEFAULT 0)""")
        c.execute("""CREATE TABLE IF NOT EXISTS settings(
          k TEXT PRIMARY KEY, v TEXT NOT NULL)""")
        c.execute("INSERT OR IGNORE INTO settings(k,v) VALUES('list_style','bullets')")


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


def get_items(topic_id: int, status: str):
    with conn() as c:
        return [dict(r) for r in c.execute(
            "SELECT * FROM items WHERE topic_id=? AND status=? ORDER BY pos,id",
            (topic_id, status))]


def add_item(topic_id: int, body: str, status: str = "planned") -> int:
    with conn() as c:
        mx = c.execute("SELECT COALESCE(MAX(pos),-1) FROM items WHERE topic_id=? AND status=?",
                       (topic_id, status)).fetchone()[0]
        cur = c.execute("INSERT INTO items(topic_id,body,status,pos) VALUES(?,?,?,?)",
                        (topic_id, body.strip(), status, mx + 1))
        return cur.lastrowid


def edit_item(iid: int, body: str):
    with conn() as c:
        c.execute("UPDATE items SET body=? WHERE id=?", (body.strip(), iid))


def delete_item(iid: int):
    with conn() as c:
        c.execute("DELETE FROM items WHERE id=?", (iid,))


def move_item(iid: int, to_status: str, to_index: int | None = None):
    with conn() as c:
        r = c.execute("SELECT topic_id,status,pos FROM items WHERE id=?", (iid,)).fetchone()
        if not r:
            return
        tid, frm, _ = r["topic_id"], r["status"], r["pos"]
        if frm != to_status:
            c.execute("UPDATE items SET status=?,pos=999999 WHERE id=?", (to_status, iid))
            for t in ("planned", "done"):
                rows = c.execute("SELECT id FROM items WHERE topic_id=? AND status=? ORDER BY pos,id",
                                 (tid, t)).fetchall()
                base = [x["id"] for x in rows]
                if iid in base:
                    base.remove(iid)
                if t == to_status and to_index is not None:
                    base.insert(max(0, min(to_index, len(base))), iid)
                for p, x in enumerate(base):
                    c.execute("UPDATE items SET pos=? WHERE id=?", (p, x))
        elif to_index is not None:
            rows = [x["id"] for x in c.execute(
                "SELECT id FROM items WHERE topic_id=? AND status=? ORDER BY pos,id", (tid, frm))]
            rows.remove(iid)
            rows.insert(max(0, min(to_index, len(rows))), iid)
            for p, x in enumerate(rows):
                c.execute("UPDATE items SET pos=? WHERE id=?", (p, x))


def get_style() -> str:
    with conn() as c:
        r = c.execute("SELECT v FROM settings WHERE k='list_style'").fetchone()
        return r["v"] if r else "bullets"


def set_style(v: str):
    v = "numbered" if v == "numbered" else "bullets"
    with conn() as c:
        c.execute("INSERT OR REPLACE INTO settings(k,v) VALUES('list_style',?)", (v,))


def full_state():
    init_db()
    out = {"style": get_style(), "topics": []}
    for t in list_topics():
        out["topics"].append({"id": t["id"], "name": t["name"],
                              "planned": get_items(t["id"], "planned"),
                              "done": get_items(t["id"], "done")})
    return out
