from __future__ import annotations

from typing import List, Dict, Any, Optional
from dataclasses import dataclass, field
import statistics
import math
import time

from kernel.schemas.signal_schema import SignalSchema
from kernel.schemas.pattern_schema import PatternSchema

from kernel.patterns.pattern_engine import pattern_engine

from kernel.utils.logger import get_child_logger


logger = get_child_logger("trend_detector")


# =========================================================
# TREND RESULT
# =========================================================

@dataclass
class TrendResult:

    trend_type: str

    direction: str

    slope: float

    strength: float

    confidence: float

    volatility: float

    mean_value: float

    min_value: float

    max_value: float

    sample_size: int

    metadata: Dict[str, Any] = field(
        default_factory=dict
    )

    # -----------------------------------------------------
    # SERIALIZATION
    # -----------------------------------------------------

    def to_dict(self) -> Dict[str, Any]:

        return {
            "trend_type": self.trend_type,
            "direction": self.direction,
            "slope": self.slope,
            "strength": self.strength,
            "confidence": self.confidence,
            "volatility": self.volatility,
            "mean_value": self.mean_value,
            "min_value": self.min_value,
            "max_value": self.max_value,
            "sample_size": self.sample_size,
            "metadata": self.metadata,
        }


# =========================================================
# TREND DETECTOR
# =========================================================

