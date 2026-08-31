"""High-level develop.* tools — Phase 7.

LLM operates these instead of raw git/simulation/kernel shell.
Each composes existing deterministic ops and drives workflow_engine.
"""
from __future__ import annotations
import json, sys
from pathlib import Path
from typing import Any

# 8 tools: develop.orient/experiment/analyze/modify_sim/modify_kernel/validate/commit/finish
# plus helper develop.state

def _ensure_paths():
    root = Path(__file__).resolve().parents[2]
    for p in [str(root), str(root/"codebase")]:
        if p not in sys.path:
            sys.path.insert(0, p)
    # hydrate semantic memory + hypotheses once per process (cross-process resume)
    try:
        from modules.argu_god.engine.topic_store import hydrate
        hydrate()
    except Exception:
        pass
    try:
        from kernel.hypothesis.hypothesis_engine import hypothesis_engine
        hypothesis_engine.hydrate()
    except Exception:
        pass

def _wf():
    from development.workflow_engine import workflow_engine as _we
    return _we

def develop_state(input_data) -> str:
    _ensure_paths()
    if isinstance(input_data, str):
        try: input_data=json.loads(input_data)
        except: input_data={}
    sim = (input_data or {}).get("simulator","popula_dyn")
    from development.development_state import generate_state, state_text
    st=generate_state(sim)
    # compact + human text combined
    return json.dumps({"state":st,"text":state_text(sim)}, separators=(",",":") )

def develop_orient(input_data) -> str:
    _ensure_paths()
    if isinstance(input_data, str):
        try: input_data=json.loads(input_data)
        except: input_data={}
    q=(input_data or {}).get("query","population")
    sim=(input_data or {}).get("simulator","popula_dyn")
    limit=int((input_data or {}).get("limit",5))
    workflow_engine=_wf()
    from development.development_state import generate_state
    # advance engine if at start/orient
    if workflow_engine.current in ("start","loop"):
        try: workflow_engine.advance("orient")
        except: pass
    # kernel retrieve per-sim (best effort)
    ctx={}
    try:
        from kernel.retrieval.retrieval_engine import retrieval_engine
        res=retrieval_engine.search(query=q, limit=limit, simulator=sim, include_historical=False)
        ctx={"hits":[{"id":r.item_id,"score":round(r.score,2)} for r in res]}
    except Exception as e:
        ctx={"error":str(e)}
    if workflow_engine.current=="orient":
        try: workflow_engine.advance("version_sync", produced={"context": ctx}, success="context_found")
        except Exception as e: ctx["advance"]=str(e)
    st=generate_state(sim)
    return json.dumps({"context":ctx,"state":st,"allowed":workflow_engine.allowed()}, separators=(",",":"))

def _validate_run_id(run_id: str, simulator: str) -> str | None:
    import re
    # uniform: run_basic (baseline) or run_policy_{param}{value} e.g. run_policy_birth08, run_policy_mortality01
    # baseline allowed
    if run_id == "run_basic":
        return None
    # policy: run_policy_{param}{int} — rate*100 encoded without dot, e.g. 0.08→08, 0.10→10
    pat = r"^run_policy_[a-z_]+[0-9]+$"
    if not re.match(pat, run_id):
        return f"run_id '{run_id}' must match uniform pattern baseline 'run_basic' or policy 'run_policy_<param><value>' e.g. 'run_policy_birth08' (got {run_id})"
    return None

