from __future__ import annotations

from dataclasses import dataclass, field, asdict
from typing import Dict, List, Any, Optional
from datetime import datetime
import uuid


def generate_id(prefix: str = "signal") -> str:
    return f"{prefix}_{uuid.uuid4().hex[:12]}"


def utc_now() -> str:
    return datetime.utcnow().isoformat()


@dataclass
class SignalSource:
    source_type: str
    source_id: str
    source_name: str = ""


@dataclass
class SignalEvidence:
    evidence_id: str
    evidence_type: str
    content: str = ""
    confidence: float = 1.0

    metadata: Dict[str, Any] = field(default_factory=dict)


@dataclass
class SignalContext:
    unit_id: Optional[str] = None
    unit_type: Optional[str] = None

    location: Optional[str] = None
    timeline_ref: Optional[str] = None

    related_units: List[str] = field(default_factory=list)
    related_events: List[str] = field(default_factory=list)

    tags: List[str] = field(default_factory=list)


@dataclass
class SignalMetrics:
    strength: float = 0.0
    intensity: float = 0.0
    frequency: float = 0.0
    volatility: float = 0.0
    confidence: float = 1.0


@dataclass
class SignalMetadata:
    created_at: str = field(default_factory=utc_now)
    updated_at: str = field(default_factory=utc_now)

    created_by: str = "system"

    version: int = 1

    labels: Dict[str, str] = field(default_factory=dict)
    extra: Dict[str, Any] = field(default_factory=dict)


@dataclass
class SignalSchema:
    signal_id: str
    signal_type: str

    value: Any

    category: str = "general"
    subtype: str = "generic"

    timestamp: str = field(default_factory=utc_now)

    source: Optional[SignalSource] = None

    context: SignalContext = field(default_factory=SignalContext)

    metrics: SignalMetrics = field(default_factory=SignalMetrics)

    evidence: List[SignalEvidence] = field(default_factory=list)

    metadata: SignalMetadata = field(default_factory=SignalMetadata)

    active: bool = True

    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)

    @classmethod
    def create(
        cls,
        signal_type: str,
        value: Any,
        category: str = "general",
        subtype: str = "generic",
        source_type: str = "system",
        source_id: str = "internal",
        source_name: str = ""
    ) -> "SignalSchema":

        return cls(
            signal_id=generate_id(signal_type),
            signal_type=signal_type,
            value=value,
            category=category,
            subtype=subtype,
            source=SignalSource(
                source_type=source_type,
                source_id=source_id,
                source_name=source_name
            )
        )

    def add_evidence(
        self,
        evidence_type: str,
        content: str,
        confidence: float = 1.0,
        metadata: Optional[Dict[str, Any]] = None
    ):

        self.evidence.append(
            SignalEvidence(
                evidence_id=generate_id("evidence"),
                evidence_type=evidence_type,
                content=content,
                confidence=confidence,
                metadata=metadata or {}
            )
        )

    def add_related_unit(self, unit_id: str):

        if unit_id not in self.context.related_units:
            self.context.related_units.append(unit_id)

    def add_related_event(self, event_id: str):

        if event_id not in self.context.related_events:
            self.context.related_events.append(event_id)

    def add_tag(self, tag: str):

        if tag not in self.context.tags:
            self.context.tags.append(tag)

    def update_confidence(self, confidence: float):
        self.metrics.confidence = max(0.0, min(1.0, confidence))
        self.metadata.updated_at = utc_now()

    def deactivate(self):
        self.active = False
        self.metadata.updated_at = utc_now()