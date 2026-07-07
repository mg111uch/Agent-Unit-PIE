from __future__ import annotations

from dataclasses import dataclass, field
from typing import Dict, List, Optional, Any
from collections import defaultdict
import time

from kernel.utils.logger import get_child_logger

from kernel.schemas.pattern_schema import PatternSchema
from kernel.schemas.signal_schema import SignalSchema
from kernel.schemas.event_schema import EventSchema

from kernel.patterns.pattern_engine import pattern_engine

from kernel.memory.semantic_memory import (
    semantic_memory
)

logger = get_child_logger(
    "hypothesis_engine"
)

# HYPOTHESIS

@dataclass
class Hypothesis:
    hypothesis_id: str
    title: str
    description: str
    hypothesis_type: str
    category: str = "general"
    confidence: float = 0.5
    plausibility: float = 0.5
    novelty: float = 0.5
    status: str = "proposed"
    supporting_evidence: List[str] = field(
        default_factory=list
    )
    contradicting_evidence: List[str] = field(
        default_factory=list
    )
    related_patterns: List[str] = field(
        default_factory=list
    )
    related_concepts: List[str] = field(
        default_factory=list
    )
    predictions: List[str] = field(
        default_factory=list
    )
    created_at: float = field(
        default_factory=time.time
    )
    updated_at: float = field(
        default_factory=time.time
    )
    metadata: Dict[str, Any] = field(
        default_factory=dict
    )
    # SERIALIZATION
    def to_dict(self) -> Dict[str, Any]:
        return {
            "hypothesis_id":
            self.hypothesis_id,
            "title":
            self.title,
            "description":
            self.description,
            "hypothesis_type":
            self.hypothesis_type,
            "category":
            self.category,
            "confidence":
            self.confidence,
            "plausibility":
            self.plausibility,
            "novelty":
            self.novelty,
            "status":
            self.status,
            "supporting_evidence":
            self.supporting_evidence,
            "contradicting_evidence":
            self.contradicting_evidence,
            "related_patterns":
            self.related_patterns,
            "related_concepts":
            self.related_concepts,
            "predictions":
            self.predictions,
            "created_at":
            self.created_at,
            "updated_at":
            self.updated_at,
            "metadata":
            self.metadata,
        }

# HYPOTHESIS ENGINE

