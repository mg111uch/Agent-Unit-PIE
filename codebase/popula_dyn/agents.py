"""
metadata:
  summary: "This Python file defines agent classes for a population dynamics simulation, including LandPatch for crop regrowth, FarmerAgent with farming and lifecycle behaviors, HealerAgent for health services, ToolmakerAgent for tool production enhancing skills, and TraderAgent for wealth exchange."
  dependencies: ["base_classes.py", "constants.py"]
  tags: ["simulation", "agents", "population", "farming", "economy"]
  hierarchy_mapping:
    classes:
      LandPatch:
        inherits: Agent
        methods: ["__init__", "step"]
      FarmerAgent:
        inherits: Agent
        methods: ["__init__", "step", "move", "harvest", "consume", "interact_with_specialists", "mate", "check_death"]
      HealerAgent:
        inherits: Agent
        methods: ["__init__", "step"]
      ToolmakerAgent:
        inherits: Agent
        methods: ["__init__", "step"]
      TraderAgent:
        inherits: Agent
        methods: ["__init__", "step"]
    functions: []
  graph_methods:
    dependency_graph: {"nodes": [{"id": "LandPatch", "type": "class"}, {"id": "FarmerAgent", "type": "class"}, {"id": "HealerAgent", "type": "class"}, {"id": "ToolmakerAgent", "type": "class"}, {"id": "TraderAgent", "type": "class"}], "edges": []}
    cfg_outline: "FarmerAgent.step: if not alive return; age+=1; move; harvest; consume; interact_with_specialists; mate; check_death. LandPatch.step: regrow crops. Specialist steps: perform their actions."
"""
# === Imports ===
import numpy as np
from typing import Dict, List, Tuple, Optional, Any, Set
from base_classes import Agent
from constants import PARAMS

# === Agent Classes ===

class LandPatch(Agent):
    """Passive agent representing fertile land patches with crop regrowth.

    Attributes:
        fertility (float): Base crop yield (0-10).
        current_crops (float): Current available crops, regrows each step.
    """
    def __init__(self, unique_id: int, model: 'Model', fertility: float = 5.0) -> None:
        """Initialize the land patch with fertility level."""
        super().__init__(unique_id, model)
        self.fertility = fertility  # Base crop yield (0-10)
        self.current_crops = fertility  # Current available crops (regrows each step)

    def step(self) -> None:
        """Regrow crops towards base fertility."""
        regrowth_rate = 0.1
        self.current_crops = min(self.fertility, self.current_crops + (self.fertility - self.current_crops) * regrowth_rate)

