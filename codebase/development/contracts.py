"""Workflow contracts — Phase 6.

Every node is machine-readable. LLM decides WHAT to investigate;
engine decides HOW transitions execute (deterministic).
"""
from __future__ import annotations
from typing import Dict, List, Any, Tuple

REQUIRED_FIELDS = {"id", "goal", "outputs", "success", "next"}
OPTIONAL_FIELDS = {"inputs", "preconditions", "actions", "failure", "mdRef", "subgraph"}

def validate_node(node: Dict[str, Any]) -> Tuple[bool, List[str]]:
    errs: List[str] = []
    nid = node.get("id", "?")
    for f in REQUIRED_FIELDS:
        if f not in node:
            errs.append(f"{nid}: missing required field '{f}'")
    if "id" not in node or not isinstance(node["id"], str) or not node["id"]:
        errs.append("node id must be non-empty string")
    for k in ("outputs", "success", "inputs", "preconditions", "actions"):
        if k in node and not isinstance(node[k], list):
            errs.append(f"{nid}: '{k}' must be list")
    if "next" in node and not isinstance(node["next"], list):
        errs.append(f"{nid}: 'next' must be list of edge target ids")
    # success/failure are predicates (list of strings)
    return (len(errs) == 0, errs)

def validate_workflow(data: Dict[str, Any]) -> Tuple[bool, List[str]]:
    errs: List[str] = []
    nodes = data.get("nodes", [])
    edges = data.get("edges", [])
    if not nodes:
        errs.append("workflow has no nodes")
        return False, errs
    ids = set()
    for n in nodes:
        # support both legacy [id,label,shape,color,x,y,w,h,mdRef,subgraph] and dict form
        obj = _to_dict(n)
        ok, e = validate_node(obj)
        errs.extend(e)
        if obj.get("id") in ids:
            errs.append(f"duplicate id {obj.get('id')}")
        ids.add(obj.get("id"))
    # every edge target must exist or be special
    for e in edges:
        if not isinstance(e, list) or len(e) < 2:
            errs.append(f"edge {e} malformed")
            continue
        src, dst = e[0], e[1]
        if src not in ids:
            errs.append(f"edge src {src} unknown")
        if dst not in ids:
            errs.append(f"edge dst {dst} unknown")
        # validate next consistency: if node.next non-empty, edges from node must cover it
    for n in nodes:
        obj = _to_dict(n)
        nxt = set(obj.get("next", []))
        outs = {d for s, d in [(x[0], x[1]) for x in edges if x[0]==obj.get("id")]}
        if nxt and not nxt.issubset(outs):
            errs.append(f"{obj.get('id')}: next {nxt} not subset of edges {outs}")
    return (len(errs)==0, errs)

def _to_dict(n: Any) -> Dict[str, Any]:
    if isinstance(n, dict):
        return n
    # legacy array: [id,label,shape,color,x,y,w,h,mdRef,subgraph]
    if isinstance(n, list):
        keys = ["id","label","shape","color","x","y","w","h","mdRef","subgraph"]
        d: Dict[str, Any] = {}
        for i,k in enumerate(keys):
            if i < len(n) and n[i]!="":
                d[k]=n[i]
        # legacy has no contract fields — synthesize minimal
        if "goal" not in d:
            d["goal"]=d.get("label","")
        if "outputs" not in d:
            d["outputs"]=[]
        if "success" not in d:
            d["success"]=[]
        if "next" not in d:
            d["next"]=[]
        return d
    return {}

