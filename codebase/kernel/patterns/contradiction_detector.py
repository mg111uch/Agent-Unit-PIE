from __future__ import annotations

from typing import Dict, List, Optional, Any, Set
from dataclasses import dataclass, field

from kernel.utils.logger import get_child_logger
from kernel.memory.semantic_memory import semantic_memory

logger = get_child_logger("contradiction_detector")

DEFAULT_CONTRADICTION_TYPES = ["contradicts"]
DEFAULT_AGREE_STANCES = ["agree"]

@dataclass
class ContradictionResult:
    claim_a_id: str
    claim_b_id: str
    claim_a_title: str
    claim_b_title: str
    edge_id: str
    relation_type: str
    confidence: float = 1.0
    node_confidence_a: float = 1.0
    node_confidence_b: float = 1.0

    def to_dict(self) -> Dict[str, Any]:
        return {
            "claim_a_id": self.claim_a_id,
            "claim_b_id": self.claim_b_id,
            "claim_a_title": self.claim_a_title,
            "claim_b_title": self.claim_b_title,
            "edge_id": self.edge_id,
            "relation_type": self.relation_type,
            "confidence": self.confidence,
            "node_confidence_a": self.node_confidence_a,
            "node_confidence_b": self.node_confidence_b,
        }

def detect_contradictions(
    believed_node_ids: List[str],
    relation_types: Optional[List[str]] = None,
    min_confidence: float = 0.5,
    min_edge_weight: float = 0.3,
) -> List[ContradictionResult]:
    if not believed_node_ids:
        return []

    types = relation_types or DEFAULT_CONTRADICTION_TYPES
    believed_set: Set[str] = set(believed_node_ids)
    results: List[ContradictionResult] = []

    for edge_id, edge in semantic_memory.edges.items():
        if edge.relation_type not in types:
            continue
        if edge.confidence < min_edge_weight:
            continue

        src_in = edge.source_node_id in believed_set
        tgt_in = edge.target_node_id in believed_set
        if not (src_in and tgt_in):
            continue

        src_node = semantic_memory.get_node(edge.source_node_id)
        tgt_node = semantic_memory.get_node(edge.target_node_id)
        if not src_node or not tgt_node:
            continue
        if src_node.confidence < min_confidence or tgt_node.confidence < min_confidence:
            continue

        results.append(ContradictionResult(
            claim_a_id=edge.source_node_id,
            claim_b_id=edge.target_node_id,
            claim_a_title=src_node.title or src_node.node_id,
            claim_b_title=tgt_node.title or tgt_node.node_id,
            edge_id=edge_id,
            relation_type=edge.relation_type,
            confidence=edge.confidence,
            node_confidence_a=src_node.confidence,
            node_confidence_b=tgt_node.confidence,
        ))

    return results

def _resolve_to_node_id(key: str, info: Dict[str, Any], id_field: str) -> str:
    node_id = info.get(id_field, key)
    if node_id in semantic_memory.nodes:
        return node_id
    for nid, node in semantic_memory.nodes.items():
        if node.title == key or node.title == node_id:
            return nid
    return node_id


def detect_contradictions_for_beliefs(
    beliefs: Dict[str, Dict[str, Any]],
    id_field: str = "node_id",
    stance_field: str = "stance",
    confidence_field: str = "confidence",
    agree_stances: Optional[List[str]] = None,
    claim_filter: Optional[str] = None,
) -> List[ContradictionResult]:
    agree = agree_stances or DEFAULT_AGREE_STANCES
    believed_ids: List[str] = []

    for key, info in beliefs.items():
        if not isinstance(info, dict):
            continue
        stance = info.get(stance_field, "")
        if stance not in agree:
            continue
        if claim_filter is not None and key != claim_filter:
            continue
        node_id = _resolve_to_node_id(key, info, id_field)
        believed_ids.append(node_id)

    return detect_contradictions(believed_ids)
