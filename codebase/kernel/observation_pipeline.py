"""
kernel/observation_pipeline.py

Universal cognition ingestion pipeline.

Core Flow:
raw observation
    → normalized observation
    → event generation
    → signal generation
    → pattern detection
    → memory update

This pipeline acts as the central nervous system of agent_unit_pie.
All ingestion systems should eventually route through this pipeline.

Supported future sources:
- conversations
- PDFs
- newspapers
- websites
- simulations
- stock feeds
- sensors
- podcasts
- videos
- reports
"""

from __future__ import annotations

import uuid
import logging
from datetime import datetime, timezone
from typing import Any, Dict, List, Optional


logger = logging.getLogger(__name__)


class ObservationPipeline:
    """
    Central cognition pipeline.

    Responsibilities:
    - normalize observations
    - create events
    - generate signals
    - detect patterns
    - update memory
    - dispatch cognition hooks
    """

    def __init__(
        self,
        event_engine=None,
        signal_engine=None,
        pattern_engine=None,
        memory_router=None,
        compression_engine=None,
    ):

        self.event_engine = event_engine
        self.signal_engine = signal_engine
        self.pattern_engine = pattern_engine
        self.memory_router = memory_router
        self.compression_engine = compression_engine

    # ============================================================
    # MAIN ENTRY
    # ============================================================

    def process(
        self,
        observation: Dict[str, Any],
    ) -> Dict[str, Any]:
        """
        Main cognition pipeline entry point.

        Parameters
        ----------
        observation : dict
            Raw observation data.

        Returns
        -------
        dict
            Full cognition processing result.
        """

        try:

            # ----------------------------------------------------
            # STEP 1 — NORMALIZE
            # ----------------------------------------------------

            normalized_observation = self.normalize_observation(
                observation
            )

            # ----------------------------------------------------
            # STEP 2 — EVENT GENERATION
            # ----------------------------------------------------

            events = self.generate_events(
                normalized_observation
            )

            # ----------------------------------------------------
            # STEP 3 — SIGNAL GENERATION
            # ----------------------------------------------------

            signals = self.generate_signals(
                normalized_observation,
                events,
            )

            # ----------------------------------------------------
            # STEP 4 — PATTERN DETECTION
            # ----------------------------------------------------

            patterns = self.detect_patterns(
                normalized_observation,
                events,
                signals,
            )

            # ----------------------------------------------------
            # STEP 5 — MEMORY UPDATE
            # ----------------------------------------------------

            self.update_memory(
                observation=normalized_observation,
                events=events,
                signals=signals,
                patterns=patterns,
            )

            # ----------------------------------------------------
            # STEP 6 — OPTIONAL COMPRESSION
            # ----------------------------------------------------

            self.run_compression_if_needed()

            # ----------------------------------------------------
            # FINAL RESULT
            # ----------------------------------------------------

            result = {
                "status": "success",
                "observation": normalized_observation,
                "events": events,
                "signals": signals,
                "patterns": patterns,
                "processed_at": self.utc_now(),
            }

            return result

        except Exception as e:

            logger.exception(
                "Observation pipeline failed."
            )

            return {
                "status": "error",
                "error": str(e),
                "processed_at": self.utc_now(),
            }

    # ============================================================
    # NORMALIZATION
    # ============================================================

    def normalize_observation(
        self,
        observation: Dict[str, Any],
    ) -> Dict[str, Any]:
        """
        Normalize observation into canonical schema.
        """

        normalized = {
            "observation_id": observation.get(
                "observation_id",
                str(uuid.uuid4()),
            ),
            "timestamp": observation.get(
                "timestamp",
                self.utc_now(),
            ),
            "unit_id": observation.get(
                "unit_id",
                "unknown_unit",
            ),
            "unit_type": observation.get(
                "unit_type",
                "unknown",
            ),
            "source": observation.get(
                "source",
                "unknown",
            ),
            "observation_type": observation.get(
                "observation_type",
                "generic_observation",
            ),
            "content": observation.get(
                "content",
                {},
            ),
            "metadata": observation.get(
                "metadata",
                {},
            ),
            "confidence": float(
                observation.get("confidence", 0.5)
            ),
        }

        return normalized

    # ============================================================
    # EVENT GENERATION
    # ============================================================

    def generate_events(
        self,
        observation: Dict[str, Any],
    ) -> List[Dict[str, Any]]:
        """
        Convert observation into events.
        """

        if self.event_engine is None:
            return []

        return self.event_engine.process_observation(
            observation
        )

    # ============================================================
    # SIGNAL GENERATION
    # ============================================================

    def generate_signals(
        self,
        observation: Dict[str, Any],
        events: List[Dict[str, Any]],
    ) -> List[Dict[str, Any]]:
        """
        Generate signals from events + observations.
        """

        if self.signal_engine is None:
            return []

        return self.signal_engine.generate_signals(
            observation=observation,
            events=events,
        )

    # ============================================================
    # PATTERN DETECTION
    # ============================================================

    def detect_patterns(
        self,
        observation: Dict[str, Any],
        events: List[Dict[str, Any]],
        signals: List[Dict[str, Any]],
    ) -> List[Dict[str, Any]]:
        """
        Detect higher-order patterns.
        """

        if self.pattern_engine is None:
            return []

        return self.pattern_engine.detect_patterns(
            observation=observation,
            events=events,
            signals=signals,
        )

    # ============================================================
    # MEMORY UPDATE
    # ============================================================

    def update_memory(
        self,
        observation: Dict[str, Any],
        events: List[Dict[str, Any]],
        signals: List[Dict[str, Any]],
        patterns: List[Dict[str, Any]],
    ) -> None:
        """
        Route cognition artifacts into memory systems.
        """

        if self.memory_router is None:
            return

        try:

            self.memory_router.store_observation(
                observation
            )

            for event in events:
                self.memory_router.store_event(
                    event
                )

            for signal in signals:
                self.memory_router.store_signal(
                    signal
                )

            for pattern in patterns:
                self.memory_router.store_pattern(
                    pattern
                )

        except Exception:
            logger.exception(
                "Memory update failed."
            )

    # ============================================================
    # COMPRESSION
    # ============================================================

    def run_compression_if_needed(self) -> None:
        """
        Optional memory compression step.
        """

        if self.compression_engine is None:
            return

        try:

            self.compression_engine.run_cycle()

        except Exception:
            logger.exception(
                "Compression cycle failed."
            )

    # ============================================================
    # HELPERS
    # ============================================================

    @staticmethod
    def utc_now() -> str:
        """
        UTC ISO timestamp.
        """

        return datetime.now(
            timezone.utc
        ).isoformat()

    # ============================================================
    # HEALTH CHECK
    # ============================================================

    def health_check(self) -> Dict[str, Any]:
        """
        Pipeline component status.
        """

        return {
            "event_engine": self.event_engine is not None,
            "signal_engine": self.signal_engine is not None,
            "pattern_engine": self.pattern_engine is not None,
            "memory_router": self.memory_router is not None,
            "compression_engine": self.compression_engine is not None,
        }