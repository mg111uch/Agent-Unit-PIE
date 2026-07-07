from __future__ import annotations

from dataclasses import dataclass, field
from typing import Dict, List, Optional, Any, Set
from collections import defaultdict
import time

from kernel.utils.logger import get_child_logger

from kernel.memory.semantic_memory import (
    semantic_memory,
    SemanticNode,
)

from kernel.memory.episodic_memory import (
    episodic_memory,
)

from kernel.patterns.pattern_engine import (
    pattern_engine,
)

from kernel.retrieval.retrieval_engine import (
    retrieval_engine,
    RetrievalResult,
)

logger = get_child_logger(
    "hierarchy_retriever"
)

# HIERARCHY NODE

@dataclass
class HierarchyNode:
    node_id: str
    title: str
    node_type: str
    level: int = 0
    parent_id: Optional[str] = None
    children: List[str] = field(
        default_factory=list
    )
    metadata: Dict[str, Any] = field(
        default_factory=dict
    )
    # SERIALIZATION
    def to_dict(self) -> Dict[str, Any]:
        return {
            "node_id":
            self.node_id,
            "title":
            self.title,
            "node_type":
            self.node_type,
            "level":
            self.level,
            "parent_id":
            self.parent_id,
            "children":
            self.children,
            "metadata":
            self.metadata,
        }

# HIERARCHY RETRIEVER

