from __future__ import annotations

from dataclasses import dataclass, field, asdict
from typing import Dict, List, Any, Optional
from datetime import datetime
import uuid


def generate_id(prefix: str = "unit") -> str:
    return f"{prefix}_{uuid.uuid4().hex[:12]}"


def utc_now() -> str:
    return datetime.utcnow().isoformat()


@dataclass
class UnitIdentity:
    unit_id: str
    unit_type: str
    name: str = ""
    created_at: str = field(default_factory=utc_now)
    source: str = "system"


@dataclass
class UnitState:
    active: bool = True
    lifecycle_stage: str = "unknown"

    health: float = 1.0
    energy: float = 1.0
    stability: float = 1.0

    location: Optional[str] = None
    timestamp: str = field(default_factory=utc_now)


@dataclass
class UnitResources:
    resources: Dict[str, float] = field(default_factory=dict)

    def add(self, key: str, value: float):
        self.resources[key] = self.resources.get(key, 0.0) + value

    def consume(self, key: str, value: float):
        self.resources[key] = max(
            0.0,
            self.resources.get(key, 0.0) - value
        )


@dataclass
class UnitTraits:
    traits: Dict[str, Any] = field(default_factory=dict)


@dataclass
class UnitBehavior:
    behavior_id: str
    behavior_type: str
    enabled: bool = True
    priority: int = 0
    metadata: Dict[str, Any] = field(default_factory=dict)


@dataclass
class UnitSignalRef:
    signal_id: str
    signal_type: str
    confidence: float = 1.0
    timestamp: str = field(default_factory=utc_now)


@dataclass
class UnitRelation:
    relation_id: str
    relation_type: str
    target_unit_id: str
    strength: float = 1.0
    metadata: Dict[str, Any] = field(default_factory=dict)


@dataclass
class UnitMemory:
    episodic: List[str] = field(default_factory=list)
    semantic: List[str] = field(default_factory=list)
    pattern_refs: List[str] = field(default_factory=list)
    hypothesis_refs: List[str] = field(default_factory=list)


@dataclass
class UnitMetadata:
    confidence: float = 1.0
    tags: List[str] = field(default_factory=list)
    labels: Dict[str, str] = field(default_factory=dict)

    source_refs: List[str] = field(default_factory=list)

    created_at: str = field(default_factory=utc_now)
    updated_at: str = field(default_factory=utc_now)


@dataclass
class UnitSchema:
    identity: UnitIdentity

    state: UnitState = field(default_factory=UnitState)
    resources: UnitResources = field(default_factory=UnitResources)
    traits: UnitTraits = field(default_factory=UnitTraits)

    behaviors: List[UnitBehavior] = field(default_factory=list)
    signals: List[UnitSignalRef] = field(default_factory=list)
    relations: List[UnitRelation] = field(default_factory=list)

    memory: UnitMemory = field(default_factory=UnitMemory)

    metadata: UnitMetadata = field(default_factory=UnitMetadata)

    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)

    @classmethod
    def create(
        cls,
        unit_type: str,
        name: str = "",
        source: str = "system"
    ) -> "UnitSchema":

        identity = UnitIdentity(
            unit_id=generate_id(unit_type),
            unit_type=unit_type,
            name=name,
            source=source
        )

        return cls(identity=identity)

    def add_behavior(
        self,
        behavior_type: str,
        priority: int = 0,
        metadata: Optional[Dict[str, Any]] = None
    ):

        self.behaviors.append(
            UnitBehavior(
                behavior_id=generate_id("behavior"),
                behavior_type=behavior_type,
                priority=priority,
                metadata=metadata or {}
            )
        )

    def add_signal(
        self,
        signal_id: str,
        signal_type: str,
        confidence: float = 1.0
    ):

        self.signals.append(
            UnitSignalRef(
                signal_id=signal_id,
                signal_type=signal_type,
                confidence=confidence
            )
        )

    def add_relation(
        self,
        relation_type: str,
        target_unit_id: str,
        strength: float = 1.0,
        metadata: Optional[Dict[str, Any]] = None
    ):

        self.relations.append(
            UnitRelation(
                relation_id=generate_id("relation"),
                relation_type=relation_type,
                target_unit_id=target_unit_id,
                strength=strength,
                metadata=metadata or {}
            )
        )

    def update_timestamp(self):
        self.metadata.updated_at = utc_now()