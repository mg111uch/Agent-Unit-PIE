"""Thin kernel bus: publish_event/signal/observation + subscribe.

Delegates ONLY to existing engines (event_engine, signal_engine,
observation_pipeline.normalize, memory_engine). No engine logic,
no new store (kernel.db via memory_engine). Stdlib + kernel only.
"""
from __future__ import annotations

from typing import Any, Callable, Dict, List, Union

from kernel.events.event_engine import event_engine
from kernel.signals.signal_engine import signal_engine
from kernel.events import event_extractor
from kernel.signals import signal_router
from kernel.schemas.event_schema import EventSchema
from kernel.schemas.signal_schema import SignalSchema

_SUBSCRIBE_KINDS = ("event", "signal")


def subscribe(kind: str, name: str, handler: Callable) -> bool:
    """Register handler for an event_type (kind=event) or signal_type."""
    if kind not in _SUBSCRIBE_KINDS:
        raise ValueError(f"kind must be one of {_SUBSCRIBE_KINDS}")
    if kind == "event":
        event_engine.register_handler(name, handler)
    else:
        # Router-only: publish_signal invokes the router list after
        # emit, so registering in the engine too would fire twice.
        signal_router.register(name, handler)
    return True


def unsubscribe(kind: str, name: str, handler: Callable) -> bool:
    if kind == "event":
        event_engine.unregister_handler(name, handler)
    else:
        signal_router.unregister(name, handler)
    return True


def publish_event(
    event: Union[Dict[str, Any], EventSchema],
    **kw: Any,
) -> EventSchema:
    """Dict -> extractor -> emit; EventSchema -> emit. Returns the event."""
    if isinstance(event, dict):
        event = event_extractor.extract(event)
    return event_engine.emit_event(event, **kw)


def publish_signal(
    signal: Union[Dict[str, Any], SignalSchema],
    **kw: Any,
) -> SignalSchema:
    """Dict -> SignalSchema.create -> emit. Returns the signal."""
    if isinstance(signal, dict):
        d = signal
        signal = SignalSchema.create(
            signal_type=str(d.get("signal_type", "pattern_detected")),
            value=d.get("value"),
            category=str(d.get("category", "general")),
            subtype=str(d.get("subtype", "generic")),
            source_type=str(d.get("source_type", "system")),
            source_id=str(d.get("source_unit_id", "internal")),
            source_name=str(d.get("source_name", "")),
        )
        signal.metrics.confidence = float(d.get("confidence", 0.8))
        signal.metrics.importance = float(d.get("importance", 0.5))
        for key, val in (d.get("metadata", {}) or {}).items():
            signal.metadata.extra[key] = val
    emitted = signal_engine.emit_signal(signal, **kw)
    for handler in signal_router.route(emitted):
        try:
            handler(emitted)
        except Exception:
            pass
    return emitted


def publish_observation(observation: Dict[str, Any]) -> Dict[str, Any]:
    """observation -> normalize -> event + signal. Returns ids + objects."""
    from kernel.observation_pipeline import ObservationPipeline
    normalized = ObservationPipeline().normalize_observation(
        observation or {}
    )
    content = normalized.get("content", {})
    if not isinstance(content, dict):
        content = {"value": content}
    prov = dict((observation or {}).get("metadata", {}) or {})
    event = publish_event({
        "event_type": observation.get("event_type", "observation_created"),
        "title": observation.get("title", "observation"),
        "description": observation.get("description", ""),
        "source_unit_id": normalized.get("unit_id", "unknown_unit"),
        "source_type": "observation",
        "confidence": normalized.get("confidence", 0.5),
        "metadata": {**prov, "observation_id": normalized["observation_id"]},
    })
    signal = publish_signal({
        "signal_type": observation.get("signal_type", "pattern_detected"),
        "value": (observation or {}).get("signal_value", content),
        "category": observation.get("category", "general"),
        "source_unit_id": normalized.get("unit_id", "unknown_unit"),
        "source_type": "observation",
        "confidence": normalized.get("confidence", 0.5),
        "metadata": {**prov, "event_id": event.event_id},
    })
    event.generated_signals.append(signal.signal_id)
    return {
        "observation_id": normalized["observation_id"],
        "event": event,
        "signal": signal,
    }


def stats() -> Dict[str, Any]:
    return {
        "events": event_engine.stats(),
        "signals": signal_engine.stats(),
        "router": signal_router.stats(),
    }
