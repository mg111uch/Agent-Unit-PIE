"""
core/agent_factory.py

Agent configuration factory for behavior-based simulation.

Purpose
-------
Maps old agent types (farmer, healer, toolmaker, trader, land)
to unit configurations with appropriate behavior lists.

Usage
-----
    from core.agent_factory import AGENT_CONFIGS, create_unit
    
    config = AGENT_CONFIGS["farmer"]
    unit = create_unit("farmer", model, position=(x, y))
"""

import uuid
from typing import Dict, Any, Optional


AGENT_CONFIGS = {
    "farmer": {
        "unit_type": "human",
        "behaviors": [
            "move",
            "harvest",
            "consume_metabolism",
            "reproduce",
            "survival",
        ],
        "initial_state": {
            "age": 0,
            "gender": "M",
            "skill": 0.5,
            "wealth": 5.0,
            "alive": True,
            "death_prob_modifier": 0.0,
        },
        "initial_resources": {
            "wealth": 5.0,
        },
    },
    "healer": {
        "unit_type": "specialist",
        "behaviors": [
            "move",
            "heal",
        ],
        "initial_state": {
            "healing_rate": 0.1,
            "healing_cost": 0.5,
            "wealth": 5.0,
            "alive": True,
        },
        "initial_resources": {
            "wealth": 5.0,
        },
    },
    "toolmaker": {
        "unit_type": "specialist",
        "behaviors": [
            "move",
            "produce",
        ],
        "initial_state": {
            "tool_production_rate": 0.1,
            "tool_quality": 0.1,
            "tool_cost": 1.0,
            "inventory": 0,
            "wealth": 5.0,
            "alive": True,
        },
        "initial_resources": {
            "wealth": 5.0,
        },
    },
    "trader": {
        "unit_type": "specialist",
        "behaviors": [
            "move",
            "trade_ag",
        ],
        "initial_state": {
            "trade_margin": 0.05,
            "trade_range": 2,
            "wealth": 5.0,
            "alive": True,
        },
        "initial_resources": {
            "wealth": 5.0,
        },
    },
    "land": {
        "unit_type": "land",
        "behaviors": [
            "regrow",
        ],
        "initial_state": {
            "fertility": 5.0,
            "current_crops": 5.0,
        },
        "initial_resources": {
            "crops": 5.0,
        },
    },
}


def create_unit_config(
    agent_type: str,
    model: Any = None,
    position: Optional[tuple] = None,
    seed: Optional[int] = None,
    **overrides,
) -> Dict[str, Any]:
    """
    Create a unit configuration with unique ID.

    Parameters
    ----------
    agent_type : str
        Type: "farmer", "healer", "toolmaker", "trader", "land"
    model : Model, optional
        Simulation model for id generation
    position : tuple, optional
        (x, y) position on grid
    seed : int, optional
        Random seed for initialization
    **overrides
        Override default values

    Returns
    -------
    dict
        Unit configuration with unit_id, behaviors, state, resources
    """
    import numpy as np

    if agent_type not in AGENT_CONFIGS:
        raise ValueError(f"Unknown agent type: {agent_type}")

    config = AGENT_CONFIGS[agent_type].copy()

    rng = np.random.RandomState(seed)
    unit_id = str(uuid.uuid4())

    unit_config = {
        "unit_id": unit_id,
        "unit_type": config["unit_type"],
        "behaviors": config["behaviors"].copy(),
        "position": position,
    }

    initial_state = config.get("initial_state", {}).copy()
    if agent_type == "farmer":
        initial_state.setdefault("age", rng.randint(0, 80))
        initial_state.setdefault("gender", rng.choice(["M", "F"]))

    for key, value in overrides.items():
        if key in initial_state:
            initial_state[key] = value
        elif key == "position":
            unit_config["position"] = value

    unit_config["state"] = initial_state

    initial_resources = config.get("initial_resources", {}).copy()
    unit_config["resources"] = {
        k: v for k, v in initial_resources.items() if v is not None
    }

    unit_config["alive"] = initial_state.get("alive", True)

    return unit_config


def get_agent_behaviors(agent_type: str) -> list:
    """Get behavior list for agent type."""

    if agent_type not in AGENT_CONFIGS:
        return []

    return AGENT_CONFIGS[agent_type]["behaviors"].copy()


def get_agent_type_from_behavior(behavior_name: str) -> Optional[str]:
    """Find agent type that uses a given behavior."""

    for agent_type, config in AGENT_CONFIGS.items():
        if behavior_name in config["behaviors"]:
            return agent_type

    return None


def list_agent_types() -> list:
    """List all available agent types."""

    return list(AGENT_CONFIGS.keys())


def summary() -> Dict[str, Any]:
    """Get factory summary."""

    return {
        "agent_types": list_agent_types(),
        "configs": {
            at: {
                "behaviors": cfg["behaviors"],
                "unit_type": cfg["unit_type"],
            }
            for at, cfg in AGENT_CONFIGS.items()
        },
    }