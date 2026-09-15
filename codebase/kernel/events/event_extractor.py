"""Raw observation dict -> canonical EventSchema (single purpose).

No engine logic, no persistence. Validates the event_type against
kernel/ontology/event_types.py; unknown types keep their name with
category "general" (never invent a canonical type).
Stdlib + schemas only.
"""
from __future__ import annotations

from typing import Any, Dict, List

from kernel.schemas.event_schema import EventSchema
from kernel.ontology.event_types import (
    is_valid_event_type,
    get_event_category,
)


def extract(raw: Dict[str, Any]) -> EventSchema:
    """Build a canonical EventSchema from a raw observation dict.

    Accepted keys: event_type, title, description, source_unit_id,
    source_type, confidence, importance, urgency, tags, metadata,
    participants [{unit_id, unit_type, role}], evidence [str].
    """
    raw = raw or {}
    event_type = str(raw.get("event_type", "observation_created"))
    category = get_event_category(event_type)
    if not is_valid_event_type(event_type):
        category = raw.get("category", "general")
    event = EventSchema.create(
        event_type=event_type,
        title=str(raw.get("title", event_type)),
        description=str(raw.get("description", "")),
        category=category,
        subtype=str(raw.get("subtype", "generic")),
        source_type=str(raw.get("source_type", "system")),
        source_id=str(raw.get("source_unit_id", "internal")),
        source_name=str(raw.get("source_name", "")),
    )
    metrics = raw.get("metrics", {})
    event.metrics.confidence = float(
        raw.get("confidence", metrics.get("confidence", 0.8))
    )
    event.metrics.importance = float(
        raw.get("importance", metrics.get("importance", 0.5))
    )
    event.metrics.urgency = float(
        raw.get("urgency", metrics.get("urgency", 0.3))
    )
    for i, tag in enumerate(raw.get("tags", []) or []):
        event.metadata.labels[f"tag_{i}"] = str(tag)
    event.metadata.extra.update(raw.get("metadata", {}) or {})
    for p in raw.get("participants", []) or []:
        if isinstance(p, dict) and p.get("unit_id"):
            event.add_participant(
                p["unit_id"],
                p.get("unit_type", "unknown"),
                p.get("role", "participant"),
            )
    for e in raw.get("evidence", []) or []:
        event.add_evidence("observation", str(e))
    return event


def extract_many(items: List[Dict[str, Any]]) -> List[EventSchema]:
    return [extract(item) for item in items or []]