class TrendDetector:

    def __init__(self):

        self.minimum_samples = 3

    # =====================================================
    # MAIN TREND DETECTION
    # =====================================================

    def detect_trend(
        self,
        signals: List[SignalSchema],
        trend_name: str = "generic_trend",
    ) -> Optional[TrendResult]:

        numeric_values = []

        timestamps = []

        valid_signals = []

        for signal in signals:

            if isinstance(
                signal.value,
                (int, float)
            ):

                numeric_values.append(
                    float(signal.value)
                )

                timestamps.append(
                    signal.timestamps.created_at_unix
                )

                valid_signals.append(
                    signal
                )

        if (
            len(numeric_values)
            < self.minimum_samples
        ):

            logger.warning(
                "Insufficient samples "
                "for trend detection"
            )

            return None

        # -------------------------------------------------
        # METRICS
        # -------------------------------------------------

        slope = self._calculate_slope(
            numeric_values
        )

        volatility = self._calculate_volatility(
            numeric_values
        )

        strength = abs(slope)

        direction = self._get_direction(
            slope
        )

        confidence = self._calculate_confidence(
            numeric_values,
            slope,
            volatility
        )

        trend_type = self._classify_trend(
            slope,
            volatility
        )

        result = TrendResult(

            trend_type=trend_type,

            direction=direction,

            slope=slope,

            strength=strength,

            confidence=confidence,

            volatility=volatility,

            mean_value=statistics.mean(
                numeric_values
            ),

            min_value=min(numeric_values),

            max_value=max(numeric_values),

            sample_size=len(numeric_values),

            metadata={

                "trend_name":
                trend_name,

                "start_value":
                numeric_values[0],

                "end_value":
                numeric_values[-1],

                "signal_count":
                len(valid_signals),
            },
        )

        logger.info(
            f"Trend detected: "
            f"{trend_name} -> {direction}"
        )

        return result

    # =====================================================
    # CREATE TREND PATTERN
    # =====================================================

    def detect_and_register_pattern(
        self,
        signals: List[SignalSchema],
        trend_name: str = "trend"
    ) -> Optional[PatternSchema]:

        result = self.detect_trend(
            signals=signals,
            trend_name=trend_name,
        )

        if not result:
            return None

        pattern = PatternSchema.create(

            pattern_type="trend_pattern",

            title=f"{trend_name} trend",

            description=(
                f"{trend_name} shows "
                f"{result.direction} "
                f"behaviour"
            ),

            source_ids=[
                signal.signal_id
                for signal in signals
            ],

            category="trend",

            subtype=result.direction,
        )

        pattern.metrics.confidence = (
            result.confidence
        )

        pattern.metrics.importance = min(
            1.0,
            result.strength
        )

        pattern.metadata.extra.update(
            result.to_dict()
        )

        return pattern_engine.register_pattern(
            pattern
        )

    # =====================================================
    # SLOPE
    # =====================================================

    def _calculate_slope(
        self,
        values: List[float]
    ) -> float:

        n = len(values)

        x = list(range(n))

        x_mean = statistics.mean(x)

        y_mean = statistics.mean(values)

        numerator = sum(
            (
                (x[i] - x_mean)
                * (values[i] - y_mean)
            )
            for i in range(n)
        )

        denominator = sum(
            (
                (x[i] - x_mean) ** 2
            )
            for i in range(n)
        )

        if denominator == 0:
            return 0.0

        return numerator / denominator

    # =====================================================
    # VOLATILITY
    # =====================================================

    def _calculate_volatility(
        self,
        values: List[float]
    ) -> float:

        if len(values) <= 1:
            return 0.0

        try:

            return statistics.stdev(values)

        except Exception:

            return 0.0

    # =====================================================
    # CONFIDENCE
    # =====================================================

    def _calculate_confidence(
        self,
        values: List[float],
        slope: float,
        volatility: float,
    ) -> float:

        avg = abs(
            statistics.mean(values)
        )

        if avg == 0:
            avg = 1e-6

        normalized_slope = abs(
            slope / avg
        )

        stability_factor = 1.0 / (
            1.0 + volatility
        )

        confidence = (
            normalized_slope
            * stability_factor
        )

        return max(
            0.0,
            min(confidence, 1.0)
        )

    # =====================================================
    # DIRECTION
    # =====================================================

    def _get_direction(
        self,
        slope: float
    ) -> str:

        threshold = 0.001

        if slope > threshold:
            return "increasing"

        if slope < -threshold:
            return "decreasing"

        return "stable"

    # =====================================================
    # TREND CLASSIFICATION
    # =====================================================

    def _classify_trend(
        self,
        slope: float,
        volatility: float
    ) -> str:

        if volatility > abs(slope) * 5:

            return "volatile"

        if abs(slope) < 0.001:

            return "stable"

        if slope > 0:

            return "growth"

        return "decline"

    # =====================================================
    # MOVING AVERAGE
    # =====================================================

    def moving_average(
        self,
        values: List[float],
        window_size: int = 3
    ) -> List[float]:

        if window_size <= 0:
            raise ValueError(
                "window_size must be > 0"
            )

        if len(values) < window_size:
            return []

        averages = []

        for i in range(
            len(values) - window_size + 1
        ):

            window = values[
                i : i + window_size
            ]

            averages.append(
                sum(window)
                / window_size
            )

        return averages

    # =====================================================
    # ANOMALY DETECTION
    # =====================================================

    def detect_anomalies(
        self,
        values: List[float],
        z_threshold: float = 2.0
    ) -> List[Dict[str, Any]]:

        if len(values) < 2:
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

            z_score = (
                value - mean_value
            ) / std_dev

            if abs(z_score) >= z_threshold:

                anomalies.append({

                    "index":
                    idx,

                    "value":
                    value,

                    "z_score":
                    z_score,
                })

        return anomalies

    # =====================================================
    # CYCLE DETECTION
    # =====================================================

    def detect_simple_cycles(
        self,
        values: List[float]
    ) -> Dict[str, Any]:

        if len(values) < 6:

            return {
                "cycle_detected": False
            }

        peaks = []

        valleys = []

        for i in range(
            1,
            len(values) - 1
        ):

            if (
                values[i]
                > values[i - 1]
                and values[i]
                > values[i + 1]
            ):

                peaks.append(i)

            if (
                values[i]
                < values[i - 1]
                and values[i]
                < values[i + 1]
            ):

                valleys.append(i)

        cycle_detected = (
            len(peaks) >= 2
            and len(valleys) >= 2
        )

        return {

            "cycle_detected":
            cycle_detected,

            "peak_count":
            len(peaks),

            "valley_count":
            len(valleys),

            "peaks":
            peaks,

            "valleys":
            valleys,
        }

    # =====================================================
    # SUMMARY
    # =====================================================

    def summarize_trend(
        self,
        result: TrendResult
    ) -> str:

        return (
            f"Trend: {result.direction}, "
            f"type={result.trend_type}, "
            f"slope={round(result.slope, 4)}, "
            f"confidence={round(result.confidence, 3)}, "
            f"volatility={round(result.volatility, 3)}"
        )


# =========================================================
# GLOBAL DETECTOR
# =====================================================

trend_detector = TrendDetector()