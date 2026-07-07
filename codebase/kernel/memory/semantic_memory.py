from __future__ import annotations

from dataclasses import dataclass, field
from typing import Dict, List, Any, Optional, Set
from collections import defaultdict
import time

from kernel.utils.logger import get_child_logger
from kernel.memory.memory_engine import memory_engine

logger = get_child_logger("semantic_memory")

# SEMANTIC NODE

@dataclass
class SemanticNode:
    node_id: str
    node_type: str
    title: str = ""
    content: str = ""
    concepts: List[str] = field(default_factory=list)
    tags: List[str] = field(default_factory=list)
    metadata: Dict[str, Any] = field(default_factory=dict)
    confidence: float = 1.0
    importance: float = 0.5
    created_at: float = field(default_factory=time.time)
    updated_at: float = field(default_factory=time.time)
    source_refs: List[str] = field(default_factory=list)
    # SERIALIZATION
    def to_dict(self) -> Dict[str, Any]:
        return {
            "node_id": self.node_id,
            "node_type": self.node_type,
            "title": self.title,
            "content": self.content,
            "concepts": self.concepts,
            "tags": self.tags,
            "metadata": self.metadata,
            "confidence": self.confidence,
            "importance": self.importance,
            "created_at": self.created_at,
            "updated_at": self.updated_at,
            "source_refs": self.source_refs,
        }

# SEMANTIC EDGE

@dataclass
class SemanticEdge:
    edge_id: str
    source_node_id: str
    target_node_id: str
    relation_type: str
    weight: float = 1.0
    confidence: float = 1.0
    metadata: Dict[str, Any] = field(default_factory=dict)
    created_at: float = field(default_factory=time.time)
    # SERIALIZATION
    def to_dict(self) -> Dict[str, Any]:
        return {
            "edge_id": self.edge_id,
            "source_node_id": self.source_node_id,
            "target_node_id": self.target_node_id,
            "relation_type": self.relation_type,
            "weight": self.weight,
            "confidence": self.confidence,
            "metadata": self.metadata,
            "created_at": self.created_at,
        }

# SEMANTIC MEMORY

