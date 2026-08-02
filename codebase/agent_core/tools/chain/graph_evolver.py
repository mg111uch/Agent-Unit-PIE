"""GraphEvolver: maintain the evolving workflow graph in SQLite.

Sources:
  - chain_specs (handwritten + approved mined)  -> chain cluster nodes + step edges
  - chain_candidates (repeated, not yet promoted)-> "would-be shortcut" edges
  - tool_sequences (session telemetry)          -> per-tool usage stats + DO/AVOID notes
  - manually upserted graph_notes               -> appended as-is

Runs from the session-end hook; deterministic, no LLM in the loop. Every evolution
bumps graph_state.version so renderers / status tools know the graph changed.
"""

from __future__ import annotations

import json
import time
from collections import Counter, defaultdict
from typing import Any, Dict, List, Optional

from agent_core.tools.chain.chain_store import chain_store
from agent_core.tools.chain.chains import CHAIN_SPECS

# Cluster id + label for the workflow each chain embodies.
_CLUSTER_LABELS = {
    "probe_module": "Workflow: module orientation",
    "orient_symbols": "Workflow: symbol fetch (CALIBRATE→FETCH)",
    "doc_audit": "Workflow: doc health audit",
    "safe_edit": "Workflow: safe edit",
}


class GraphEvolver:
    def __init__(self, store=None):
        self._store = store or chain_store

    # --- public API ---

    def evolve(self) -> int:
        """Rebuild the graph from current sources. Returns nodes written."""
        self._clear_nodes_and_edges()
        self._sync_chains()
        self._sync_candidates()
        self._sync_sequences()
        self._store.bump_graph_state()
        return len(self._store.get_graph()["nodes"])

    def get_summary(self) -> Dict[str, Any]:
        g = self._store.get_graph()
        state = self._store.get_graph_state()
        notes = self._store.list_notes()
        pending = [s for s in self._store.list_specs() if s["status"] == "pending"]
        return {
            "version": state["version"],
            "nodes": len(g["nodes"]),
            "edges": len(g["edges"]),
            "clusters": len(g["clusters"]),
            "pending_chains": [s["name"] for s in pending],
            "notes": notes,
        }

    def sweep_stale_chains(self) -> List[str]:
        """Demote approved mined chains unused for > stale_after_days days.

        Handwritten chains are never touched. Inactive chains stay stored (and
        recoverable via chain_admin activate) but are no longer registered live.
        """
        from agent_core.config import WORKFLOW_LEARN_STALE_AFTER_DAYS
        if WORKFLOW_LEARN_STALE_AFTER_DAYS <= 0:
            return []
        cutoff = time.time() - WORKFLOW_LEARN_STALE_AFTER_DAYS * 86400
        demoted: List[str] = []
        for spec in self._store.list_specs(status="approved"):
            if spec.get("source") != "mined":
                continue
            if not spec.get("last_used_at") or spec["last_used_at"] >= cutoff:
                continue
            self._store.set_status(spec["name"], "inactive")
            try:
                from agent_core.tools import registry
                registry.unregister(spec["name"])
            except Exception:
                pass
            demoted.append(spec["name"])
        return demoted

    # --- context hints (feedback loop to the LLM) ---

    def workflow_hints(self) -> str:
        """Compact markdown hints injected into the turn context.

        Lists live approved chains (name + one-liner) and the top DO/AVOID notes
        from the graph. Chains are included only when the chain tool pack is
        exposed to the LLM (tool_packs.chain on), so hints never reference a tool
        the agent cannot call. Capped to keep per-turn cost negligible.
        """
        parts: List[str] = []
        chain_exposed = "chain" in _active_packs()
        if not chain_exposed:
            parts.append("[workflow chains disabled — enable tool_packs.chain to use them]")
        else:
            chains = list(self._store.list_specs(status="approved"))
            # Handwritten chains live in CHAIN_SPECS (not the store); expose them too.
            known = {s["name"] for s in chains}
            for spec in CHAIN_SPECS:
                if spec.name not in known:
                    chains.append({
                        "name": spec.name,
                        "description": spec.description,
                        "steps": [{"tool": s.tool} for s in spec.steps],
                    })
            if chains:
                lines = ["[workflow chains — prefer these over the individual steps]"]
                for s in chains[:4]:
                    steps = ", ".join(st["tool"] for st in s.get("steps", []))
                    lines.append(f"- {s['name']}: {s['description'][:90]} ({steps})")
                parts.append("\n".join(lines))
        notes = self._store.list_notes(limit=6)
        if notes:
            lines = ["[workflow notes — DO/AVOID learned from usage]"]
            for n in notes:
                tag = "DO" if n.get("tag") == "do" else "AVOID"
                lines.append(f"- {tag}: {n['text'][:120]}")
            parts.append("\n".join(lines))
        joined = "\n\n".join(parts)
        return joined[:900]  # hard cap — hints must stay cheap

    # --- internals ---

    def _clear_nodes_and_edges(self):
        conn = _conn()
        conn.execute("DELETE FROM graph_nodes")
        conn.execute("DELETE FROM graph_edges")
        conn.execute("DELETE FROM graph_clusters")
        conn.commit()

    def _sync_chains(self):
        rows = self._store.list_specs(status="approved")
        chains = list(CHAIN_SPECS)
        for row in rows:
            chains.append(row)
        seen: set = set()
        for spec in chains:
            name = spec["name"] if isinstance(spec, dict) else spec.name
            if name in seen:
                continue
            seen.add(name)
            steps = spec["steps"] if isinstance(spec, dict) else [
                {"tool": s.tool, "name": s.name} for s in spec.steps
            ]
            self._add_chain(name, steps, self._chain_color(spec))

    @staticmethod
    def _chain_color(spec) -> str:
        if isinstance(spec, dict):
            return "#c8f0c8" if spec.get("read_only") else "#f0c8c8"
        return "#c8f0c8"

    def _add_chain(self, name: str, steps: List[Dict[str, Any]], color: str):
        cluster_id = f"cluster_{name}"
        label = _CLUSTER_LABELS.get(name, f"Workflow: {name}")
        self._store.upsert_cluster(cluster_id, label, chain_id=name, color=color)
        prev: Optional[str] = None
        for step in steps:
            tool = step["tool"]
            node_id = f"{name}__{step.get('name') or tool}"
            self._store.upsert_node(node_id, tool, shape="rect",
                                    color="#e0f0e0", cluster_id=cluster_id, chain_id=name)
            if prev:
                self._store.upsert_edge(prev, node_id, "")
            prev = node_id

    def _sync_candidates(self):
        for cand in self._store.list_candidates(limit=100):
            seq = cand["tool_seq"]
            if len(seq) < 2:
                continue
            for tool in (seq[0], seq[-1]):
                nid = f"cand_{tool}"
                self._store.upsert_node(nid, tool, shape="diamond",
                                        color="#fff0c0", stats={"candidate": True})
            self._store.upsert_edge(f"cand_{seq[0]}", f"cand_{seq[-1]}",
                                    f"x{cand['occurrences']}")

    def _sync_sequences(self):
        counts: Counter = Counter()
        sources: Dict[str, set] = defaultdict(set)
        for seq in self._store.list_sequences(limit=500):
            for tool in seq["tool_seq"]:
                counts[tool] += 1
                sources[tool].add(seq["session_id"])
        for tool, n in counts.most_common(30):
            node_id = f"tool_{tool}"
            self._store.upsert_node(
                node_id, tool, shape="rect", color="#e0e8ff",
                stats={"uses": n, "sessions": len(sources[tool])},
            )
        # DO/AVOID notes from observed repetition.
        for tool, n in counts.most_common(5):
            if n < 2:
                continue
            self._store.upsert_note(
                "Observed usage",
                f"'{tool}' called {n} times across {len(sources[tool])} sessions — "
                "consider promoting the enclosing sequence into a chain.",
                "do",
            )


def _conn():
    from kernel.persistence.db import kernel_db
    return kernel_db.conn


def _active_packs():
    try:
        from agent_core.config import resolve_active_tool_packs
        return set(resolve_active_tool_packs())
    except Exception:
        return set()


graph_evolver = GraphEvolver()
