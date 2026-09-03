"""Paper gate + live boundary. Research agent must never auto-execute live."""
from __future__ import annotations
from datetime import datetime, timezone
from typing import Any, Dict
from ..data.store import connect, ensure_schema


def propose_paper(strategy: Dict[str, Any], human_approved: bool = False,
                  db_path: str | None = None) -> Dict[str, Any]:
    """Always blocked unless human_approved=True. Records proposal in market.db."""
    ensure_schema(db_path)
    pid = f"paper_{abs(hash(str(strategy))) % 10**8}"
    if not human_approved:
        return {"status": "BLOCKED", "proposal_id": pid,
                "message": "paper trading requires human_approved=True"}
    con = connect(db_path)
    try:
        import json
        con.execute("INSERT OR REPLACE INTO paper_proposals VALUES(?,?,?,?,?)",
                    (pid, json.dumps(strategy), "APPROVED", 1,
                     datetime.now(timezone.utc).isoformat()))
        con.commit()
    finally:
        con.close()
    return {"status": "APPROVED", "proposal_id": pid}


def execute_live(*args: Any, **kwargs: Any) -> None:
    raise NotImplementedError("live execution is behind human approval boundary; not available to research agent")
