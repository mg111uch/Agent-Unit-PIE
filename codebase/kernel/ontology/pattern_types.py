"""
kernel/ontology/pattern_types.py

Global ontology for pattern classification.

Purpose
-------
Defines canonical pattern categories used across:

- humans
- organizations
- companies
- cities
- countries
- simulations
- financial systems
- ecosystems
- digital twins

Core Philosophy
----------------
Patterns are higher-order abstractions extracted from:

signals
events
relations
timelines
behaviors
simulations

This ontology prevents schema drift and keeps
all cognition layers interoperable.
"""

from __future__ import annotations

# ROOT PATTERN TYPES

PATTERN_TYPES = {

    # TEMPORAL

    "temporal": {
        "recurring",
        "seasonal",
        "cyclic",
        "trend_up",
        "trend_down",
        "stagnation",
        "acceleration",
        "deceleration",
        "volatility",
        "phase_transition",
        "timeline_shift",
    },

    # BEHAVIORAL

    "behavioral": {
        "habit",
        "addiction",
        "avoidance",
        "motivation_cycle",
        "burnout",
        "learning_growth",
        "social_dependency",
        "risk_taking",
        "discipline_pattern",
        "emotional_instability",
        "decision_bias",
        "attention_drift",
    },

    # ECONOMIC

    "economic": {
        "wealth_accumulation",
        "wealth_decay",
        "resource_scarcity",
        "resource_abundance",
        "market_growth",
        "market_crash",
        "inflation_pattern",
        "capital_concentration",
        "trade_expansion",
        "economic_inequality",
        "liquidity_stress",
        "supply_chain_disruption",
    },

    # FINANCIAL

    "financial": {
        "bullish_trend",
        "bearish_trend",
        "pump_and_dump",
        "smart_money_flow",
        "institutional_accumulation",
        "retail_panic",
        "sector_rotation",
        "breakout_pattern",
        "support_resistance",
        "speculative_bubble",
        "market_manipulation",
        "high_volatility_cluster",
    },

    # SOCIAL

    "social": {
        "community_growth",
        "social_fragmentation",
        "polarization",
        "cooperation_cycle",
        "conflict_escalation",
        "migration_pattern",
        "cultural_shift",
        "social_trust_decay",
        "tribalization",
        "collective_behavior",
        "mass_hysteria",
        "information_propagation",
    },

    # GOVERNANCE

    "governance": {
        "bureaucratic_expansion",
        "corruption_pattern",
        "power_concentration",
        "policy_instability",
        "institutional_decay",
        "governance_efficiency",
        "public_fund_leakage",
        "elite_capture",
        "administrative_bottleneck",
        "regulatory_capture",
        "state_expansion",
        "civil_unrest",
    },

    # ORGANIZATIONAL

    "organizational": {
        "productivity_decline",
        "innovation_growth",
        "team_fragmentation",
        "hierarchy_rigidity",
        "communication_breakdown",
        "talent_loss",
        "execution_bottleneck",
        "leadership_dependency",
        "knowledge_silo",
        "organizational_learning",
        "process_optimization",
        "scaling_failure",
    },

    # INFRASTRUCTURE

    "infrastructure": {
        "traffic_congestion",
        "urban_sprawl",
        "infrastructure_decay",
        "power_instability",
        "water_stress",
        "housing_pressure",
        "transport_optimization",
        "resource_distribution_failure",
        "network_fragmentation",
        "critical_dependency",
    },

    # ENVIRONMENTAL

    "environmental": {
        "climate_shift",
        "resource_depletion",
        "pollution_growth",
        "ecosystem_recovery",
        "biodiversity_loss",
        "drought_cycle",
        "flood_risk_pattern",
        "temperature_instability",
        "environmental_collapse",
    },

    # HEALTH

    "health": {
        "fatigue_cycle",
        "stress_accumulation",
        "recovery_pattern",
        "disease_spread",
        "sleep_instability",
        "health_improvement",
        "metabolic_decline",
        "burnout_progression",
        "behavior_health_correlation",
    },

    # KNOWLEDGE

    "knowledge": {
        "knowledge_growth",
        "misinformation_spread",
        "belief_reinforcement",
        "contradiction_cluster",
        "cognitive_bias",
        "emergent_hypothesis",
        "insight_generation",
        "learning_acceleration",
        "memory_decay",
    },

    # SIMULATION

    "simulation": {
        "population_growth",
        "population_collapse",
        "city_formation",
        "civilization_expansion",
        "resource_war",
        "migration_wave",
        "technological_acceleration",
        "social_collapse",
        "economic_boom_bust",
        "agent_specialization",
        "hierarchy_emergence",
        "system_instability",
    },

    # RELATIONAL

    "relational": {
        "strong_correlation",
        "inverse_correlation",
        "causal_chain",
        "dependency_loop",
        "feedback_loop",
        "contradiction",
        "reinforcement_cycle",
        "cross_unit_influence",
        "network_centralization",
        "relation_instability",
    },

    # ANOMALY

    "anomaly": {
        "outlier_event",
        "unexpected_behavior",
        "signal_spike",
        "structural_break",
        "rare_pattern",
        "abnormal_growth",
        "abnormal_decline",
        "systemic_anomaly",
        "unknown_pattern",
    },

    # OPPORTUNITY

    "opportunity": {
        "investment_opportunity",
        "market_gap",
        "innovation_opportunity",
        "policy_opportunity",
        "arbitrage_pattern",
        "growth_window",
        "emerging_sector",
        "undervalued_asset",
        "optimization_potential",
    },

    # RISK

    "risk": {
        "collapse_risk",
        "financial_risk",
        "governance_risk",
        "social_risk",
        "systemic_risk",
        "conflict_risk",
        "dependency_risk",
        "fragility_pattern",
        "instability_cluster",
    },
}

# FLAT LOOKUP

ALL_PATTERN_TYPES = sorted({
    item
    for category in PATTERN_TYPES.values()
    for item in category
})

# CATEGORY LOOKUP

PATTERN_CATEGORY_LOOKUP = {}

for category, values in PATTERN_TYPES.items():

    for value in values:

        PATTERN_CATEGORY_LOOKUP[value] = category

# HELPERS

def is_valid_pattern_type(
    pattern_type: str,
) -> bool:

    return (
        pattern_type
        in ALL_PATTERN_TYPES
    )

def get_pattern_category(
    pattern_type: str,
) -> str:

    return (
        PATTERN_CATEGORY_LOOKUP.get(
            pattern_type,
            "unknown",
        )
    )

def get_patterns_by_category(
    category: str,
):

    return PATTERN_TYPES.get(
        category,
        set(),
    )

def list_pattern_categories():
    return sorted(
        PATTERN_TYPES.keys()
    )

def list_all_pattern_types():
    return ALL_PATTERN_TYPES