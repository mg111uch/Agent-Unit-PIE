"""
simulation_engine/unit_agent.py

Universal simulation unit agent.

Purpose
-------
Replaces hardcoded civilization-specific agents like:

- FarmerAgent
- TraderAgent
- HealerAgent

with a fully generic:

UnitAgent

This allows the SAME simulation engine to simulate:

- humans
- companies
- organizations
- cities
- countries
- stocks
- markets
- ecosystems
- digital twins

Core Philosophy
----------------
A unit does NOT contain hardcoded logic.

Instead:

unit
    + behaviors
    + signals
    + resources
    + relations
    + goals
    + constraints

determine emergent behavior.
"""

from __future__ import annotations

import uuid
import logging
from copy import deepcopy
from datetime import datetime, timezone
from typing import Dict, Any, List, Optional


logger = logging.getLogger(__name__)


class UnitAgent:
    """
    Universal simulation unit.
    """

    # ============================================================
    # INIT
    # ============================================================

    def __init__(
        self,
        unit_id: Optional[str] = None,
        unit_type: str = "generic_unit",
        state: Optional[Dict[str, Any]] = None,
        resources: Optional[Dict[str, Any]] = None,
        behaviors: Optional[List[str]] = None,
        goals: Optional[List[Dict[str, Any]]] = None,
        relations: Optional[List[Dict[str, Any]]] = None,
        metadata: Optional[Dict[str, Any]] = None,
    ):

        self.unit_id = unit_id or str(uuid.uuid4())

        self.unit_type = unit_type

        self.state = state or {}

        self.resources = resources or {}

        self.behaviors = behaviors or []

        self.goals = goals or []

        self.relations = relations or []

        self.metadata = metadata or {}

        # --------------------------------------------------------
        # RUNTIME
        # --------------------------------------------------------

        self.active_signals: List[Dict[str, Any]] = []

        self.generated_events: List[Dict[str, Any]] = []

        self.internal_memory: List[Dict[str, Any]] = []

        self.alive = True

        self.created_at = self.utc_now()

        self.last_step_at = None

    # ============================================================
    # MAIN STEP
    # ============================================================

    def step(
        self,
        world_state: Optional[Dict[str, Any]] = None,
        behavior_registry=None,
    ) -> List[Dict[str, Any]]:
        """
        Execute one simulation step.
        """

        self.generated_events = []

        self.last_step_at = self.utc_now()

        if not self.alive:
            return []

        logger.debug(
            f"Unit step: {self.unit_id}"
        )

        # --------------------------------------------------------
        # EXECUTE BEHAVIORS
        # --------------------------------------------------------

        for behavior_name in self.behaviors:

            behavior = None

            if behavior_registry:

                behavior = (
                    behavior_registry.get_behavior(
                        behavior_name
                    )
                )

            if behavior is None:

                logger.warning(
                    f"Behavior not found: {behavior_name}"
                )

                continue

            try:

                result = behavior.execute(
                    unit=self,
                    world_state=world_state or {},
                )

                if result:

                    self.process_behavior_result(
                        result
                    )

            except Exception:

                logger.exception(
                    f"Behavior execution failed: {behavior_name}"
                )

        # --------------------------------------------------------
        # DECAY SIGNALS
        # --------------------------------------------------------

        self.decay_signals()

        return deepcopy(
            self.generated_events
        )

    # ============================================================
    # PROCESS BEHAVIOR RESULT
    # ============================================================

    def process_behavior_result(
        self,
        result: Dict[str, Any],
    ) -> None:
        """
        Process outputs from behavior execution.
        """

        # --------------------------------------------------------
        # STATE UPDATE
        # --------------------------------------------------------

        state_updates = result.get(
            "state_updates",
            {},
        )

        self.state.update(state_updates)

        # --------------------------------------------------------
        # RESOURCE UPDATE
        # --------------------------------------------------------

        resource_updates = result.get(
            "resource_updates",
            {},
        )

        for key, value in resource_updates.items():

            self.resources[key] = (
                self.resources.get(key, 0)
                + value
            )

        # --------------------------------------------------------
        # SIGNALS
        # --------------------------------------------------------

        signals = result.get(
            "signals",
            [],
        )

        for signal in signals:

            self.add_signal(signal)

        # --------------------------------------------------------
        # EVENTS
        # --------------------------------------------------------

        events = result.get(
            "events",
            [],
        )

        for event in events:

            self.add_event(event)

        # --------------------------------------------------------
        # MEMORY
        # --------------------------------------------------------

        memories = result.get(
            "memory",
            [],
        )

        self.internal_memory.extend(memories)

    # ============================================================
    # SIGNAL MANAGEMENT
    # ============================================================

    def add_signal(
        self,
        signal: Dict[str, Any],
    ) -> None:
        """
        Add active signal.
        """

        signal.setdefault(
            "timestamp",
            self.utc_now(),
        )

        signal.setdefault(
            "unit_id",
            self.unit_id,
        )

        self.active_signals.append(signal)

    def decay_signals(self) -> None:
        """
        Decay transient signals over time.
        """

        remaining = []

        for signal in self.active_signals:

            strength = float(
                signal.get(
                    "strength",
                    1.0,
                )
            )

            decay_rate = float(
                signal.get(
                    "decay_rate",
                    0.05,
                )
            )

            strength -= decay_rate

            signal["strength"] = strength

            if strength > 0:
                remaining.append(signal)

        self.active_signals = remaining

    # ============================================================
    # EVENT MANAGEMENT
    # ============================================================

    def add_event(
        self,
        event: Dict[str, Any],
    ) -> None:
        """
        Add generated event.
        """

        event.setdefault(
            "event_id",
            str(uuid.uuid4()),
        )

        event.setdefault(
            "timestamp",
            self.utc_now(),
        )

        event.setdefault(
            "unit_id",
            self.unit_id,
        )

        event.setdefault(
            "unit_type",
            self.unit_type,
        )

        self.generated_events.append(event)

    # ============================================================
    # GOAL MANAGEMENT
    # ============================================================

    def add_goal(
        self,
        goal: Dict[str, Any],
    ) -> None:

        self.goals.append(goal)

    def remove_goal(
        self,
        goal_id: str,
    ) -> bool:

        initial_count = len(self.goals)

        self.goals = [
            g
            for g in self.goals
            if g.get("goal_id") != goal_id
        ]

        return len(self.goals) < initial_count

    # ============================================================
    # RELATION MANAGEMENT
    # ============================================================

    def add_relation(
        self,
        relation: Dict[str, Any],
    ) -> None:

        self.relations.append(relation)

    # ============================================================
    # RESOURCE MANAGEMENT
    # ============================================================

    def modify_resource(
        self,
        resource_name: str,
        delta: float,
    ) -> None:

        self.resources[resource_name] = (
            self.resources.get(resource_name, 0)
            + delta
        )

    def get_resource(
        self,
        resource_name: str,
        default: float = 0.0,
    ) -> float:

        return float(
            self.resources.get(
                resource_name,
                default,
            )
        )

    # ============================================================
    # STATE MANAGEMENT
    # ============================================================

    def set_state(
        self,
        key: str,
        value: Any,
    ) -> None:

        self.state[key] = value

    def get_state(
        self,
        key: str,
        default: Any = None,
    ) -> Any:

        return self.state.get(
            key,
            default,
        )

    # ============================================================
    # SERIALIZATION
    # ============================================================

    def to_dict(self) -> Dict[str, Any]:
        """
        Export unit state.
        """

        return {
            "unit_id": self.unit_id,
            "unit_type": self.unit_type,
            "state": deepcopy(self.state),
            "resources": deepcopy(
                self.resources
            ),
            "behaviors": deepcopy(
                self.behaviors
            ),
            "goals": deepcopy(self.goals),
            "relations": deepcopy(
                self.relations
            ),
            "metadata": deepcopy(
                self.metadata
            ),
            "active_signals": deepcopy(
                self.active_signals
            ),
            "alive": self.alive,
            "created_at": self.created_at,
            "last_step_at": self.last_step_at,
        }

    @classmethod
    def from_dict(
        cls,
        data: Dict[str, Any],
    ) -> "UnitAgent":
        """
        Restore unit from serialized state.
        """

        agent = cls(
            unit_id=data.get("unit_id"),
            unit_type=data.get("unit_type", "generic_unit"),
            state=data.get("state", {}),
            resources=data.get(
                "resources",
                {},
            ),
            behaviors=data.get(
                "behaviors",
                [],
            ),
            goals=data.get(
                "goals",
                [],
            ),
            relations=data.get(
                "relations",
                [],
            ),
            metadata=data.get(
                "metadata",
                {},
            ),
        )

        agent.active_signals = data.get(
            "active_signals",
            [],
        )

        agent.alive = data.get(
            "alive",
            True,
        )

        agent.created_at = data.get(
            "created_at",
            cls.utc_now(),
        )

        agent.last_step_at = data.get(
            "last_step_at"
        )

        return agent

    # ============================================================
    # LIFECYCLE
    # ============================================================

    def terminate(
        self,
        reason: str = "unknown",
    ) -> None:
        """
        Mark unit inactive.
        """

        self.alive = False

        self.add_event(
            {
                "event_type": "unit_terminated",
                "reason": reason,
            }
        )

    # ============================================================
    # DEBUG
    # ============================================================

    def summary(self) -> Dict[str, Any]:
        """
        Lightweight runtime summary.
        """

        return {
            "unit_id": self.unit_id,
            "unit_type": self.unit_type,
            "alive": self.alive,
            "behavior_count": len(
                self.behaviors
            ),
            "signal_count": len(
                self.active_signals
            ),
            "resource_count": len(
                self.resources
            ),
            "goal_count": len(
                self.goals
            ),
        }

    # ============================================================
    # HELPERS
    # ============================================================

    @staticmethod
    def utc_now() -> str:

        return datetime.now(
            timezone.utc
        ).isoformat()