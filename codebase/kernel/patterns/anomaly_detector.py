from __future__ import annotations

from dataclasses import dataclass, field
from typing import List, Dict, Any, Optional
import statistics
import math
import time

from kernel.schemas.signal_schema import SignalSchema
from kernel.schemas.event_schema import EventSchema
from kernel.schemas.pattern_schema import PatternSchema

from kernel.patterns.pattern_engine import pattern_engine

from kernel.utils.logger import get_child_logger


logger = get_child_logger("anomaly_detector")


# =========================================================
# ANOMALY RESULT
# =========================================================

@dataclass
class AnomalyResult:

    anomaly_type: str

    severity: float

    confidence: float

    anomaly_score: float

    source_ids: List[str]

    affected_values: List[float]

    mean_value: float

    std_deviation: float

    threshold: float

    detected_at: float = field(
        default_factory=time.time
    )

    metadata: Dict[str, Any] = field(
        default_factory=dict
    )

    # -----------------------------------------------------
    # SERIALIZATION
    # -----------------------------------------------------

    def to_dict(self) -> Dict[str, Any]:

        return {

            "anomaly_type":
            self.anomaly_type,

            "severity":
            self.severity,

            "confidence":
            self.confidence,

            "anomaly_score":
            self.anomaly_score,

            "source_ids":
            self.source_ids,

            "affected_values":
            self.affected_values,

            "mean_value":
            self.mean_value,

            "std_deviation":
            self.std_deviation,

            "threshold":
            self.threshold,

            "detected_at":
            self.detected_at,

            "metadata":
            self.metadata,
        }


# =========================================================
# ANOMALY DETECTOR
# =========================================================

