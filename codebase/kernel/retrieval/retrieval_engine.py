from __future__ import annotations

from typing import Dict, List, Optional, Any
from collections import defaultdict
import math
import time

from kernel.utils.logger import get_child_logger

from kernel.memory.working_memory import (
    working_memory
)

from kernel.memory.episodic_memory import (
    episodic_memory,
    Episode,
)

from kernel.memory.semantic_memory import (
    semantic_memory,
    SemanticNode,
)

from kernel.patterns.pattern_engine import (
    pattern_engine
)

from kernel.events.timeline_engine import (
    timeline_engine
)

logger = get_child_logger("retrieval_engine")

# RETRIEVAL RESULT

class RetrievalResult:
    def __init__(
        self,
        item_id: str,
        item_type: str,
        score: float,
        content: Any,
        metadata: Optional[Dict] = None,
    ):
        self.item_id = item_id
        self.item_type = item_type
        self.score = score
        self.content = content
        self.metadata = metadata or {}
    # SERIALIZATION
    def to_dict(self) -> Dict[str, Any]:
        return {
            "item_id":
            self.item_id,
            "item_type":
            self.item_type,
            "score":
            self.score,
            "content":
            self.content,
            "metadata":
            self.metadata,
        }

# RETRIEVAL ENGINE

class RetrievalEngine:
    def __init__(self):
        self.default_limit = 10

    # helpers for Phase 3 version-aware filtering
    def _valid_for_retrieval(self, node, simulator: Optional[str], include_historical: bool) -> bool:
        # simulator isolation: strictly per-sim if simulator given
        try:
            from kernel.simulation_version import is_compatible
            md = getattr(node, "metadata", {}) or {}
            obs = md.get("observation", {}) or {}
            sim = obs.get("simulator") or md.get("validity", {}).get("simulator")
            if simulator and sim and sim != simulator:
                return False
            # validity status
            validity = md.get("validity", {}) if isinstance(md, dict) else {}
            if not include_historical and validity.get("status") == "HISTORICAL":
                return False
            # version compatibility if both have version_id
            if simulator and not include_historical:
                find_ver = obs.get("version_id") or validity.get("valid_for_version")
                # query version is latest for this simulator
                try:
                    from kernel.simulation_version import get_current_version
                    cur = get_current_version(simulator)
                    query_ver = cur["version_id"] if cur else None
                    if find_ver and query_ver and not is_compatible(find_ver, query_ver, simulator=simulator):
                        return False
                except Exception:
                    pass
        except Exception:
            pass
        return True

    # GLOBAL SEARCH
    def search(
        self,
        query: str,
        limit: int = 10,
        simulator: Optional[str] = None,
        include_historical: bool = False,
    ) -> List[RetrievalResult]:
        results = []
        # SEMANTIC MEMORY
        semantic_results = (
            self.search_semantic_memory(
                query=query,
                limit=limit,
                simulator=simulator,
                include_historical=include_historical,
            )
        )
        results.extend(
            semantic_results
        )
        # EPISODIC MEMORY
        episodic_results = (
            self.search_episodic_memory(
                query=query,
                limit=limit,
                simulator=simulator,
                include_historical=include_historical,
            )
        )
        results.extend(
            episodic_results
        )
        # WORKING MEMORY
        working_results = (
            self.search_working_memory(
                query=query,
                limit=limit
            )
        )
        results.extend(
            working_results
        )
        # SORT
        results.sort(
            key=lambda x: x.score,
            reverse=True
        )
        return results[:limit]
    # SEMANTIC MEMORY SEARCH
    def search_semantic_memory(
        self,
        query: str,
        limit: int = 10,
        simulator: Optional[str] = None,
        include_historical: bool = False,
    ) -> List[RetrievalResult]:
        query_lower = query.lower()
        results = []
        for node in semantic_memory.nodes.values():
            if not self._valid_for_retrieval(node, simulator, include_historical):
                continue
            searchable_text = " ".join([
                node.title,
                node.content,
                " ".join(node.tags),
                " ".join(node.concepts),
            ]).lower()
            score = self._calculate_text_score(
                query_lower,
                searchable_text
            )
            if score <= 0:
                continue
            score *= (
                node.importance
                * node.confidence
            )
            results.append(
                RetrievalResult(
                    item_id=node.node_id,
                    item_type="semantic_node",
                    score=score,
                    content=node.to_dict(),
                    metadata={
                        "node_type":
                        node.node_type,
                        "simulator": (node.metadata.get("observation", {}) or {}).get("simulator") if isinstance(node.metadata, dict) else None,
                    },
                )
            )
        results.sort(
            key=lambda x: x.score,
            reverse=True
        )
        return results[:limit]
    # EPISODIC MEMORY SEARCH
    def search_episodic_memory(
        self,
        query: str,
        limit: int = 10,
        simulator: Optional[str] = None,
        include_historical: bool = False,
    ) -> List[RetrievalResult]:
        query_lower = query.lower()
        results = []
        for episode in episodic_memory.episodes.values():
            # per-sim filter for episodic: check simulator in metadata/tags
            if simulator:
                ep_sim = (episode.metadata or {}).get("simulator")
                if ep_sim and ep_sim != simulator:
                    continue
                if not ep_sim and simulator not in (episode.tags or []):
                    # if no simulator tag, keep only if query is generic; for strict per-sim, skip generic episodes
                    pass
            searchable_text = " ".join([
                episode.summary,
                " ".join(
                    episode.tags
                ),
            ]).lower()
            score = self._calculate_text_score(
                query_lower,
                searchable_text
            )
            if score <= 0:
                continue
            score *= (
                episode.importance
                * episode.confidence
            )
            results.append(
                RetrievalResult(
                    item_id=episode.episode_id,
                    item_type="episode",
                    score=score,
                    content=episode.to_dict(),
                    metadata={
                        "episode_type":
                        episode.episode_type,
                        "simulator": (episode.metadata or {}).get("simulator"),
                    },
                )
            )
        results.sort(
            key=lambda x: x.score,
            reverse=True
        )
        return results[:limit]
    # WORKING MEMORY SEARCH
    def search_working_memory(
        self,
        query: str,
        limit: int = 10,
    ) -> List[RetrievalResult]:
        query_lower = query.lower()
        results = []
        for memory in (
            working_memory.memories.values()
        ):
            searchable_text = str(
                memory.content
            ).lower()
            score = self._calculate_text_score(
                query_lower,
                searchable_text
            )
            if score <= 0:
                continue
            score *= (
                memory.importance
                * memory.confidence
            )
            results.append(
                RetrievalResult(
                    item_id=memory.memory_id,
                    item_type="working_memory",
                    score=score,
                    content=memory.to_dict(),
                    metadata={
                        "memory_type":
                        memory.memory_type,
                    },
                )
            )
        results.sort(
            key=lambda x: x.score,
            reverse=True
        )
        return results[:limit]
    # PATTERN RETRIEVAL
    def retrieve_patterns(
        self,
        pattern_type: Optional[str] = None,
        limit: int = 10,
    ) -> List[RetrievalResult]:
        results = []
        patterns = (
            pattern_engine.patterns.values()
        )
        for pattern in patterns:
            if (
                pattern_type
                and pattern.pattern_type
                != pattern_type
            ):
                continue
            score = (
                pattern.metrics.importance
                * pattern.metrics.confidence
            )
            results.append(
                RetrievalResult(
                    item_id=pattern.pattern_id,
                    item_type="pattern",
                    score=score,
                    content=pattern.to_dict(),
                    metadata={
                        "pattern_type":
                        pattern.pattern_type,
                    },
                )
            )
        results.sort(
            key=lambda x: x.score,
            reverse=True
        )
        return results[:limit]
    # TIMELINE RETRIEVAL
    def retrieve_recent_timeline(
        self,
        limit: int = 20
    ) -> List[RetrievalResult]:
        entries = (
            timeline_engine
            .get_recent_entries(limit)
        )
        results = []
        for entry in entries:
            score = (
                entry.importance
            )
            results.append(
                RetrievalResult(
                    item_id=entry.entry_id,
                    item_type="timeline_entry",
                    score=score,
                    content=entry.to_dict(),
                )
            )
        return results
    # CONTEXT RETRIEVAL
    def build_context(
        self,
        query: str,
        max_items: int = 20,
        simulator: Optional[str] = None,
        include_historical: bool = False,
    ) -> Dict[str, Any]:
        search_results = self.search(
            query=query,
            limit=max_items,
            simulator=simulator,
            include_historical=include_historical,
        )
        patterns = self.retrieve_patterns(
            limit=5
        )
        recent_timeline = (
            self.retrieve_recent_timeline(
                limit=10
            )
        )
        context = {
            "query":
            query,
            "retrieved_items": [
                r.to_dict()
                for r in search_results
            ],
            "patterns": [
                p.to_dict()
                for p in patterns
            ],
            "recent_timeline": [
                t.to_dict()
                for t in recent_timeline
            ],
            "generated_at":
            time.time(),
        }
        return context
    # TEXT MATCHING
    def _calculate_text_score(
        self,
        query: str,
        text: str
    ) -> float:
        if not query or not text:
            return 0.0
        query_words = set(
            query.split()
        )
        text_words = set(
            text.split()
        )
        if not query_words:
            return 0.0
        overlap = (
            query_words
            & text_words
        )
        score = (
            len(overlap)
            / len(query_words)
        )
        # Exact phrase boost
        if query in text:
            score += 0.5
        return score
    # MEMORY SUMMARY
    def memory_summary(
        self
    ) -> Dict[str, Any]:
        return {
            "working_memory_count":
            len(
                working_memory.memories
            ),
            "episodic_memory_count":
            len(
                episodic_memory.episodes
            ),
            "semantic_memory_count":
            len(
                semantic_memory.nodes
            ),
            "pattern_count":
            len(
                pattern_engine.patterns
            ),
            "timeline_entries":
            len(
                timeline_engine.timeline
            ),
        }
    # CLEAR
    def clear_all_retrieval_cache(
        self
    ):
        logger.info(
            "Retrieval cache cleared"
        )

# GLOBAL ENGINE

retrieval_engine = RetrievalEngine()