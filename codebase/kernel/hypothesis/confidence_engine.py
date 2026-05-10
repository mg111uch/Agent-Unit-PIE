from __future__ import annotations

from dataclasses import dataclass, field
from typing import Dict, List, Optional, Any
import statistics
import math
import time

from kernel.utils.logger import (
    get_child_logger
)

from kernel.schemas.signal_schema import (
    SignalSchema
)

from kernel.schemas.event_schema import (
    EventSchema
)

from kernel.schemas.pattern_schema import (
    PatternSchema
)

from kernel.hypothesis.hypothesis_engine import (
    Hypothesis
)


logger = get_child_logger(
    "confidence_engine"
)


# =========================================================
# CONFIDENCE RESULT
# =========================================================

@dataclass
class ConfidenceResult:

    final_confidence: float

    evidence_score: float

    consistency_score: float

    source_reliability_score: float

    temporal_score: float

    quantity_score: float

    metadata: Dict[str, Any] = field(
        default_factory=dict
    )

    created_at: float = field(
        default_factory=time.time
    )

    # -----------------------------------------------------
    # SERIALIZATION
    # -----------------------------------------------------

    def to_dict(self) -> Dict[str, Any]:

        return {

            "final_confidence":
            self.final_confidence,

            "evidence_score":
            self.evidence_score,

            "consistency_score":
            self.consistency_score,

            "source_reliability_score":
            self.source_reliability_score,

            "temporal_score":
            self.temporal_score,

            "quantity_score":
            self.quantity_score,

            "metadata":
            self.metadata,

            "created_at":
            self.created_at,
        }


# =========================================================
# CONFIDENCE ENGINE
# =========================================================

