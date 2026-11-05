"""Funnel report (REV-01): real numbers or explicit "unknown".

Two sources, never invented:
- PIE `market.db`: prospects + transactions (always available)
- FireFlow `GET /api/metrics/funnel`: contacted/responses/proposals/pilots/won
  (merged in when a `ff` payload is supplied)

Every stage carries `source` so a reader can tell a measured number from a
missing one. `time_to_first_revenue` is the North-Star metric.
"""
from __future__ import annotations

import json
from typing import Any, Dict, Optional

from modules.economy import ledger, revenue

STAGES = ("prospects", "researched", "contacted", "responses",
          "proposals", "pilots", "won", "revenue", "cost", "margin")


def _prospect_counts(db_path: Optional[str] = None) -> Dict[str, int]:
    rows = ledger.list_table("prospects", db_path=db_path)
    counts = {"prospects": len(rows)}
    # "researched" = has at least one evidence pointer (honest proxy).
    # list_table returns the raw column, so accept both shapes.
    def has_evidence(r: Dict[str, Any]) -> bool:
        raw = r.get("evidence")
        if raw is None:
            raw = r.get("evidence_json")
        if isinstance(raw, str):
            try:
                raw = json.loads(raw or "[]")
            except ValueError:
                return False
        return bool(raw)
    counts["researched"] = sum(1 for r in rows if has_evidence(r))
    return counts


def _money_counts(db_path: Optional[str] = None) -> Dict[str, float]:
    txs = ledger.list_table("transactions", db_path=db_path)
    revenue_in = sum(float(t.get("amount") or 0) for t in txs
                     if str(t.get("kind", "")).lower() in ("payment", "income")
                     and float(t.get("amount") or 0) > 0)
    cost = sum(float(t.get("amount") or 0) for t in txs
               if str(t.get("kind", "")).lower() in ("payout", "expense"))
    return {"revenue": round(revenue_in, 2), "cost": round(cost, 2),
            "margin": round(revenue_in - cost, 2)}


def _ff_stage(ff: Dict[str, Any], key: str) -> Optional[float]:
    candidates = (
        key, f"{key}_count", key.rstrip("s"), f"{key.rstrip('s')}_count",
    )
    for c in candidates:
        if c in (ff or {}):
            try:
                return float(ff[c])
            except (TypeError, ValueError):
                return None
    nested = (ff or {}).get("stages")
    if isinstance(nested, dict) and key in nested:
        return float(nested[key])
    return None


def build(db_path: Optional[str] = None,
          ff: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
    """Merge both sources into one funnel with per-stage provenance."""
    local = _prospect_counts(db_path)
    money = _money_counts(db_path)
    stages: Dict[str, Any] = {}
    for s in STAGES:
        if s in money:
            stages[s] = {"value": money[s], "source": "market.db:transactions"}
        elif s in local:
            stages[s] = {"value": local[s], "source": "market.db:prospects"}
        else:
            value = _ff_stage(ff or {}, s)
            stages[s] = ({"value": value, "source": "fireflow:/api/metrics/funnel"}
                         if value is not None
                         else {"value": None, "source": "unavailable"})

    counts = {k: v["value"] for k, v in stages.items() if isinstance(v["value"], (int, float))}
    rates = revenue.funnel({k: counts[k] for k in
                            ("prospects", "researched", "contacted", "responses",
                             "proposals", "pilots", "won") if k in counts})

    events = [
        {"stage": "prospect", "ts": t.get("ts") or 0}
        for t in ledger.list_table("transactions", db_path=db_path)
        if str(t.get("kind")).lower() == "prospect"
    ]
    return {
        "stages": stages,
        "conversion": rates["conversion"],
        "end_to_end": rates["end_to_end"],
        "time_to_first_revenue": revenue.time_to_first_revenue(events),
        "missing": [k for k, v in stages.items() if v["value"] is None],
        "fireflow_connected": ff is not None,
    }


def render(report: Dict[str, Any]) -> str:
    lines = ["stage            value   source"]
    for k, v in report["stages"].items():
        lines.append(f"{k:<16} {str(v['value']):>6}   {v['source']}")
    t = report["time_to_first_revenue"]
    lines.append(f"time_to_first_revenue: {t['status']} ({t.get('days')})")
    if report["missing"]:
        lines.append("missing: " + ", ".join(report["missing"]))
    return "\n".join(lines)


def main(argv=None) -> int:
    import argparse
    ap = argparse.ArgumentParser()
    ap.add_argument("--ff", default=None, help="path to a captured FireFlow funnel JSON")
    ap.add_argument("--json", action="store_true")
    a = ap.parse_args(argv)
    ff = json.loads(open(a.ff).read()) if a.ff else None
    report = build(ff=ff)
    print(json.dumps(report, indent=1) if a.json else render(report))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
