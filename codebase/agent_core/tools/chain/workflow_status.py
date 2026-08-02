"""workflow_status: observer/meta tool exposing the live workflow graph,
mining candidates, and pending-approval chains.

Read-only summary built from the SQLite graph state — no LLM in the loop.
"""

from __future__ import annotations

import json
from typing import Any, Dict

from agent_core.tools.chain.chain_store import chain_store
from agent_core.tools.chain.graph_evolver import graph_evolver


def workflow_status(input_data=None) -> str:
    if isinstance(input_data, str):
        try:
            input_data = json.loads(input_data)
        except Exception:
            input_data = {}
    mode = (input_data or {}).get("mode", "summary")

    if mode == "evolve":
        nodes = graph_evolver.evolve()
        return f"Evolved workflow graph: {nodes} nodes."

    g = graph_evolver.get_summary()
    if mode == "summary":
        pending = ", ".join(g["pending_chains"]) or "none"
        return (
            f"Workflow graph v{g['version']}: {g['nodes']} nodes, {g['edges']} edges, "
            f"{g['clusters']} clusters. Pending-approval chains: {pending}."
        )

    if mode == "full":
        graph = chain_store.get_graph()
        lines = [
            f"Workflow graph v{g['version']} — {g['nodes']} nodes, {g['edges']} edges, "
            f"{g['clusters']} clusters",
            "",
            "Nodes:",
        ]
        for n in graph["nodes"]:
            cluster = f" [in {n['cluster_id']}]" if n.get("cluster_id") else ""
            lines.append(f"  {n['id']}: {n['label']}{cluster}")
        lines.append("")
        lines.append("Edges:")
        for e in graph["edges"]:
            lines.append(f"  {e['src']} -> {e['dst']}" + (f" ({e['label']})" if e["label"] else ""))
        lines.append("")
        lines.append("Clusters:")
        for c in graph["clusters"]:
            lines.append(f"  {c['id']}: {c['label']} (chain {c['chain_id']})")
        if g["notes"]:
            lines.append("")
            lines.append("Notes:")
            for n in g["notes"][:20]:
                lines.append(f"  [{n['tag']}] {n['section']}: {n['text']}")
        if g["pending_chains"]:
            lines.append("")
            lines.append(f"Pending approval: {', '.join(g['pending_chains'])} "
                         "(approve via chain_admin)")
        return "\n".join(lines)

    if mode == "candidates":
        rows = chain_store.list_candidates()
        if not rows:
            return "No mining candidates yet."
        lines = ["Mining candidates (repeated tool sequences):"]
        for r in rows:
            savings = f", ~{r.get('savings_est', 0)} tok saved" if r.get("savings_est") else ""
            lines.append(f"  {r['signature']}  x{r['occurrences']}{savings}")
        return "\n".join(lines)

    return ("workflow_status modes: summary (default) | full | candidates | evolve. "
            "Use 'evolve' to rebuild the graph from chains/candidates/session telemetry.")


workflow_status_tool = workflow_status
