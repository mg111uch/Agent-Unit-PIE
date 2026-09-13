"""Policy trees: each tree = one backtest run's top-3 subtrees (strategies).

Statuses: ACTIVE -> DEMOTING (exit-only, still listed) -> DEAD (flat, hidden).
A tree is created only from a COMPLETE research run (promote gate).
"""
from __future__ import annotations
from datetime import datetime, timezone
from typing import Any, Dict, List


def _now() -> str:
    return datetime.now(timezone.utc).isoformat()


def ensure(con) -> None:
    con.execute("CREATE TABLE IF NOT EXISTS paper_trees(tree_id TEXT PRIMARY KEY,"
                " policy TEXT, run_id TEXT, status TEXT DEFAULT 'ACTIVE',"
                " created_at TEXT DEFAULT '')")
    con.execute("CREATE TABLE IF NOT EXISTS paper_tree_members(tree_id TEXT,"
                " strategy TEXT, added_at TEXT DEFAULT '',"
                " PRIMARY KEY(tree_id, strategy))")
    con.execute("CREATE TABLE IF NOT EXISTS paper_orders(id INTEGER PRIMARY KEY"
                " AUTOINCREMENT, strategy TEXT, symbol TEXT, signal_ts TEXT,"
                " status TEXT DEFAULT 'PENDING', created_at TEXT DEFAULT '')")


def list_trees(db_path: str | None = None, include_dead: bool = False) -> List[Dict[str, Any]]:
    from ..data.store import connect
    con = connect(db_path)
    try:
        ensure(con)
        q = "SELECT tree_id,policy,run_id,status,created_at FROM paper_trees ORDER BY created_at"
        rows = con.execute(q).fetchall()
    finally:
        con.close()
    out = [{"tree_id": r[0], "policy": r[1], "run_id": r[2], "status": r[3],
            "created_at": r[4]} for r in rows]
    return out if include_dead else [t for t in out if t["status"] != "DEAD"]


def members(tree_id: str, db_path: str | None = None) -> List[str]:
    from ..data.store import connect
    con = connect(db_path)
    try:
        ensure(con)
        return [r[0] for r in con.execute(
            "SELECT strategy FROM paper_tree_members WHERE tree_id=?", (tree_id,)).fetchall()]
    finally:
        con.close()


def tree_of(strategy: str, db_path: str | None = None) -> Dict[str, Any] | None:
    from ..data.store import connect
    con = connect(db_path)
    try:
        ensure(con)
        r = con.execute("SELECT t.tree_id,t.policy,t.run_id,t.status FROM paper_trees t"
                        " JOIN paper_tree_members m ON m.tree_id=t.tree_id"
                        " WHERE m.strategy=?", (strategy,)).fetchone()
        return {"tree_id": r[0], "policy": r[1], "run_id": r[2], "status": r[3]} if r else None
    finally:
        con.close()


def is_exit_only(strategy: str, cap: Dict[str, Any],
                 db_path: str | None = None) -> bool:
    """DEMOTING-tree member or manual capital.yaml retired_trees entry."""
    if strategy in (cap.get("retired_trees") or []):
        return True
    try:
        t = tree_of(strategy, db_path)
        return bool(t and t["status"] == "DEMOTING")
    except Exception:
        return False


def live_strategies(db_path: str | None = None) -> List[str]:
    """Member strategies of all non-DEAD trees (empty = registry unused)."""
    from ..data.store import connect
    con = connect(db_path)
    try:
        ensure(con)
        return [r[0] for r in con.execute(
            "SELECT DISTINCT m.strategy FROM paper_tree_members m"
            " JOIN paper_trees t ON t.tree_id=m.tree_id WHERE t.status!='DEAD'").fetchall()]
    finally:
        con.close()


def default_tree(db_path: str | None = None) -> Dict[str, Any] | None:
    """Newest ACTIVE tree (fallback: newest non-DEAD) for portfolio default."""
    trees = list_trees(db_path)
    if not trees:
        return None
    for t in reversed(trees):
        if t["status"] == "ACTIVE":
            return t
    return trees[-1]


def create_tree(policy: str, run_id: str, strategies: List[str],
                db_path: str | None = None) -> Dict[str, Any]:
    """Promote: previous ACTIVE -> DEMOTING, new tree ACTIVE with members."""
    from ..data.store import connect
    con = connect(db_path)
    try:
        ensure(con)
        n = con.execute("SELECT COUNT(*) FROM paper_trees").fetchone()[0]
        tid = f"T{n + 1}/{policy}"
        con.execute("UPDATE paper_trees SET status='DEMOTING' WHERE status='ACTIVE'")
        con.execute("INSERT INTO paper_trees(tree_id,policy,run_id,status,created_at)"
                    " VALUES(?,?,?,?,?)",
                    (tid, policy, run_id, "ACTIVE", _now()))
        for s in strategies[:3]:
            con.execute("INSERT OR IGNORE INTO paper_tree_members VALUES(?,?,?)",
                        (tid, s, _now()))
        con.commit()
        return {"tree_id": tid, "policy": policy, "run_id": run_id,
                "status": "ACTIVE", "members": strategies[:3]}
    finally:
        con.close()


def demote(strategy: str, db_path: str | None = None) -> bool:
    """Move one subtree out of its ACTIVE tree into its own DEMOTING splinter."""
    from ..data.store import connect
    con = connect(db_path)
    try:
        ensure(con)
        r = con.execute("SELECT tree_id FROM paper_tree_members WHERE strategy=?",
                        (strategy,)).fetchone()
        if not r:
            return False
        old = r[0]
        n = con.execute("SELECT COUNT(*) FROM paper_trees").fetchone()[0]
        tid = f"T{n + 1}/demoted"
        con.execute("INSERT INTO paper_trees(tree_id,policy,run_id,status,created_at)"
                    " VALUES(?,?,?, 'DEMOTING',?)",
                    (tid, f"demoted from {old}", "", _now()))
        con.execute("DELETE FROM paper_tree_members WHERE tree_id=? AND strategy=?",
                    (old, strategy))
        con.execute("INSERT OR IGNORE INTO paper_tree_members VALUES(?,?,?)",
                    (tid, strategy, _now()))
        con.commit()
        return True
    finally:
        con.close()


def sweep_dead(db_path: str | None = None) -> List[str]:
    """DEMOTING trees with 0 OPEN + 0 PENDING -> DEAD. Returns new dead ids."""
    from ..data.store import connect
    con = connect(db_path)
    dead = []
    try:
        ensure(con)
        ids = [r[0] for r in con.execute(
            "SELECT tree_id FROM paper_trees WHERE status='DEMOTING'").fetchall()]
        for tid in ids:
            syms = [r[0] for r in con.execute(
                "SELECT strategy FROM paper_tree_members WHERE tree_id=?", (tid,)).fetchall()]
            if not syms:
                con.execute("UPDATE paper_trees SET status='DEAD' WHERE tree_id=?", (tid,))
                dead.append(tid)
                continue
            q = ",".join("?" * len(syms))
            n_open = con.execute(f"SELECT COUNT(*) FROM paper_trades WHERE strategy IN ({q})"
                                 " AND status='OPEN'", syms).fetchone()[0]
            n_pend = con.execute(f"SELECT COUNT(*) FROM paper_orders WHERE strategy IN ({q})"
                                 " AND status='PENDING'", syms).fetchone()[0]
            if not n_open and not n_pend:
                con.execute("UPDATE paper_trees SET status='DEAD' WHERE tree_id=?", (tid,))
                dead.append(tid)
        con.commit()
    finally:
        con.close()
    return dead