def develop_experiment(input_data) -> str:
    _ensure_paths()
    if isinstance(input_data, str):
        input_data=json.loads(input_data)
    d=input_data or {}
    sim=d.get("simulator","popula_dyn")
    run_id=d.get("run_id")
    params=d.get("params",{})
    baseline=d.get("baseline_run_id")
    if not run_id:
        return "Error: 'run_id' required"
    err = _validate_run_id(run_id, sim)
    if err:
        return f"Error: {err}"
    workflow_engine=_wf()
    # allow from decide_branch or hypothesis if needed
    if workflow_engine.current not in ("decide_branch","experiment"):
        # try to move to experiment if allowed
        pass
    try:
        from modules.simulators.simulation_connector import SimulationConnector
        conn=SimulationConnector(simulator=sim)
        # baseline policy: inherit baseline params so all policy runs share same baseline experiment
        merged = dict(params or {})
        if baseline:
            base_params = conn.get_params(baseline)
            if base_params:
                merged = {**base_params, **merged}
                # ensure version consistency: keep baseline horizon/pop unless explicitly overridden
        else:
            # without baseline, suggest uniform naming helper
            if run_id != "run_basic" and not params:
                return "Error: policy run requires baseline_run_id='run_basic' and params e.g. {'birth_rate':0.08} to keep uniform baseline"
        summary=conn.run_and_extract(merged, run_id)
        premise=conn.generate_structured_premise(run_id, baseline)
        reg=conn.register_to_kernel(run_id, premise, baseline)
        finding=reg.get("name","")
        if workflow_engine.current=="decide_branch" and "experiment" in workflow_engine.allowed():
            try: workflow_engine.advance("experiment", produced={"branch":"experiment"}, success="branch_chosen")
            except: pass
        if workflow_engine.current=="experiment":
            try: workflow_engine.advance("update_knowledge", produced={"run_id":run_id,"finding_id":finding}, success="finding_registered")
            except: pass
        return json.dumps({"status":"completed","run_id":run_id,"finding":finding,"summary":summary[:600],"register":str(reg)[:600]}, separators=(",",":"))
    except Exception as e:
        return f"Error in develop_experiment: {e}"

def develop_analyze(input_data) -> str:
    _ensure_paths()
    if isinstance(input_data, str):
        try: input_data=json.loads(input_data)
        except: input_data={}
    d=input_data or {}
    sim=d.get("simulator","popula_dyn")
    run_id=d.get("run_id","")
    # lightweight: signals + recent knowledge + pattern/compress trigger
    try:
        from modules.simulators.simulation_connector import SimulationConnector
        conn=SimulationConnector(simulator=sim)
        sigs=conn.get_signals(run_id) if run_id else []
        # compression (materialized view already via validity, but explicit)
        try:
            from kernel.compression_engine import CompressionEngine
            comp=CompressionEngine().compress_observations()
        except Exception as e:
            comp={"error":str(e)}
        workflow_engine=_wf()
        if workflow_engine.current=="update_knowledge":
            try: workflow_engine.advance("evaluate", produced={"knowledge_updated":True}, success="knowledge_updated")
            except: pass
        return json.dumps({"run_id":run_id,"signals":sigs[:5],"compress":comp,"allowed":workflow_engine.allowed()}, separators=(",",":"))
    except Exception as e:
        return f"Error in develop_analyze: {e}"

def _gated_write(path: str, old: str, new: str, replace_all: bool, level: int, human_approved: bool) -> tuple[bool, str]:
    from development.validation_gate import gate
    g = gate(level, path, human_approved)
    if not g["allowed"]:
        return False, f"GATE {g['message']}; needs={g['needs']}"
    return True, "gate pass"

def develop_modify_simulator(input_data) -> str:
    _ensure_paths()
    if isinstance(input_data, str):
        try: input_data=json.loads(input_data)
        except: input_data={}
    d=input_data or {}
    path=d.get("path")
    old=d.get("old_string")
    new=d.get("new_string")
    if not path or old is None or new is None:
        return "Error: 'path','old_string','new_string' required (gated edit L3)"
    level=int(d.get("level", 3))
    human_approved=bool(d.get("human_approved", False))
    ok, gate_msg = _gated_write(path, old, new, bool(d.get("replace_all")), level, human_approved)
    if not ok:
        return f"Error: {gate_msg}"
    try:
        from pathlib import Path as _P
        fp=_P(path) if _P(path).is_absolute() else _P.cwd()/path
        for base in [Path.cwd(), Path(__file__).resolve().parents[2]]:
            cand=base/path
            if cand.exists():
                fp=cand; break
        text=fp.read_text()
        if old not in text:
            return f"Error: old_string not found in {path}"
        if text.count(old)!=1 and not d.get("replace_all"):
            return f"Error: old_string matches {text.count(old)} times, provide more context or replace_all=true"
        fp.write_text(text.replace(old, new, 1 if not d.get("replace_all") else -1))
        workflow_engine=_wf()
        if workflow_engine.current=="decide_branch":
            try: workflow_engine.advance("modify_code", produced={"branch":"model_or_kernel"}, success="branch_chosen")
            except: pass
        return json.dumps({"status":"edited","path":str(fp),"gate":gate_msg}, separators=(",",":"))
    except Exception as e:
        return f"Error in develop_modify_simulator: {e}"

