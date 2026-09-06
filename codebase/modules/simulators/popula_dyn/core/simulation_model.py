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
from modules.simulators.popula_dyn.core.society import society_state
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
        self._spawn_counter = 0
        self._id_counter = 0  # deterministic init ids u00001… (uuid fallback untouched)
        self.epoch = params.get("epoch", "Agricultural")  # Phase 3: macro regime var
        self.births = 0
        self.deaths = 0
        self.births_total = 0
        self.deaths_total = 0
        self.death_causes = {"starvation": 0, "old_age": 0, "hazard": 0}
        self.death_causes_total = {"starvation": 0, "old_age": 0, "hazard": 0}
        self.successful_healings = 0
        self.successful_healings_total = 0
        self.tools_produced = 0
        self.trades_executed = 0
        self.wealth_traded = 0
        self.firms_hires = 0
        self.firms_hires_total = 0
        self.firms_invested = 0
        self.firms_invested_total = 0
        self._init_units()
        self.datacollector = DataCollector(
            model_reporters={
                "Population": lambda m: m.get_population_count(),
                "Total_Wealth": lambda m: m.get_total_wealth(),
                "Avg_Skill": lambda m: m.get_average_skill(),
                "Births": "births",
                "Deaths": "deaths",
                "Deaths_Starvation": lambda m: m.death_causes["starvation"],
                "Deaths_OldAge": lambda m: m.death_causes["old_age"],
                "Deaths_Hazard": lambda m: m.death_causes["hazard"],
                "Births_Cumul": "births_total",
                "Deaths_Cumul": "deaths_total",
                "Healer_Count": lambda m: m.get_unit_type_count("specialist", "heal"),
                "Toolmaker_Count": lambda m: m.get_unit_type_count("specialist", "produce"),
                "Trader_Count": lambda m: m.get_unit_type_count("specialist", "trade_ag"),
                "Successful_Healings": "successful_healings",
                "Healed_Cumul": "successful_healings_total",
                "Tools_Produced": "tools_produced",
                "Trades_Executed": "trades_executed",
                "Wealth_Traded": "wealth_traded",
                "Firms_Hired": "firms_hires",
                "Hired_Cumul": "firms_hires_total",
                "Capital_Stock": lambda m: sum(
                    float(u.get_state("capital_stock", 0) or 0)
                    for u in m.units.values()
                    if u.unit_type == "firm" and u.alive),
                # SocietyState per-step series (policy curves, not just endpoints)
                "Gini": lambda m: m.society_snapshot()["gini"],
                "Food_Security": lambda m: m.society_snapshot()["food_security"],
                "Skilled_Share": lambda m: m.society_snapshot()["skilled_share"],
                "Health_Index": lambda m: m.society_snapshot()["health_index"],
                "Wealth_PerCapita": lambda m: (m.society_snapshot()["wealth_total"]
                                               / max(1, m.society_snapshot()["population"])),
                "Sex_M": lambda m: m.get_sex_count("M"),
                "Sex_F": lambda m: m.get_sex_count("F"),
            }
        )
        self._soc_cache: Dict[str, Any] = {}
        self._soc_step = -1
    def _init_units(self) -> None:
        """Initialize all units from agent configs."""
        params = self.params
        grid_width = params.get("grid_width", PARAMS["grid_width"])
        grid_height = params.get("grid_height", PARAMS["grid_height"])
        rng = self.random
        years = params.get("years", PARAMS["years"])
        max_age = params.get("max_age", PARAMS["max_age"])
        fertile_min = params.get("fertile_min_age", PARAMS["fertile_min_age"])
        if years >= max_age - fertile_min:
            import logging
            logging.getLogger("popula_dyn").warning(f"years {years} >= max_age-fertile_min {max_age-fertile_min}: initial cohort will exit fertile window; expect last-year births dip without overlapping generations")
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
                unit.resources["crops"] = float(fertility)
        initial_pop = params.get("initial_pop", PARAMS["initial_pop"])
        for _ in range(initial_pop):
            x, y = self.spatial_engine.get_random_position(rng)
            # Phase C: concentrate initial ages in fertile window for overlapping generations
            if rng.random() < 0.8:
                age = rng.randint(15, 40)
            else:
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
            x, y = self.spatial_engine.get_random_position(rng)
            unit = self._create_unit(
                "healer",
                position=(x, y),
                healing_rate=params.get("healer_healing_rate", PARAMS["healer_healing_rate"]),
                healing_cost=params.get("healer_healing_cost", PARAMS["healer_healing_cost"]),
                seed=rng.randint(0, 100000),
            )
        initial_toolmakers = params.get("initial_toolmakers", PARAMS["initial_toolmakers"])
        for _ in range(initial_toolmakers):
            x, y = self.spatial_engine.get_random_position(rng)
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
            x, y = self.spatial_engine.get_random_position(rng)
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
        self._id_counter += 1
        config = create_unit_config(
            agent_type=agent_type,
            model=self,
            position=position,
            seed=seed,
            unit_id=f"u{self._id_counter:05d}",
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
            self.births_total += 1
        return unit

    def step(self) -> None:
        """Advance simulation by one tick."""
        self.births = 0
        self.deaths = 0
        self.death_causes = {"starvation": 0, "old_age": 0, "hazard": 0}
        self.successful_healings = 0
        self.tools_produced = 0
        self.trades_executed = 0
        self.wealth_traded = 0
        self.firms_hires = 0
        self.firms_invested = 0
        world_state = {
            "params": self.params,
            "grid": self.spatial_engine,
            "model": self,
            "seed": self.random.randint(0, 1000000),
            "rng": self.random,
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
            self._execute_behaviors(unit, world_state)
            age = unit.get_state("age", 0)
            if age is not None:
                unit.set_state("age", age + 1)
        dead_units = [u for u in self.units.values() if not u.alive]
        for unit in dead_units:
            position = unit.get_state("position")
            if position:
                self.spatial_engine.remove_agent(unit)
            del self.units[unit.unit_id]
            self.deaths += 1
            self.deaths_total += 1
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
                import logging
                logging.getLogger("popula_dyn").debug(f"behavior {behavior_name} {unit.unit_id} failed: {e}")
    def _process_behavior_result(
        self,
        unit: UnitAgent,
        result: Dict[str, Any],
    ) -> None:
        """Process behavior output."""
        spawn = result.get("spawn")
        if spawn is not None:
            if not isinstance(spawn, dict):
                raise ValueError("behavior spawn intent must be a unit-data dict")
            self._spawn_counter += 1
            spawn = {**spawn, "unit_id": f"child-s{self.step_count}-{self._spawn_counter}"}
            child = self.add_unit(spawn)
            for event in result.get("events", []):
                if event.get("event_type") == "birth" and not event.get("child_id"):
                    event["child_id"] = child.unit_id
        state_updates = result.get("state_updates", {})
        for key, value in state_updates.items():
            unit.set_state(key, value)
        resource_updates = result.get("resource_updates", {})
        for key, value in resource_updates.items():
            unit.modify_resource(key, value)
        # cross-unit intents: model applies by id (skip missing/dead)
        for eff in result.get("unit_effects", []) or []:
            target = self.units.get((eff or {}).get("unit_id", ""))
            if target is None or not target.alive:
                continue
            for key, value in (eff.get("state_updates", {}) or {}).items():
                target.set_state(key, value)
            for key, value in (eff.get("resource_updates", {}) or {}).items():
                target.modify_resource(key, value)
        events = result.get("events", [])
        for event in events:
            event_type = event.get("event_type")
            if event_type == "birth":
                # births owned by add_unit only; event is informational
                pass
            elif event_type == "death":
                # categorized causes owned here (per-step + cumulative)
                reason = event.get("reason", "hazard")
                if reason not in self.death_causes:
                    reason = "hazard"
                self.death_causes[reason] += 1
                self.death_causes_total[reason] += 1
            elif event_type == "healed":
                self.successful_healings += 1
                self.successful_healings_total += 1
            elif event_type == "tool_produced":
                self.tools_produced += 1
            elif event_type == "trade_executed":
                self.trades_executed += 1
                self.wealth_traded += event.get("amount", 0)
            elif event_type == "hired":
                self.firms_hires += 1
                self.firms_hires_total += 1
            elif event_type == "invested":
                self.firms_invested += 1
                self.firms_invested_total += 1
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
    def get_sex_count(self, gender: str) -> int:
        """Alive humans by gender (metrics split)."""
        return sum(1 for u in self.units.values()
                   if u.unit_type == "human" and u.alive
                   and u.get_state("gender") == gender)

    def society_snapshot(self) -> Dict[str, Any]:
        """Cached-per-step SocietyState (one unit scan shared by all reporters)."""
        if self._soc_step != self.step_count:
            self._soc_cache = society_state(self)
            self._soc_step = self.step_count
        return self._soc_cache

    def get_dataframe(self) -> pd.DataFrame:
        """Get collected data as dataframe."""
        return self.datacollector.get_model_vars_dataframe()

    def summary(self) -> Dict[str, Any]:
        """Get simulation summary."""
        return {
            "step_count": self.step_count,
            "epoch": getattr(self, "epoch", "Agricultural"),
            "total_units": len(self.units),
            "population": self.get_population_count(),
            "total_wealth": self.get_total_wealth(),
            "avg_skill": self.get_average_skill(),
            "births": self.births,
            "deaths": self.deaths,
            "births_total": self.births_total,
            "deaths_total": self.deaths_total,
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