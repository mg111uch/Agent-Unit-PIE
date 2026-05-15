"""
behaviours/base_behavior.py

Base class for all behavior classes.
"""

from typing import Dict, Any, Optional


class BaseBehavior:
    """
    Base reusable behavior class.

    All behaviors must implement execute() which returns:
    {
        "state_updates": {},
        "resource_updates": {},
        "signals": [],
        "events": [],
        "memory": []
    }
    """

    behavior_name = "base_behavior"

    def execute(
        self,
        unit,
        world_state: Optional[Dict[str, Any]] = None,
    ) -> Dict[str, Any]:
        """
        Execute behavior logic.

        Parameters
        ----------
        unit : UnitAgent
            The unit executing the behavior.
        world_state : dict, optional
            Global simulation state including params, grid, model, etc.

        Returns
        -------
        dict
            Behavior results with state_updates, resource_updates, signals, events, memory.
        """

        raise NotImplementedError(
            f"{self.__class__.__name__} must implement execute()"
        )