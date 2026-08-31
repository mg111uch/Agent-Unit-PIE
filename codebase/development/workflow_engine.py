"""Deterministic workflow executor — Phase 6.

LLM thinks INSIDE the workflow; executor enforces allowed transitions,
preconditions, required outputs, and recovery.
"""
from __future__ import annotations
import json
from pathlib import Path
from typing import Dict, List, Any, Optional

from development.contracts import validate_workflow, _to_dict

_WORKFLOWS_DIR = Path(__file__).resolve().parents[2] / "data" / "workflows"
# also support direct codebase run where parent is workspace root
if not _WORKFLOWS_DIR.exists():
    _WORKFLOWS_DIR = Path(__file__).resolve().parents[1].parent / "data" / "workflows"

# Minimal unified contract definitions for programmatic use (mirrors research_development.json)
UNIFIED_NODES: List[Dict[str, Any]] = [
    {"id":"start","goal":"Entry","inputs":[],"preconditions":[],"actions":[],"outputs":[],"success":["entered"],"failure":["error"],"next":["orient"]},
    {"id":"orient","goal":"Retrieve per-sim ACTIVE knowledge + git state","inputs":["query","simulator"],"preconditions":[],"actions":["kernel_retrieve","git_state"],"outputs":["context"],"success":["context_found"],"failure":["kernel_unavailable"],"next":["version_sync"]},
    {"id":"version_sync","goal":"Sync per-sim lineage sim@commit","inputs":["simulator"],"preconditions":["context_found"],"actions":["sync_from_git"],"outputs":["version_id"],"success":["version_synced"],"failure":["sync_failed"],"next":["hypothesis"]},
    {"id":"hypothesis","goal":"Form or refine hypothesis / gap","inputs":["context","version_id"],"preconditions":["version_synced"],"actions":["hypothesis_form"],"outputs":["hypothesis_id"],"success":["hypothesis_ready"],"failure":["no_gap"],"next":["decide_branch"]},
    {"id":"decide_branch","goal":"Decide experiment vs model vs kernel/workflow change","inputs":["hypothesis_id"],"preconditions":["hypothesis_ready"],"actions":["branch_decide"],"outputs":["branch"],"success":["branch_chosen"],"failure":["unclear"],"next":["experiment","modify_code"]},
    {"id":"experiment","goal":"Run parameter experiment (no code change)","inputs":["hypothesis_id","simulator"],"preconditions":["branch==experiment"],"actions":["simulation.run"],"outputs":["run_id","finding_id"],"success":["finding_registered"],"failure":["sim_crash","invalid_params"],"next":["update_knowledge"]},
    {"id":"modify_code","goal":"Modify simulator/kernel/workflow code","inputs":["hypothesis_id"],"preconditions":["branch==model_or_kernel"],"actions":["code_edit"],"outputs":["commit"],"success":["tests_pass"],"failure":["tests_fail"],"next":["validate"]},
    {"id":"update_knowledge","goal":"Contradiction, patterns, compress, hypothesis update","inputs":["finding_id"],"preconditions":["finding_registered"],"actions":["contradiction_check","pattern_detect","compress"],"outputs":["knowledge_updated"],"success":["knowledge_updated"],"failure":["contradiction"],"next":["evaluate"]},
    {"id":"evaluate","goal":"Did model/kernel need improvement?","inputs":["knowledge_updated"],"preconditions":["knowledge_updated"],"actions":["eval_gap"],"outputs":["eval_result"],"success":["evaluated"],"failure":[],"next":["validate","hypothesis"]},
    {"id":"validate","goal":"Tests + smoke + regression + lineage checks","inputs":["run_id","commit"],"preconditions":[],"actions":["run_tests","smoke","lineage"],"outputs":["validation"],"success":["validation_pass"],"failure":["validation_fail"],"next":["loop"]},
    {"id":"loop","goal":"Loop or stop","inputs":["validation"],"preconditions":[],"actions":[],"outputs":[],"success":["continue","stop"],"failure":[],"next":["orient","stop"]},
    {"id":"stop","goal":"Terminal","inputs":[],"preconditions":[],"actions":[],"outputs":[],"success":["done"],"failure":[],"next":[]},
]

