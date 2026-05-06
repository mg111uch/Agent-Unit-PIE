"""
metadata:
  summary: "This Python file provides base classes for multi-agent simulations, including Agent for entity behavior, MultiGrid for toroidal spatial positioning, Model for simulation orchestration, and DataCollector for tracking metrics."
  dependencies: []
  tags: ["simulation", "base_classes", "grid", "agents", "data_collection"]
  hierarchy_mapping:
    classes:
      Agent:
        inherits: null
        methods: ["__init__", "step"]
      MultiGrid:
        inherits: null
        methods: ["__init__", "place_agent", "remove_agent", "move_agent", "get_cell_list_contents", "get_neighborhood", "is_cell_empty", "get_neighbors"]
      Model:
        inherits: null
        methods: ["__init__", "next_id", "step"]
      DataCollector:
        inherits: null
        methods: ["__init__", "collect", "get_model_vars_dataframe"]
    functions: []
  graph_methods:
    dependency_graph: {"nodes": [{"id": "Agent", "type": "class"}, {"id": "MultiGrid", "type": "class"}, {"id": "Model", "type": "class"}, {"id": "DataCollector", "type": "class"}], "edges": []}
    cfg_outline: "Agent.step: pass. Model.step: pass. DataCollector.collect: iterate reporters, append data."
"""
# === Imports ===
import numpy as np
import pandas as pd
from typing import Dict, List, Tuple, Optional, Any, Set

# === Base Classes ===

class Agent:
    """Base class for all agents in the simulation.

    Attributes:
        unique_id (int): Unique identifier for the agent.
        model (Model): Reference to the model containing the agent.
        pos (Optional[Tuple[int, int]]): Current position on the grid.
        random (np.random.RandomState): Random number generator.
    """
    def __init__(self, unique_id: int, model: 'Model') -> None:
        """Initialize the agent with unique ID and model reference."""
        self.unique_id = unique_id
        self.model = model
        self.pos: Optional[Tuple[int, int]] = None
        self.random = self.model.random

    def step(self) -> None:
        """Perform one step of the agent's behavior. To be overridden by subclasses."""
        pass

class MultiGrid:
    """Custom grid class for managing agent positions in a toroidal space.

    Attributes:
        width (int): Width of the grid.
        height (int): Height of the grid.
        torus (bool): Whether the grid wraps around edges.
        grid (Dict[Tuple[int, int], List[Agent]]): Dictionary mapping positions to lists of agents.
    """
    def __init__(self, width: int, height: int, torus: bool = True) -> None:
        """Initialize the grid with given dimensions."""
        self.width = width
        self.height = height
        self.torus = torus
        self.grid: Dict[Tuple[int, int], List[Agent]] = {}
        for x in range(width):
            for y in range(height):
                self.grid[(x, y)] = []

    def place_agent(self, agent: Agent, pos: Tuple[int, int]) -> None:
        """Place an agent at the specified position."""
        if pos in self.grid:
            self.grid[pos].append(agent)
            agent.pos = pos

    def remove_agent(self, agent: Agent) -> None:
        """Remove an agent from its current position."""
        if agent.pos in self.grid:
            self.grid[agent.pos].remove(agent)
            agent.pos = None

    def move_agent(self, agent: Agent, pos: Tuple[int, int]) -> None:
        """Move an agent to a new position."""
        self.remove_agent(agent)
        self.place_agent(agent, pos)

    def get_cell_list_contents(self, positions: List[Tuple[int, int]]) -> List[Agent]:
        """Get all agents at the specified positions."""
        contents = []
        for pos in positions:
            if pos in self.grid:
                contents.extend(self.grid[pos])
        return contents

    def get_neighborhood(self, pos: Tuple[int, int], moore: bool = True, include_center: bool = False, radius: int = 1) -> List[Tuple[int, int]]:
        """Get neighboring positions within the given radius."""
        x, y = pos
        neighbors = []
        for dx in range(-radius, radius + 1):
            for dy in range(-radius, radius + 1):
                if not moore and abs(dx) + abs(dy) > radius:
                    continue
                if not include_center and dx == 0 and dy == 0:
                    continue
                nx, ny = x + dx, y + dy
                if self.torus:
                    nx %= self.width
                    ny %= self.height
                if 0 <= nx < self.width and 0 <= ny < self.height:
                    neighbors.append((nx, ny))
        return neighbors

    def is_cell_empty(self, pos: Tuple[int, int]) -> bool:
        """Check if a cell is empty."""
        return len(self.grid.get(pos, [])) == 0

    def get_neighbors(self, pos: Tuple[int, int], moore: bool = True, radius: int = 1, include_center: bool = False) -> List[Agent]:
        """Get all agents in neighboring positions."""
        neighborhood = self.get_neighborhood(pos, moore, include_center, radius)
        neighbors = []
        for p in neighborhood:
            neighbors.extend(self.grid.get(p, []))
        return neighbors

class Model:
    """Base class for simulation models.

    Attributes:
        agents (Set[Agent]): Set of all agents in the model.
        random (np.random.RandomState): Random number generator.
        _next_id (int): Counter for assigning unique IDs.
    """
    def __init__(self) -> None:
        """Initialize the model with an empty agent set and random state."""
        self.agents: Set[Agent] = set()
        self.random = np.random.RandomState()
        self._next_id = 0

    @property
    def next_id(self) -> int:
        """Get the next unique ID and increment the counter."""
        self._next_id += 1
        return self._next_id - 1

    def step(self) -> None:
        """Perform one step of the simulation. To be overridden by subclasses."""
        pass

class DataCollector:
    """Class for collecting data from the model during simulation.

    Attributes:
        model_reporters (Dict[str, Any]): Dictionary of reporter functions or attributes.
        data (Dict[str, List[Any]]): Collected data for each reporter.
    """
    def __init__(self, model_reporters: Dict[str, Any]) -> None:
        """Initialize the data collector with reporters."""
        self.model_reporters = model_reporters
        self.data: Dict[str, List[Any]] = {name: [] for name in model_reporters}

    def collect(self, model: Model) -> None:
        """Collect data from the model using the reporters."""
        for name, func in self.model_reporters.items():
            if callable(func):
                self.data[name].append(func(model))
            else:
                self.data[name].append(getattr(model, func))

    def get_model_vars_dataframe(self) -> pd.DataFrame:
        """Return the collected data as a pandas DataFrame."""
        import pandas as pd
        return pd.DataFrame(self.data)