class ConfidenceEngine:

    def __init__(self):

        self.default_source_reliability = 0.7

        self.minimum_confidence = 0.0

        self.maximum_confidence = 1.0

    # =====================================================
    # SIGNAL CONFIDENCE
    # =====================================================

    def evaluate_signal_confidence(
        self,
        signals: List[SignalSchema]
    ) -> ConfidenceResult:

        if not signals:

            return self._empty_result()

        evidence_score = (
            self._calculate_signal_evidence(
                signals
            )
        )

        consistency_score = (
            self._calculate_signal_consistency(
                signals
            )
        )

        source_score = (
            self._calculate_source_reliability(
                [
                    s.metadata.source
                    for s in signals
                ]
            )
        )

        temporal_score = (
            self._calculate_temporal_score(
                [
                    s.timestamps
                    .created_at_unix
                    for s in signals
                ]
            )
        )

        quantity_score = (
            self._calculate_quantity_score(
                len(signals)
            )
        )

        final_confidence = (
            evidence_score * 0.25
            + consistency_score * 0.25
            + source_score * 0.2
            + temporal_score * 0.15
            + quantity_score * 0.15
        )

        final_confidence = (
            self._clamp_confidence(
                final_confidence
            )
        )

        return ConfidenceResult(

            final_confidence=
            final_confidence,

            evidence_score=
            evidence_score,

            consistency_score=
            consistency_score,

            source_reliability_score=
            source_score,

            temporal_score=
            temporal_score,

            quantity_score=
            quantity_score,

            metadata={

                "signal_count":
                len(signals)
            },
        )

    # =====================================================
    # EVENT CONFIDENCE
    # =====================================================

    def evaluate_event_confidence(
        self,
        events: List[EventSchema]
    ) -> ConfidenceResult:

        if not events:

            return self._empty_result()

        evidence_score = statistics.mean([

            e.metrics.confidence

            for e in events
        ])

        importance_values = [

            e.metrics.importance

            for e in events
        ]

        consistency_score = (
            self._inverse_variance_score(
                importance_values
            )
        )

        source_score = (
            self.default_source_reliability
        )

        temporal_score = (
            self._calculate_temporal_score(
                [
                    e.timestamps
                    .created_at_unix
                    for e in events
                ]
            )
        )

        quantity_score = (
            self._calculate_quantity_score(
                len(events)
            )
        )

        final_confidence = (
            evidence_score * 0.3
            + consistency_score * 0.25
            + source_score * 0.15
            + temporal_score * 0.15
            + quantity_score * 0.15
        )

        return ConfidenceResult(

            final_confidence=
            self._clamp_confidence(
                final_confidence
            ),

            evidence_score=
            evidence_score,

            consistency_score=
            consistency_score,

            source_reliability_score=
            source_score,

            temporal_score=
            temporal_score,

            quantity_score=
            quantity_score,

            metadata={

                "event_count":
                len(events)
            },
        )

    # =====================================================
    # PATTERN CONFIDENCE
    # =====================================================

    def evaluate_pattern_confidence(
        self,
        patterns: List[PatternSchema]
    ) -> ConfidenceResult:

        if not patterns:

            return self._empty_result()

        evidence_score = statistics.mean([

            p.metrics.confidence

            for p in patterns
        ])

        consistency_score = (
            self._inverse_variance_score(
                [
                    p.metrics.confidence
                    for p in patterns
                ]
            )
        )

        source_score = (
            self.default_source_reliability
        )

        temporal_score = 0.8

        quantity_score = (
            self._calculate_quantity_score(
                len(patterns)
            )
        )

        final_confidence = (
            evidence_score * 0.35
            + consistency_score * 0.25
            + source_score * 0.15
            + temporal_score * 0.1
            + quantity_score * 0.15
        )

        return ConfidenceResult(

            final_confidence=
            self._clamp_confidence(
                final_confidence
            ),

            evidence_score=
            evidence_score,

            consistency_score=
            consistency_score,

            source_reliability_score=
            source_score,

            temporal_score=
            temporal_score,

            quantity_score=
            quantity_score,
        )

    # =====================================================
    # HYPOTHESIS CONFIDENCE
    # =====================================================

    def evaluate_hypothesis_confidence(
        self,
        hypothesis: Hypothesis
    ) -> ConfidenceResult:

        support_count = len(
            hypothesis.supporting_evidence
        )

        contradiction_count = len(
            hypothesis
            .contradicting_evidence
        )

        total = (
            support_count
            + contradiction_count
        )

        evidence_score = (
            support_count / total
            if total > 0
            else 0.5
        )

        consistency_score = (
            hypothesis.plausibility
        )

        source_score = (
            self.default_source_reliability
        )

        temporal_score = 0.7

        quantity_score = (
            self._calculate_quantity_score(
                total
            )
        )

        final_confidence = (
            evidence_score * 0.35
            + consistency_score * 0.25
            + source_score * 0.1
            + temporal_score * 0.1
            + quantity_score * 0.2
        )

        return ConfidenceResult(

            final_confidence=
            self._clamp_confidence(
                final_confidence
            ),

            evidence_score=
            evidence_score,

            consistency_score=
            consistency_score,

            source_reliability_score=
            source_score,

            temporal_score=
            temporal_score,

            quantity_score=
            quantity_score,

            metadata={

                "supporting_evidence":
                support_count,

                "contradicting_evidence":
                contradiction_count,
            },
        )

    # =====================================================
    # SIGNAL EVIDENCE
    # =====================================================

    def _calculate_signal_evidence(
        self,
        signals: List[SignalSchema]
    ) -> float:

        return statistics.mean([

            s.metrics.confidence

            for s in signals
        ])

    # =====================================================
    # SIGNAL CONSISTENCY
    # =====================================================

    def _calculate_signal_consistency(
        self,
        signals: List[SignalSchema]
    ) -> float:

        numeric_values = []

        for signal in signals:

            if isinstance(
                signal.value,
                (int, float)
            ):

                numeric_values.append(
                    float(signal.value)
                )

        if len(numeric_values) <= 1:
            return 0.7

        return self._inverse_variance_score(
            numeric_values
        )

    # =====================================================
    # SOURCE RELIABILITY
    # =====================================================

    def _calculate_source_reliability(
        self,
        sources: List[Optional[str]]
    ) -> float:

        if not sources:
            return (
                self.default_source_reliability
            )

        reliability_scores = []

        for source in sources:

            if not source:

                reliability_scores.append(
                    0.5
                )

            elif "official" in source:

                reliability_scores.append(
                    0.95
                )

            elif "verified" in source:

                reliability_scores.append(
                    0.9
                )

            elif "sensor" in source:

                reliability_scores.append(
                    0.85
                )

            else:

                reliability_scores.append(
                    self.default_source_reliability
                )

        return statistics.mean(
            reliability_scores
        )

    # =====================================================
    # TEMPORAL SCORE
    # =====================================================

    def _calculate_temporal_score(
        self,
        timestamps: List[float]
    ) -> float:

        if len(timestamps) <= 1:
            return 0.7

        now = time.time()

        age_scores = []

        for ts in timestamps:

            age_seconds = now - ts

            age_days = (
                age_seconds / 86400
            )

            freshness = math.exp(
                -age_days / 30
            )

            age_scores.append(
                freshness
            )

        return statistics.mean(
            age_scores
        )

    # =====================================================
    # QUANTITY SCORE
    # =====================================================

    def _calculate_quantity_score(
        self,
        quantity: int
    ) -> float:

        if quantity <= 0:
            return 0.0

        return min(
            1.0,
            math.log(quantity + 1, 10)
        )

    # =====================================================
    # INVERSE VARIANCE
    # =====================================================

    def _inverse_variance_score(
        self,
        values: List[float]
    ) -> float:

        if len(values) <= 1:
            return 0.8

        try:

            variance = (
                statistics.variance(
                    values
                )
            )

            score = 1.0 / (
                1.0 + variance
            )

            return self._clamp_confidence(
                score
            )

        except Exception:

            return 0.5

    # =====================================================
    # CLAMP
    # =====================================================

    def _clamp_confidence(
        self,
        value: float
    ) -> float:

        return max(
            self.minimum_confidence,
            min(
                self.maximum_confidence,
                value
            )
        )

    # =====================================================
    # EMPTY RESULT
    # =====================================================

    def _empty_result(
        self
    ) -> ConfidenceResult:

        return ConfidenceResult(

            final_confidence=0.0,

            evidence_score=0.0,

            consistency_score=0.0,

            source_reliability_score=0.0,

            temporal_score=0.0,

            quantity_score=0.0,
        )

    # =====================================================
    # SUMMARY
    # =====================================================

    def summarize(
        self,
        result: ConfidenceResult
    ) -> str:

        return (
            f"Confidence("
            f"final="
            f"{round(result.final_confidence,3)}, "
            f"evidence="
            f"{round(result.evidence_score,3)}, "
            f"consistency="
            f"{round(result.consistency_score,3)}"
            f")"
        )


# =========================================================
# GLOBAL ENGINE
# =========================================================

confidence_engine = (
    ConfidenceEngine()
)