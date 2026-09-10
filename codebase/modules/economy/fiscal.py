"""Fiscal persistence: policy + economy runs -> queryable cost-vs-benefit.

One domain store only (market.db alongside Phase-1 tables; kernel.db stays
cognition-only). `fiscal_runs` accumulates one row per run across sessions.
record_* use INSERT OR IGNORE -> content-hash ids are idempotent.
"""
from __future__ import annotations
import hashlib
import json
from datetime import datetime, timezone
from typing import Any, Dict, List, Optional
from . import ledger

CODE_VERSION = "fiscal-v1"

FISCAL_SCHEMA = """
CREATE TABLE IF NOT EXISTS fiscal_runs(
  run_id TEXT PRIMARY KEY, policy_id TEXT DEFAULT '', source TEXT DEFAULT '',
  cost REAL DEFAULT 0.0, cost_json TEXT DEFAULT '{}',
  benefit REAL DEFAULT 0.0, welfare REAL DEFAULT 0.0,
  passed INTEGER DEFAULT 0, code_version TEXT DEFAULT '',
  ts TEXT DEFAULT '');
"""


def _now() -> str:
    return datetime.now(timezone.utc).isoformat()


def _fid(payload: Dict[str, Any]) -> str:
    canon = json.dumps(payload, sort_keys=True, default=str)
    return "fisc-" + hashlib.sha1(canon.encode()).hexdigest()[:12]


def _split_money(v: Any) -> tuple:
    if isinstance(v, dict):
        tot = round(sum(float(x or 0) for x in v.values()), 2)
        return tot, json.dumps({k: round(float(x or 0), 2) for k, x in v.items()},
                               sort_keys=True)
    try:
        return round(float(v or 0), 2), "{}"
    except (TypeError, ValueError):
        return 0.0, "{}"


def ensure_fiscal(db_path: Optional[str] = None) -> str:
    ledger.ensure_schema(db_path)
    con = ledger.connect(db_path)
    try:
        con.executescript(FISCAL_SCHEMA)
        con.commit()
    finally:
        con.close()
    return str(ledger.get_db_path(db_path))


def record_fiscal(run: Any = None, policy: Any = None, costs: Any = 0.0,
                  benefits: Any = 0.0, source: str = "",
                  welfare: Any = 0.0, passed: bool = False,
                  code_version: str = CODE_VERSION,
                  db_path: Optional[str] = None) -> str:
    """Log one run's cost vs benefit. run/policy optional (hashed when absent)."""
    pid = run if isinstance(run, str) else ""
    pol = policy if isinstance(policy, str) else ""
    cost, cost_json = _split_money(costs)
    benefit, _ = _split_money(benefits)
    try:
        welf = round(float(welfare or 0), 3)
    except (TypeError, ValueError):
        welf = 0.0
    rid = pid or _fid({"policy": pol, "cost": cost, "benefit": benefit,
                       "source": source, "welfare": welf})
    con = ledger.connect(db_path)
    try:
        con.executescript(ledger.SCHEMA + FISCAL_SCHEMA)
        con.execute("INSERT OR IGNORE INTO fiscal_runs VALUES(?,?,?,?,?,?,?,?,?,?)",
                    (rid, pol, source, cost, cost_json, benefit, welf,
                     int(bool(passed)), code_version, _now()))
        con.commit()
        return rid
    finally:
        con.close()


def query_fiscal(filters: Optional[Dict[str, Any]] = None,
                 db_path: Optional[str] = None) -> List[Dict[str, Any]]:
    """Cost-vs-benefit rows; filters: policy_id, source, passed."""
    f = filters or {}
    q = ("SELECT *, (benefit - cost) AS net FROM fiscal_runs")
    clauses, args = [], []
    if f.get("policy_id"):
        clauses.append("policy_id=?")
        args.append(f["policy_id"])
    if f.get("source"):
        clauses.append("source=?")
        args.append(f["source"])
    if "passed" in f:
        clauses.append("passed=?")
        args.append(int(bool(f["passed"])))
    if clauses:
        q += " WHERE " + " AND ".join(clauses)
    q += " ORDER BY ts"
    con = ledger.connect(db_path)
    try:
        con.row_factory = ledger.sqlite3.Row
        return [dict(r) for r in con.execute(q, tuple(args)).fetchall()]
    finally:
        con.close()
