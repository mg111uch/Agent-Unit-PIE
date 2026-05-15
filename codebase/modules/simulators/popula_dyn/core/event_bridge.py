"""
simulation_engine/event_bridge.py

Simulation → Cognition bridge.

Purpose
-------
Connects simulation outputs into the kernel cognition pipeline.

Core Flow
---------
simulation events
    → observations
    → event pipeline
    → signal generation
    → pattern detection
    → memory update

This file is the critical bridge between:

simulation_engine
and
kernel cognition system.

Without this bridge, simulations remain isolated.
"""

from __future__ import annotations

import logging
from datetime import datetime, timezone
from typing import Dict, Any, List, Optional


logger = logging.getLogger(__name__)


class EventBridge:
    """
    Simulation cognition bridge.
    """

    # ============================================================
    # INIT
    # ============================================================

    def __init__(
        self,
        observation_pipeline=None,
    ):

        self.observation_pipeline = (
            observation_pipeline
        )

    # ============================================================
    # MAIN ENTRY
    # ============================================================

    def process_simulation_step(
        self,
        simulation_id: str,
        events: List[Dict[str, Any]],
        metadata: Optional[
            Dict[str, Any]
        ] = None,
    ) -> List[Dict[str, Any]]:
        """
        Process all events from one simulation step.
        """

        results = []

        logger.debug(
            f"Processing simulation step "
            f"for {simulation_id}"
        )

        for event in events:

            try:

                observation = (
                    self.convert_event_to_observation(
                        simulation_id=simulation_id,
                        event=event,
                        metadata=metadata,
                    )
                )

                result = (
                    self.process_observation(
                        observation
                    )
                )

                results.append(result)

            except Exception:

                logger.exception(
                    "Failed processing simulation event."
                )

        return results

    # ============================================================
    # SINGLE EVENT
    # ============================================================

    def process_simulation_event(
        self,
        simulation_id: str,
        event: Dict[str, Any],
        metadata: Optional[
            Dict[str, Any]
        ] = None,
    ) -> Dict[str, Any]:
        """
        Process single simulation event.
        """

        observation = (
            self.convert_event_to_observation(
                simulation_id=simulation_id,
                event=event,
                metadata=metadata,
            )
        )

        return self.process_observation(
            observation
        )

    # ============================================================
    # EVENT → OBSERVATION
    # ============================================================

    def convert_event_to_observation(
        self,
        simulation_id: str,
        event: Dict[str, Any],
        metadata: Optional[
            Dict[str, Any]
        ] = None,
    ) -> Dict[str, Any]:
        """
        Convert simulation event into universal observation.
        """

        observation = {
            "timestamp": self.utc_now(),
            "source": "simulation_engine",
            "simulation_id": simulation_id,
            "observation_type": (
                "simulation_event"
            ),
            "unit_id": event.get(
                "unit_id",
                "unknown_unit",
            ),
            "unit_type": event.get(
                "unit_type",
                "generic_unit",
            ),
            "content": event,
            "metadata": metadata or {},
            "confidence": 1.0,
        }

        return observation

    # ============================================================
    # OBSERVATION PIPELINE
    # ============================================================

    def process_observation(
        self,
        observation: Dict[str, Any],
    ) -> Dict[str, Any]:
        """
        Send observation into cognition pipeline.
        """

        if self.observation_pipeline is None:

            logger.warning(
                "Observation pipeline missing."
            )

            return {
                "status": "skipped",
                "reason": (
                    "observation_pipeline_missing"
                ),
                "observation": observation,
            }

        return (
            self.observation_pipeline.process(
                observation
            )
        )

    # ============================================================
    # BULK PROCESSING
    # ============================================================

    def process_multiple_simulations(
        self,
        simulation_batches: List[
            Dict[str, Any]
        ],
    ) -> List[Dict[str, Any]]:
        """
        Process multiple simulation batches.
        """

        all_results = []

        for batch in simulation_batches:

            simulation_id = batch.get(
                "simulation_id",
                "unknown_simulation",
            )

            events = batch.get(
                "events",
                [],
            )

            metadata = batch.get(
                "metadata",
                {},
            )

            result = (
                self.process_simulation_step(
                    simulation_id=simulation_id,
                    events=events,
                    metadata=metadata,
                )
            )

            all_results.extend(result)

        return all_results

    # ============================================================
    # SIMULATION SNAPSHOT
    # ============================================================

    def process_simulation_snapshot(
        self,
        simulation_id: str,
        snapshot: Dict[str, Any],
    ) -> Dict[str, Any]:
        """
        Convert world snapshot into observation.
        """

        observation = {
            "timestamp": self.utc_now(),
            "source": "simulation_snapshot",
            "simulation_id": simulation_id,
            "observation_type": (
                "simulation_snapshot"
            ),
            "unit_id": simulation_id,
            "unit_type": "simulation_world",
            "content": snapshot,
            "metadata": {},
            "confidence": 1.0,
        }

        return self.process_observation(
            observation
        )

    # ============================================================
    # HEALTH CHECK
    # ============================================================

    def health_check(
        self,
    ) -> Dict[str, Any]:

        return {
            "observation_pipeline": (
                self.observation_pipeline
                is not None
            )
        }

    # ============================================================
    # HELPERS
    # ============================================================

    @staticmethod
    def utc_now() -> str:

        return datetime.now(
            timezone.utc
        ).isoformat()