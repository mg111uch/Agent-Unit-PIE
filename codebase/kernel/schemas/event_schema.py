from __future__ import annotations

from dataclasses import dataclass, field, asdict
from typing import Dict, List, Any, Optional
from datetime import datetime
import uuid


def generate_id(prefix: str = "event") -> str:
    return f"{prefix}_{uuid.uuid4().hex[:12]}"


def utc_now() -> str:
    return datetime.utcnow().isoformat()


# =========================================================
# EVENT SOURCE
# =========================================================

@dataclass
class EventSource:
    source_type: str
    source_id: str

    source_name: str = ""

    confidence: float = 1.0


# =========================================================
# EVENT PARTICIPANT
# =========================================================

@dataclass
class EventParticipant:
    unit_id: str
    unit_type: str

    role: str = "participant"

    impact_score: float = 0.0


# =========================================================
# EVENT LOCATION
# =========================================================

@dataclass
class EventLocation:
    location_id: str = ""
    name: str = ""

    latitude: Optional[float] = None
    longitude: Optional[float] = None

    region: Optional[str] = None
    country: Optional[str] = None


# =========================================================
# EVENT METRICS
# =========================================================

@dataclass
class EventMetrics:
    severity: float = 0.0
    importance: float = 0.0
    confidence: float = 1.0

    economic_impact: float = 0.0
    social_impact: float = 0.0
    political_impact: float = 0.0


# =========================================================
# EVENT EVIDENCE
# =========================================================

@dataclass
class EventEvidence:
    evidence_id: str
    evidence_type: str

    content: str = ""

    source_ref: str = ""

    confidence: float = 1.0

    metadata: Dict[str, Any] = field(default_factory=dict)


# =========================================================
# EVENT RELATION
# =========================================================

@dataclass
class EventRelation:
    related_event_id: str
    relation_type: str

    strength: float = 1.0


# =========================================================
# EVENT METADATA
# =========================================================

@dataclass
class EventMetadata:
    created_at: str = field(default_factory=utc_now)
    updated_at: str = field(default_factory=utc_now)

    created_by: str = "system"

    labels: Dict[str, str] = field(default_factory=dict)

    tags: List[str] = field(default_factory=list)

    extra: Dict[str, Any] = field(default_factory=dict)


# =========================================================
# MAIN EVENT SCHEMA
# =========================================================

@dataclass
class EventSchema:
    event_id: str
    event_type: str

    title: str = ""
    description: str = ""

    category: str = "general"
    subtype: str = "generic"

    timestamp: str = field(default_factory=utc_now)

    start_time: Optional[str] = None
    end_time: Optional[str] = None

    source: Optional[EventSource] = None

    participants: List[EventParticipant] = field(default_factory=list)

    location: Optional[EventLocation] = None

    metrics: EventMetrics = field(default_factory=EventMetrics)

    evidence: List[EventEvidence] = field(default_factory=list)

    relations: List[EventRelation] = field(default_factory=list)

    generated_signals: List[str] = field(default_factory=list)

    metadata: EventMetadata = field(default_factory=EventMetadata)

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
        event_type: str,
        title: str = "",
        description: str = "",
        category: str = "general",
        subtype: str = "generic",
        source_type: str = "system",
        source_id: str = "internal",
        source_name: str = ""
    ) -> "EventSchema":

        return cls(
            event_id=generate_id(event_type),
            event_type=event_type,
            title=title,
            description=description,
            category=category,
            subtype=subtype,
            source=EventSource(
                source_type=source_type,
                source_id=source_id,
                source_name=source_name
            )
        )

    # -----------------------------------------------------
    # PARTICIPANTS
    # -----------------------------------------------------

    def add_participant(
        self,
        unit_id: str,
        unit_type: str,
        role: str = "participant",
        impact_score: float = 0.0
    ):

        self.participants.append(
            EventParticipant(
                unit_id=unit_id,
                unit_type=unit_type,
                role=role,
                impact_score=impact_score
            )
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
            EventEvidence(
                evidence_id=generate_id("evidence"),
                evidence_type=evidence_type,
                content=content,
                source_ref=source_ref,
                confidence=confidence,
                metadata=metadata or {}
            )
        )

    # -----------------------------------------------------
    # RELATIONS
    # -----------------------------------------------------

    def add_relation(
        self,
        related_event_id: str,
        relation_type: str,
        strength: float = 1.0
    ):

        self.relations.append(
            EventRelation(
                related_event_id=related_event_id,
                relation_type=relation_type,
                strength=strength
            )
        )

    # -----------------------------------------------------
    # SIGNALS
    # -----------------------------------------------------

    def add_generated_signal(self, signal_id: str):

        if signal_id not in self.generated_signals:
            self.generated_signals.append(signal_id)

    # -----------------------------------------------------
    # TAGS
    # -----------------------------------------------------

    def add_tag(self, tag: str):

        if tag not in self.metadata.tags:
            self.metadata.tags.append(tag)

    # -----------------------------------------------------
    # LOCATION
    # -----------------------------------------------------

    def set_location(
        self,
        name: str,
        location_id: str = "",
        latitude: Optional[float] = None,
        longitude: Optional[float] = None,
        region: Optional[str] = None,
        country: Optional[str] = None
    ):

        self.location = EventLocation(
            location_id=location_id,
            name=name,
            latitude=latitude,
            longitude=longitude,
            region=region,
            country=country
        )

    # -----------------------------------------------------
    # STATUS
    # -----------------------------------------------------

    def deactivate(self):

        self.active = False
        self.metadata.updated_at = utc_now()

    def update_timestamp(self):

        self.metadata.updated_at = utc_now()