"""Phase 2: Validity scope — concept-level invalidation per simulator.

Strictly isolated per simulator, selective by affected_concepts.
"""
from __future__ import annotations

from typing import List, Dict, Any

from kernel.utils.logger import get_child_logger

logger = get_child_logger("validity")

def _find_concepts_for_node(node) -> List[str]:
    md = getattr(node, "metadata", {}) or {}
    obs = md.get("observation", {}) or {}
    # consolidated nodes carry affected_concepts directly (materialized view)
    if isinstance(md, dict) and md.get("affected_concepts"):
        try:
            return sorted(set(md.get("affected_concepts") or []))
        except Exception:
            pass
    # derive from scenario keys + signals
    keys: List[str] = []
    scen = obs.get("scenario", {}) if isinstance(obs, dict) else {}
    if isinstance(scen, dict):
        keys.extend(str(k).lower() for k in scen.keys())
    sigs = obs.get("signals", []) if isinstance(obs, dict) else []
    # also premise content fallback
    content = (getattr(node, "content", "") or "").lower()
    # map keys/sigs to concepts via ontology-aware registry
    try:
        from kernel.schemas.simulation_schema import _load_ontology_concepts
        registry = _load_ontology_concepts()
        from pathlib import Path as _P
        out: set[str] = set()
        for k in keys:
            kl = str(k).lower()
            for mod, concepts in registry.items():
                ml = mod.lower()
                if kl == ml or _P(ml).stem == kl or kl in concepts:
                    out.update(concepts)
        for s in sigs:
            s_low = str(s).lower()
            for mod, concepts in registry.items():
                ml = mod.lower()
                if s_low == ml or _P(ml).stem == s_low or s_low in concepts:
                    out.update(concepts)
        # premise keywords
        if "population" in content:
            out.update(["population_growth", "mortality"])
        if "wealth" in content:
            out.add("wealth")
        return sorted(out) or ["population_growth"]
    except Exception:
        return ["population_growth"]


def mark_stale_findings(simulator: str, new_version_id: str) -> List[str]:
    from kernel.simulation_version import affected_by
    from kernel.persistence.db import kernel_db
    from kernel.memory.semantic_memory import semantic_memory
    from kernel.memory.memory_engine import memory_engine
    try:
        from kernel.simulator_registry import sim_topic
        topic = sim_topic(simulator)
    except Exception:
        topic = "popu_sim" if simulator == "popula_dyn" else f"sim_{simulator}"
    new_ver = kernel_db.load_simulation_version(new_version_id, simulator=simulator)
    if not new_ver:
        new_ver = kernel_db.load_simulation_version(new_version_id)
    if not new_ver:
        return []
    new_concepts = new_ver.get("affected_concepts", []) or []
    if not new_concepts:
        logger.info(f"validity: {simulator} {new_version_id} no affected concepts → no invalidation")
        return []
    invalidated: List[str] = []
    for node in list(semantic_memory.search_by_topic(topic)):
        md = node.metadata or {}
        # skip consolidated nodes — handled via materialized-view recompute, not direct invalidation
        if getattr(node, "node_type", "") == "consolidated_observation":
            continue
        if isinstance(md.get("observation"), dict) and md["observation"].get("consolidated"):
            continue
        validity = md.get("validity", {}) if isinstance(md, dict) else {}
        # only ACTIVE and same simulator
        if validity.get("status") == "HISTORICAL":
            continue
        if validity.get("simulator", simulator) != simulator:
            continue
        # same version as new → not stale (current)
        if validity.get("valid_for_version") == new_version_id:
            continue
        find_concepts = _find_concepts_for_node(node)
        if not affected_by(find_concepts, new_concepts):
            continue
        # patch validity
        new_validity = {
            "valid_for_version": validity.get("valid_for_version", "V0"),
            "status": "HISTORICAL",
            "simulator": simulator,
            "invalidated_by": new_version_id,
            "affected_concepts": new_concepts,
        }
        node.metadata["validity"] = new_validity
        node.metadata["observation"] = {**node.metadata.get("observation", {}), "validity": new_validity}
        # persist both generic and structured
        try:
            memory_engine.save_object("semantic", node.node_id, node.to_dict())
        except Exception:
            pass
        try:
            kernel_db.save_semantic_node(node.node_id, node.node_type, node.title, node.content, node.concepts, node.tags, node.importance, node.confidence, node.created_at, node.updated_at, node.topic_id, metadata=node.metadata)
        except Exception:
            pass
        invalidated.append(node.node_id)
    if invalidated:
        logger.info(f"validity: marked {len(invalidated)} {simulator} findings HISTORICAL by {new_version_id} concepts={new_concepts}")
        # also persist export
        try:
            from argu_god.engine.topic_store import write_export
            write_export(topic)
        except Exception:
            pass
        # materialized view: recompute consolidated knowledge from remaining ACTIVE evidence
        try:
            from kernel.compression_engine import CompressionEngine
            CompressionEngine().recompute_consolidated(simulator, invalidated_ids=invalidated, new_version_id=new_version_id)
        except Exception as e:
            logger.warning(f"validity: recompute_consolidated failed for {simulator}: {e}")
    else:
        # even if no raw findings invalidated, consolidated sources may have drifted — opportunistic recompute
        try:
            from kernel.compression_engine import CompressionEngine
            CompressionEngine().recompute_consolidated(simulator, invalidated_ids=[], new_version_id=new_version_id)
        except Exception:
            pass
    return invalidated


def active_findings(simulator: str) -> List[Any]:
    from kernel.memory.semantic_memory import semantic_memory
    try:
        from kernel.simulator_registry import sim_topic
        topic = sim_topic(simulator)
    except Exception:
        topic = "popu_sim" if simulator == "popula_dyn" else f"sim_{simulator}"
    out = []
    for n in semantic_memory.search_by_topic(topic):
        v = n.metadata.get("validity", {}) if isinstance(n.metadata, dict) else {}
        if v.get("status", "ACTIVE") == "ACTIVE":
            out.append(n)
    return out
