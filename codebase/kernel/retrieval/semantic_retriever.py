from __future__ import annotations

from dataclasses import dataclass, field
from typing import Dict, List, Optional, Any, Set
from collections import defaultdict
import math
import time

from kernel.utils.logger import get_child_logger

from kernel.memory.semantic_memory import (
    semantic_memory,
    SemanticNode,
)

from kernel.patterns.pattern_engine import (
    pattern_engine,
)

from kernel.retrieval.retrieval_engine import (
    retrieval_engine,
    RetrievalResult,
)


logger = get_child_logger(
    "semantic_retriever"
)


# =========================================================
# SEMANTIC SEARCH RESULT
# =========================================================

@dataclass
class SemanticSearchResult:

    node_id: str

    score: float

    depth: int

    node: Dict[str, Any]

    matched_concepts: List[str] = field(
        default_factory=list
    )

    related_nodes: List[str] = field(
        default_factory=list
    )

    metadata: Dict[str, Any] = field(
        default_factory=dict
    )

    # -----------------------------------------------------
    # SERIALIZATION
    # -----------------------------------------------------

    def to_dict(self) -> Dict[str, Any]:

        return {

            "node_id":
            self.node_id,

            "score":
            self.score,

            "depth":
            self.depth,

            "node":
            self.node,

            "matched_concepts":
            self.matched_concepts,

            "related_nodes":
            self.related_nodes,

            "metadata":
            self.metadata,
        }


# =========================================================
# SEMANTIC RETRIEVER
# =========================================================

