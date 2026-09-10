"""Phase 1 ledger: economy tables in data/market.db (SQLite only).

Same db-path/connect pattern as stock_analyser/data/store.py.
record_* use INSERT OR IGNORE → content-hash ids are idempotent.
"""
from __future__ import annotations
import json
import sqlite3
from dataclasses import asdict
from pathlib import Path
from typing import Any, Dict, List, Optional

SCHEMA = """
CREATE TABLE IF NOT EXISTS units(
  unit_id TEXT PRIMARY KEY, kind TEXT, name TEXT, region TEXT,
  capabilities_json TEXT DEFAULT '[]');
CREATE TABLE IF NOT EXISTS opportunities(
  opportunity_id TEXT PRIMARY KEY, problem TEXT, customer TEXT,
  price REAL, cost REAL, margin REAL, startup_cost REAL,
  time_to_revenue TEXT DEFAULT '', moonshot_relevance REAL DEFAULT 0.0,
  scalability REAL DEFAULT 0.0, adjacency REAL DEFAULT 0.0);
CREATE TABLE IF NOT EXISTS tasks(
  task_id TEXT PRIMARY KEY, objective TEXT, budget REAL,
  deadline TEXT DEFAULT '', verification TEXT DEFAULT '', reward REAL DEFAULT 0.0);
CREATE TABLE IF NOT EXISTS transactions(
  tx_id TEXT PRIMARY KEY, sender TEXT, recipient TEXT,
  amount REAL, kind TEXT DEFAULT 'payment', ts TEXT DEFAULT '');
"""


def get_db_path(db_path: Optional[str] = None) -> Path:
    if db_path:
        return Path(db_path)
    # codebase/modules/economy/ledger.py -> workspace/data/market.db
    here = Path(__file__).resolve()
    ws = here.parents[3]  # .../Agentic_Unit_PIE
    cand = ws / "data" / "market.db"
    if cand.parent.exists():
        return cand
    return Path("data/market.db")


def connect(db_path: Optional[str] = None) -> sqlite3.Connection:
    p = get_db_path(db_path)
    p.parent.mkdir(parents=True, exist_ok=True)
    con = sqlite3.connect(str(p))
    con.execute("PRAGMA journal_mode=WAL")
    return con


def ensure_schema(db_path: Optional[str] = None) -> str:
    con = connect(db_path)
    try:
        con.executescript(SCHEMA)
        con.commit()
        _migrate_units(con)
        _migrate_opportunities(con)
        con.commit()
    finally:
        con.close()
    return str(get_db_path(db_path))


def _migrate_opportunities(con: sqlite3.Connection) -> None:
    """Add scalability/adjacency to pre-7-factor DBs. Fresh DBs no-op."""
    try:
        cols = {r[1] for r in con.execute("PRAGMA table_info(opportunities)").fetchall()}
        if "scalability" not in cols:
            con.execute("ALTER TABLE opportunities ADD COLUMN scalability REAL DEFAULT 0.0")
        if "adjacency" not in cols:
            con.execute("ALTER TABLE opportunities ADD COLUMN adjacency REAL DEFAULT 0.0")
    except Exception:
        pass


def _migrate_units(con: sqlite3.Connection) -> None:
    """Legacy actors -> units, data-preserving. actors table never dropped."""
    try:
        tables = {r[0] for r in con.execute(
            "SELECT name FROM sqlite_master WHERE type='table'").fetchall()}
        if "actors" in tables and "units" in tables:
            con.execute("INSERT OR IGNORE INTO units SELECT * FROM actors")
    except Exception:
        pass  # fresh DBs have no actors table; nothing to carry over


def _row(con: sqlite3.Connection, q: str, args: tuple) -> Optional[Dict[str, Any]]:
    con.row_factory = sqlite3.Row
    r = con.execute(q, args).fetchone()
    return dict(r) if r else None


