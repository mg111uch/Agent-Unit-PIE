"""
behavior_registry.py

Thin behavior registry that imports from behaviours/ package.

Purpose
-------
Provides modular reusable behaviors for UnitAgent.
This replaces hardcoded logic in old_str/agents.py.

Usage
-----
    from behavior_registry import BehaviorRegistry
    
    registry = BehaviorRegistry()
    registry.execute_behavior("move", unit, world_state)
    
    # Or get behavior instance:
    behavior = registry.get_behavior("harvest")
    result = behavior.execute(unit, world_state)
"""

import logging
from typing import Dict, Any, Optional, List

from modules.simulators.popula_dyn.behaviours import (
    BaseBehavior,
    IdleBehavior,
    MoveBehavior,
    HarvestBehavior,
    ConsumeResourcesBehavior,
    ConsumeMetabolismBehavior,
    ReproduceBehavior,
    SurvivalBehavior,
    RegenerateEnergyBehavior,
    HealBehavior,
    ProduceBehavior,
    TradeBehavior,
    TradeBehaviorAg,
    LearnBehavior,
    RegrowBehavior,
)

logger = logging.getLogger(__name__)


class BehaviorRegistry:
    """
    Global reusable behavior registry.

    Behaviors are now split into separate files in behaviours/ directory.
    This registry imports and manages them.
    """

    def __init__(self):

        self.behaviors: Dict[str, BaseBehavior] = {}

        self.register_default_behaviors()

    def register_default_behaviors(self) -> None:
        """Register all built-in behaviors."""

        self.register_behavior(IdleBehavior())
        self.register_behavior(ConsumeResourcesBehavior())
        self.register_behavior(RegenerateEnergyBehavior())
        self.register_behavior(TradeBehavior())
        self.register_behavior(LearnBehavior())
        self.register_behavior(MoveBehavior())
        self.register_behavior(HarvestBehavior())
        self.register_behavior(ConsumeMetabolismBehavior())
        self.register_behavior(ReproduceBehavior())
        self.register_behavior(SurvivalBehavior())
        self.register_behavior(HealBehavior())
        self.register_behavior(ProduceBehavior())
        self.register_behavior(TradeBehaviorAg())
        self.register_behavior(RegrowBehavior())

    def register_behavior(self, behavior: BaseBehavior) -> None:
        """Register a behavior instance."""

        name = behavior.behavior_name
        self.behaviors[name] = behavior
        logger.debug(f"Registered behavior: {name}")

    def get_behavior(self, behavior_name: str) -> Optional[BaseBehavior]:
        """Retrieve behavior by name."""

        return self.behaviors.get(behavior_name)

    def behavior_exists(self, behavior_name: str) -> bool:
        """Check if behavior exists."""

        return behavior_name in self.behaviors

    def remove_behavior(self, behavior_name: str) -> bool:
        """Remove a registered behavior."""

        if behavior_name not in self.behaviors:
            return False

        del self.behaviors[behavior_name]
        logger.debug(f"Removed behavior: {behavior_name}")

        return True

    def list_behaviors(self) -> List[str]:
        """List all available behaviors."""

        return sorted(self.behaviors.keys())

    def execute_behavior(
        self,
        behavior_name: str,
        unit,
        world_state: Optional[Dict[str, Any]] = None,
    ) -> Dict[str, Any]:
        """Execute behavior directly."""

        behavior = self.get_behavior(behavior_name)

        if behavior is None:
            raise ValueError(f"Behavior not found: {behavior_name}")

        return behavior.execute(unit=unit, world_state=world_state or {})

    def summary(self) -> Dict[str, Any]:
        """Get registry summary."""

        return {
            "behavior_count": len(self.behaviors),
            "behaviors": self.list_behaviors(),
        }