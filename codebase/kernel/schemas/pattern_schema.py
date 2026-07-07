from __future__ import annotations

from dataclasses import dataclass, field, asdict
from typing import Dict, List, Any, Optional
from datetime import datetime
import uuid

def generate_id(prefix: str = "pattern") -> str:
    return f"{prefix}_{uuid.uuid4().hex[:12]}"

def utc_now() -> str:
    return datetime.utcnow().isoformat()

# PATTERN SOURCE

@dataclass
class PatternSource:
    source_type: str
    source_id: str
    source_name: str = ""
    confidence: float = 1.0

# PATTERN SIGNAL REFERENCE

@dataclass
class PatternSignalRef:
    signal_id: str
    signal_type: str
    weight: float = 1.0
    confidence: float = 1.0

# PATTERN EVENT REFERENCE

@dataclass
class PatternEventRef:
    event_id: str
    event_type: str
    weight: float = 1.0

# PATTERN UNIT REFERENCE

@dataclass
class PatternUnitRef:
    unit_id: str
    unit_type: str
    role: str = "participant"
    influence_score: float = 0.0

# PATTERN METRICS

@dataclass
class PatternMetrics:
    confidence: float = 1.0
    strength: float = 0.0
    frequency: float = 0.0
    persistence: float = 0.0
    novelty: float = 0.0
    anomaly_score: float = 0.0
    predictive_score: float = 0.0

# PATTERN TIMELINE

@dataclass
class PatternTimeline:
    detected_at: str = field(default_factory=utc_now)
    first_seen_at: Optional[str] = None
    last_seen_at: Optional[str] = None
    active_window_start: Optional[str] = None
    active_window_end: Optional[str] = None

# PATTERN CAUSAL LINK

@dataclass
class PatternCausalLink:
    target_pattern_id: str
    relation_type: str
    strength: float = 1.0
    confidence: float = 1.0

# PATTERN EVIDENCE

@dataclass
class PatternEvidence:
    evidence_id: str
    evidence_type: str
    content: str = ""
    source_ref: str = ""
    confidence: float = 1.0
    metadata: Dict[str, Any] = field(default_factory=dict)

# PATTERN METADATA

@dataclass
class PatternMetadata:
    created_at: str = field(default_factory=utc_now)
    updated_at: str = field(default_factory=utc_now)
    created_by: str = "system"
    labels: Dict[str, str] = field(default_factory=dict)
    tags: List[str] = field(default_factory=list)
    extra: Dict[str, Any] = field(default_factory=dict)

# MAIN PATTERN SCHEMA

@dataclass
class PatternSchema:
    pattern_id: str
    pattern_type: str
    title: str = ""
    description: str = ""
    category: str = "general"
    subtype: str = "generic"
    source: Optional[PatternSource] = None
    units: List[PatternUnitRef] = field(default_factory=list)
    signals: List[PatternSignalRef] = field(default_factory=list)
    events: List[PatternEventRef] = field(default_factory=list)
    causal_links: List[PatternCausalLink] = field(default_factory=list)
    metrics: PatternMetrics = field(default_factory=PatternMetrics)
    timeline: PatternTimeline = field(default_factory=PatternTimeline)
    evidence: List[PatternEvidence] = field(default_factory=list)
    metadata: PatternMetadata = field(default_factory=PatternMetadata)
    active: bool = True
    # SERIALIZATION
    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)

    # FACTORY
    @classmethod
    def create(
        cls,
        pattern_type: str,
        title: str = "",
        description: str = "",
        category: str = "general",
        subtype: str = "generic",
        source_type: str = "system",
        source_id: str = "internal",
        source_name: str = ""
    ) -> "PatternSchema":
        return cls(
            pattern_id=generate_id(pattern_type),
            pattern_type=pattern_type,
            title=title,
            description=description,
            category=category,
            subtype=subtype,
            source=PatternSource(
                source_type=source_type,
                source_id=source_id,
                source_name=source_name
            )
        )
    # UNIT REFERENCES
    def add_unit(
        self,
        unit_id: str,
        unit_type: str,
        role: str = "participant",
        influence_score: float = 0.0
    ):
        self.units.append(
            PatternUnitRef(
                unit_id=unit_id,
                unit_type=unit_type,
                role=role,
                influence_score=influence_score
            )
        )
    # SIGNAL REFERENCES
    def add_signal(
        self,
        signal_id: str,
        signal_type: str,
        weight: float = 1.0,
        confidence: float = 1.0
    ):
        self.signals.append(
            PatternSignalRef(
                signal_id=signal_id,
                signal_type=signal_type,
                weight=weight,
                confidence=confidence
            )
        )
    # EVENT REFERENCES
    def add_event(
        self,
        event_id: str,
        event_type: str,
        weight: float = 1.0
    ):
        self.events.append(
            PatternEventRef(
                event_id=event_id,
                event_type=event_type,
                weight=weight
            )
        )
    # CAUSAL LINKS
    def add_causal_link(
        self,
        target_pattern_id: str,
        relation_type: str,
        strength: float = 1.0,
        confidence: float = 1.0
    ):
        self.causal_links.append(
            PatternCausalLink(
                target_pattern_id=target_pattern_id,
                relation_type=relation_type,
                strength=strength,
                confidence=confidence
            )
        )
    # EVIDENCE
    def add_evidence(
        self,
        evidence_type: str,
        content: str,
        source_ref: str = "",
        confidence: float = 1.0,
        metadata: Optional[Dict[str, Any]] = None
    ):
        self.evidence.append(
            PatternEvidence(
                evidence_id=generate_id("evidence"),
                evidence_type=evidence_type,
                content=content,
                source_ref=source_ref,
                confidence=confidence,
                metadata=metadata or {}
            )
        )
    # TAGS
    def add_tag(self, tag: str):
        if tag not in self.metadata.tags:
            self.metadata.tags.append(tag)

    # METRICS
    def update_confidence(self, confidence: float):
        self.metrics.confidence = max(0.0, min(1.0, confidence))

    def update_strength(self, strength: float):
        self.metrics.strength = max(0.0, min(1.0, strength))

    # STATUS
    def deactivate(self):
        self.active = False
        self.timeline.active_window_end = utc_now()
        self.metadata.updated_at = utc_now()

    def update_timestamp(self):
        self.metadata.updated_at = utc_now()