def record_unit(a: Any, db_path: Optional[str] = None) -> str:
    d = asdict(a) if not isinstance(a, dict) else dict(a)
    con = connect(db_path)
    try:
        con.executescript(SCHEMA)
        _migrate_units(con)
        con.execute("INSERT OR IGNORE INTO units VALUES(?,?,?,?,?)",
                    (d["unit_id"], d["kind"], d["name"], d.get("region", ""),
                     json.dumps(d.get("capabilities", []))))
        con.commit()
        return d["unit_id"]
    finally:
        con.close()


def record_opportunity(o: Any, db_path: Optional[str] = None) -> str:
    d = asdict(o) if not isinstance(o, dict) else dict(o)
    con = connect(db_path)
    try:
        con.executescript(SCHEMA)
        _migrate_opportunities(con)
        con.execute(
            "INSERT OR IGNORE INTO opportunities(opportunity_id,problem,customer,"
            "price,cost,margin,startup_cost,time_to_revenue,moonshot_relevance,"
            "scalability,adjacency) VALUES(?,?,?,?,?,?,?,?,?,?,?)",
            (d["opportunity_id"], d["problem"], d["customer"], d["price"],
             d["cost"], d["margin"], d["startup_cost"],
             d.get("time_to_revenue", ""), d.get("moonshot_relevance", 0.0),
             d.get("scalability", 0.0), d.get("adjacency", 0.0)))
        con.commit()
        return d["opportunity_id"]
    finally:
        con.close()


def record_task(t: Any, db_path: Optional[str] = None) -> str:
    d = asdict(t) if not isinstance(t, dict) else dict(t)
    con = connect(db_path)
    try:
        con.executescript(SCHEMA)
        con.execute("INSERT OR IGNORE INTO tasks VALUES(?,?,?,?,?,?)",
                    (d["task_id"], d["objective"], d["budget"],
                     d.get("deadline", ""), d.get("verification", ""),
                     d.get("reward", 0.0)))
        con.commit()
        return d["task_id"]
    finally:
        con.close()


def record_tx(x: Any, db_path: Optional[str] = None) -> str:
    d = x.to_dict() if hasattr(x, "to_dict") else (
        asdict(x) if not isinstance(x, dict) else dict(x))
    frm = d.get("from", d.get("from_"))
    con = connect(db_path)
    try:
        con.executescript(SCHEMA)
        con.execute("INSERT OR IGNORE INTO transactions VALUES(?,?,?,?,?,?)",
                    (d["tx_id"], frm, d["to"], d["amount"],
                     d.get("kind", "payment"), d.get("ts", "")))
        con.commit()
        return d["tx_id"]
    finally:
        con.close()


def get_unit(uid: str, db_path: Optional[str] = None) -> Optional[Dict[str, Any]]:
    con = connect(db_path)
    try:
        r = _row(con, "SELECT * FROM units WHERE unit_id=?", (uid,))
        if r:
            r["capabilities"] = json.loads(r.pop("capabilities_json", "[]"))
        return r
    finally:
        con.close()


def get_opportunity(oid: str, db_path: Optional[str] = None) -> Optional[Dict[str, Any]]:
    con = connect(db_path)
    try:
        return _row(con, "SELECT * FROM opportunities WHERE opportunity_id=?", (oid,))
    finally:
        con.close()


def get_task(tid: str, db_path: Optional[str] = None) -> Optional[Dict[str, Any]]:
    con = connect(db_path)
    try:
        return _row(con, "SELECT * FROM tasks WHERE task_id=?", (tid,))
    finally:
        con.close()


def get_tx(txid: str, db_path: Optional[str] = None) -> Optional[Dict[str, Any]]:
    con = connect(db_path)
    try:
        return _row(con, "SELECT * FROM transactions WHERE tx_id=?", (txid,))
    finally:
        con.close()


def list_table(table: str, db_path: Optional[str] = None) -> List[Dict[str, Any]]:
    assert table in ("units", "opportunities", "tasks", "transactions")
    con = connect(db_path)
    try:
        con.row_factory = sqlite3.Row
        return [dict(r) for r in con.execute(f"SELECT * FROM {table}").fetchall()]
    finally:
        con.close()
