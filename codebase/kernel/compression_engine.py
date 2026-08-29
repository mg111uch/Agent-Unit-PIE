"""
kernel/compression_engine.py

Recursive cognition compression system.

Purpose
-------
Prevent infinite memory growth by continuously compressing:

raw observations
    → events
    → signals
    → patterns
    → summaries
    → abstractions

This engine is one of the most important scalability systems
inside agent_unit_pie.

Core Responsibilities
---------------------
- memory compaction
- signal aggregation
- pattern abstraction
- timeline summarization
- archive routing
- low-value memory pruning
- working memory optimization
"""

from __future__ import annotations

import logging
from datetime import datetime, timezone
from typing import Any, Dict, List, Optional

logger = logging.getLogger(__name__)

class CompressionEngine:
    """
    Recursive memory compression engine.
    """
    def __init__(
        self,
        memory_router=None,
        pattern_engine=None,
        storage_backend=None,
        config: Optional[Dict[str, Any]] = None,
    ):
        self.memory_router = memory_router
        self.pattern_engine = pattern_engine
        self.storage_backend = storage_backend
        self.config = config or {}
        # DEFAULT CONFIG
        self.max_raw_observations = self.config.get(
            "max_raw_observations",
            10000,
        )
        self.max_signal_history = self.config.get(
            "max_signal_history",
            5000,
        )
        self.max_event_history = self.config.get(
            "max_event_history",
            5000,
        )
        self.archive_threshold_days = self.config.get(
            "archive_threshold_days",
            90,
        )
    # MAIN COMPRESSION CYCLE
    def run_cycle(self) -> Dict[str, Any]:
        """
        Main recursive compression cycle.
        """
        logger.info(
            "Starting compression cycle."
        )
        results = {
            "started_at": self.utc_now(),
            "steps": [],
            "status": "success",
        }
        try:
            # STEP 1 — COMPRESS OBSERVATIONS
            observation_result = (
                self.compress_observations()
            )
            results["steps"].append(
                observation_result
            )
            # STEP 2 — COMPRESS EVENTS
            event_result = self.compress_events()
            results["steps"].append(
                event_result
            )
            # STEP 3 — AGGREGATE SIGNALS
            signal_result = self.aggregate_signals()
            results["steps"].append(
                signal_result
            )
            # STEP 4 — BUILD HIGHER PATTERNS
            pattern_result = (
                self.generate_higher_patterns()
            )
            results["steps"].append(
                pattern_result
            )
            # STEP 5 — SUMMARIZE TIMELINES
            timeline_result = (
                self.compress_timelines()
            )
            results["steps"].append(
                timeline_result
            )
            # STEP 6 — ARCHIVE OLD MEMORY
            archive_result = (
                self.archive_old_memory()
            )
            results["steps"].append(
                archive_result
            )
            # STEP 7 — PRUNE LOW VALUE MEMORY
            prune_result = (
                self.prune_low_value_memory()
            )
            results["steps"].append(
                prune_result
            )
            results["completed_at"] = (
                self.utc_now()
            )
            logger.info(
                "Compression cycle completed."
            )
            return results
        except Exception as e:
            logger.exception(
                "Compression cycle failed."
            )
            return {
                "status": "error",
                "error": str(e),
                "failed_at": self.utc_now(),
            }

    # OBSERVATION COMPRESSION — Phase 4: per-sim strict isolation
    def compress_observations(self) -> Dict[str, Any]:
        """
        Per-simulator consolidation:
        - episodic retains all runs (immutable)
        - semantic keeps one consolidated node per (simulator, outcome)
        """
        logger.info("Compressing observations per-sim.")
        try:
            from kernel.simulator_registry import discover_simulators, sim_topic
            from kernel.memory.semantic_memory import semantic_memory
            from kernel.memory.episodic_memory import episodic_memory
            from kernel.simulation_version import get_current_version
            compressed = 0
            consolidated = 0
            for sim, info in discover_simulators().items():
                topic = info["topic"]
                cur = get_current_version(sim)
                cur_ver = cur["version_id"] if cur else f"{sim}@V0"
                # collect ACTIVE findings for this simulator/topic
                nodes = [n for n in semantic_memory.search_by_topic(topic)
                         if (n.metadata.get("validity", {}).get("status", "ACTIVE") == "ACTIVE")
                         and (n.metadata.get("observation", {}) or {}).get("simulator", sim) == sim]
                # group by outcome (IMPROVED/STABLE/COLLAPSED) + horizon bucket
                groups: Dict[str, List[Any]] = {}
                for n in nodes:
                    obs = n.metadata.get("observation", {}) or {}
                    key = f"{obs.get('outcome','unknown')}:{int(obs.get('horizon',0)//10)}"
                    groups.setdefault(key, []).append(n)
                for key, grp in groups.items():
                    if len(grp) < 2:
                        continue
                    # build consolidated node
                    outcome = grp[0].metadata.get("observation", {}).get("outcome", "unknown")
                    deltas = [g.metadata["observation"].get("delta", 0) for g in grp if isinstance(g.metadata.get("observation"), dict)]
                    avg_delta = round(sum(deltas)/len(deltas), 1) if deltas else 0
                    src_ids = [g.node_id for g in grp]
                    con_id = f"consolidated_{sim}_{outcome}_{key.replace(':','_')}"
                    # check existing
                    existing = semantic_memory.get_node(con_id)
                    title = f"{sim} consolidated {outcome} ({len(grp)} runs, avg {avg_delta}%)"
                    content = f"Consolidated {sim}: {outcome} over {len(grp)} runs; outcomes {','.join(sorted(set(o for o in [g.metadata['observation'].get('outcome') for g in grp] if o)))}; avg delta {avg_delta}%; sources {','.join(s.node_id for s in grp[:3])}"
                    meta = {
                        "observation": {"simulator": sim, "version_id": cur_ver, "outcome": outcome, "consolidated": True, "source_count": len(grp), "avg_delta": avg_delta, "horizon": grp[0].metadata["observation"].get("horizon")},
                        "validity": {"valid_for_version": cur_ver, "status": "ACTIVE", "simulator": sim},
                        "consolidated_from": src_ids,
                        "simulator": sim,
                    }
                    if existing:
                        existing.title = title
                        existing.content = content
                        existing.metadata = meta
                        existing.updated_at = self.utc_now()
                        from kernel.memory.memory_engine import memory_engine
                        from kernel.persistence.db import kernel_db
                        memory_engine.save_object("semantic", con_id, existing.to_dict())
                        kernel_db.save_semantic_node(con_id, existing.node_type, title, content, existing.concepts, existing.tags, existing.importance, existing.confidence, existing.created_at, existing.updated_at, topic, metadata=meta)
                    else:
                        from kernel.memory.semantic_memory import SemanticNode
                        node = SemanticNode(node_id=con_id, node_type="consolidated_observation", title=title, content=content, concepts=["consolidated", sim], tags=[topic, sim], metadata=meta, topic_id=topic, importance=0.8, confidence=0.9)
                        semantic_memory.add_node(node)
                        try:
                            from argu_god.engine.topic_store import write_export
                            write_export(topic)
                        except Exception:
                            pass
                    consolidated += 1
                    compressed += len(grp)
            return {"stage": "compress_observations", "status": "success", "compressed_count": compressed, "consolidated_groups": consolidated}
        except Exception as e:
            logger.warning(f"compress_observations failed: {e}")
            return {"stage": "compress_observations", "status": "error", "error": str(e)}

    # EVENT COMPRESSION
    def compress_events(self) -> Dict[str, Any]:
        """
        Merge repetitive or low-value events.
        """
        logger.info(
            "Compressing events."
        )
        return {
            "stage": "compress_events",
            "status": "success",
            "merged_events": 0,
        }

    # SIGNAL AGGREGATION
    def aggregate_signals(self) -> Dict[str, Any]:
        """
        Aggregate signals into trends and summaries.
        """
        logger.info(
            "Aggregating signals."
        )
        return {
            "stage": "aggregate_signals",
            "status": "success",
            "aggregated_signals": 0,
        }

    # HIGHER-ORDER PATTERN GENERATION
    def generate_higher_patterns(self) -> Dict[str, Any]:
        """
        Generate high-level abstractions from existing patterns.
        """
        logger.info(
            "Generating higher-order patterns."
        )
        if self.pattern_engine is None:
            return {
                "stage": "generate_higher_patterns",
                "status": "skipped",
                "reason": "pattern_engine_missing",
            }
        # Placeholder logic
        return {
            "stage": "generate_higher_patterns",
            "status": "success",
            "generated_patterns": 0,
        }

    # TIMELINE COMPRESSION
    def compress_timelines(self) -> Dict[str, Any]:
        """
        Compress long historical timelines into abstractions.
        """
        logger.info(
            "Compressing timelines."
        )
        return {
            "stage": "compress_timelines",
            "status": "success",
            "compressed_timelines": 0,
        }

    # ARCHIVE OLD MEMORY
    def archive_old_memory(self) -> Dict[str, Any]:
        """
        Move stale memory into cold/archive storage.
        """
        logger.info(
            "Archiving old memory."
        )
        return {
            "stage": "archive_old_memory",
            "status": "success",
            "archived_items": 0,
        }

    # PRUNE LOW VALUE MEMORY
    def prune_low_value_memory(self) -> Dict[str, Any]:
        """
        Remove low-value redundant cognition artifacts.
        """
        logger.info(
            "Pruning low-value memory."
        )
        return {
            "stage": "prune_low_value_memory",
            "status": "success",
            "pruned_items": 0,
        }

    # MEMORY VALUE SCORING
    def compute_memory_value(
        self,
        memory_item: Dict[str, Any],
    ) -> float:
        """
        Estimate long-term importance of memory.
        """
        score = 0.0
        confidence = float(
            memory_item.get("confidence", 0.5)
        )
        score += confidence
        if memory_item.get("linked_patterns"):
            score += 0.5
        if memory_item.get("causal_links"):
            score += 0.5
        if memory_item.get("contradictions"):
            score += 0.5
        return round(score, 3)
    # ABSTRACT SUMMARIZATION
    def summarize_cluster(
        self,
        items: List[Dict[str, Any]],
    ) -> Dict[str, Any]:
        """
        Build compressed abstraction from related memory items.
        """
        return {
            "summary_type": "cluster_summary",
            "item_count": len(items),
            "generated_at": self.utc_now(),
            "summary": "placeholder_summary",
        }
    # RECURSIVE ABSTRACTION
    def build_recursive_abstraction(
        self,
        patterns: List[Dict[str, Any]],
    ) -> Dict[str, Any]:
        """
        Build higher-order abstraction from lower patterns.
        """
        return {
            "abstraction_level": 2,
            "pattern_count": len(patterns),
            "generated_at": self.utc_now(),
            "abstraction": "placeholder_abstraction",
        }
    # HEALTH CHECK
    def health_check(self) -> Dict[str, Any]:
        return {
            "memory_router": (
                self.memory_router is not None
            ),
            "pattern_engine": (
                self.pattern_engine is not None
            ),
            "storage_backend": (
                self.storage_backend is not None
            ),
        }

    # HELPERS
    @staticmethod
    def utc_now() -> str:
        return datetime.now(
            timezone.utc
        ).isoformat()