class FarmerAgent(Agent):
    """Active agent representing farmers who farm, consume, mate, and move.

    Attributes:
        age (int): Age of the farmer.
        gender (str): Gender ('M' or 'F').
        skill (float): Farming efficiency (0-1).
        wealth (float): Stored crops/food.
        alive (bool): Whether the farmer is alive.
        children (List[int]): List of child agent IDs.
        death_prob_modifier (float): Modifier to death probability from healers.
    """
    def __init__(self, unique_id: int, model: 'Model', age: Optional[int] = None, gender: Optional[str] = None, skill: float = 0.5) -> None:
        """Initialize the farmer agent with given or random attributes."""
        super().__init__(unique_id, model)
        self.age = age if age is not None else np.random.randint(0, PARAMS["max_age"])
        self.gender = gender if gender else np.random.choice(["M", "F"])
        self.skill = skill  # Farming efficiency (0-1)
        self.wealth = 5.0  # Stored crops/food
        self.alive = True
        self.children: List[int] = []  # List of child agent IDs (for inheritance later)
        self.death_prob_modifier = 0.0  # Modifier set by Healers

    def step(self) -> None:
        """Perform one step of farmer behavior."""
        if not self.alive:
            return

        # Reset death probability modifier at the start of the step
        self.death_prob_modifier = 0.0

        # Chain of behaviors (modular: each can be overridden for game)
        self.age += 1
        self.move()
        self.harvest()
        self.consume()
        self.interact_with_specialists()  # New interaction step
        self.mate()
        self.check_death()

    def move(self) -> None:
        """Move to a random adjacent cell."""
        # TODO: From Schelling/Sugarscape: Scan neighborhood (vision radius), move to higher fertility if unhappy
        # Skeleton: Random move to adjacent cell
        possible_moves = self.model.grid.get_neighborhood(self.pos, moore=True, include_center=False)
        if possible_moves:
            new_pos = possible_moves[self.random.randint(len(possible_moves))]
            self.model.grid.move_agent(self, new_pos)

    def harvest(self) -> None:
        """Harvest crops from the land patch at current position."""
        cell_contents = self.model.grid.get_cell_list_contents([self.pos])
        land_patches = [c for c in cell_contents if isinstance(c, LandPatch)]
        if land_patches:
            patch = land_patches[0]
            # Harvest amount: scaled by skill, up to available crops
            max_harvest = self.skill * 3.0  # Max per year based on skill
            harvest_amount = min(patch.current_crops, max_harvest)
            self.wealth += harvest_amount
            patch.current_crops -= harvest_amount

    def consume(self) -> None:
        """Consume food based on metabolism."""
        self.wealth -= PARAMS["metabolism"]
        if self.wealth < 0:
            self.wealth = 0  # No negative wealth, but triggers higher death risk in check_death

    def interact_with_specialists(self) -> None:
        """Interact with nearby specialists (healers, toolmakers, traders)."""
        neighbors = self.model.grid.get_neighbors(self.pos, moore=True, radius=PARAMS["vision"], include_center=False)

        # Interact with Healers
        healers = [n for n in neighbors if isinstance(n, HealerAgent)]
        if healers:
            healer = self.random.choice(healers)
            # Farmer attempts to get healing (Healer's step handles the cost and success)
            # The healer agent's step method will modify the farmer's death_prob_modifier if successful

        # Interact with Toolmakers
        toolmakers = [n for n in neighbors if isinstance(n, ToolmakerAgent)]
        if toolmakers:
            toolmaker = self.random.choice(toolmakers)
            # Farmer attempts to buy a tool (Toolmaker's step handles the cost and inventory)
            # The toolmaker agent's step method will modify the farmer's skill if successful

        # Interact with Traders
        traders = [n for n in neighbors if isinstance(n, TraderAgent)]
        if traders:
            trader = self.random.choice(traders)
            # Farmer potentially engages in trade (Trader's step handles the transaction)
            # The trader agent's step method will modify the wealth of both parties if trade occurs

    def mate(self) -> None:
        """Attempt to mate with a nearby fertile partner."""
        # Only if fertile
        if self.age < PARAMS["fertile_min_age"] or self.age > PARAMS["fertile_max_age"]:
            return

        # Find potential partners in neighborhood
        neighbors = self.model.grid.get_neighbors(self.pos, moore=True, radius=PARAMS["vision"])
        potential_partners = [
            n for n in neighbors
            if isinstance(n, FarmerAgent) and n.alive and n.gender != self.gender
            and PARAMS["fertile_min_age"] <= n.age <= PARAMS["fertile_max_age"]
        ]

        if potential_partners:
            partner = self.random.choice(potential_partners)
            if self.random.random() < PARAMS["birth_rate"]:
                # Create child
                child = FarmerAgent(
                    self.model.next_id,  # Use next_id for child unique_id
                    self.model,
                    age=0,
                    gender=self.random.choice(["M", "F"]),
                    skill=(self.skill + partner.skill) / 2
                )
                # Place at parent's pos (or random neighbor for space)
                child_pos = self.pos
                # Try to place at a random neighbor if current pos is preferred, but since MultiGrid allows multiple agents, place directly
                neighbor_list = self.model.grid.get_neighborhood(self.pos, moore=True, include_center=True)
                if neighbor_list:
                    child_pos = neighbor_list[self.random.randint(len(neighbor_list))]

                self.model.grid.place_agent(child, child_pos)
                self.model.agents.add(child)
                self.children.append(child.unique_id)
                partner.children.append(child.unique_id)
                self.model.births += 1

    def check_death(self) -> None:
        """Check if the farmer dies based on various factors."""
        # Base death prob, modified by age, starvation, etc.
        death_prob = PARAMS["death_rate"]

        # Starvation multiplier
        if self.wealth < 1.0:
            death_prob *= 5.0

        # Age multiplier (increases after 60)
        death_prob *= 1.5

        # Hard max age
        if self.age > PARAMS["max_age"]:
            death_prob = 1.0

        # Apply healer modifier
        death_prob += self.death_prob_modifier
        death_prob = max(0.0, death_prob)  # Ensure death probability is not negative

        if self.random.random() < death_prob:
            self.model.deaths += 1
            self.alive = False
            # Agent removal from grid and model.agents list is now handled in the model's step function

class HealerAgent(Agent):
    """Agent representing a healer who can improve farmer health.

    Attributes:
        healing_rate (float): Probability of successful healing attempt.
        healing_cost (float): Wealth cost for healing a farmer.
        wealth (float): Healer's wealth.
    """
    def __init__(self, unique_id: int, model: 'Model', healing_rate: float = 0.1, healing_cost: float = 0.5) -> None:
        """Initialize the healer agent."""
        super().__init__(unique_id, model)
        self.healing_rate = healing_rate  # Probability of successful healing attempt
        self.healing_cost = healing_cost  # Wealth cost for healing a farmer
        self.wealth = model.healer_wealth

    def step(self) -> None:
        """Attempt to heal nearby farmers."""
        # Find nearby farmers
        neighbors = self.model.grid.get_neighbors(self.pos, moore=True, radius=1)
        potential_patients = [
            n for n in neighbors
            if isinstance(n, FarmerAgent) and n.alive and n.wealth >= self.healing_cost  # Only heal if farmer can afford it
        ]

        if potential_patients:
            patient = self.random.choice(potential_patients)
            if self.random.random() < self.healing_rate:
                # Reduce farmer's death probability for this step
                patient.death_prob_modifier = -0.5  # Example: Halve the effective death probability
                patient.wealth -= self.healing_cost  # Charge the farmer
                self.model.successful_healings += 1
            else:
                # Still charge a smaller fee for attempted healing? Or just no effect?
                # For now, no effect if healing fails
                pass