class HierarchyRetriever:
    def __init__(self):
        self.hierarchy_nodes: Dict[
            str,
            HierarchyNode
        ] = {}
        self.root_nodes: Set[str] = set()
        self.parent_index = defaultdict(list)

    # NODE MANAGEMENT
    def add_node(
        self,
        node: HierarchyNode
    ):
        self.hierarchy_nodes[
            node.node_id
        ] = node
        if node.parent_id:
            self.parent_index[
                node.parent_id
            ].append(node.node_id)
            if (
                node.parent_id
                in self.hierarchy_nodes
            ):
                parent = self.hierarchy_nodes[
                    node.parent_id
                ]
                if (
                    node.node_id
                    not in parent.children
                ):
                    parent.children.append(
                        node.node_id
                    )
        else:
            self.root_nodes.add(
                node.node_id
            )
        logger.info(
            f"Hierarchy node added: "
            f"{node.node_id}"
        )
    # CREATE NODE
    def create_node(
        self,
        node_id: str,
        title: str,
        node_type: str,
        level: int = 0,
        parent_id: Optional[str] = None,
        metadata: Optional[Dict] = None,
    ) -> HierarchyNode:
        node = HierarchyNode(
            node_id=node_id,
            title=title,
            node_type=node_type,
            level=level,
            parent_id=parent_id,
            metadata=metadata or {},
        )
        self.add_node(node)
        return node
    # BUILD FROM SEMANTIC GRAPH
    def build_from_semantic_memory(
        self
    ):
        for semantic_node in (
            semantic_memory.nodes.values()
        ):
            parent_id = (
                semantic_node.metadata.get(
                    "parent_id"
                )
            )
            level = (
                semantic_node.metadata.get(
                    "hierarchy_level",
                    0
                )
            )
            self.create_node(
                node_id=
                semantic_node.node_id,
                title=
                semantic_node.title,
                node_type=
                semantic_node.node_type,
                level=level,
                parent_id=parent_id,
                metadata={
                    "semantic":
                    True
                },
            )
        logger.info(
            "Hierarchy built from "
            "semantic memory"
        )
    # HIERARCHICAL RETRIEVAL
    def retrieve_hierarchy_context(
        self,
        node_id: str,
        depth: int = 2,
    ) -> Dict[str, Any]:
        if (
            node_id
            not in self.hierarchy_nodes
        ):
            return {}
        visited = set()
        hierarchy = self._recursive_collect(
            node_id=node_id,
            depth=depth,
            visited=visited,
        )
        return hierarchy
    # RECURSIVE COLLECTION
    def _recursive_collect(
        self,
        node_id: str,
        depth: int,
        visited: Set[str],
    ) -> Dict[str, Any]:
        if node_id in visited:
            return {}
        if depth < 0:
            return {}
        visited.add(node_id)
        node = self.hierarchy_nodes.get(
            node_id
        )
        if not node:
            return {}
        children_data = []
        for child_id in node.children:
            child_context = (
                self._recursive_collect(
                    node_id=child_id,
                    depth=depth - 1,
                    visited=visited,
                )
            )
            if child_context:
                children_data.append(
                    child_context
                )
        return {
            "node":
            node.to_dict(),
            "children":
            children_data,
        }
    # PATH RETRIEVAL
    def get_node_path(
        self,
        node_id: str
    ) -> List[HierarchyNode]:
        path = []
        current = self.hierarchy_nodes.get(
            node_id
        )
        while current:
            path.append(current)
            if not current.parent_id:
                break
            current = (
                self.hierarchy_nodes.get(
                    current.parent_id
                )
            )
        return list(reversed(path))
    # SUBTREE RETRIEVAL
    def get_subtree_nodes(
        self,
        node_id: str,
        depth: int = 3,
    ) -> List[HierarchyNode]:
        results = []
        visited = set()
        self._collect_subtree(
            node_id=node_id,
            depth=depth,
            visited=visited,
            results=results,
        )
        return results
    def _collect_subtree(
        self,
        node_id: str,
        depth: int,
        visited: Set[str],
        results: List[HierarchyNode],
    ):
        if node_id in visited:
            return
        if depth < 0:
            return
        visited.add(node_id)
        node = self.hierarchy_nodes.get(
            node_id
        )
        if not node:
            return
        results.append(node)
        for child_id in node.children:
            self._collect_subtree(
                node_id=child_id,
                depth=depth - 1,
                visited=visited,
                results=results,
            )
    # TOPIC RETRIEVAL
    def retrieve_topic_context(
        self,
        topic: str,
        depth: int = 2,
        limit: int = 10,
    ) -> Dict[str, Any]:
        search_results = (
            retrieval_engine.search(
                query=topic,
                limit=limit
            )
        )
        hierarchy_contexts = []
        for result in search_results:
            if (
                result.item_id
                in self.hierarchy_nodes
            ):
                context = (
                    self.retrieve_hierarchy_context(
                        node_id=result.item_id,
                        depth=depth,
                    )
                )
                hierarchy_contexts.append(
                    context
                )
        return {
            "topic":
            topic,
            "results": [
                r.to_dict()
                for r in search_results
            ],
            "hierarchies":
            hierarchy_contexts,
            "generated_at":
            time.time(),
        }
    # SEMANTIC CLUSTER RETRIEVAL
    def retrieve_semantic_cluster(
        self,
        concept: str,
        limit: int = 20,
    ) -> Dict[str, Any]:
        nodes = (
            semantic_memory
            .search_by_concept(
                concept
            )
        )
        nodes = nodes[:limit]
        cluster = []
        for node in nodes:
            neighbors = (
                semantic_memory
                .get_neighbors(
                    node.node_id
                )
            )
            cluster.append({
                "node":
                node.to_dict(),
                "neighbors": [
                    n.to_dict()
                    for n in neighbors
                ],
            })
        return {
            "concept":
            concept,
            "cluster":
            cluster,
            "node_count":
            len(cluster),
        }
    # ROOT RETRIEVAL
    def get_root_nodes(
        self
    ) -> List[HierarchyNode]:
        return [
            self.hierarchy_nodes[rid]
            for rid in self.root_nodes
            if rid in self.hierarchy_nodes
        ]
    # SEARCH HIERARCHY
    def search_hierarchy(
        self,
        query: str
    ) -> List[HierarchyNode]:
        query = query.lower()
        results = []
        for node in (
            self.hierarchy_nodes.values()
        ):
            searchable = " ".join([
                node.title,
                node.node_type,
            ]).lower()
            if query in searchable:
                results.append(node)
        return results
    # STATS
    def stats(
        self
    ) -> Dict[str, Any]:
        return {
            "total_nodes":
            len(self.hierarchy_nodes),
            "root_nodes":
            len(self.root_nodes),
            "parent_links":
            len(self.parent_index),
        }
    # CLEAR
    def clear(self):
        self.hierarchy_nodes.clear()
        self.root_nodes.clear()
        self.parent_index.clear()
        logger.warning(
            "Hierarchy retriever cleared"
        )

# GLOBAL RETRIEVER

hierarchy_retriever = (
    HierarchyRetriever()
)