"""Relation retrieval over the city graph (KRN-02).

The city graph is the smallest real relation set we have, so it is the first
consumer: factory `requires` electricity, road `serves` cluster, worker
`employed_by` firm, ward `contains` neighbourhood, policy `affects` industry.

Edges are ordinary `semantic_memory` edges (one store, `kernel.db`), typed with
those relation names. Retrieval answers "what depends on what" with a path, so
an LLM gets a causal chain instead of a flat list of nodes.
"""
from __future__ import annotations

import hashlib
from typing import Any, Dict, Iterable, List, Optional

CITY_RELATIONS = ("requires", "serves", "employed_by", "contains",
                  "affects", "supplies", "funds")
_INVERSE = {"employed_by": "employs", "requires": "required_by",
            "serves": "served_by", "contains": "part_of",
            "affects": "affected_by", "supplies": "supplied_by",
            "funds": "funded_by"}


def _edge_id(source: str, relation: str, target: str) -> str:
    digest = hashlib.sha1(f"{source}|{relation}|{target}".encode()).hexdigest()[:12]
    return f"rel_{digest}"


class RelationRetriever:
    """Typed edges + neighbourhood/path queries over semantic memory."""

    def __init__(self, memory=None):
        self._memory = memory

    @property
    def memory(self):
        if self._memory is None:
            from kernel.memory.semantic_memory import semantic_memory
            self._memory = semantic_memory
        return self._memory

    # --- write -----------------------------------------------------------
    def link(self, source: str, target: str, relation: str,
             confidence: float = 0.9, topic: str = "",
             metadata: Optional[Dict[str, Any]] = None) -> str:
        if relation not in CITY_RELATIONS:
            raise ValueError(f"relation must be one of {CITY_RELATIONS}")
        eid = _edge_id(source, relation, target)
        self.memory.create_edge(
            edge_id=eid, source_node_id=source, target_node_id=target,
            relation_type=relation, confidence=confidence,
            metadata=metadata or {}, topic_id=topic, persist=True)
        return eid

    def seed(self, spec: Iterable[Dict[str, Any]]) -> Dict[str, Any]:
        """Load a city-graph spec: [{source, target, relation, ...}]."""
        linked, skipped = [], []
        for row in spec or []:
            try:
                linked.append(self.link(row["source"], row["target"],
                                        row["relation"],
                                        float(row.get("confidence", 0.9)),
                                        row.get("topic", ""),
                                        row.get("metadata")))
            except (KeyError, ValueError, TypeError) as e:
                skipped.append({"row": row, "reason": str(e)})
        return {"linked": linked, "skipped": skipped}

    # --- read ------------------------------------------------------------
    def relations(self, node_id: str,
                  relation: Optional[str] = None) -> Dict[str, List[Dict[str, Any]]]:
        out = {"out": [], "in": []}
        for edge in self.memory.edges.values():
            if relation and edge.relation_type != relation:
                continue
            if edge.source_node_id == node_id:
                out["out"].append(self._row(edge, "out"))
            elif edge.target_node_id == node_id:
                out["in"].append(self._row(edge, "in"))
        return out

    def neighbors(self, node_id: str,
                  relation: Optional[str] = None) -> List[str]:
        rel = self.relations(node_id, relation)
        ids = [r["target"] for r in rel["out"]] + [r["source"] for r in rel["in"]]
        return sorted(set(ids))

    def explain(self, node_id: str, depth: int = 2,
                relation: Optional[str] = None) -> Dict[str, Any]:
        """Breadth-first causal paths from a node (cycle-safe)."""
        paths: List[List[Dict[str, str]]] = []
        queue: List[tuple] = [(node_id, [])]
        seen = {node_id}
        while queue:
            current, path = queue.pop(0)
            if len(path) >= max(1, depth):
                paths.append(path)
                continue
            rel = self.relations(current, relation)
            if not rel["out"]:
                if path:
                    paths.append(path)
                continue
            for edge in rel["out"]:
                if edge["target"] in seen:
                    paths.append(path + [edge])
                    continue
                seen.add(edge["target"])
                queue.append((edge["target"], path + [edge]))
        return {"node_id": node_id, "paths": paths,
                "path_count": len(paths),
                "relations": list(CITY_RELATIONS)}

    def city_summary(self, topic: str = "") -> Dict[str, Any]:
        """Counts per relation, so a city graph can be checked at a glance."""
        counts: Dict[str, int] = {}
        for edge in self.memory.edges.values():
            if edge.relation_type not in CITY_RELATIONS:
                continue
            if topic and edge.topic_id != topic:
                continue
            counts[edge.relation_type] = counts.get(edge.relation_type, 0) + 1
        return {"topic": topic or "(all)", "counts": counts,
                "edges": sum(counts.values())}

    def _row(self, edge, direction: str) -> Dict[str, Any]:
        return {
            "edge_id": edge.edge_id,
            "relation": edge.relation_type,
            "inverse": _INVERSE.get(edge.relation_type, ""),
            "source": edge.source_node_id,
            "target": edge.target_node_id,
            "confidence": edge.confidence,
            "direction": direction,
        }


relation_retriever = RelationRetriever()
