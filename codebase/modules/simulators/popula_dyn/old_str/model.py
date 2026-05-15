import numpy as np
import pandas as pd
from typing import Dict, List, Tuple, Optional, Any, Set
from base_classes import Model, DataCollector
from agents import LandPatch, FarmerAgent, HealerAgent, ToolmakerAgent, TraderAgent
from constants import PARAMS

# === Model Class ===

class AgriculturalModel(Model):
    #Main model orchestrating agents and space.

    def __init__(self, params: Dict[str, Any] = PARAMS) -> None:
        """Initialize the agricultural model with agents and grid."""
        super().__init__()
        self.params = params
        seed = params.get("seed", None)
        if seed is not None:
            self.random = np.random.RandomState(seed)
        self._next_id = 0
        grid_width = self.params.get("grid_width", PARAMS["grid_width"])
        grid_height = self.params.get("grid_height", PARAMS["grid_height"])
        from base_classes import MultiGrid
        self.grid = MultiGrid(grid_width, grid_height, True)
        # Use Mesa's built-in agents set instead of custom list
        self.successful_healings = 0
        self.tools_produced = 0
        self.trades_executed = 0
        self.wealth_traded = 0
        # Create LandPatches (fill grid)
        for x in range(grid_width):
            for y in range(grid_height):
                patch = LandPatch(self.next_id, self, np.random.uniform(1, 10))
                self.grid.place_agent(patch, (x, y))
                self.agents.add(patch)
        # Initialize wealth for specialists
        self.healer_wealth = 5.0
        self.toolmaker_wealth = 5.0
        self.trader_wealth = 5.0
        # Create Farmers
        initial_pop = self.params.get("initial_pop", PARAMS["initial_pop"])
        for i in range(initial_pop):
            x = self.random.randint(0, grid_width)
            y = self.random.randint(0, grid_height)
            age = self.random.randint(0, self.params.get("max_age", PARAMS["max_age"]))
            gender = self.random.choice(["M", "F"])
            agent = FarmerAgent(self.next_id, self, age, gender)
            self.grid.place_agent(agent, (x, y))
            self.agents.add(agent)
        # Create Healers
        initial_healers = self.params.get("initial_healers", PARAMS["initial_healers"])
        for i in range(initial_healers):
            x = self.random.randint(0, grid_width)
            y = self.random.randint(0, grid_height)
            agent = HealerAgent(
                self.next_id,
                self,
                healing_rate=self.params.get("healer_healing_rate", PARAMS["healer_healing_rate"]),
                healing_cost=self.params.get("healer_healing_cost", PARAMS["healer_healing_cost"])
            )
            self.grid.place_agent(agent, (x, y))
            self.agents.add(agent)
        # Create Toolmakers
        initial_toolmakers = self.params.get("initial_toolmakers", PARAMS["initial_toolmakers"])
        for i in range(initial_toolmakers):
            x = self.random.randint(0, grid_width)
            y = self.random.randint(0, grid_height)
            agent = ToolmakerAgent(
                self.next_id,
                self,
                tool_production_rate=self.params.get("toolmaker_production_rate", PARAMS["toolmaker_production_rate"]),
                tool_quality=self.params.get("toolmaker_quality", PARAMS["toolmaker_quality"]),
                tool_cost=self.params.get("toolmaker_cost", PARAMS["toolmaker_cost"])
            )
            self.grid.place_agent(agent, (x, y))
            self.agents.add(agent)
        # Create Traders
        initial_traders = self.params.get("initial_traders", PARAMS["initial_traders"])
        for i in range(initial_traders):
            x = self.random.randint(0, grid_width)
            y = self.random.randint(0, grid_height)
            agent = TraderAgent(
                self.next_id,
                self,
                trade_margin=self.params.get("trader_margin", PARAMS["trader_margin"]),
                trade_range=self.params.get("trader_range", PARAMS["trader_range"])
            )
            self.grid.place_agent(agent, (x, y))
            self.agents.add(agent)
        self.fertility_movement = params.get("fertility_movement", False)
        self.datacollector = DataCollector(
            model_reporters={
                "Population": lambda m: len([a for a in m.agents if isinstance(a, FarmerAgent) and getattr(a, 'alive', True)]),
                "Total_Wealth": lambda m: sum(getattr(a, 'wealth', 0) for a in m.agents if hasattr(a, 'wealth') and getattr(a, 'alive', True)),
                "Avg_Skill": lambda m: np.mean([a.skill for a in m.agents if isinstance(a, FarmerAgent) and getattr(a, 'alive', True)]) if any(isinstance(a, FarmerAgent) and getattr(a, 'alive', True) for a in m.agents) else 0,
                "Births": "births",
                "Deaths": "deaths",
                "Healer_Count": lambda m: len([a for a in m.agents if isinstance(a, HealerAgent) and getattr(a, 'alive', True)]),
                "Toolmaker_Count": lambda m: len([a for a in m.agents if isinstance(a, ToolmakerAgent) and getattr(a, 'alive', True)]),
                "Trader_Count": lambda m: len([a for a in m.agents if isinstance(a, TraderAgent) and getattr(a, 'alive', True)]),
                "Successful_Healings": "successful_healings",
                "Tools_Produced": "tools_produced",
                "Trades_Executed": "trades_executed",
                "Wealth_Traded": "wealth_traded",
            }
        )

    def step(self) -> None:
        """Advance the model by one time step."""
        self.births = 0
        self.deaths = 0
        self.successful_healings = 0  # Reset counters each step
        self.tools_produced = 0
        self.trades_executed = 0
        self.wealth_traded = 0

        # Activate patches first (sequential regrowth)
        patch_agents = [a for a in self.agents if isinstance(a, LandPatch)]
        for agent in patch_agents:
            agent.step()

        # Then random farmers and other agents (filter alive where applicable)
        # Create a list of agents that are not LandPatches
        active_agents = [a for a in self.agents if not isinstance(a, LandPatch)]
        # Filter out dead agents from this list if they have an 'alive' attribute
        active_agents = [a for a in active_agents if getattr(a, 'alive', True)]

        # Shuffle to randomize order
        self.random.shuffle(active_agents)
        for agent in active_agents:
            try:
                agent.step()
            except Exception as e:
                print(f"Error in agent {agent.unique_id} step: {e}")
                # Continue with other agents

        # Remove dead agents from the agent set *after* all agents have stepped
        dead_agents = [a for a in self.agents if hasattr(a, 'alive') and not a.alive]
        for agent in dead_agents:
            self.grid.remove_agent(agent)
            self.agents.remove(agent)

        self.datacollector.collect(self)

    def fertility_based_move(self, agent) -> None:
        """Move the agent to the neighboring patch with the highest fertility if better than current."""
        if not isinstance(agent, FarmerAgent):
            return

        # Get current fertility
        cell_contents = self.grid.get_cell_list_contents([agent.pos])
        current_fertility = 0
        for c in cell_contents:
            if isinstance(c, LandPatch):
                current_fertility = c.fertility
                break

        # Scan neighborhood
        neighborhood = self.grid.get_neighborhood(agent.pos, moore=True, include_center=True, radius=self.params.get("vision", 2))
        best_pos = agent.pos
        best_fertility = current_fertility
        for pos in neighborhood:
            cell_contents = self.grid.get_cell_list_contents([pos])
            for c in cell_contents:
                if isinstance(c, LandPatch):
                    if c.fertility > best_fertility:
                        best_fertility = c.fertility
                        best_pos = pos
                    break

        if best_pos != agent.pos:
            self.grid.move_agent(agent, best_pos)