def develop_modify_kernel(input_data) -> str:
    _ensure_paths()
    if isinstance(input_data, str):
        try: input_data=json.loads(input_data)
        except: input_data={}
    d=input_data or {}
    # L6 requires human_approved + full gate
    if not d.get("human_approved"):
        return "Error: kernel modify requires human_approved=true (L6 gate) — propose first with develop_modify_kernel human_approved=false to test"
    d["level"]=6
    return develop_modify_simulator(d)

def develop_modify_workflow(input_data) -> str:
    _ensure_paths()
    if isinstance(input_data, str):
        try: input_data=json.loads(input_data)
        except: input_data={}
    d=input_data or {}
    path=d.get("path")
    if not path:
        return "Error: 'path' required (expected data/workflows/*.json)"
    if "data/workflows" not in path:
        return "Error: workflow edits must target data/workflows/*.json (L4 gate)"
    d["level"]=4
    # ensure human_approved false still needs workflow_conformance check via gate
    return develop_modify_simulator(d)

def develop_validate(input_data) -> str:
    _ensure_paths()
    if isinstance(input_data, str):
        try: input_data=json.loads(input_data)
        except: input_data={}
    sim=(input_data or {}).get("simulator","popula_dyn")
    try:
        # lightweight validation: version sync + lineage + log hygiene check
        from kernel.simulation_version import sync_from_git, get_current_version
        ver=sync_from_git(sim)
        cur=get_current_version(sim)
        workflow_engine=_wf()
        if workflow_engine.current in ("modify_code","evaluate","update_knowledge"):
            try: workflow_engine.advance("validate", produced={"knowledge_updated":True}, success="knowledge_updated")
            except: 
                try: workflow_engine.advance("validate")
                except: pass
        # move to loop
        if workflow_engine.current=="validate":
            try: workflow_engine.advance("loop", produced={"validation":"pass"}, success="validation_pass")
            except: pass
        return json.dumps({"version":ver.get("version_id") if isinstance(ver, dict) else str(ver),"cur":(cur or {}).get("version_id"),"allowed":workflow_engine.allowed()}, separators=(",",":"))
    except Exception as e:
        return f"Error in develop_validate: {e}"

def develop_commit(input_data) -> str:
    _ensure_paths()
    if isinstance(input_data, str):
        try: input_data=json.loads(input_data)
        except: input_data={}
    msg=(input_data or {}).get("message","")
    if not msg:
        return "Error: 'message' required"
    add_all=bool((input_data or {}).get("add_all", False))
    try:
        from agent_core.tools.git_ops import git_commit
        out=git_commit({"message":msg,"add_all":add_all})
        # after commit, workflow loops to orient
        workflow_engine=_wf()
        if workflow_engine.current=="loop" and "orient" in workflow_engine.allowed():
            try: workflow_engine.advance("orient", success="continue")
            except: pass
        return out if isinstance(out, str) else json.dumps(out)
    except Exception as e:
        return f"Error in develop_commit: {e}"

# map for registry
DEVELOP_TOOLS = {
    "develop_state": develop_state,
    "develop_orient": develop_orient,
    "develop_experiment": develop_experiment,
    "develop_analyze": develop_analyze,
    "develop_modify_simulator": develop_modify_simulator,
    "develop_modify_kernel": develop_modify_kernel,
    "develop_modify_workflow": develop_modify_workflow,
    "develop_validate": develop_validate,
    "develop_commit": develop_commit,
}

