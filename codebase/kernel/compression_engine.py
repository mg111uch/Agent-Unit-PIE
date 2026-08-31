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

    # OBSERVATION COMPRESSION — Phase 4: per-sim strict isolation + materialized view
    def compress_observations(self) -> Dict[str, Any]:
        """
        Per-simulator consolidation (materialized view):
        - episodic retains all runs (immutable)
        - semantic keeps one consolidated node per (simulator, outcome, horizon_bucket)
        - consolidated nodes carry simulator, source_findings, source_versions, affected_concepts, validity, derived_at
        - excluded: consolidated_observation nodes themselves (to avoid self-grouping)
        """
        logger.info("Compressing observations per-sim.")
        try:
            from kernel.simulator_registry import discover_simulators
            from kernel.memory.semantic_memory import semantic_memory
            from kernel.simulation_version import get_current_version
            compressed = 0
            consolidated = 0
            for sim, info in discover_simulators().items():
                topic = info["topic"]
                cur = get_current_version(sim)
                cur_ver = cur["version_id"] if cur else f"{sim}@V0"
                # collect ACTIVE raw findings (exclude consolidated nodes to avoid double counting)
                nodes = [n for n in semantic_memory.search_by_topic(topic)
                         if (n.metadata.get("validity", {}).get("status", "ACTIVE") == "ACTIVE")
                         and (n.metadata.get("observation", {}) or {}).get("simulator", sim) == sim
                         and n.node_type != "consolidated_observation"
                         and not (n.metadata.get("observation", {}) or {}).get("consolidated")]
                # group by outcome + horizon bucket
                groups: Dict[str, List[Any]] = {}
                for n in nodes:
                    obs = n.metadata.get("observation", {}) or {}
                    key = f"{obs.get('outcome','unknown')}:{int(obs.get('horizon',0)//10)}"
                    groups.setdefault(key, []).append(n)
                for key, grp in groups.items():
                    if len(grp) < 2:
                        continue
                    outcome = grp[0].metadata.get("observation", {}).get("outcome", "unknown")
                    deltas = [g.metadata["observation"].get("delta", 0) for g in grp if isinstance(g.metadata.get("observation"), dict)]
                    avg_delta = round(sum(deltas)/len(deltas), 1) if deltas else 0
                    src_ids = [g.node_id for g in grp]
                    src_vers = sorted(set((g.metadata.get("observation", {}) or {}).get("version_id") or g.metadata.get("validity", {}).get("valid_for_version", "") for g in grp if ((g.metadata.get("observation", {}) or {}).get("version_id") or g.metadata.get("validity", {}).get("valid_for_version"))))
                    # affected_concepts = union of source finding concepts
                    try:
                        from kernel.validity import _find_concepts_for_node
                        aff: set[str] = set()
                        for g in grp:
                            aff.update(_find_concepts_for_node(g))
                        affected = sorted(aff)
                    except Exception:
                        affected = []
                    con_id = f"consolidated_{sim}_{outcome}_{key.replace(':','_')}"
                    existing = semantic_memory.get_node(con_id)
                    title = f"{sim} consolidated {outcome} ({len(grp)} runs, avg {avg_delta}%)"
                    content = f"Consolidated {sim}: {outcome} over {len(grp)} runs; outcomes {','.join(sorted(set(o for o in [g.metadata['observation'].get('outcome') for g in grp] if o)))}; avg delta {avg_delta}%; sources {','.join(s.node_id for s in grp[:3])}"
                    meta = {
                        "observation": {"simulator": sim, "version_id": cur_ver, "outcome": outcome, "consolidated": True, "source_count": len(grp), "avg_delta": avg_delta, "horizon": grp[0].metadata["observation"].get("horizon")},
                        "validity": {"valid_for_version": cur_ver, "status": "ACTIVE", "simulator": sim},
                        "consolidated_from": src_ids,
                        "source_findings": src_ids,
                        "source_versions": src_vers,
                        "affected_concepts": affected,
                        "simulator": sim,
                        "derived_at": self.utc_now(),
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
                        node = SemanticNode(node_id=con_id, node_type="consolidated_observation", title=title, content=content, concepts=["consolidated", sim] + affected[:3], tags=[topic, sim], metadata=meta, topic_id=topic, importance=0.8, confidence=0.9)
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

    def recompute_consolidated(self, simulator: str, invalidated_ids: Optional[List[str]] = None, new_version_id: Optional[str] = None) -> Dict[str, Any]:
        """Materialized-view rebuild: after invalidation, prune sources and recompute or HISTORICAL."""
        try:
            from kernel.simulator_registry import sim_topic
            from kernel.memory.semantic_memory import semantic_memory
            from kernel.memory.memory_engine import memory_engine
            from kernel.persistence.db import kernel_db
            from kernel.simulation_version import get_current_version
            topic = sim_topic(simulator)
            cur = get_current_version(simulator)
            cur_ver = new_version_id or (cur["version_id"] if cur else f"{simulator}@V0")
            invalid_set = set(invalidated_ids or [])
            # also detect HISTORICAL sources via validity status
            # need to inspect consolidated nodes for this sim
            affected_nodes = [n for n in semantic_memory.search_by_topic(topic) if n.node_type == "consolidated_observation" and n.metadata.get("simulator", simulator) == simulator]
            recomputed = 0
            hist = 0
            removed = 0
            for c in list(affected_nodes):
                src_ids: List[str] = c.metadata.get("source_findings") or c.metadata.get("consolidated_from") or []
                if not src_ids:
                    continue
                # if none of sources invalidated and still ACTIVE, skip (no need to recompute)
                if invalid_set and not (set(src_ids) & invalid_set):
                    # also check if any source now HISTORICAL (conservative recompute)
                    has_hist = any((semantic_memory.get_node(sid) and semantic_memory.get_node(sid).metadata.get("validity", {}).get("status") == "HISTORICAL") for sid in src_ids)
                    if not has_hist:
                        continue
                # filter to remaining ACTIVE sources
                remaining: List[Any] = []
                remaining_ids: List[str] = []
                remaining_vers: set[str] = set()
                for sid in src_ids:
                    node = semantic_memory.get_node(sid)
                    if not node:
                        continue
                    if node.metadata.get("validity", {}).get("status") == "HISTORICAL":
                        continue
                    remaining.append(node)
                    remaining_ids.append(sid)
                    v = (node.metadata.get("observation", {}) or {}).get("version_id") or node.metadata.get("validity", {}).get("valid_for_version")
                    if v:
                        remaining_vers.add(v)
                if len(remaining) < 2:
                    # not enough evidence → mark HISTORICAL (keep node for audit, filtered from retrieval)
                    c.metadata["validity"] = {"valid_for_version": c.metadata.get("validity", {}).get("valid_for_version", cur_ver), "status": "HISTORICAL", "simulator": simulator, "invalidated_by": cur_ver, "affected_concepts": c.metadata.get("affected_concepts", [])}
                    c.metadata["observation"] = {**c.metadata.get("observation", {}), "validity": c.metadata["validity"]}
                    c.updated_at = self.utc_now()
                    memory_engine.save_object("semantic", c.node_id, c.to_dict())
                    kernel_db.save_semantic_node(c.node_id, c.node_type, c.title, c.content, c.concepts, c.tags, c.importance, c.confidence, c.created_at, c.updated_at, topic, metadata=c.metadata)
                    hist += 1
                    # if only 0-1 remaining, optionally remove to avoid clutter — keep HISTORICAL for traceability
                    continue
                # recompute from remaining
                deltas = [r.metadata["observation"].get("delta", 0) for r in remaining if isinstance(r.metadata.get("observation"), dict)]
                avg_delta = round(sum(deltas)/len(deltas), 1) if deltas else 0
                outcome = remaining[0].metadata.get("observation", {}).get("outcome", "unknown")
                try:
                    from kernel.validity import _find_concepts_for_node
                    aff: set[str] = set()
                    for r in remaining:
                        aff.update(_find_concepts_for_node(r))
                    affected = sorted(aff)
                except Exception:
                    affected = c.metadata.get("affected_concepts", [])
                c.title = f"{simulator} consolidated {outcome} ({len(remaining)} runs, avg {avg_delta}%)"
                c.content = f"Consolidated {simulator}: {outcome} over {len(remaining)} runs; avg delta {avg_delta}%; sources {','.join(remaining_ids[:3])} (recomputed)"
                c.metadata["source_findings"] = remaining_ids
                c.metadata["consolidated_from"] = remaining_ids
                c.metadata["source_versions"] = sorted(remaining_vers)
                c.metadata["affected_concepts"] = affected
                c.metadata["derived_at"] = self.utc_now()
                c.metadata["validity"] = {"valid_for_version": cur_ver, "status": "ACTIVE", "simulator": simulator}
                c.metadata["observation"] = {**c.metadata.get("observation", {}), "source_count": len(remaining), "avg_delta": avg_delta, "validity": c.metadata["validity"], "version_id": cur_ver}
                c.updated_at = self.utc_now()
                memory_engine.save_object("semantic", c.node_id, c.to_dict())
                kernel_db.save_semantic_node(c.node_id, c.node_type, c.title, c.content, c.concepts, c.tags, c.importance, c.confidence, c.created_at, c.updated_at, topic, metadata=c.metadata)
                recomputed += 1
            if hist or recomputed:
                try:
                    from argu_god.engine.topic_store import write_export
                    write_export(topic)
                except Exception:
                    pass
            return {"stage": "recompute_consolidated", "status": "success", "simulator": simulator, "recomputed": recomputed, "historical": hist, "removed": removed}
        except Exception as e:
            logger.warning(f"recompute_consolidated failed: {e}")
            return {"stage": "recompute_consolidated", "status": "error", "error": str(e)}

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