class SemanticMemory:
    def __init__(self):
        self.nodes: Dict[str, SemanticNode] = {}
        self.edges: Dict[str, SemanticEdge] = {}
        self.tag_index = defaultdict(set)
        self.concept_index = defaultdict(set)
        self.type_index = defaultdict(set)
        self.relation_index = defaultdict(set)
        self.adjacency = defaultdict(set)

    # NODE MANAGEMENT
    def add_node(
        self,
        node: SemanticNode,
        persist: bool = True
    ):
        self.nodes[node.node_id] = node
        # Indexes
        self.type_index[
            node.node_type
        ].add(node.node_id)
        for tag in node.tags:
            self.tag_index[tag].add(
                node.node_id
            )
        for concept in node.concepts:
            self.concept_index[
                concept
            ].add(node.node_id)
        if persist:
            memory_engine.save_object(
                memory_type="semantic",
                object_id=node.node_id,
                data=node.to_dict()
            )
        logger.info(
            f"Semantic node added: {node.node_id}"
        )
    def create_node(
        self,
        node_id: str,
        node_type: str,
        title: str = "",
        content: str = "",
        concepts: Optional[List[str]] = None,
        tags: Optional[List[str]] = None,
        metadata: Optional[Dict[str, Any]] = None,
        confidence: float = 1.0,
        importance: float = 0.5,
        source_refs: Optional[List[str]] = None,
        persist: bool = True,
    ) -> SemanticNode:
        node = SemanticNode(
            node_id=node_id,
            node_type=node_type,
            title=title,
            content=content,
            concepts=concepts or [],
            tags=tags or [],
            metadata=metadata or {},
            confidence=confidence,
            importance=importance,
            source_refs=source_refs or [],
        )
        self.add_node(
            node,
            persist=persist
        )
        return node
    # EDGE MANAGEMENT
    def add_edge(
        self,
        edge: SemanticEdge,
        persist: bool = True
    ):
        self.edges[
            edge.edge_id
        ] = edge
        self.relation_index[
            edge.relation_type
        ].add(edge.edge_id)
        self.adjacency[
            edge.source_node_id
        ].add(edge.target_node_id)
        if persist:
            memory_engine.save_object(
                memory_type="semantic",
                object_id=edge.edge_id,
                data=edge.to_dict()
            )
        logger.info(
            f"Semantic edge added: {edge.edge_id}"
        )
    def create_edge(
        self,
        edge_id: str,
        source_node_id: str,
        target_node_id: str,
        relation_type: str,
        weight: float = 1.0,
        confidence: float = 1.0,
        metadata: Optional[Dict[str, Any]] = None,
        persist: bool = True,
    ) -> SemanticEdge:
        edge = SemanticEdge(
            edge_id=edge_id,
            source_node_id=source_node_id,
            target_node_id=target_node_id,
            relation_type=relation_type,
            weight=weight,
            confidence=confidence,
            metadata=metadata or {},
        )
        self.add_edge(
            edge,
            persist=persist
        )
        return edge
    # RETRIEVAL
    def get_node(
        self,
        node_id: str
    ) -> Optional[SemanticNode]:
        return self.nodes.get(node_id)
    def get_edge(
        self,
        edge_id: str
    ) -> Optional[SemanticEdge]:
        return self.edges.get(edge_id)
    # SEARCH
    def search_by_tag(
        self,
        tag: str
    ) -> List[SemanticNode]:
        node_ids = self.tag_index.get(
            tag,
            set()
        )
        return [
            self.nodes[nid]
            for nid in node_ids
            if nid in self.nodes
        ]
    def search_by_concept(
        self,
        concept: str
    ) -> List[SemanticNode]:
        node_ids = self.concept_index.get(
            concept,
            set()
        )
        return [
            self.nodes[nid]
            for nid in node_ids
            if nid in self.nodes
        ]
    def search_by_type(
        self,
        node_type: str
    ) -> List[SemanticNode]:
        node_ids = self.type_index.get(
            node_type,
            set()
        )
        return [
            self.nodes[nid]
            for nid in node_ids
            if nid in self.nodes
        ]
    def search_content(
        self,
        query: str
    ) -> List[SemanticNode]:
        query = query.lower()
        results = []
        for node in self.nodes.values():
            searchable_text = " ".join([
                node.title,
                node.content,
                " ".join(node.tags),
                " ".join(node.concepts),
            ]).lower()
            if query in searchable_text:
                results.append(node)
        results.sort(
            key=lambda x: x.importance,
            reverse=True
        )
        return results
    # GRAPH OPERATIONS
    def get_neighbors(
        self,
        node_id: str
    ) -> List[SemanticNode]:
        neighbor_ids = self.adjacency.get(
            node_id,
            set()
        )
        return [
            self.nodes[nid]
            for nid in neighbor_ids
            if nid in self.nodes
        ]
    def get_connected_nodes(
        self,
        node_id: str,
        depth: int = 1
    ) -> List[SemanticNode]:
        visited: Set[str] = set()
        queue = [(node_id, 0)]
        results = []
        while queue:
            current_id, current_depth = queue.pop(0)
            if current_id in visited:
                continue
            visited.add(current_id)
            if current_id in self.nodes:
                results.append(
                    self.nodes[current_id]
                )
            if current_depth >= depth:
                continue
            neighbors = self.adjacency.get(
                current_id,
                set()
            )
            for neighbor_id in neighbors:
                queue.append(
                    (
                        neighbor_id,
                        current_depth + 1
                    )
                )
        return results
    # REMOVE
    def remove_node(
        self,
        node_id: str
    ) -> bool:
        if node_id not in self.nodes:
            return False
        node = self.nodes[node_id]
        # Remove indexes
        for tag in node.tags:
            if node_id in self.tag_index[tag]:
                self.tag_index[tag].remove(
                    node_id
                )
        for concept in node.concepts:
            if node_id in self.concept_index[concept]:
                self.concept_index[concept].remove(
                    node_id
                )
        if node_id in self.type_index[node.node_type]:
            self.type_index[node.node_type].remove(
                node_id
            )
        # Remove adjacency
        if node_id in self.adjacency:
            del self.adjacency[node_id]
        # Remove connected edges
        edge_ids_to_remove = []
        for edge_id, edge in self.edges.items():
            if (
                edge.source_node_id == node_id
                or edge.target_node_id == node_id
            ):
                edge_ids_to_remove.append(edge_id)
        for edge_id in edge_ids_to_remove:
            self.remove_edge(edge_id)
        del self.nodes[node_id]
        logger.info(
            f"Semantic node removed: {node_id}"
        )
        return True
    def remove_edge(
        self,
        edge_id: str
    ) -> bool:
        if edge_id not in self.edges:
            return False
        edge = self.edges[edge_id]
        if edge_id in self.relation_index[edge.relation_type]:
            self.relation_index[
                edge.relation_type
            ].remove(edge_id)
        if (
            edge.source_node_id
            in self.adjacency
        ):
            if (
                edge.target_node_id
                in self.adjacency[edge.source_node_id]
            ):
                self.adjacency[
                    edge.source_node_id
                ].remove(
                    edge.target_node_id
                )
        del self.edges[edge_id]
        logger.info(
            f"Semantic edge removed: {edge_id}"
        )
        return True
    # LOAD FROM DISK
    def load_node_from_disk(
        self,
        node_id: str
    ) -> Optional[SemanticNode]:
        data = memory_engine.load_object(
            memory_type="semantic",
            object_id=node_id
        )
        if not data:
            return None
        node = SemanticNode(**data)
        self.add_node(
            node,
            persist=False
        )
        return node
    # STATS
    def stats(self) -> Dict[str, Any]:
        return {
            "total_nodes": len(self.nodes),
            "total_edges": len(self.edges),
            "unique_tags": len(self.tag_index),
            "unique_concepts": len(self.concept_index),
            "node_types": len(self.type_index),
            "relation_types": len(self.relation_index),
        }

    # CLEAR
    def clear(self):
        self.nodes.clear()
        self.edges.clear()
        self.tag_index.clear()
        self.concept_index.clear()
        self.type_index.clear()
        self.relation_index.clear()
        self.adjacency.clear()
        logger.warning(
            "Semantic memory cleared"
        )

# GLOBAL INSTANCE

semantic_memory = SemanticMemory()