from __future__ import annotations

from typing import List, Dict, Any, Optional

from kernel.schemas.signal_schema import SignalSchema
from kernel.ontology.signal_types import (
    signal_type_exists,
    get_signal_type,
)

from kernel.utils.logger import get_child_logger


logger = get_child_logger("signal_validator")


# =========================================================
# VALIDATION RESULT
# =========================================================

class SignalValidationResult:

    def __init__(self):

        self.valid: bool = True

        self.errors: List[str] = []

        self.warnings: List[str] = []

    # -----------------------------------------------------
    # HELPERS
    # -----------------------------------------------------

    def add_error(
        self,
        message: str
    ):

        self.valid = False

        self.errors.append(message)

    def add_warning(
        self,
        message: str
    ):

        self.warnings.append(message)

    # -----------------------------------------------------
    # SERIALIZATION
    # -----------------------------------------------------

    def to_dict(self) -> Dict[str, Any]:

        return {
            "valid": self.valid,
            "errors": self.errors,
            "warnings": self.warnings,
        }


# =========================================================
# SIGNAL VALIDATOR
# =========================================================

class SignalValidator:

    # =====================================================
    # MAIN VALIDATION
    # =====================================================

    def validate(
        self,
        signal: SignalSchema
    ) -> SignalValidationResult:

        result = SignalValidationResult()

        self._validate_basic_fields(
            signal,
            result
        )

        self._validate_signal_type(
            signal,
            result
        )

        self._validate_metrics(
            signal,
            result
        )

        self._validate_value(
            signal,
            result
        )

        self._validate_metadata(
            signal,
            result
        )

        return result

    # =====================================================
    # BASIC FIELD VALIDATION
    # =====================================================

    def _validate_basic_fields(
        self,
        signal: SignalSchema,
        result: SignalValidationResult
    ):

        if not signal.signal_id:

            result.add_error(
                "Missing signal_id"
            )

        if not signal.signal_type:

            result.add_error(
                "Missing signal_type"
            )

        if not signal.source_unit_id:

            result.add_error(
                "Missing source_unit_id"
            )

        if signal.value is None:

            result.add_warning(
                "Signal value is None"
            )

    # =====================================================
    # SIGNAL TYPE VALIDATION
    # =====================================================

    def _validate_signal_type(
        self,
        signal: SignalSchema,
        result: SignalValidationResult
    ):

        if not signal_type_exists(
            signal.signal_type
        ):

            result.add_warning(
                f"Unknown signal type: "
                f"{signal.signal_type}"
            )

            return

        signal_definition = get_signal_type(
            signal.signal_type
        )

        # Category check
        if (
            signal_definition
            and signal.category
            != signal_definition.category
        ):

            result.add_warning(
                f"Signal category mismatch: "
                f"{signal.category}"
            )

    # =====================================================
    # METRICS VALIDATION
    # =====================================================

    def _validate_metrics(
        self,
        signal: SignalSchema,
        result: SignalValidationResult
    ):

        confidence = (
            signal.metrics.confidence
        )

        importance = (
            signal.metrics.importance
        )

        urgency = (
            signal.metrics.urgency
        )

        volatility = (
            signal.metrics.volatility
        )

        metric_values = {
            "confidence": confidence,
            "importance": importance,
            "urgency": urgency,
            "volatility": volatility,
        }

        for metric_name, metric_value in (
            metric_values.items()
        ):

            if (
                metric_value < 0.0
                or metric_value > 1.0
            ):

                result.add_error(
                    f"Invalid {metric_name}: "
                    f"{metric_value}. "
                    f"Must be between 0 and 1."
                )

    # =====================================================
    # VALUE VALIDATION
    # =====================================================

    def _validate_value(
        self,
        signal: SignalSchema,
        result: SignalValidationResult
    ):

        value = signal.value

        # Numeric sanity checks
        if isinstance(value, (int, float)):

            if value != value:

                result.add_error(
                    "Signal value is NaN"
                )

            if value == float("inf"):

                result.add_error(
                    "Signal value is infinity"
                )

            if value == float("-inf"):

                result.add_error(
                    "Signal value is negative infinity"
                )

        # Empty string
        if isinstance(value, str):

            if not value.strip():

                result.add_warning(
                    "Signal value is empty string"
                )

        # Large payload warning
        if isinstance(
            value,
            (dict, list, str)
        ):

            size = len(str(value))

            if size > 100000:

                result.add_warning(
                    "Large signal payload detected"
                )

    # =====================================================
    # METADATA VALIDATION
    # =====================================================

    def _validate_metadata(
        self,
        signal: SignalSchema,
        result: SignalValidationResult
    ):

        # Tag validation
        tags = signal.metadata.tags

        if not isinstance(tags, list):

            result.add_error(
                "Metadata tags must be list"
            )

        # Extra metadata validation
        extra = signal.metadata.extra

        if not isinstance(extra, dict):

            result.add_error(
                "Metadata extra must be dict"
            )

    # =====================================================
    # QUICK VALIDATION
    # =====================================================

    def is_valid(
        self,
        signal: SignalSchema
    ) -> bool:

        result = self.validate(signal)

        return result.valid

    # =====================================================
    # ASSERT VALID
    # =====================================================

    def assert_valid(
        self,
        signal: SignalSchema
    ):

        result = self.validate(signal)

        if not result.valid:

            error_message = "\n".join(
                result.errors
            )

            raise ValueError(
                f"Signal validation failed:\n"
                f"{error_message}"
            )

    # =====================================================
    # LOG VALIDATION RESULT
    # =====================================================

    def log_validation_result(
        self,
        signal: SignalSchema,
        result: SignalValidationResult
    ):

        if result.valid:

            logger.info(
                f"Signal valid: "
                f"{signal.signal_id}"
            )

        else:

            logger.error(
                f"Signal invalid: "
                f"{signal.signal_id}"
            )

            for error in result.errors:

                logger.error(error)

        for warning in result.warnings:

            logger.warning(warning)


# =========================================================
# GLOBAL VALIDATOR
# =========================================================

signal_validator = SignalValidator()