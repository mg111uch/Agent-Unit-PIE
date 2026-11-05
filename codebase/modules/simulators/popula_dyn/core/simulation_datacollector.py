"""Per-step metric collector for SimulationModel (split out of the model)."""
from __future__ import annotations

from typing import Any, Callable, Dict, List

import pandas as pd


def build_reporters() -> Dict[str, Any]:
    """Per-step columns: agrarian counters + SocietyState + urban pack."""
    return {
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
        "Prospect_Moves": "prospect_moves",
        "Prospected_Cumul": "prospect_moves_total",
        "Capacity_Capped": "capacity_capped",
        "Capped_Cumul": "capacity_capped_total",
        "Scarcity": "scarcity_index",
        "Avg_Adaptability": lambda m: float(sum(
            float(u.get_state("adaptability", 1.0) or 1.0)
            for u in m.units.values()
            if u.unit_type == "human" and u.alive)
            / max(1, m.get_population_count())),
        # SocietyState per-step series (policy curves, not just endpoints)
        "Gini": lambda m: m.society_snapshot()["gini"],
        "Food_Security": lambda m: m.society_snapshot()["food_security"],
        "Skilled_Share": lambda m: m.society_snapshot()["skilled_share"],
        "Health_Index": lambda m: m.society_snapshot()["health_index"],
        "Wealth_PerCapita": lambda m: (m.society_snapshot()["wealth_total"]
                                       / max(1, m.society_snapshot()["population"])),
        "Sex_M": lambda m: m.get_sex_count("M"),
        "Sex_F": lambda m: m.get_sex_count("F"),
        # SIM-03 Phase A labour market
        "Urban_Output": lambda m: getattr(m, "urban_output", 0.0),
        "Wage_Bill": lambda m: getattr(m, "wage_bill", 0.0),
        "Employment_Rate": lambda m: m.society_snapshot().get("employment_rate", 0.0),
        # SIM-03 Phase B utilities, logistics and municipal budget
        "Power_Reliability": lambda m: getattr(m, "power_reliability_actual", 0.0),
        "Water_Supply": lambda m: getattr(m, "water_supply", 0.0),
        "Traffic_Congestion": lambda m: getattr(m, "traffic_congestion", 0.0),
        "Municipal_Balance": lambda m: getattr(m, "municipal_balance", 0.0),
    }


class DataCollector:
    """Data collector for simulation metrics."""

    def __init__(self, model_reporters: Dict[str, Any]):
        self.model_reporters = model_reporters
        self.data: Dict[str, List[Any]] = {name: [] for name in model_reporters}

    def collect(self, model: Any) -> None:
        """Collect data from model."""
        for name, func in self.model_reporters.items():
            self.data[name].append(func(model) if callable(func)
                                   else getattr(model, func, None))

    def get_model_vars_dataframe(self) -> pd.DataFrame:
        """Return collected data as dataframe."""
        return pd.DataFrame(self.data)
