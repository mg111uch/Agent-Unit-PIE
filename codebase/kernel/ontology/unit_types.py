from dataclasses import dataclass, field
from typing import Dict, List, Optional

# UNIT TYPE DEFINITION

@dataclass
class UnitTypeDefinition:
    unit_type: str
    category: str
    description: str = ""
    parent_type: Optional[str] = None
    allowed_behaviors: List[str] = field(default_factory=list)
    allowed_resources: List[str] = field(default_factory=list)
    allowed_signals: List[str] = field(default_factory=list)
    allowed_relations: List[str] = field(default_factory=list)
    tags: List[str] = field(default_factory=list)

# CORE UNIT TYPES

UNIT_TYPES: Dict[str, UnitTypeDefinition] = {

    # HUMAN SYSTEMS

    "human": UnitTypeDefinition(
        unit_type="human",
        category="biological",

        description="Individual human entity.",

        allowed_behaviors=[
            "move",
            "learn",
            "communicate",
            "trade",
            "consume",
            "work",
            "reproduce",
            "invest",
            "decide"
        ],

        allowed_resources=[
            "money",
            "food",
            "energy",
            "knowledge",
            "time",
            "social_capital"
        ],

        allowed_signals=[
            "stress",
            "motivation",
            "health_change",
            "wealth_change",
            "belief_shift",
            "fatigue"
        ],

        allowed_relations=[
            "friend",
            "family",
            "employee_of",
            "member_of",
            "investor_in"
        ],

        tags=[
            "mindmap_supported",
            "behavior_trackable"
        ]
    ),

    # ORGANIZATIONS

    "company": UnitTypeDefinition(
        unit_type="company",
        category="organization",

        description="Business or corporate entity.",

        allowed_behaviors=[
            "hire",
            "fire",
            "invest",
            "produce",
            "expand",
            "trade",
            "research"
        ],

        allowed_resources=[
            "capital",
            "employees",
            "infrastructure",
            "data",
            "inventory"
        ],

        allowed_signals=[
            "revenue_growth",
            "revenue_decline",
            "market_expansion",
            "debt_stress",
            "innovation_growth"
        ],

        allowed_relations=[
            "supplier_of",
            "partner_of",
            "competitor_of",
            "located_in"
        ],

        tags=[
            "economic_unit",
            "market_entity"
        ]
    ),

    # GEOGRAPHIC SYSTEMS

    "city": UnitTypeDefinition(
        unit_type="city",
        category="geographic",

        description="Urban settlement and economic-social system.",

        allowed_behaviors=[
            "expand",
            "allocate_budget",
            "develop_infrastructure",
            "regulate",
            "trade"
        ],

        allowed_resources=[
            "population",
            "budget",
            "water",
            "energy",
            "land",
            "infrastructure"
        ],

        allowed_signals=[
            "population_growth",
            "migration",
            "traffic_stress",
            "economic_growth",
            "crime_rise",
            "pollution"
        ],

        allowed_relations=[
            "connected_to",
            "governed_by",
            "trades_with"
        ],

        tags=[
            "digital_twin_supported",
            "spatial_unit"
        ]
    ),

    "state": UnitTypeDefinition(
        unit_type="state",
        category="geographic",

        description="Administrative state-level entity.",

        allowed_behaviors=[
            "govern",
            "allocate_budget",
            "regulate",
            "invest",
            "tax"
        ],

        allowed_resources=[
            "budget",
            "population",
            "infrastructure",
            "energy"
        ],

        allowed_signals=[
            "gdp_growth",
            "unemployment",
            "policy_shift",
            "capital_flow"
        ],

        allowed_relations=[
            "contains",
            "governed_by",
            "trades_with"
        ]
    ),

    "country": UnitTypeDefinition(
        unit_type="country",
        category="geographic",

        description="Nation-state level entity.",

        allowed_behaviors=[
            "govern",
            "trade",
            "regulate",
            "invest",
            "expand_influence"
        ],

        allowed_resources=[
            "gdp",
            "population",
            "energy",
            "military",
            "technology"
        ],

        allowed_signals=[
            "economic_growth",
            "inflation",
            "trade_surplus",
            "political_instability"
        ],

        allowed_relations=[
            "allied_with",
            "trades_with",
            "conflicts_with"
        ],

        tags=[
            "macro_system"
        ]
    ),

    # FINANCIAL SYSTEMS

    "stock": UnitTypeDefinition(
        unit_type="stock",
        category="financial",

        description="Tradable market asset.",

        allowed_behaviors=[
            "rise",
            "fall",
            "split",
            "merge"
        ],

        allowed_resources=[
            "market_cap",
            "volume",
            "liquidity"
        ],

        allowed_signals=[
            "bullish",
            "bearish",
            "high_volatility",
            "accumulation",
            "distribution"
        ],

        allowed_relations=[
            "belongs_to_sector",
            "issued_by"
        ],

        tags=[
            "market_entity"
        ]
    ),

    # KNOWLEDGE SYSTEMS

    "knowledge_domain": UnitTypeDefinition(
        unit_type="knowledge_domain",
        category="knowledge",

        description="Structured body of knowledge.",

        allowed_behaviors=[
            "evolve",
            "branch",
            "merge"
        ],

        allowed_resources=[
            "documents",
            "research",
            "evidence"
        ],

        allowed_signals=[
            "consensus_shift",
            "contradiction_detected",
            "hypothesis_growth"
        ],

        allowed_relations=[
            "related_to",
            "contradicts",
            "supports"
        ]
    ),

    # AI SYSTEMS

    "ai_agent": UnitTypeDefinition(
        unit_type="ai_agent",
        category="artificial",

        description="Autonomous cognitive agent.",

        allowed_behaviors=[
            "observe",
            "reason",
            "simulate",
            "debate",
            "summarize",
            "predict"
        ],

        allowed_resources=[
            "compute",
            "memory",
            "knowledge"
        ],

        allowed_signals=[
            "confidence_change",
            "contradiction_detected",
            "pattern_detected"
        ],

        allowed_relations=[
            "collaborates_with",
            "derived_from"
        ],

        tags=[
            "recursive_system"
        ]
    )
}

# HELPER FUNCTIONS

def get_unit_type(unit_type: str) -> Optional[UnitTypeDefinition]:
    return UNIT_TYPES.get(unit_type)

def unit_type_exists(unit_type: str) -> bool:
    return unit_type in UNIT_TYPES

def list_unit_types() -> List[str]:
    return list(UNIT_TYPES.keys())

def get_unit_types_by_category(category: str) -> List[str]:
    return [
        name
        for name, definition in UNIT_TYPES.items()
        if definition.category == category
    ]