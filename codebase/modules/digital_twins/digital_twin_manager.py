"""
digital_twins/digital_twin_manager.py

Unified digital twin manager.

Purpose
-------
Manages digital twins for all unit systems inside
agent_unit_pie.

A digital twin is a continuously evolving virtual
representation of a real or simulated unit.

Supported Twin Domains
----------------------
- humans
- organizations
- companies
- cities
- states
- countries
- markets
- ecosystems
- economies
- AI agents
- infrastructure systems

Core Responsibilities
---------------------
- create digital twins
- maintain twin states
- sync real-world observations
- simulate future trajectories
- compare reality vs prediction
- detect deviations
- generate behavioral forecasts
- generate economic forecasts
- snapshot historical states
- evolve twin knowledge

Core Philosophy
----------------
A digital twin is not static storage.

It is:

- memory
- simulation
- prediction
- behavior model
- resource model
- timeline model
- probabilistic future generator

Digital twins are central for:

- forecasting
- opportunity analysis
- corruption analysis
- urban planning
- behavioral prediction
- economic optimization
"""

from __future__ import annotations

import copy
import logging

from datetime import datetime, timezone
from typing import Dict, Any, Optional, List

logger = logging.getLogger(__name__)

class DigitalTwinManager:
    """
    Unified digital twin orchestration layer.
    """
    # INIT
    def __init__(
        self,
        unit_registry=None,
        simulation_engine=None,
        memory_engine=None,
        pattern_engine=None,
        timeline_engine=None,
        event_engine=None,
        storage_engine=None,
        config: Optional[
            Dict[str, Any]
        ] = None,
    ):
        self.unit_registry = (
            unit_registry
        )
        self.simulation_engine = (
            simulation_engine
        )
        self.memory_engine = (
            memory_engine
        )
        self.pattern_engine = (
            pattern_engine
        )
        self.timeline_engine = (
            timeline_engine
        )
        self.event_engine = (
            event_engine
        )
        self.storage_engine = (
            storage_engine
        )
        self.config = config or {}
        # ACTIVE TWINS
        self.digital_twins: Dict[
            str,
            Dict[str, Any]
        ] = {}
        # SNAPSHOT HISTORY
        self.snapshots: Dict[
            str,
            List[Dict[str, Any]]
        ] = {}
    # CREATE TWIN
    def create_twin(
        self,
        unit_id: str,
        metadata: Optional[
            Dict[str, Any]
        ] = None,
    ) -> Optional[Dict[str, Any]]:
        """
        Create digital twin from unit.
        """
        unit = self.resolve_unit(
            unit_id
        )
        if unit is None:
            logger.warning(
                f"Cannot create twin. "
                f"Unit not found: {unit_id}"
            )
            return None
        twin = {
            "twin_id": (
                f"twin_{unit_id}"
            ),
            "unit_id": unit_id,
            "unit_type": unit.get(
                "unit_type",
                "unknown",
            ),
            "created_at": (
                self.utc_now()
            ),
            "updated_at": (
                self.utc_now()
            ),
            "state": copy.deepcopy(
                unit
            ),
            "simulation_state": {},
            "behavior_model": {},
            "resource_model": {},
            "timeline_model": {},
            "predictions": [],
            "deviations": [],
            "metadata": (
                metadata or {}
            ),
        }
        self.digital_twins[
            unit_id
        ] = twin
        self.snapshots.setdefault(
            unit_id,
            [],
        )
        logger.info(
            f"Created digital twin "
            f"for unit: {unit_id}"
        )
        return twin
    # GET TWIN
    def get_twin(
        self,
        unit_id: str,
    ) -> Optional[Dict[str, Any]]:
        """
        Retrieve digital twin.
        """
        return self.digital_twins.get(
            unit_id
        )
    # REMOVE TWIN
    def remove_twin(
        self,
        unit_id: str,
    ) -> bool:
        """
        Remove digital twin.
        """
        if (
            unit_id
            not in self.digital_twins
        ):
            return False
        del self.digital_twins[
            unit_id
        ]
        logger.info(
            f"Removed digital twin: "
            f"{unit_id}"
        )
        return True
    # SYNC STATE
    def sync_twin(
        self,
        unit_id: str,
    ) -> bool:
        """
        Synchronize twin with live unit.
        """
        twin = self.get_twin(
            unit_id
        )
        if twin is None:
            return False
        unit = self.resolve_unit(
            unit_id
        )
        if unit is None:
            return False
        # SAVE SNAPSHOT BEFORE UPDATE
        self.create_snapshot(
            unit_id
        )
        # UPDATE STATE
        twin["state"] = (
            copy.deepcopy(unit)
        )
        twin["updated_at"] = (
            self.utc_now()
        )
        return True
    # CREATE SNAPSHOT
    def create_snapshot(
        self,
        unit_id: str,
    ) -> Optional[Dict[str, Any]]:
        """
        Save historical twin snapshot.
        """
        twin = self.get_twin(
            unit_id
        )
        if twin is None:
            return None
        snapshot = {
            "timestamp": (
                self.utc_now()
            ),
            "state": copy.deepcopy(
                twin["state"]
            ),
            "simulation_state": (
                copy.deepcopy(
                    twin[
                        "simulation_state"
                    ]
                )
            ),
        }
        self.snapshots[
            unit_id
        ].append(snapshot)
        return snapshot
    # GET SNAPSHOTS
    def get_snapshots(
        self,
        unit_id: str,
        limit: int = 50,
    ) -> List[Dict[str, Any]]:
        """
        Retrieve historical snapshots.
        """
        snapshots = self.snapshots.get(
            unit_id,
            [],
        )
        return snapshots[-limit:]
    # SIMULATE FUTURE
    def simulate_future(
        self,
        unit_id: str,
        future_ticks: int = 30,
    ) -> Dict[str, Any]:
        """
        Generate future trajectory.
        """
        twin = self.get_twin(
            unit_id
        )
        if twin is None:
            return {}
        # WORLD SIMULATION ENGINE
        if self.simulation_engine:
            try:
                projection = (
                    self.simulation_engine
                    .generate_projection(
                        unit_id=unit_id,
                        future_ticks=(
                            future_ticks
                        ),
                    )
                )
                twin[
                    "simulation_state"
                ] = projection
                twin[
                    "predictions"
                ].append(
                    {
                        "timestamp": (
                            self.utc_now()
                        ),
                        "projection": (
                            projection
                        ),
                    }
                )
                return projection
            except Exception:
                logger.exception(
                    "Future simulation failed."
                )
        return {}
    # COMPARE REALITY
    def compare_prediction_vs_reality(
        self,
        unit_id: str,
    ) -> Dict[str, Any]:
        """
        Compare predicted state with live state.
        """
        twin = self.get_twin(
            unit_id
        )
        if twin is None:
            return {}
        unit = self.resolve_unit(
            unit_id
        )
        if unit is None:
            return {}
        predicted = twin.get(
            "simulation_state",
            {},
        )
        comparison = {
            "unit_id": unit_id,
            "timestamp": (
                self.utc_now()
            ),
            "deviations": [],
        }
        # SIMPLE STATE DIFFERENCE
        predicted_state = predicted.get(
            "current_state",
            {},
        )
        for key, value in (
            predicted_state.items()
        ):
            actual = unit.get(key)
            if actual != value:
                comparison[
                    "deviations"
                ].append(
                    {
                        "field": key,
                        "predicted": value,
                        "actual": actual,
                    }
                )
        twin["deviations"].append(
            comparison
        )
        return comparison
    # BUILD BEHAVIOR MODEL
    def build_behavior_model(
        self,
        unit_id: str,
    ) -> Dict[str, Any]:
        """
        Generate behavior profile model.
        """
        twin = self.get_twin(
            unit_id
        )
        if twin is None:
            return {}
        behaviors = (
            twin["state"].get(
                "behaviors",
                [],
            )
        )
        model = {
            "behavior_count": len(
                behaviors
            ),
            "behaviors": behaviors,
            "dominant_behavior": (
                behaviors[0]
                if behaviors
                else None
            ),
        }
        twin[
            "behavior_model"
        ] = model
        return model
    # BUILD RESOURCE MODEL
    def build_resource_model(
        self,
        unit_id: str,
    ) -> Dict[str, Any]:
        """
        Generate resource model.
        """
        twin = self.get_twin(
            unit_id
        )
        if twin is None:
            return {}
        resources = (
            twin["state"].get(
                "resources",
                {},
            )
        )
        total_resources = sum(
            float(v)
            for v in resources.values()
            if isinstance(
                v,
                (int, float),
            )
        )
        model = {
            "resource_types": len(
                resources
            ),
            "total_resources": (
                total_resources
            ),
            "resources": resources,
        }
        twin[
            "resource_model"
        ] = model
        return model
    # BUILD TIMELINE MODEL
    def build_timeline_model(
        self,
        unit_id: str,
    ) -> Dict[str, Any]:
        """
        Generate timeline evolution model.
        """
        twin = self.get_twin(
            unit_id
        )
        if twin is None:
            return {}
        snapshots = self.get_snapshots(
            unit_id
        )
        model = {
            "snapshot_count": len(
                snapshots
            ),
            "first_snapshot": (
                snapshots[0][
                    "timestamp"
                ]
                if snapshots
                else None
            ),
            "latest_snapshot": (
                snapshots[-1][
                    "timestamp"
                ]
                if snapshots
                else None
            ),
        }
        twin[
            "timeline_model"
        ] = model
        return model
    # EVOLVE TWIN
    def evolve_twin(
        self,
        unit_id: str,
    ) -> Dict[str, Any]:
        """
        Fully evolve digital twin cognition.
        """
        twin = self.get_twin(
            unit_id
        )
        if twin is None:
            return {}
        self.sync_twin(
            unit_id
        )
        behavior_model = (
            self.build_behavior_model(
                unit_id
            )
        )
        resource_model = (
            self.build_resource_model(
                unit_id
            )
        )
        timeline_model = (
            self.build_timeline_model(
                unit_id
            )
        )
        future_projection = (
            self.simulate_future(
                unit_id
            )
        )
        return {
            "unit_id": unit_id,
            "behavior_model": (
                behavior_model
            ),
            "resource_model": (
                resource_model
            ),
            "timeline_model": (
                timeline_model
            ),
            "future_projection": (
                future_projection
            ),
        }
    # EXPORT TWIN
    def export_twin(
        self,
        unit_id: str,
    ) -> Dict[str, Any]:
        """
        Export full twin state.
        """
        twin = self.get_twin(
            unit_id
        )
        if twin is None:
            return {}
        return copy.deepcopy(
            twin
        )
    # LIST TWINS
    def list_twins(
        self,
    ) -> List[str]:
        """
        List all active digital twins.
        """
        return sorted(
            self.digital_twins.keys()
        )
    # HEALTH CHECK
    def health_check(
        self,
    ) -> Dict[str, Any]:
        return {
            "digital_twins": len(
                self.digital_twins
            ),
            "snapshots": sum(
                len(v)
                for v in (
                    self.snapshots.values()
                )
            ),
            "unit_registry": (
                self.unit_registry
                is not None
            ),
            "simulation_engine": (
                self.simulation_engine
                is not None
            ),
            "memory_engine": (
                self.memory_engine
                is not None
            ),
            "pattern_engine": (
                self.pattern_engine
                is not None
            ),
            "timeline_engine": (
                self.timeline_engine
                is not None
            ),
            "event_engine": (
                self.event_engine
                is not None
            ),
        }
    # HELPERS
    def resolve_unit(
        self,
        unit_id: str,
    ) -> Optional[Dict[str, Any]]:
        if self.unit_registry is None:
            return None
        return self.unit_registry.get_unit(
            unit_id
        )
    @staticmethod
    def utc_now() -> str:
        return datetime.now(
            timezone.utc
        ).isoformat()