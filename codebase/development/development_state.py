"""Generated development state — Phase 7.

Compact (<2KB) snapshot derived from Git, simulator lineage, hypotheses, recent runs.
LLM receives: CURRENT STATE + RELEVANT KNOWLEDGE + ALLOWED ACTIONS + SUCCESS CRITERIA.
"""
from __future__ import annotations
import json, hashlib, time
from pathlib import Path
from typing import Dict, List, Any, Optional

_WORKFLOWS_DIR = Path(__file__).resolve().parents[2] / "data" / "workflows"
_STATE_BUDGET = 1900  # bytes, leave margin for 2KB

def _git_commit(sim: Optional[str]=None) -> str:
    try:
        if sim:
            from kernel.git_version import sim_commit
            return sim_commit(sim, short=True) or "unknown"
        from kernel.git_version import current_commit
        return current_commit(short=True) or "unknown"
    except Exception:
        return "unknown"

def _sim_version(sim: str="popula_dyn") -> Optional[Dict[str,Any]]:
    try:
        from kernel.simulation_version import get_current_version
        return get_current_version(sim)
    except Exception:
        return None

def _hypotheses() -> List[Dict[str,Any]]:
    try:
        from kernel.hypothesis.hypothesis_engine import hypothesis_engine
        out=[]
        for h in list(hypothesis_engine.hypotheses.values())[:10]:
            out.append({"id":h.hypothesis_id,"title":h.title[:60],"type":h.hypothesis_type,"cat":h.category,"status":h.status,"conf":round(h.confidence,2)})
        return out
    except Exception:
        return []

def _open_gaps() -> List[Dict[str,Any]]:
    try:
        from kernel.hypothesis.hypothesis_engine import hypothesis_engine
        gaps=[]
        for h in hypothesis_engine.hypotheses.values():
            if h.hypothesis_type=="known_gap" or h.category=="gap":
                gaps.append({"id":h.hypothesis_id,"title":h.title[:50]})
        return gaps[:5]
    except Exception:
        return []

def _recent_runs(limit:int=5) -> List[Dict[str,Any]]:
    try:
        from kernel.persistence.db import kernel_db
        rows = kernel_db.conn.execute("SELECT run_id,simulator,version_id,horizon,status FROM simulation_runs ORDER BY created_at DESC LIMIT ?", (limit,)).fetchall()
        return [{"run_id":r["run_id"],"sim":r["simulator"],"ver":r["version_id"][:18],"h":r["horizon"]} for r in rows]
    except Exception:
        return []

def _workflow_version() -> str:
    try:
        p=_WORKFLOWS_DIR/"research_development.json"
        if p.exists():
            h=hashlib.sha256(p.read_bytes()).hexdigest()[:7]
            return f"rd@{h}"
        return "unknown"
    except Exception:
        return "unknown"

def generate_state(simulator: str="popula_dyn", query: str="") -> Dict[str,Any]:
    git=_git_commit()
    sim_c=_git_commit(simulator)
    cur=_sim_version(simulator)
    hyps=_hypotheses()
    gaps=_open_gaps()
    runs=_recent_runs()
    aff=(cur or {}).get("affected_concepts",[]) if cur else []
    # recommended_next via workflow_engine
    try:
        from development.workflow_engine import workflow_engine
        allowed=workflow_engine.allowed()
        cur_node=workflow_engine.current
    except Exception:
        allowed=["orient"]; cur_node="start"
    state: Dict[str,Any]={
        "sim":simulator,
        "git":git,
        "sim_commit":sim_c,
        "sim_version":(cur or {}).get("version_id",""),
        "aff_concepts":aff[:5],
        "wf_ver":_workflow_version(),
        "wf_node":cur_node,
        "allowed":allowed,
        "hyps":hyps[:4],
        "gaps":gaps[:3],
        "runs":runs,
        "ts":int(time.time()),
    }
    # budget trim: if >1900 bytes, drop hyps/gaps/runs detail
    raw=json.dumps(state, separators=(",",":"))
    if len(raw.encode())> _STATE_BUDGET:
        state["hyps"]=state["hyps"][:2]
        state["gaps"]=state["gaps"][:1]
        state["runs"]=state["runs"][:2]
        raw=json.dumps(state, separators=(",",":"))
    if len(raw.encode())> _STATE_BUDGET:
        # last resort: drop hyps titles
        state["hyps"]=[{"id":h["id"],"status":h["status"]} for h in state["hyps"]]
        raw=json.dumps(state, separators=(",",":"))
    state["_bytes"]=len(raw.encode())
    return state

def state_text(simulator: str="popula_dyn") -> str:
    s=generate_state(simulator)
    lines=[f"CURRENT STATE sim={s['sim']} git={s['git']} sim_commit={s['sim_commit']} wf={s['wf_ver']} node={s['wf_node']}"]
    lines.append(f"ALLOWED: {','.join(s['allowed'])}")
    if s.get("sim_version"):
        lines.append(f"VERSION {s['sim_version']} aff={','.join(s['aff_concepts'])}")
    if s["hyps"]:
        lines.append("HYPS: " + "; ".join(f"{h['id']}[{h['status']}]" for h in s["hyps"]))
    if s["gaps"]:
        lines.append("GAPS: " + ",".join(g["id"] for g in s["gaps"]))
    if s["runs"]:
        lines.append("RUNS: " + ",".join(r["run_id"] for r in s["runs"]))
    return "\n".join(lines)