class HypothesisEngine:
    def __init__(self):
        self.hypotheses: Dict[
            str,
            Hypothesis
        ] = {}
        self.type_index = defaultdict(list)
        self.category_index = defaultdict(list)
        self.status_index = defaultdict(list)

    # CREATE HYPOTHESIS
    def create_hypothesis(
        self,
        hypothesis_id: str,
        title: str,
        description: str,
        hypothesis_type: str,
        category: str = "general",
        confidence: float = 0.5,
        plausibility: float = 0.5,
        novelty: float = 0.5,
        related_patterns: Optional[
            List[str]
        ] = None,
        related_concepts: Optional[
            List[str]
        ] = None,
        predictions: Optional[
            List[str]
        ] = None,
        metadata: Optional[Dict] = None,
    ) -> Hypothesis:
        hypothesis = Hypothesis(
            hypothesis_id=hypothesis_id,
            title=title,
            description=description,
            hypothesis_type=hypothesis_type,
            category=category,
            confidence=confidence,
            plausibility=plausibility,
            novelty=novelty,
            related_patterns=
            related_patterns or [],
            related_concepts=
            related_concepts or [],
            predictions=
            predictions or [],
            metadata=
            metadata or {},
        )
        self.register_hypothesis(
            hypothesis
        )
        return hypothesis
    # REGISTER
    def register_hypothesis(
        self,
        hypothesis: Hypothesis
    ):
        self.hypotheses[
            hypothesis.hypothesis_id
        ] = hypothesis
        self.type_index[
            hypothesis.hypothesis_type
        ].append(
            hypothesis.hypothesis_id
        )
        self.category_index[
            hypothesis.category
        ].append(
            hypothesis.hypothesis_id
        )
        self.status_index[
            hypothesis.status
        ].append(
            hypothesis.hypothesis_id
        )
        logger.info(
            f"Hypothesis registered: "
            f"{hypothesis.hypothesis_id}"
        )
    # AUTO GENERATE FROM PATTERNS
    def generate_from_patterns(
        self,
        patterns: List[PatternSchema]
    ) -> List[Hypothesis]:
        hypotheses = []
        for pattern in patterns:
            title = (
                f"Hypothesis from "
                f"{pattern.pattern_type}"
            )
            description = (
                f"Observed pattern "
                f"'{pattern.title}' "
                f"may indicate deeper "
                f"causal structure."
            )
            hypothesis_id = (
                f"hypothesis_"
                f"{pattern.pattern_id}"
            )
            hypothesis = self.create_hypothesis(
                hypothesis_id=
                hypothesis_id,
                title=title,
                description=description,
                hypothesis_type=
                "pattern_inference",
                category=
                pattern.category,
                confidence=
                pattern.metrics.confidence,
                plausibility=
                pattern.metrics.confidence,
                novelty=0.6,
                related_patterns=[
                    pattern.pattern_id
                ],
                related_concepts=
                pattern.metadata.tags,
                predictions=[
                    "Pattern likely to "
                    "repeat in future.",
                    "Related signals may "
                    "show similar behaviour.",
                ],
                metadata={
                    "source_pattern":
                    pattern.pattern_id,
                },
            )
            hypotheses.append(
                hypothesis
            )
        return hypotheses
    # ADD EVIDENCE
    def add_supporting_evidence(
        self,
        hypothesis_id: str,
        evidence_id: str,
    ):
        hypothesis = self.hypotheses.get(
            hypothesis_id
        )
        if not hypothesis:
            return
        if (
            evidence_id
            not in
            hypothesis.supporting_evidence
        ):
            hypothesis.supporting_evidence.append(
                evidence_id
            )
            hypothesis.confidence = min(
                1.0,
                hypothesis.confidence + 0.05
            )
            hypothesis.updated_at = (
                time.time()
            )
    def add_contradicting_evidence(
        self,
        hypothesis_id: str,
        evidence_id: str,
    ):
        hypothesis = self.hypotheses.get(
            hypothesis_id
        )
        if not hypothesis:
            return
        if (
            evidence_id
            not in
            hypothesis.contradicting_evidence
        ):
            hypothesis.contradicting_evidence.append(
                evidence_id
            )
            hypothesis.confidence = max(
                0.0,
                hypothesis.confidence - 0.05
            )
            hypothesis.updated_at = (
                time.time()
            )
    # VALIDATION
    def validate_hypothesis(
        self,
        hypothesis_id: str
    ) -> Dict[str, Any]:
        hypothesis = self.hypotheses.get(
            hypothesis_id
        )
        if not hypothesis:
            return {
                "valid": False
            }
        support_count = len(
            hypothesis.supporting_evidence
        )
        contradiction_count = len(
            hypothesis.contradicting_evidence
        )
        total = (
            support_count
            + contradiction_count
        )
        validation_score = 0.5
        if total > 0:
            validation_score = (
                support_count / total
            )
        if validation_score >= 0.7:
            status = "supported"
        elif validation_score <= 0.3:
            status = "rejected"
        else:
            status = "uncertain"
        hypothesis.status = status
        hypothesis.updated_at = time.time()
        return {
            "hypothesis_id":
            hypothesis_id,
            "validation_score":
            validation_score,
            "support_count":
            support_count,
            "contradiction_count":
            contradiction_count,
            "status":
            status,
        }
    # SEARCH
    def get_hypothesis(
        self,
        hypothesis_id: str
    ) -> Optional[Hypothesis]:
        return self.hypotheses.get(
            hypothesis_id
        )
    def get_by_type(
        self,
        hypothesis_type: str
    ) -> List[Hypothesis]:
        ids = self.type_index.get(
            hypothesis_type,
            []
        )
        return [
            self.hypotheses[hid]
            for hid in ids
            if hid in self.hypotheses
        ]
    def get_by_category(
        self,
        category: str
    ) -> List[Hypothesis]:
        ids = self.category_index.get(
            category,
            []
        )
        return [
            self.hypotheses[hid]
            for hid in ids
            if hid in self.hypotheses
        ]
    def get_by_status(
        self,
        status: str
    ) -> List[Hypothesis]:
        ids = self.status_index.get(
            status,
            []
        )
        return [
            self.hypotheses[hid]
            for hid in ids
            if hid in self.hypotheses
        ]
    # SEMANTIC EXPORT
    def export_to_semantic_memory(
        self,
        hypothesis_id: str
    ):
        hypothesis = self.hypotheses.get(
            hypothesis_id
        )
        if not hypothesis:
            return
        semantic_memory.create_node(
            node_id=
            hypothesis.hypothesis_id,
            node_type=
            "hypothesis",
            title=
            hypothesis.title,
            content=
            hypothesis.description,
            concepts=
            hypothesis.related_concepts,
            tags=[
                hypothesis.hypothesis_type,
                hypothesis.category,
                hypothesis.status,
            ],
            importance=
            hypothesis.confidence,
            confidence=
            hypothesis.plausibility,
            metadata={
                "predictions":
                hypothesis.predictions,
                "related_patterns":
                hypothesis.related_patterns,
            },
        )
    # STATS
    def stats(self) -> Dict[str, Any]:
        return {
            "total_hypotheses":
            len(self.hypotheses),
            "types":
            len(self.type_index),
            "categories":
            len(self.category_index),
            "statuses":
            len(self.status_index),
        }

    # CLEAR
    def clear(self):
        self.hypotheses.clear()
        self.type_index.clear()
        self.category_index.clear()
        self.status_index.clear()
        logger.warning(
            "Hypothesis engine cleared"
        )

# GLOBAL ENGINE

hypothesis_engine = (
    HypothesisEngine()
)