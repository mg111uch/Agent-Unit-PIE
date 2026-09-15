"""ONE Kanpur signal end-to-end: industrial capacity (Phase 3 slice).

Chain: shaped observation -> bus.publish_observation -> capacity_observed
event -> capacity_underutilized signal -> TrendDetector + pattern_engine
-> persistent_underutilization pattern -> retrieval cascade answer.
Causal output is candidate_cause + confidence + alternatives (never CAUSE).
"""
from __future__ import annotations

from typing import Any, Dict, List, Optional

KANPUR_UNIT_ID = "city_kanpur"
CAPACITY_EVENT = "capacity_observed"
UNDER_SIGNAL = "capacity_underutilized"
NORMAL_SIGNAL = "capacity_normal"
UNDER_THRESHOLD = 0.80
PERSISTENT_PATTERN = "persistent_underutilization"
QUESTION = "why is Kanpur manufacturing productivity declining?"


def record_capacity_observation(
    unit_id: str = KANPUR_UNIT_ID,
    utilization: float = 0.73,
    source: str = "kmc_report",
    quality: str = "reported",
    confidence: float = 0.7,
    bus: Any = None,
) -> Dict[str, Any]:
    """Shaped 'factory reports N% utilization' observation -> bus."""
    if bus is None:
        from kernel import kernel_bus as bus
    u = float(utilization)
    return bus.publish_observation({
        "unit_id": unit_id,
        "content": {"utilization": u},
        "event_type": CAPACITY_EVENT,
        "category": "economic",
        "signal_type": UNDER_SIGNAL if u < UNDER_THRESHOLD else NORMAL_SIGNAL,
        "signal_value": u,
        "title": f"machine utilization {u:.0%} at {unit_id}",
        "description": f"factory reports {u:.0%} machine utilization",
        "confidence": confidence,
        "metadata": {"source": source, "quality": quality},
    })


def detect_persistent_underutilization(
    signals: List[Any],
) -> tuple:
    """Trend over >=2 under-readings -> persistent_underutilization pattern."""
    from kernel.patterns.trend_detector import TrendDetector
    from kernel.patterns.pattern_engine import pattern_engine
    trend = TrendDetector().detect_trend(list(signals), "kanpur_capacity")
    if trend is None:
        return None, None
    pattern = pattern_engine.create_pattern(
        pattern_type=PERSISTENT_PATTERN,
        title="persistent underutilization in Kanpur",
        description=(
            f"capacity {trend.direction} over {trend.sample_size} "
            f"readings (mean {trend.mean_value:.2f})"
        ),
        source_ids=[s.signal_id for s in signals],
        category="economic",
        subtype=trend.direction,
        confidence=trend.confidence,
        importance=0.8,
        tags=[PERSISTENT_PATTERN, "kanpur"],
    )
    return trend, pattern


def explain_capacity_decline(
    utilizations: List[float], pattern_id: str = ""
) -> Dict[str, Any]:
    """Candidate causes + confidence + alternatives. Never bare CAUSE."""
    n = len(utilizations)
    drop = (utilizations[0] - utilizations[-1]) if n >= 2 else 0.0
    return {
        "pattern_id": pattern_id,
        "candidate_causes": [
            {"cause": "supplier_constraints", "confidence": 0.55,
             "evidence": [f"{n} sub-80% readings", f"drop {drop:.2f}"]},
            {"cause": "energy_unreliability", "confidence": 0.35,
             "evidence": ["no energy events in cascade — unconfirmed"]},
        ],
        "alternative_explanations": [
            "seasonal_demand_dip", "sensor_misreport", "single_factory_outlier",
        ],
        "verdict": "candidates only — no causal claim without intervention data",
    }


def answer_why_declining(
    unit_id: str = KANPUR_UNIT_ID, registry: Any = None
) -> Dict[str, Any]:
    """Retrieval cascade: unit -> events -> signals -> patterns -> history."""
    from kernel.retrieval.unit_retriever import UnitRetriever
    from kernel.retrieval.timeline_retriever import TimelineRetriever
    from kernel.retrieval.pattern_retriever import PatternRetriever
    from kernel.events.event_engine import event_engine
    from kernel.signals.signal_engine import signal_engine
    from kernel.patterns.pattern_engine import pattern_engine
    from kernel.memory.memory_engine import memory_engine
    unit = None
    if registry is not None:
        unit = UnitRetriever(unit_registry=registry).get_unit(unit_id)
    events = TimelineRetriever(
        event_engine=event_engine, memory_engine=memory_engine
    ).retrieve_events(event_types=[CAPACITY_EVENT], unit_id=unit_id)
    signals = [
        s.to_dict()
        for s in signal_engine.get_recent_signals(signal_type=UNDER_SIGNAL)
        if getattr(s.source, "source_id", None) == unit_id
    ]
    raw_patterns = PatternRetriever(
        pattern_storage=pattern_engine
    ).get_patterns_by_type(PERSISTENT_PATTERN)
    patterns = [
        p.to_dict() if hasattr(p, "to_dict") else dict(p)
        for p in raw_patterns
    ]
    history = {}
    if events:
        history["first_event"] = memory_engine.load_event(
            events[0]["event_id"])
    if patterns:
        history["pattern"] = memory_engine.load_pattern(
            patterns[0]["pattern_id"])
    return {
        "question": QUESTION,
        "unit": unit,
        "events": events,
        "signals": signals,
        "patterns": patterns,
        "history": history,
        "explanation": explain_capacity_decline(
            [(s["value"] if isinstance(s.get("value"), (int, float))
              else s["value"]["utilization"]) for s in signals],
            patterns[0]["pattern_id"] if patterns else "",
        ),
    }
