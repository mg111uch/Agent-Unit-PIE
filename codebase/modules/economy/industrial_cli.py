"""Thin I/O bridge: FireFlow capability search over PIE industrial graph.

Usage: python codebase/modules/economy/industrial_cli.py '<json>'
Input: {"op": "suppliers"|"ladder", "businesses": [{"ref":..., "name":...,
  "capabilities": [...], "region": "..."}], "capability": "welding",
  "region": "Kanpur" (optional), "have": [...] (ladder only),
  "target": "..." (ladder only)}
Suppliers output: {"suppliers": [...]} ranked most-capable first.
Ladder output: {"target":..., "path": [...], "rungs": [{"capability":...,
  "have": bool, "suppliers": n}]} — base first, target last; have-first order
within missing (climb rung by rung, no jumps).
Uses a temp market.db (never touches the real ledger). All logic lives in
industrial.py / objects.py / ledger.py.
"""
from __future__ import annotations
import json
import sys
import tempfile
from pathlib import Path

try:
    from . import industrial as _IN
    from . import ledger as _LG
except ImportError:
    sys.path.insert(0, str(Path(__file__).resolve().parents[2]))
    from modules.economy import industrial as _IN
    from modules.economy import ledger as _LG


def main() -> None:
    raw = sys.argv[1] if len(sys.argv) > 1 else sys.stdin.read()
    try:
        payload = json.loads(raw)
    except Exception as e:
        print(json.dumps({"error": f"bad JSON input: {e}"}))
        raise SystemExit(1)
    capability = (payload.get("capability") or "").strip()
    op = payload.get("op", "suppliers")
    if op == "ladder":
        target = (payload.get("target") or "").strip()
        if not target:
            print(json.dumps({"error": "target is required"}))
            raise SystemExit(1)
        have = set(payload.get("have", []) or [])
    elif not capability:
        print(json.dumps({"error": "capability is required"}))
        raise SystemExit(1)
    region = (payload.get("region") or "").strip() or None
    tmp = tempfile.mkdtemp()
    db = str(Path(tmp) / "ind.db")
    try:
        for b in payload.get("businesses", []):
            _LG.record_unit({
                "unit_id": str(b.get("ref", b.get("name", "?"))),
                "kind": "firm", "name": str(b.get("name", "?")),
                "region": str(b.get("region", "") or ""),
                "capabilities": list(b.get("capabilities") or []),
            }, db)
        if op == "ladder":
            path = _IN.dependency_path(target, 4, db)
            climb = path[::-1]  # base first, target last: rung-by-rung order
            rungs = [{"capability": c, "have": c in have,
                      "suppliers": len(_IN.find_suppliers(c, None, db))}
                     for c in climb]
            print(json.dumps({"target": target, "path": climb, "rungs": rungs}))
            return
        hits = _IN.find_suppliers(capability, region, db)
    except Exception as e:
        print(json.dumps({"error": f"query failed: {e}"}))
        raise SystemExit(1)
    print(json.dumps({"suppliers": [
        {"ref": h["unit_id"], "name": h["name"], "region": h.get("region", ""),
         "capabilities": h.get("capabilities", [])} for h in hits]}))


if __name__ == "__main__":
    main()