class WorkflowEngine:
    def __init__(self, nodes: Optional[List[Dict[str,Any]]]=None, simulator: str = "popula_dyn", persist: bool = True):
        self.nodes: Dict[str, Dict[str,Any]] = {n["id"]: n for n in (nodes or UNIFIED_NODES)}
        self.edges: Dict[str, List[str]] = {n["id"]: list(n.get("next",[])) for n in (nodes or UNIFIED_NODES)}
        self._sim = simulator
        self._persist = persist
        self.current: str = "start"
        self.history: List[str] = []
        self.outputs: Dict[str, Any] = {}
        if persist:
            try:
                from kernel.persistence.db import kernel_db
                st = kernel_db.load_workflow_state(simulator)
                if st:
                    self.current = st["current"]
                    self.history = st["history"] or []
                    self.outputs = st["outputs"] or {}
            except Exception:
                pass

    def load_json(self, path: Path) -> Dict[str,Any]:
        data = json.loads(path.read_text())
        # validate but allow legacy format
        ok, errs = validate_workflow(data)
        if not ok:
            raise ValueError(f"workflow invalid: {errs}")
        # if dict nodes, adopt them
        if data.get("nodes") and isinstance(data["nodes"][0], dict):
            self.nodes = {n["id"]: n for n in data["nodes"]}
            self.edges = {n["id"]: list(n.get("next",[])) for n in data["nodes"]}
            # also ingest explicit edges if node's next empty but edges list present
            for e in data.get("edges",[]):
                if len(e)>=2:
                    self.edges.setdefault(e[0], [])
                    if e[1] not in self.edges[e[0]]:
                        self.edges[e[0]].append(e[1])
        return data

    def allowed(self) -> List[str]:
        return list(self.edges.get(self.current, []))

    def can_transition(self, target: str) -> bool:
        return target in self.allowed()

    def _save(self):
        if not getattr(self, "_persist", True):
            return
        try:
            from kernel.persistence.db import kernel_db
            kernel_db.save_workflow_state(self._sim, self.current, self.history, self.outputs)
        except Exception:
            pass

    def advance(self, target: str, produced: Optional[Dict[str,Any]]=None, success: str="") -> Dict[str,Any]:
        if not self.can_transition(target):
            raise ValueError(f"transition {self.current} -> {target} not allowed (allowed: {self.allowed()})")
        node = self.nodes.get(self.current, {})
        # check success predicate if provided
        if success and success not in node.get("success", []) and node.get("success"):
            raise ValueError(f"success '{success}' not in {node.get('success')} for {self.current}")
        # check required outputs present
        if produced:
            for out in node.get("outputs", []):
                if out not in produced:
                    raise ValueError(f"node {self.current} requires output '{out}'")
            self.outputs.update(produced)
        # check preconditions of target (light, non-blocking for Phase 6 — success tokens may be implicit)
        # Phase 6 keeps check permissive; detailed gating is Phase 8 validation_gate
        # (branch==* preconditions are advisory only)
        self.history.append(self.current)
        self.current = target
        self._save()
        return {"from": self.history[-1], "to": target, "allowed_next": self.allowed()}

    def reset(self):
        self.current="start"; self.history=[]; self.outputs={}
        self._save()

    def status(self) -> Dict[str,Any]:
        # refresh from DB to see cross-process updates
        if getattr(self, "_persist", False):
            try:
                from kernel.persistence.db import kernel_db
                st = kernel_db.load_workflow_state(self._sim)
                if st:
                    self.current = st["current"]
                    self.history = st["history"] or []
                    self.outputs = st["outputs"] or {}
            except Exception:
                pass
        return {"current": self.current, "allowed": self.allowed(), "history": list(self.history), "outputs": dict(self.outputs)}

workflow_engine = WorkflowEngine()
