"""Policy experiment registry: every run = full lineage record.

Record: {policy_id, city_id, twin_version, simulator_version (sim@commit),
baseline_id, parameters, hypothesis_id, seed, results, confidence,
validation}. Persisted via memory_engine (kernel.db only, tmp in smoke).
"""
from __future__ import annotations

from typing import Any, Dict, Optional


def record_experiment(
    policy_id: str,
    city_id: str,
    twin_version: str,
    simulator_version: str,
    baseline_id: str,
    parameters: Dict[str, Any],
    hypothesis_id: str,
    seed: int,
    results: Dict[str, Any],
    confidence: float,
    validation: Dict[str, Any],
) -> Dict[str, Any]:
    exp_id = f"pex_{city_id}_{policy_id[:12]}_s{seed}"
    return {
        "exp_id": exp_id,
        "policy_id": policy_id,
        "city_id": city_id,
        "twin_version": twin_version,
        "simulator_version": simulator_version,
        "baseline_id": baseline_id,
        "parameters": parameters,
        "hypothesis_id": hypothesis_id,
        "seed": seed,
        "results": results,
        "confidence": float(confidence),
        "validation": validation,
    }


def save_experiment(record: Dict[str, Any], engine: Any = None) -> str:
    if engine is None:
        from kernel.memory.memory_engine import memory_engine as engine
    return engine.save_object("policy_experiment", record["exp_id"], record)


def load_experiment(exp_id: str, engine: Any = None) -> Optional[Dict[str, Any]]:
    if engine is None:
        from kernel.memory.memory_engine import memory_engine as engine
    return engine.load_object("policy_experiment", exp_id)


def save_finding(finding_id: str, record: Dict[str, Any], engine: Any = None) -> str:
    """Kernel finding, finding-only: one memory object, no other writes."""
    if engine is None:
        from kernel.memory.memory_engine import memory_engine as engine
    return engine.save_object("finding", finding_id, record)