class AnomalyDetector:

    def __init__(self):

        self.default_z_threshold = 2.5

        self.minimum_samples = 5

    # =====================================================
    # Z-SCORE ANOMALY DETECTION
    # =====================================================

    def detect_zscore_anomalies(
        self,
        signals: List[SignalSchema],
        z_threshold: Optional[float] = None,
    ) -> List[AnomalyResult]:

        z_threshold = (
            z_threshold
            or self.default_z_threshold
        )

        numeric_signals = []

        values = []

        for signal in signals:

            if isinstance(
                signal.value,
                (int, float)
            ):

                numeric_signals.append(
                    signal
                )

                values.append(
                    float(signal.value)
                )

        if len(values) < self.minimum_samples:

            logger.warning(
                "Insufficient samples for "
                "anomaly detection"
            )

            return []

        mean_value = statistics.mean(
            values
        )

        std_dev = statistics.stdev(
            values
        )

        if std_dev == 0:
            return []

        anomalies = []

        for idx, value in enumerate(values):

            z_score = abs(
                (
                    value - mean_value
                ) / std_dev
            )

            if z_score >= z_threshold:

                signal = numeric_signals[idx]

                severity = min(
                    1.0,
                    z_score / 10.0
                )

                confidence = min(
                    1.0,
                    z_score / z_threshold
                )

                result = AnomalyResult(

                    anomaly_type=
                    "zscore_outlier",

                    severity=severity,

                    confidence=confidence,

                    anomaly_score=z_score,

                    source_ids=[
                        signal.signal_id
                    ],

                    affected_values=[
                        value
                    ],

                    mean_value=mean_value,

                    std_deviation=std_dev,

                    threshold=z_threshold,

                    metadata={

                        "signal_type":
                        signal.signal_type,

                        "source_unit_id":
                        signal.source_unit_id,

                        "z_score":
                        z_score,
                    },
                )

                anomalies.append(result)

        logger.info(
            f"Detected "
            f"{len(anomalies)} anomalies"
        )

        return anomalies

    # =====================================================
    # SPIKE DETECTION
    # =====================================================

    def detect_spikes(
        self,
        signals: List[SignalSchema],
        spike_ratio: float = 2.0,
    ) -> List[AnomalyResult]:

        numeric_signals = []

        values = []

        for signal in signals:

            if isinstance(
                signal.value,
                (int, float)
            ):

                numeric_signals.append(
                    signal
                )

                values.append(
                    float(signal.value)
                )

        if len(values) < 3:
            return []

        anomalies = []

        for i in range(
            1,
            len(values)
        ):

            prev_value = values[i - 1]

            current_value = values[i]

            if prev_value == 0:
                continue

            ratio = abs(
                current_value
                / prev_value
            )

            if ratio >= spike_ratio:

                signal = numeric_signals[i]

                severity = min(
                    1.0,
                    ratio / 10.0
                )

                result = AnomalyResult(

                    anomaly_type=
                    "value_spike",

                    severity=severity,

                    confidence=0.8,

                    anomaly_score=ratio,

                    source_ids=[
                        signal.signal_id
                    ],

                    affected_values=[
                        prev_value,
                        current_value
                    ],

                    mean_value=
                    statistics.mean(values),

                    std_deviation=
                    statistics.stdev(values),

                    threshold=spike_ratio,

                    metadata={

                        "previous_value":
                        prev_value,

                        "current_value":
                        current_value,

                        "spike_ratio":
                        ratio,
                    },
                )

                anomalies.append(result)

        return anomalies

    # =====================================================
    # DROPOUT DETECTION
    # =====================================================

    def detect_dropouts(
        self,
        signals: List[SignalSchema],
        dropout_ratio: float = 0.5,
    ) -> List[AnomalyResult]:

        numeric_signals = []

        values = []

        for signal in signals:

            if isinstance(
                signal.value,
                (int, float)
            ):

                numeric_signals.append(
                    signal
                )

                values.append(
                    float(signal.value)
                )

        if len(values) < 3:
            return []

        anomalies = []

        for i in range(
            1,
            len(values)
        ):

            prev_value = values[i - 1]

            current_value = values[i]

            if prev_value == 0:
                continue

            ratio = (
                current_value
                / prev_value
            )

            if ratio <= dropout_ratio:

                signal = numeric_signals[i]

                severity = min(
                    1.0,
                    (1.0 - ratio)
                )

                result = AnomalyResult(

                    anomaly_type=
                    "value_dropout",

                    severity=severity,

                    confidence=0.75,

                    anomaly_score=1.0-ratio,

                    source_ids=[
                        signal.signal_id
                    ],

                    affected_values=[
                        prev_value,
                        current_value
                    ],

                    mean_value=
                    statistics.mean(values),

                    std_deviation=
                    statistics.stdev(values),

                    threshold=dropout_ratio,

                    metadata={

                        "previous_value":
                        prev_value,

                        "current_value":
                        current_value,

                        "drop_ratio":
                        ratio,
                    },
                )

                anomalies.append(result)

        return anomalies

    # =====================================================
    # PATTERN REGISTRATION
    # =====================================================

    def register_anomaly_patterns(
        self,
        anomalies: List[AnomalyResult]
    ) -> List[PatternSchema]:

        patterns = []

        for anomaly in anomalies:

            pattern = PatternSchema.create(

                pattern_type=
                "anomaly_pattern",

                title=
                anomaly.anomaly_type,

                description=(
                    f"Detected anomaly: "
                    f"{anomaly.anomaly_type}"
                ),

                source_ids=
                anomaly.source_ids,

                category=
                "anomaly",

                subtype=
                anomaly.anomaly_type,
            )

            pattern.metrics.confidence = (
                anomaly.confidence
            )

            pattern.metrics.importance = (
                anomaly.severity
            )

            pattern.metadata.extra.update(
                anomaly.to_dict()
            )

            registered = (
                pattern_engine
                .register_pattern(
                    pattern
                )
            )

            patterns.append(
                registered
            )

        return patterns

    # =====================================================
    # FULL PIPELINE
    # =====================================================

    def analyze_signals(
        self,
        signals: List[SignalSchema]
    ) -> Dict[str, Any]:

        zscore_anomalies = (
            self.detect_zscore_anomalies(
                signals
            )
        )

        spike_anomalies = (
            self.detect_spikes(
                signals
            )
        )

        dropout_anomalies = (
            self.detect_dropouts(
                signals
            )
        )

        all_anomalies = (
            zscore_anomalies
            + spike_anomalies
            + dropout_anomalies
        )

        patterns = (
            self.register_anomaly_patterns(
                all_anomalies
            )
        )

        return {

            "total_anomalies":
            len(all_anomalies),

            "zscore_anomalies":
            len(zscore_anomalies),

            "spike_anomalies":
            len(spike_anomalies),

            "dropout_anomalies":
            len(dropout_anomalies),

            "patterns_created":
            len(patterns),

            "anomalies": [
                a.to_dict()
                for a in all_anomalies
            ],
        }

    # =====================================================
    # SUMMARY
    # =====================================================

    def summarize_anomaly(
        self,
        anomaly: AnomalyResult
    ) -> str:

        return (
            f"Anomaly("
            f"type={anomaly.anomaly_type}, "
            f"severity={round(anomaly.severity,3)}, "
            f"confidence={round(anomaly.confidence,3)}, "
            f"score={round(anomaly.anomaly_score,3)}"
            f")"
        )


# =========================================================
# GLOBAL DETECTOR
# =========================================================

anomaly_detector = AnomalyDetector()