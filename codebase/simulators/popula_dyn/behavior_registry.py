"""
simulation_engine/behavior_registry.py

Universal behavior registry system.

Purpose
-------
Provides modular reusable behaviors for UnitAgent.

This replaces hardcoded logic such as:

- FarmerAgent.harvest()
- TraderAgent.trade()
- HealerAgent.heal()

with:

behavior.execute(unit, world_state)

Core Philosophy
----------------
Behaviors are reusable cognition/action modules.

Examples
--------
- consume_resources
- trade
- migrate
- invest
- communicate
- negotiate
- produce
- learn
- attack
- collaborate
- innovate

The SAME behavior system can operate across:

- humans
- companies
- cities
- countries
- markets
- ecosystems
"""

from __future__ import annotations

import logging
from typing import Dict, Any, Optional, List


logger = logging.getLogger(__name__)


# ============================================================
# BASE BEHAVIOR
# ============================================================

class BaseBehavior:
    """
    Base reusable behavior class.
    """

    behavior_name = "base_behavior"

    def execute(
        self,
        unit,
        world_state: Optional[Dict[str, Any]] = None,
    ) -> Dict[str, Any]:
        """
        Execute behavior logic.

        Returns
        -------
        dict
            {
                "state_updates": {},
                "resource_updates": {},
                "signals": [],
                "events": [],
                "memory": []
            }
        """

        raise NotImplementedError


# ============================================================
# DEFAULT BEHAVIORS
# ============================================================

class IdleBehavior(BaseBehavior):

    behavior_name = "idle"

    def execute(
        self,
        unit,
        world_state=None,
    ) -> Dict[str, Any]:

        return {
            "events": [
                {
                    "event_type": "idle",
                    "description": (
                        f"{unit.unit_id} remained idle"
                    ),
                }
            ]
        }


class ConsumeResourcesBehavior(BaseBehavior):

    behavior_name = "consume_resources"

    def execute(
        self,
        unit,
        world_state=None,
    ) -> Dict[str, Any]:

        resource_updates = {}

        for resource_name in list(
            unit.resources.keys()
        ):

            value = float(
                unit.resources.get(
                    resource_name,
                    0,
                )
            )

            if value > 0:

                resource_updates[
                    resource_name
                ] = -0.1

        return {
            "resource_updates": resource_updates,
            "events": [
                {
                    "event_type": "resource_consumption",
                }
            ],
        }


class RegenerateEnergyBehavior(BaseBehavior):

    behavior_name = "regenerate_energy"

    def execute(
        self,
        unit,
        world_state=None,
    ) -> Dict[str, Any]:

        return {
            "resource_updates": {
                "energy": 1.0,
            },
            "signals": [
                {
                    "signal_type": "energy_recovery",
                    "strength": 0.5,
                    "decay_rate": 0.02,
                }
            ],
        }


class TradeBehavior(BaseBehavior):

    behavior_name = "trade"

    def execute(
        self,
        unit,
        world_state=None,
    ) -> Dict[str, Any]:

        capital = unit.get_resource(
            "capital",
            0,
        )

        if capital <= 0:

            return {
                "signals": [
                    {
                        "signal_type": "economic_stress",
                        "strength": 0.7,
                        "decay_rate": 0.03,
                    }
                ]
            }

        return {
            "resource_updates": {
                "capital": 2.0,
            },
            "events": [
                {
                    "event_type": "trade_completed",
                }
            ],
            "signals": [
                {
                    "signal_type": "market_activity",
                    "strength": 0.6,
                    "decay_rate": 0.04,
                }
            ],
        }


class LearnBehavior(BaseBehavior):

    behavior_name = "learn"

    def execute(
        self,
        unit,
        world_state=None,
    ) -> Dict[str, Any]:

        intelligence = unit.get_state(
            "intelligence",
            0,
        )

        return {
            "state_updates": {
                "intelligence": (
                    intelligence + 0.1
                )
            },
            "signals": [
                {
                    "signal_type": "knowledge_growth",
                    "strength": 0.4,
                    "decay_rate": 0.01,
                }
            ],
            "events": [
                {
                    "event_type": "learning_progress",
                }
            ],
        }


# ============================================================
# BEHAVIOR REGISTRY
# ============================================================

class BehaviorRegistry:
    """
    Global reusable behavior registry.
    """

    # ============================================================
    # INIT
    # ============================================================

    def __init__(self):

        self.behaviors: Dict[
            str,
            BaseBehavior,
        ] = {}

        self.register_default_behaviors()

    # ============================================================
    # REGISTER DEFAULTS
    # ============================================================

    def register_default_behaviors(
        self,
    ) -> None:
        """
        Register built-in behaviors.
        """

        self.register_behavior(
            IdleBehavior()
        )

        self.register_behavior(
            ConsumeResourcesBehavior()
        )

        self.register_behavior(
            RegenerateEnergyBehavior()
        )

        self.register_behavior(
            TradeBehavior()
        )

        self.register_behavior(
            LearnBehavior()
        )

    # ============================================================
    # REGISTER
    # ============================================================

    def register_behavior(
        self,
        behavior: BaseBehavior,
    ) -> None:
        """
        Register reusable behavior.
        """

        name = behavior.behavior_name

        self.behaviors[name] = behavior

        logger.info(
            f"Registered behavior: {name}"
        )

    # ============================================================
    # GET
    # ============================================================

    def get_behavior(
        self,
        behavior_name: str,
    ) -> Optional[BaseBehavior]:
        """
        Retrieve behavior instance.
        """

        return self.behaviors.get(
            behavior_name
        )

    # ============================================================
    # EXISTS
    # ============================================================

    def behavior_exists(
        self,
        behavior_name: str,
    ) -> bool:

        return (
            behavior_name
            in self.behaviors
        )

    # ============================================================
    # REMOVE
    # ============================================================

    def remove_behavior(
        self,
        behavior_name: str,
    ) -> bool:
        """
        Remove registered behavior.
        """

        if (
            behavior_name
            not in self.behaviors
        ):
            return False

        del self.behaviors[
            behavior_name
        ]

        logger.info(
            f"Removed behavior: {behavior_name}"
        )

        return True

    # ============================================================
    # LIST
    # ============================================================

    def list_behaviors(
        self,
    ) -> List[str]:
        """
        List available behaviors.
        """

        return sorted(
            self.behaviors.keys()
        )

    # ============================================================
    # EXECUTE DIRECT
    # ============================================================

    def execute_behavior(
        self,
        behavior_name: str,
        unit,
        world_state: Optional[
            Dict[str, Any]
        ] = None,
    ) -> Dict[str, Any]:
        """
        Execute behavior directly.
        """

        behavior = self.get_behavior(
            behavior_name
        )

        if behavior is None:

            raise ValueError(
                f"Behavior not found: "
                f"{behavior_name}"
            )

        return behavior.execute(
            unit=unit,
            world_state=world_state or {},
        )

    # ============================================================
    # SUMMARY
    # ============================================================

    def summary(self) -> Dict[str, Any]:

        return {
            "behavior_count": len(
                self.behaviors
            ),
            "behaviors": self.list_behaviors(),
        }