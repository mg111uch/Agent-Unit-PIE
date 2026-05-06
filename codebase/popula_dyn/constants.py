"""
metadata:
  summary: "This Python file contains a dictionary of constants for the population simulation, specifying initial populations, grid dimensions, birth and death rates, age parameters, metabolism, vision, and specialist agent configurations."
  dependencies: []
  tags: ["constants", "parameters", "simulation", "config"]
  hierarchy_mapping:
    classes: {}
    functions: []
  graph_methods:
    dependency_graph: {"nodes": [], "edges": []}
    cfg_outline: "No control flow; static parameter definitions."
"""
# === Imports ===
from typing import Dict, Any

# === Constants ===
PARAMS: Dict[str, Any] = {
    "initial_pop": 2000,
    "grid_width": 50,
    "grid_height": 50,
    "birth_rate": 0.04,  # Probability of mating success
    "death_rate": 0.01,  # Base death probability
    "fertile_min_age": 15,
    "fertile_max_age": 50,
    "max_age": 60,
    "metabolism": 1,  # Food units consumed per year
    "vision": 2,  # Cells to scan for movement/mating
    "years": 100,  # Simulation length
    "seed": None,  # For reproducibility
    # New agent initial counts
    "initial_healers": 10,
    "initial_toolmakers": 10,
    "initial_traders": 10,
    # New agent parameters (add if needed to tune)
    "healer_healing_rate": 0.1,
    "healer_healing_cost": 0.5,
    "toolmaker_production_rate": 0.1,
    "toolmaker_quality": 0.1,
    "toolmaker_cost": 1.0,
    "trader_margin": 0.05,
    "trader_range": 2,
}