"""
core/simulation_model.py

Behavior-based simulation model.

Purpose
-------
Replaces old_str/model.py AgriculturalModel with behavior-based UnitAgent.

Usage
-----
    from core.simulation_model import SimulationModel
    
    model = SimulationModel(params)
    model.step()  # Advance one tick
    model.run(years=100)  # Run full simulation
"""

from typing import Dict, Any, Optional, List
import numpy as np
import pandas as pd

from modules.simulators.popula_dyn.behavior_registry import BehaviorRegistry
from modules.simulators.popula_dyn.core.spatial_engine import SpatialEngine
from modules.simulators.popula_dyn.core.unit_agent import UnitAgent
from modules.simulators.popula_dyn.core.agent_factory import (
    AGENT_CONFIGS,
    create_unit_config,
)
from modules.simulators.popula_dyn.constants import PARAMS


class SimulationModel:
    """
    Behavior-based agricultural simulation model.
    """

    def __init__(
        self,
        params: Dict[str, Any] = PARAMS,
    ):
        self.params = params

        seed = params.get("seed", None)
        self.random = np.random.RandomState(seed)

        self.units: Dict[str, UnitAgent] = {}

        self.behavior_registry = BehaviorRegistry()

        grid_width = params.get("grid_width", PARAMS["grid_width"])
        grid_height = params.get("grid_height", PARAMS["grid_height"])
        self.spatial_engine = SpatialEngine(
            width=grid_width,
            height=grid_height,
            torus=True,
        )

        self.step_count = 0
        self.births = 0
        self.deaths = 0
        self.successful_healings = 0
        self.tools_produced = 0
        self.trades_executed = 0
        self.wealth_traded = 0

        self._init_units()

        self.datacollector = DataCollector(
            model_reporters={
                "Population": lambda m: m.get_population_count(),
                "Total_Wealth": lambda m: m.get_total_wealth(),
                "Avg_Skill": lambda m: m.get_average_skill(),
                "Births": "births",
                "Deaths": "deaths",
                "Healer_Count": lambda m: m.get_unit_type_count("specialist", "heal"),
                "Toolmaker_Count": lambda m: m.get_unit_type_count("specialist", "produce"),
                "Trader_Count": lambda m: m.get_unit_type_count("specialist", "trade_ag"),
                "Successful_Healings": "successful_healings",
                "Tools_Produced": "tools_produced",
                "Trades_Executed": "trades_executed",
                "Wealth_Traded": "wealth_traded",
            }
        )

    def _init_units(self) -> None:
        """Initialize all units from agent configs."""

        params = self.params
        grid_width = params.get("grid_width", PARAMS["grid_width"])
        grid_height = params.get("grid_height", PARAMS["grid_height"])
        rng = self.random

        land_patches = params.get("grid_width", PARAMS["grid_width"]) * params.get(
            "grid_height", PARAMS["grid_height"]
        )
        for x in range(grid_width):
            for y in range(grid_height):
                fertility = rng.uniform(1, 10)
                unit = self._create_unit(
                    "land",
                    position=(x, y),
                    fertility=fertility,
                    seed=rng.randint(0, 100000),
                )
                unit.set_state("fertility", fertility)
                unit.set_state("current_crops", fertility)

        initial_pop = params.get("initial_pop", PARAMS["initial_pop"])
        for _ in range(initial_pop):
            x = rng.randint(0, grid_width)
            y = rng.randint(0, grid_height)
            age = rng.randint(0, params.get("max_age", PARAMS["max_age"]))
            gender = rng.choice(["M", "F"])
            unit = self._create_unit(
                "farmer",
                position=(x, y),
                age=age,
                gender=gender,
                seed=rng.randint(0, 100000),
            )
            unit.set_state("age", age)
            unit.set_state("gender", gender)

        initial_healers = params.get("initial_healers", PARAMS["initial_healers"])
        for _ in range(initial_healers):
            x = rng.randint(0, grid_width)
            y = rng.randint(0, grid_height)
            unit = self._create_unit(
                "healer",
                position=(x, y),
                healing_rate=params.get("healer_healing_rate", PARAMS["healer_healing_rate"]),
                healing_cost=params.get("healer_healing_cost", PARAMS["healer_healing_cost"]),
                seed=rng.randint(0, 100000),
            )

        initial_toolmakers = params.get("initial_toolmakers", PARAMS["initial_toolmakers"])
        for _ in range(initial_toolmakers):
            x = rng.randint(0, grid_width)
            y = rng.randint(0, grid_height)
            unit = self._create_unit(
                "toolmaker",
                position=(x, y),
                tool_production_rate=params.get("toolmaker_production_rate", PARAMS["toolmaker_production_rate"]),
                tool_quality=params.get("toolmaker_quality", PARAMS["toolmaker_quality"]),
                tool_cost=params.get("toolmaker_cost", PARAMS["toolmaker_cost"]),
                seed=rng.randint(0, 100000),
            )

        initial_traders = params.get("initial_traders", PARAMS["initial_traders"])
        for _ in range(initial_traders):
            x = rng.randint(0, grid_width)
            y = rng.randint(0, grid_height)
            unit = self._create_unit(
                "trader",
                position=(x, y),
                trade_margin=params.get("trader_margin", PARAMS["trader_margin"]),
                trade_range=params.get("trader_range", PARAMS["trader_range"]),
                seed=rng.randint(0, 100000),
            )

    def _create_unit(
        self,
        agent_type: str,
        position: tuple,
        seed: Optional[int] = None,
        **overrides,
    ) -> UnitAgent:
        """Create and register a unit."""

        config = create_unit_config(
            agent_type=agent_type,
            model=self,
            position=position,
            seed=seed,
            **overrides,
        )

        unit = UnitAgent(
            unit_id=config["unit_id"],
            unit_type=config["unit_type"],
            state=config.get("state", {}),
            resources=config.get("resources", {}),
            behaviors=config["behaviors"],
        )

        unit.alive = config.get("alive", True)
        unit.set_state("position", position)

        self.units[unit.unit_id] = unit
        self.spatial_engine.place_agent(unit, position)

        return unit

    def add_unit(self, unit_data: Dict[str, Any]) -> UnitAgent:
        """Add a new unit to the simulation."""

        unit = UnitAgent(
            unit_id=unit_data.get("unit_id"),
            unit_type=unit_data.get("unit_type", "human"),
            state=unit_data.get("state", {}),
            resources=unit_data.get("resources", {}),
            behaviors=unit_data.get("behaviors", []),
        )

        unit.alive = unit_data.get("alive", True)

        position = unit_data.get("position")
        if position:
            unit.set_state("position", position)
            self.spatial_engine.place_agent(unit, position)
            self.units[unit.unit_id] = unit
            self.births += 1

        return unit

    def step(self) -> None:
        """Advance simulation by one tick."""

        self.births = 0
        self.deaths = 0
        self.successful_healings = 0
        self.tools_produced = 0
        self.trades_executed = 0
        self.wealth_traded = 0

        world_state = {
            "params": self.params,
            "grid": self.spatial_engine,
            "model": self,
            "seed": self.random.randint(0, 1000000),
        }

        land_units = [
            u for u in self.units.values()
            if u.unit_type == "land"
        ]
        for unit in land_units:
            self._execute_behaviors(unit, world_state)

        active_units = [
            u for u in self.units.values()
            if u.unit_type != "land" and u.alive
        ]
        self.random.shuffle(active_units)

        for unit in active_units:
            if not unit.alive:
                continue

            age = unit.get_state("age", 0)
            if age is not None:
                unit.set_state("age", age + 1)

            self._execute_behaviors(unit, world_state)

        dead_units = [u for u in self.units.values() if not u.alive]
        for unit in dead_units:
            position = unit.get_state("position")
            if position:
                self.spatial_engine.remove_agent(unit)
            del self.units[unit.unit_id]
            self.deaths += 1

        self.step_count += 1
        self.datacollector.collect(self)

    def _execute_behaviors(
        self,
        unit: UnitAgent,
        world_state: Dict[str, Any],
    ) -> None:
        """Execute all behaviors for a unit."""

        for behavior_name in unit.behaviors:
            behavior = self.behavior_registry.get_behavior(behavior_name)
            if behavior is None:
                continue

            try:
                result = behavior.execute(unit=unit, world_state=world_state)
                if result:
                    self._process_behavior_result(unit, result)
            except Exception as e:
                pass

    def _process_behavior_result(
        self,
        unit: UnitAgent,
        result: Dict[str, Any],
    ) -> None:
        """Process behavior output."""

        state_updates = result.get("state_updates", {})
        for key, value in state_updates.items():
            unit.set_state(key, value)

        resource_updates = result.get("resource_updates", {})
        for key, value in resource_updates.items():
            unit.modify_resource(key, value)

        events = result.get("events", [])
        for event in events:
            event_type = event.get("event_type")
            if event_type == "birth":
                self.births += 1
            elif event_type == "death":
                self.deaths += 1
            elif event_type == "healed":
                self.successful_healings += 1
            elif event_type == "tool_produced":
                self.tools_produced += 1
            elif event_type == "trade_executed":
                self.trades_executed += 1
                self.wealth_traded += event.get("amount", 0)

    def run(self, years: Optional[int] = None) -> None:
        """Run simulation for specified years."""

        years = years or self.params.get("years", PARAMS["years"])
        for _ in range(years):
            self.step()

    def get_population_count(self) -> int:
        """Get count of alive humans."""

        return sum(
            1
            for u in self.units.values()
            if u.unit_type == "human" and u.alive
        )

    def get_total_wealth(self) -> float:
        """Get total wealth of alive units."""

        return sum(
            u.get_resource("wealth", 0)
            for u in self.units.values()
            if u.alive and u.get_resource("wealth", 0) > 0
        )

    def get_average_skill(self) -> float:
        """Get average skill of alive humans."""

        skills = [
            u.get_state("skill", 0)
            for u in self.units.values()
            if u.unit_type == "human"
            and u.alive
            and u.get_state("skill") is not None
        ]
        return np.mean(skills) if skills else 0

    def get_unit_type_count(
        self,
        unit_type: str,
        behavior: Optional[str] = None,
    ) -> int:
        """Get count of units by type and optional behavior."""

        count = 0
        for u in self.units.values():
            if u.unit_type != unit_type:
                continue
            if behavior and behavior not in u.behaviors:
                continue
            if u.alive:
                count += 1
        return count

    def get_dataframe(self) -> pd.DataFrame:
        """Get collected data as dataframe."""

        return self.datacollector.get_model_vars_dataframe()

    def summary(self) -> Dict[str, Any]:
        """Get simulation summary."""

        return {
            "step_count": self.step_count,
            "total_units": len(self.units),
            "population": self.get_population_count(),
            "total_wealth": self.get_total_wealth(),
            "avg_skill": self.get_average_skill(),
            "births": self.births,
            "deaths": self.deaths,
            "spatial": self.spatial_engine.summary(),
        }


class DataCollector:
    """Data collector for simulation metrics."""

    def __init__(self, model_reporters: Dict[str, Any]):
        self.model_reporters = model_reporters
        self.data: Dict[str, List[Any]] = {
            name: [] for name in model_reporters
        }

    def collect(self, model: SimulationModel) -> None:
        """Collect data from model."""

        for name, func in self.model_reporters.items():
            if callable(func):
                self.data[name].append(func(model))
            else:
                self.data[name].append(getattr(model, func, None))

    def get_model_vars_dataframe(self) -> pd.DataFrame:
        """Return collected data as dataframe."""

        return pd.DataFrame(self.data)