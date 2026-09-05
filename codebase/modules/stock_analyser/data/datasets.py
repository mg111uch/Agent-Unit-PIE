"""Named research datasets over the `research_datasets` registry (stdlib).

A dataset pins universe + timeframe + window (+ frozen split bounds) so
validation/job/connector share one resolution instead of ad-hoc windows.
"""
from __future__ import annotations
import json
import time
from typing import Any, Dict, List
from .store import connect, ensure_schema


def register_dataset(name: str, universe: str, timeframe: str = "1D",
                     start_ts: str = "", end_ts: str = "",
                     splits: Dict[str, Any] | None = None,
                     db_path: str | None = None) -> str:
    ensure_schema(db_path)
    from .universe import resolve_asof, snapshot_hash
    anchor = end_ts or "9999"
    members = resolve_asof(universe, anchor, db_path)
    splits = dict(splits or {})
    splits.setdefault("members", members)
    splits.setdefault("universe_snapshot_hash",
                      snapshot_hash(members) if members else "")
    ds_id = f"ds_{name.strip().lower().replace(' ', '_')}"
    con = connect(db_path)
    try:
        con.execute("INSERT OR REPLACE INTO research_datasets(id,name,universe,timeframe,"
                    "start_ts,end_ts,split_json) VALUES(?,?,?,?,?,?,?)",
                    (ds_id, name, universe, timeframe, start_ts, end_ts,
                     json.dumps(splits or {})))
        con.commit()
    finally:
        con.close()
    return ds_id


def get_dataset(ds_id: str, db_path: str | None = None) -> Dict[str, Any] | None:
    ensure_schema(db_path)
    con = connect(db_path)
    try:
        r = con.execute("SELECT id,name,universe,timeframe,start_ts,end_ts,split_json"
                        " FROM research_datasets WHERE id=?", (ds_id,)).fetchone()
    finally:
        con.close()
    if not r:
        return None
    return {"id": r[0], "name": r[1], "universe": r[2], "timeframe": r[3],
            "start_ts": r[4], "end_ts": r[5], "splits": json.loads(r[6] or "{}")}


def list_datasets(db_path: str | None = None) -> List[Dict[str, Any]]:
    ensure_schema(db_path)
    con = connect(db_path)
    try:
        rows = con.execute("SELECT id,name,universe,timeframe,start_ts,end_ts"
                           " FROM research_datasets ORDER BY id").fetchall()
    finally:
        con.close()
    return [{"id": r[0], "name": r[1], "universe": r[2], "timeframe": r[3],
             "start_ts": r[4], "end_ts": r[5]} for r in rows]