class ToolmakerAgent(Agent):
    """Agent representing a toolmaker who produces tools to improve farming skill.

    Attributes:
        tool_production_rate (float): Probability of producing a tool each step.
        tool_quality (float): Amount skill is increased by using a tool.
        tool_cost (float): Wealth cost for a farmer to buy a tool.
        inventory (int): Number of tools the toolmaker has.
        wealth (float): Toolmaker's wealth.
    """
    def __init__(self, unique_id: int, model: 'Model', tool_production_rate: float = 0.1, tool_quality: float = 0.1, tool_cost: float = 1.0) -> None:
        """Initialize the toolmaker agent."""
        super().__init__(unique_id, model)
        self.tool_production_rate = tool_production_rate  # Probability of producing a tool each step
        self.tool_quality = tool_quality  # Amount skill is increased by using a tool
        self.tool_cost = tool_cost  # Wealth cost for a farmer to buy a tool
        self.inventory = 0  # Number of tools the toolmaker has
        self.wealth = model.toolmaker_wealth

    def step(self) -> None:
        """Produce tools and sell them to nearby farmers."""
        # Produce tools
        if self.random.random() < self.tool_production_rate:
            self.inventory += 1
            self.model.tools_produced += 1

        # Find nearby farmers
        neighbors = self.model.grid.get_neighbors(self.pos, moore=True, radius=1)
        potential_customers = [
            n for n in neighbors
            if isinstance(n, FarmerAgent) and n.alive and n.wealth >= self.tool_cost
        ]

        # Trade with farmers
        if self.inventory > 0 and potential_customers:
            customer = self.random.choice(potential_customers)
            # Farmer buys a tool
            customer.wealth -= self.tool_cost
            customer.skill += self.tool_quality  # Farmer's skill increases
            self.wealth += self.tool_cost  # Toolmaker gains wealth
            self.inventory -= 1

class TraderAgent(Agent):
    """Agent representing a trader who facilitates exchange between agents.

    Attributes:
        trade_margin (float): Percentage of wealth gained by trader.
        trade_range (int): Radius for finding trading partners.
        wealth (float): Trader's wealth.
    """
    def __init__(self, unique_id: int, model: 'Model', trade_margin: float = 0.05, trade_range: int = 2) -> None:
        """Initialize the trader agent."""
        super().__init__(unique_id, model)
        self.trade_margin = trade_margin  # Percentage of wealth gained by trader
        self.trade_range = trade_range  # Radius for finding trading partners
        self.wealth = model.trader_wealth

    def step(self) -> None:
        """Facilitate trade between rich and poor agents."""
        # Find potential trading partners (all agents except self)
        neighbors = self.model.grid.get_neighbors(self.pos, moore=True, radius=self.trade_range)
        potential_traders = [n for n in neighbors if n.unique_id != self.unique_id]

        # Simple trading example: Trader moves wealth from a rich agent to a poor agent, taking a cut
        if len(potential_traders) >= 2:
            # Sort by wealth
            sorted_traders = sorted(potential_traders, key=lambda agent: getattr(agent, 'wealth', 0), reverse=True)
            richest = sorted_traders[0]
            poorest = sorted_traders[-1]

            # Ensure both are agents with wealth and are not the trader
            if isinstance(richest, (FarmerAgent, ToolmakerAgent, HealerAgent)) and \
               isinstance(poorest, (FarmerAgent, ToolmakerAgent, HealerAgent)) and \
               hasattr(richest, 'wealth') and hasattr(poorest, 'wealth') and \
               richest.unique_id != self.unique_id and poorest.unique_id != self.unique_id:

                trade_amount = min(richest.wealth * 0.1, 5.0)  # Trade up to 10% of richest wealth, max 5

                if trade_amount > 0:
                    margin_amount = trade_amount * self.trade_margin
                    transfer_amount = trade_amount - margin_amount

                    richest.wealth -= trade_amount
                    poorest.wealth += transfer_amount
                    self.wealth += margin_amount  # Trader takes a cut
                    self.model.trades_executed += 1
                    self.model.wealth_traded += trade_amount