class SemanticRetriever:

    def __init__(self):

        self.max_traversal_depth = 3

        self.semantic_decay = 0.8

    # =====================================================
    # CONCEPT SEARCH
    # =====================================================

    def search_by_concept(
        self,
        concept: str,
        limit: int = 10,
    ) -> List[SemanticSearchResult]:

        concept = concept.lower()

        results = []

        for node in (
            semantic_memory.nodes.values()
        ):

            matched_concepts = []

            score = 0.0

            # ---------------------------------------------
            # CONCEPT MATCH
            # ---------------------------------------------

            for node_concept in node.concepts:

                node_concept_lower = (
                    node_concept.lower()
                )

                if concept == node_concept_lower:

                    matched_concepts.append(
                        node_concept
                    )

                    score += 1.0

                elif concept in node_concept_lower:

                    matched_concepts.append(
                        node_concept
                    )

                    score += 0.7

            # ---------------------------------------------
            # TITLE MATCH
            # ---------------------------------------------

            if concept in node.title.lower():

                score += 0.8

            # ---------------------------------------------
            # CONTENT MATCH
            # ---------------------------------------------

            if concept in node.content.lower():

                score += 0.5

            if score <= 0:
                continue

            # ---------------------------------------------
            # IMPORTANCE BOOST
            # ---------------------------------------------

            score *= (
                node.importance
                * node.confidence
            )

            neighbors = (
                semantic_memory
                .get_neighbors(
                    node.node_id
                )
            )

            result = SemanticSearchResult(

                node_id=node.node_id,

                score=score,

                depth=0,

                node=node.to_dict(),

                matched_concepts=
                matched_concepts,

                related_nodes=[
                    n.node_id
                    for n in neighbors
                ],

                metadata={
                    "node_type":
                    node.node_type
                },
            )

            results.append(result)

        results.sort(
            key=lambda x: x.score,
            reverse=True
        )

        return results[:limit]

    # =====================================================
    # SEMANTIC GRAPH TRAVERSAL
    # =====================================================

    def semantic_traversal(
        self,
        start_node_id: str,
        max_depth: int = 2,
    ) -> List[SemanticSearchResult]:

        if (
            start_node_id
            not in semantic_memory.nodes
        ):
            return []

        visited = set()

        results = []

        self._traverse_recursive(

            node_id=start_node_id,

            current_depth=0,

            max_depth=max_depth,

            visited=visited,

            results=results,

            current_score=1.0,
        )

        results.sort(
            key=lambda x: x.score,
            reverse=True
        )

        return results

    # =====================================================
    # RECURSIVE TRAVERSAL
    # =====================================================

    def _traverse_recursive(
        self,
        node_id: str,
        current_depth: int,
        max_depth: int,
        visited: Set[str],
        results: List[SemanticSearchResult],
        current_score: float,
    ):

        if node_id in visited:
            return

        if current_depth > max_depth:
            return

        visited.add(node_id)

        node = semantic_memory.nodes.get(
            node_id
        )

        if not node:
            return

        neighbors = (
            semantic_memory
            .get_neighbors(node_id)
        )

        result = SemanticSearchResult(

            node_id=node.node_id,

            score=current_score,

            depth=current_depth,

            node=node.to_dict(),

            matched_concepts=
            node.concepts,

            related_nodes=[
                n.node_id
                for n in neighbors
            ],

            metadata={
                "traversal_depth":
                current_depth
            },
        )

        results.append(result)

        # ---------------------------------------------
        # TRAVERSE NEIGHBORS
        # ---------------------------------------------

        for neighbor in neighbors:

            next_score = (
                current_score
                * self.semantic_decay
            )

            self._traverse_recursive(

                node_id=neighbor.node_id,

                current_depth=
                current_depth + 1,

                max_depth=max_depth,

                visited=visited,

                results=results,

                current_score=next_score,
            )

    # =====================================================
    # MULTI-CONCEPT SEARCH
    # =====================================================

    def multi_concept_search(
        self,
        concepts: List[str],
        limit: int = 20,
    ) -> List[SemanticSearchResult]:

        combined_scores = {}

        result_map = {}

        for concept in concepts:

            concept_results = (
                self.search_by_concept(
                    concept=concept,
                    limit=limit
                )
            )

            for result in concept_results:

                if (
                    result.node_id
                    not in combined_scores
                ):

                    combined_scores[
                        result.node_id
                    ] = 0.0

                    result_map[
                        result.node_id
                    ] = result

                combined_scores[
                    result.node_id
                ] += result.score

        final_results = []

        for node_id, score in (
            combined_scores.items()
        ):

            result = result_map[node_id]

            result.score = score

            final_results.append(result)

        final_results.sort(
            key=lambda x: x.score,
            reverse=True
        )

        return final_results[:limit]

    # =====================================================
    # SEMANTIC CONTEXT
    # =====================================================

    def build_semantic_context(
        self,
        query: str,
        limit: int = 10,
    ) -> Dict[str, Any]:

        concepts = query.lower().split()

        concept_results = (
            self.multi_concept_search(
                concepts=concepts,
                limit=limit
            )
        )

        traversed_nodes = []

        for result in concept_results[:3]:

            traversal = (
                self.semantic_traversal(
                    start_node_id=
                    result.node_id,

                    max_depth=2,
                )
            )

            traversed_nodes.extend(
                traversal
            )

        unique_nodes = {}

        for result in traversed_nodes:

            existing = unique_nodes.get(
                result.node_id
            )

            if (
                not existing
                or result.score
                > existing.score
            ):

                unique_nodes[
                    result.node_id
                ] = result

        final_nodes = list(
            unique_nodes.values()
        )

        final_nodes.sort(
            key=lambda x: x.score,
            reverse=True
        )

        return {

            "query":
            query,

            "concepts":
            concepts,

            "results": [

                r.to_dict()
                for r in final_nodes[:limit]
            ],

            "generated_at":
            time.time(),
        }

    # =====================================================
    # RELATED KNOWLEDGE
    # =====================================================

    def retrieve_related_knowledge(
        self,
        node_id: str,
        limit: int = 15,
    ) -> Dict[str, Any]:

        node = semantic_memory.nodes.get(
            node_id
        )

        if not node:

            return {}

        neighbors = (
            semantic_memory
            .get_neighbors(node_id)
        )

        related_patterns = []

        for pattern in (
            pattern_engine.patterns.values()
        ):

            if node_id in pattern.source_ids:

                related_patterns.append(
                    pattern.to_dict()
                )

        return {

            "central_node":
            node.to_dict(),

            "neighbors": [

                n.to_dict()
                for n in neighbors[:limit]
            ],

            "patterns":
            related_patterns[:limit],

            "neighbor_count":
            len(neighbors),
        }

    # =====================================================
    # CLUSTER DETECTION
    # =====================================================

    def detect_semantic_clusters(
        self,
        min_connections: int = 2,
    ) -> List[Dict[str, Any]]:

        clusters = []

        visited = set()

        for node_id in (
            semantic_memory.nodes.keys()
        ):

            if node_id in visited:
                continue

            cluster_nodes = []

            self._cluster_dfs(

                node_id=node_id,

                visited=visited,

                cluster_nodes=
                cluster_nodes,
            )

            if (
                len(cluster_nodes)
                >= min_connections
            ):

                clusters.append({

                    "cluster_size":
                    len(cluster_nodes),

                    "nodes":
                    cluster_nodes,
                })

        clusters.sort(
            key=lambda x: x["cluster_size"],
            reverse=True
        )

        return clusters

    # =====================================================
    # CLUSTER DFS
    # =====================================================

    def _cluster_dfs(
        self,
        node_id: str,
        visited: Set[str],
        cluster_nodes: List[str],
    ):

        if node_id in visited:
            return

        visited.add(node_id)

        cluster_nodes.append(node_id)

        neighbors = (
            semantic_memory
            .get_neighbors(node_id)
        )

        for neighbor in neighbors:

            self._cluster_dfs(

                node_id=
                neighbor.node_id,

                visited=visited,

                cluster_nodes=
                cluster_nodes,
            )

    # =====================================================
    # SUMMARY
    # =====================================================

    def summary(self) -> Dict[str, Any]:

        clusters = (
            self.detect_semantic_clusters()
        )

        return {

            "semantic_nodes":
            len(
                semantic_memory.nodes
            ),

            "semantic_clusters":
            len(clusters),

            "largest_cluster":
            max(
                [c["cluster_size"]
                 for c in clusters],
                default=0
            ),
        }


# =========================================================
# GLOBAL RETRIEVER
# =====================================================

semantic_retriever = (
    SemanticRetriever()
)