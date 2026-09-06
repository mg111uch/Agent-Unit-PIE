"""Phase 7 industrial graph lite: supplier/capability queries over Actors.

No new tables: capabilities indexed in-memory from the actors table.
Pure reads + in-memory BFS; never writes. SQLite/market.db only.
"""
from __future__ import annotations
import json
from collections import deque
from typing import Dict, List, Optional
from . import ledger


def _actors(db_path: Optional[str] = None) -> List[Dict]:
    ledger.ensure_schema(db_path)  # empty ledger -> empties, not a crash
    rows = ledger.list_table("actors", db_path)
    for r in rows:
        try:
            r["capabilities"] = json.loads(r.pop("capabilities_json", "[]"))
        except Exception:
            r["capabilities"] = []
    return rows


def find_suppliers(capability: str, region: Optional[str] = None,
                   db_path: Optional[str] = None) -> List[Dict]:
    """Actors holding `capability` (region filter optional), most capable first
    (capability count desc = versatility proxy; stable for ties)."""
    hits = [a for a in _actors(db_path)
            if capability in (a.get("capabilities") or [])
            and (region is None or a.get("region") == region)]
    return sorted(hits, key=lambda a: -len(a.get("capabilities") or []))


def capability_map(db_path: Optional[str] = None) -> Dict[str, List[str]]:
    """{capability: sorted [actor_ids]} over all recorded actors."""
    m: Dict[str, List[str]] = {}
    for a in _actors(db_path):
        for c in a.get("capabilities") or []:
            m.setdefault(c, []).append(a["actor_id"])
    return {k: sorted(v) for k, v in m.items()}


def gaps(product_caps: List[str],
         db_path: Optional[str] = None) -> List[str]:
    """Capabilities with zero suppliers (import-substitution leads)."""
    have = set(capability_map(db_path))
    return [c for c in product_caps if c not in have]


def dependency_path(target_cap: str, max_depth: int = 4,
                    db_path: Optional[str] = None) -> List[str]:
    """BFS over co-occurrence (caps sharing actors): [target, ..., base],
    where base = first dead-end leaf. [] if target has no suppliers."""
    co: Dict[str, set] = {}
    for a in _actors(db_path):
        caps = a.get("capabilities") or []
        for c in caps:
            co.setdefault(c, set()).update(k for k in caps if k != c)
    if target_cap not in co:
        return []
    prev: Dict[str, Optional[str]] = {target_cap: None}
    q = deque([target_cap])
    while q:
        cur = q.popleft()
        nxts = sorted(co.get(cur, ()))
        if cur != target_cap and all(n in prev for n in nxts):
            path, node = [cur], cur  # dead-end leaf = base
            while prev[node] is not None:
                node = prev[node]  # type: ignore
                path.append(node)
            return path[::-1]
        depth = 0
        node = cur
        while prev[node] is not None:
            node = prev[node]  # type: ignore
            depth += 1
        if depth >= max_depth:
            continue
        for n in nxts:
            if n not in prev:
                prev[n] = cur
                q.append(n)
    return [target_cap]
