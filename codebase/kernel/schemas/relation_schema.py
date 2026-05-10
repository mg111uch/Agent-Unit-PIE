from __future__ import annotations

from dataclasses import dataclass, field, asdict
from typing import Dict, List, Any, Optional
from datetime import datetime
import uuid


def generate_id(prefix: str = "relation") -> str:
    return f"{prefix}_{uuid.uuid4().hex[:12]}"


def utc_now() -> str:
    return datetime.utcnow().isoformat()


# =========================================================
# RELATION ENDPOINT
# =========================================================

@dataclass
class RelationEndpoint:
    unit_id: str
    unit_type: str

    role: str = "entity"


# =========================================================
# RELATION METRICS
# =========================================================

@dataclass
class RelationMetrics:
    strength: float = 1.0
    confidence: float = 1.0

    stability: float = 1.0
    volatility: float = 0.0

    interaction_frequency: float = 0.0


# =========================================================
# RELATION EVIDENCE
# =========================================================

@dataclass
class RelationEvidence:
    evidence_id: str
    evidence_type: str

    content: str = ""

    source_ref: str = ""

    confidence: float = 1.0

    timestamp: str = field(default_factory=utc_now)

    metadata: Dict[str, Any] = field(default_factory=dict)


# =========================================================
# RELATION TIMELINE
# =========================================================

@dataclass
class RelationTimeline:
    created_at: str = field(default_factory=utc_now)

    started_at: Optional[str] = None
    ended_at: Optional[str] = None

    last_interaction_at: Optional[str] = None


# =========================================================
# RELATION CONTEXT
# =========================================================

@dataclass
class RelationContext:
    domain: str = "general"

    location: Optional[str] = None

    related_events: List[str] = field(default_factory=list)
    related_signals: List[str] = field(default_factory=list)
    related_patterns: List[str] = field(default_factory=list)

    tags: List[str] = field(default_factory=list)


# =========================================================
# RELATION METADATA
# =========================================================

@dataclass
class RelationMetadata:
    created_by: str = "system"

    labels: Dict[str, str] = field(default_factory=dict)

    extra: Dict[str, Any] = field(default_factory=dict)

    version: int = 1


# =========================================================
# MAIN RELATION SCHEMA
# =========================================================

@dataclass
class RelationSchema:
    relation_id: str

    relation_type: str

    source: RelationEndpoint
    target: RelationEndpoint

    direction: str = "bidirectional"

    description: str = ""

    metrics: RelationMetrics = field(default_factory=RelationMetrics)

    timeline: RelationTimeline = field(default_factory=RelationTimeline)

    context: RelationContext = field(default_factory=RelationContext)

    evidence: List[RelationEvidence] = field(default_factory=list)

    metadata: RelationMetadata = field(default_factory=RelationMetadata)

    active: bool = True

    # -----------------------------------------------------
    # SERIALIZATION
    # -----------------------------------------------------

    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)

    # -----------------------------------------------------
    # FACTORY
    # -----------------------------------------------------

    @classmethod
    def create(
        cls,
        relation_type: str,

        source_unit_id: str,
        source_unit_type: str,

        target_unit_id: str,
        target_unit_type: str,

        direction: str = "bidirectional",
        description: str = ""
    ) -> "RelationSchema":

        return cls(
            relation_id=generate_id(relation_type),

            relation_type=relation_type,

            source=RelationEndpoint(
                unit_id=source_unit_id,
                unit_type=source_unit_type
            ),

            target=RelationEndpoint(
                unit_id=target_unit_id,
                unit_type=target_unit_type
            ),

            direction=direction,
            description=description
        )

    # -----------------------------------------------------
    # EVIDENCE
    # -----------------------------------------------------

    def add_evidence(
        self,
        evidence_type: str,
        content: str,
        source_ref: str = "",
        confidence: float = 1.0,
        metadata: Optional[Dict[str, Any]] = None
    ):

        self.evidence.append(
            RelationEvidence(
                evidence_id=generate_id("evidence"),
                evidence_type=evidence_type,
                content=content,
                source_ref=source_ref,
                confidence=confidence,
                metadata=metadata or {}
            )
        )

    # -----------------------------------------------------
    # TAGS
    # -----------------------------------------------------

    def add_tag(self, tag: str):

        if tag not in self.context.tags:
            self.context.tags.append(tag)

    # -----------------------------------------------------
    # RELATED REFERENCES
    # -----------------------------------------------------

    def add_related_event(self, event_id: str):

        if event_id not in self.context.related_events:
            self.context.related_events.append(event_id)

    def add_related_signal(self, signal_id: str):

        if signal_id not in self.context.related_signals:
            self.context.related_signals.append(signal_id)

    def add_related_pattern(self, pattern_id: str):

        if pattern_id not in self.context.related_patterns:
            self.context.related_patterns.append(pattern_id)

    # -----------------------------------------------------
    # METRICS
    # -----------------------------------------------------

    def update_strength(self, strength: float):

        self.metrics.strength = max(0.0, min(1.0, strength))

    def update_confidence(self, confidence: float):

        self.metrics.confidence = max(0.0, min(1.0, confidence))

    # -----------------------------------------------------
    # TIMELINE
    # -----------------------------------------------------

    def mark_interaction(self):

        self.timeline.last_interaction_at = utc_now()

    def deactivate(self):

        self.active = False
        self.timeline.ended_at = utc_now()