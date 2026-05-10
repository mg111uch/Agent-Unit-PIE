"""
kernel/ontology/event_types.py

Global ontology for event classification.

Purpose
-------
Defines canonical event categories used across:

- simulation engine
- cognition engine
- memory engine
- digital twins
- finance systems
- behavior systems
- organization analysis
- city/state/country models

Core Philosophy
----------------
Events are atomic observable changes occurring in time.

events
    →
signals
    →
patterns
    →
insights
    →
predictions

This ontology standardizes all event generation
across the entire agent_unit_pie architecture.
"""

from __future__ import annotations


# ============================================================
# ROOT EVENT TYPES
# ============================================================

EVENT_TYPES = {

    # --------------------------------------------------------
    # SYSTEM
    # --------------------------------------------------------

    "system": {
        "system_started",
        "system_shutdown",
        "system_error",
        "system_warning",
        "config_updated",
        "module_loaded",
        "module_unloaded",
        "health_check",
        "heartbeat",
        "storage_sync",
    },

    # --------------------------------------------------------
    # OBSERVATION
    # --------------------------------------------------------

    "observation": {
        "observation_created",
        "document_ingested",
        "news_ingested",
        "podcast_ingested",
        "video_ingested",
        "webpage_scraped",
        "sensor_update",
        "map_data_ingested",
        "timeline_update",
        "knowledge_extracted",
    },

    # --------------------------------------------------------
    # MEMORY
    # --------------------------------------------------------

    "memory": {
        "memory_created",
        "memory_updated",
        "memory_deleted",
        "working_memory_updated",
        "episodic_memory_created",
        "semantic_memory_created",
        "memory_compressed",
        "memory_retrieved",
        "memory_decay",
        "memory_conflict_detected",
    },

    # --------------------------------------------------------
    # SIGNAL
    # --------------------------------------------------------

    "signal": {
        "signal_created",
        "signal_amplified",
        "signal_decay",
        "signal_cluster_detected",
        "signal_threshold_crossed",
        "signal_conflict",
        "signal_resolved",
        "high_priority_signal",
        "weak_signal_detected",
    },

    # --------------------------------------------------------
    # PATTERN
    # --------------------------------------------------------

    "pattern": {
        "pattern_detected",
        "pattern_confirmed",
        "pattern_rejected",
        "pattern_strengthened",
        "pattern_weakened",
        "pattern_cluster_detected",
        "anomaly_detected",
        "correlation_detected",
        "causal_relation_detected",
        "trend_detected",
    },

    # --------------------------------------------------------
    # RELATION
    # --------------------------------------------------------

    "relation": {
        "relation_created",
        "relation_removed",
        "relation_strengthened",
        "relation_weakened",
        "dependency_detected",
        "feedback_loop_detected",
        "contradiction_detected",
        "entity_linked",
        "entity_unlinked",
    },

    # --------------------------------------------------------
    # HUMAN BEHAVIOR
    # --------------------------------------------------------

    "human_behavior": {
        "emotion_shift",
        "habit_detected",
        "decision_made",
        "goal_created",
        "goal_abandoned",
        "motivation_change",
        "stress_detected",
        "burnout_detected",
        "learning_progress",
        "belief_changed",
        "behavior_anomaly",
        "social_interaction",
    },

    # --------------------------------------------------------
    # ASTROLOGY / SOFT SCIENCE
    # --------------------------------------------------------

    "soft_science": {
        "horoscope_generated",
        "numerology_profile_created",
        "palmistry_profile_created",
        "behavior_prediction_generated",
        "prediction_confirmed",
        "prediction_failed",
        "personality_shift_detected",
        "mindmap_updated",
        "behavior_alignment_detected",
        "archetype_detected",
    },

    # --------------------------------------------------------
    # ECONOMIC
    # --------------------------------------------------------

    "economic": {
        "trade_completed",
        "market_growth",
        "market_crash",
        "inflation_detected",
        "resource_scarcity",
        "resource_abundance",
        "capital_flow_detected",
        "economic_shift",
        "gdp_growth",
        "gdp_decline",
        "supply_chain_disruption",
        "economic_opportunity_detected",
    },

    # --------------------------------------------------------
    # FINANCIAL
    # --------------------------------------------------------

    "financial": {
        "stock_price_spike",
        "stock_price_drop",
        "volume_spike",
        "smart_money_detected",
        "insider_pattern_detected",
        "investment_opportunity_detected",
        "market_manipulation_detected",
        "portfolio_rebalanced",
        "liquidity_crisis",
        "asset_accumulation",
        "asset_distribution",
        "financial_risk_detected",
    },

    # --------------------------------------------------------
    # ORGANIZATION
    # --------------------------------------------------------

    "organization": {
        "employee_joined",
        "employee_left",
        "team_created",
        "leadership_change",
        "project_started",
        "project_completed",
        "innovation_detected",
        "productivity_decline",
        "process_bottleneck",
        "department_conflict",
        "organizational_restructure",
    },

    # --------------------------------------------------------
    # CITY
    # --------------------------------------------------------

    "city": {
        "traffic_congestion",
        "infrastructure_failure",
        "crime_spike",
        "migration_wave",
        "housing_pressure",
        "urban_expansion",
        "public_service_failure",
        "water_shortage",
        "power_outage",
        "pollution_spike",
        "city_growth_detected",
        "district_instability",
    },

    # --------------------------------------------------------
    # GOVERNANCE
    # --------------------------------------------------------

    "governance": {
        "policy_announced",
        "policy_reverted",
        "corruption_signal_detected",
        "public_fund_transfer",
        "bureaucratic_delay",
        "regulation_created",
        "regulation_removed",
        "governance_instability",
        "civil_unrest",
        "administrative_reform",
    },

    # --------------------------------------------------------
    # GEOPOLITICAL
    # --------------------------------------------------------

    "geopolitical": {
        "border_tension",
        "trade_agreement",
        "sanction_imposed",
        "diplomatic_shift",
        "military_escalation",
        "resource_conflict",
        "alliance_formed",
        "alliance_broken",
        "geopolitical_risk_detected",
    },

    # --------------------------------------------------------
    # ENVIRONMENT
    # --------------------------------------------------------

    "environment": {
        "temperature_anomaly",
        "flood_detected",
        "drought_detected",
        "wildfire_detected",
        "pollution_detected",
        "resource_depletion",
        "ecosystem_shift",
        "climate_pattern_detected",
        "environmental_risk_detected",
    },

    # --------------------------------------------------------
    # SIMULATION
    # --------------------------------------------------------

    "simulation": {
        "simulation_started",
        "simulation_paused",
        "simulation_completed",
        "simulation_reset",
        "unit_spawned",
        "unit_terminated",
        "population_growth",
        "population_collapse",
        "scenario_generated",
        "forecast_generated",
        "emergent_behavior_detected",
        "simulation_instability",
    },

    # --------------------------------------------------------
    # DIGITAL TWIN
    # --------------------------------------------------------

    "digital_twin": {
        "digital_twin_created",
        "digital_twin_updated",
        "spatial_model_generated",
        "mobility_model_updated",
        "forecast_model_generated",
        "future_projection_created",
        "historical_snapshot_created",
        "digital_twin_divergence_detected",
    },

    # --------------------------------------------------------
    # KNOWLEDGE
    # --------------------------------------------------------

    "knowledge": {
        "entity_extracted",
        "concept_discovered",
        "hypothesis_generated",
        "hypothesis_confirmed",
        "hypothesis_rejected",
        "knowledge_gap_detected",
        "insight_generated",
        "contradiction_found",
        "new_domain_detected",
        "ontology_extended",
    },

    # --------------------------------------------------------
    # RISK
    # --------------------------------------------------------

    "risk": {
        "risk_detected",
        "collapse_risk_detected",
        "financial_risk_detected",
        "social_risk_detected",
        "conflict_risk_detected",
        "fragility_detected",
        "system_instability_detected",
        "dependency_risk_detected",
        "critical_threshold_crossed",
    },

    # --------------------------------------------------------
    # OPPORTUNITY
    # --------------------------------------------------------

    "opportunity": {
        "market_gap_detected",
        "innovation_opportunity_detected",
        "investment_window_detected",
        "growth_opportunity_detected",
        "optimization_opportunity_detected",
        "emerging_sector_detected",
        "policy_opportunity_detected",
        "strategic_advantage_detected",
    },
}


# ============================================================
# FLAT LOOKUP
# ============================================================

ALL_EVENT_TYPES = sorted({
    item
    for category in EVENT_TYPES.values()
    for item in category
})


# ============================================================
# CATEGORY LOOKUP
# ============================================================

EVENT_CATEGORY_LOOKUP = {}

for category, values in EVENT_TYPES.items():

    for value in values:

        EVENT_CATEGORY_LOOKUP[value] = category


# ============================================================
# HELPERS
# ============================================================

def is_valid_event_type(
    event_type: str,
) -> bool:

    return (
        event_type
        in ALL_EVENT_TYPES
    )


def get_event_category(
    event_type: str,
) -> str:

    return (
        EVENT_CATEGORY_LOOKUP.get(
            event_type,
            "unknown",
        )
    )


def get_events_by_category(
    category: str,
):

    return EVENT_TYPES.get(
        category,
        set(),
    )


def list_event_categories():

    return sorted(
        EVENT_TYPES.keys()
    )


def list_all_event_types():

    return ALL_EVENT_TYPES