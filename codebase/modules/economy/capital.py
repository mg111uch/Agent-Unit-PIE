"""Phase 4 capital_engine: cash-basis books + human-approval gate.

Posted income/expense live in the Phase-1 transactions table (market.db
only). Staged proposals carry status='proposed' and move no money;
approve_action executes ONLY with explicit human_approved=True
(paper-gate philosophy: money never moves on agent authority alone).
Amounts rounded to paise; negatives rejected.
"""
from __future__ import annotations
import sqlite3
from datetime import datetime, timezone
from typing import Any, Dict, List, Optional
from . import ledger
from .objects import make_tx

EXT = "external"


def _now() -> str:
    return datetime.now(timezone.utc).isoformat()


def _paise(amount: Any) -> float:
    try:
        v = round(float(amount), 2)
    except (TypeError, ValueError):
        raise ValueError(f"bad amount '{amount}'")
    if v < 0:
        raise ValueError(f"negative amount {v} rejected")
    return v


def _migrate(db_path: Optional[str] = None) -> None:
    ledger.ensure_schema(db_path)
    con = ledger.connect(db_path)
    try:
        try:
            con.execute("ALTER TABLE transactions ADD COLUMN status TEXT DEFAULT 'posted'")
            con.commit()
        except sqlite3.OperationalError:
            pass  # already migrated
    finally:
        con.close()


def _insert(tx: Any, status: str, db_path: Optional[str] = None) -> str:
    d = tx.to_dict() if hasattr(tx, "to_dict") else dict(tx)
    con = ledger.connect(db_path)
    try:
        con.execute("INSERT OR IGNORE INTO transactions VALUES(?,?,?,?,?,?,?)",
                    (d["tx_id"], d.get("from", d.get("from_")), d["to"],
                     d["amount"], d.get("kind", "payment"),
                     d.get("ts", ""), status))
        con.commit()
        return d["tx_id"]
    finally:
        con.close()


def _sums(actor: Optional[str], db_path: Optional[str]) -> float:
    con = ledger.connect(db_path)
    try:
        if actor is None:
            inn = con.execute("SELECT COALESCE(SUM(amount),0) FROM transactions "
                              "WHERE kind='income' AND status='posted'").fetchone()[0]
            out = con.execute("SELECT COALESCE(SUM(amount),0) FROM transactions "
                              "WHERE kind IN ('expense','approved') AND status='posted'").fetchone()[0]
        else:
            inn = con.execute("SELECT COALESCE(SUM(amount),0) FROM transactions "
                              "WHERE recipient=? AND status='posted'", (actor,)).fetchone()[0]
            out = con.execute("SELECT COALESCE(SUM(amount),0) FROM transactions "
                              "WHERE sender=? AND status='posted'", (actor,)).fetchone()[0]
        return round(float(inn) - float(out), 2)
    finally:
        con.close()


def earn(amount: float, actor: str, desc: str = "",
         db_path: Optional[str] = None) -> str:
    """Book income: external -> actor. Returns tx_id."""
    _migrate(db_path)
    v = _paise(amount)
    if v <= 0:
        raise ValueError("earn amount must be > 0")
    return _insert(make_tx(EXT, actor, v, "income", _now()), "posted", db_path)


def spend(amount: float, actor: str, desc: str = "",
          db_path: Optional[str] = None) -> str:
    """Book expense: actor -> external. Returns tx_id."""
    _migrate(db_path)
    v = _paise(amount)
    if v <= 0:
        raise ValueError("spend amount must be > 0")
    return _insert(make_tx(actor, EXT, v, "expense", _now()), "posted", db_path)


def balance(actor_id: str, db_path: Optional[str] = None) -> float:
    """Cash balance: posted credits - debits (proposals excluded)."""
    _migrate(db_path)
    return _sums(actor_id, db_path)


def total_profit(db_path: Optional[str] = None) -> float:
    """Global income - expense over posted entries."""
    _migrate(db_path)
    return _sums(None, db_path)


def propose_action(desc: str, cost: float, actor: str = EXT,
                   db_path: Optional[str] = None) -> Dict[str, Any]:
    """Stage a spend without moving money. Returns {tx_id, status: proposed}."""
    _migrate(db_path)
    v = _paise(cost)
    if v <= 0:
        raise ValueError("proposal cost must be > 0")
    tid = _insert(make_tx(actor, EXT, v, "proposed", _now()), "proposed", db_path)
    return {"tx_id": tid, "status": "proposed", "desc": desc, "cost": v}


def approve_action(tx_id: str, human_approved: bool = False,
                   db_path: Optional[str] = None) -> Dict[str, Any]:
    """Execute a staged proposal ONLY with explicit human approval."""
    if not human_approved:
        raise PermissionError(f"{tx_id}: money moves only with human_approved=True")
    _migrate(db_path)
    con = ledger.connect(db_path)
    try:
        con.row_factory = sqlite3.Row
        cur = con.execute("UPDATE transactions SET status='posted', kind='expense' "
                          "WHERE tx_id=? AND status='proposed'", (tx_id,))
        con.commit()
        if cur.rowcount == 0:
            raise ValueError(f"no staged proposal '{tx_id}'")
        return dict(con.execute("SELECT * FROM transactions WHERE tx_id=?",
                                (tx_id,)).fetchone() or {})
    finally:
        con.close()


def list_proposed(db_path: Optional[str] = None) -> List[Dict[str, Any]]:
    _migrate(db_path)
    con = ledger.connect(db_path)
    try:
        con.row_factory = sqlite3.Row
        return [dict(r) for r in con.execute(
            "SELECT * FROM transactions WHERE status='proposed'").fetchall()]
    finally:
        con.close()
