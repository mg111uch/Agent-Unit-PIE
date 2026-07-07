from dataclasses import dataclass, field
from typing import Dict, List, Optional

# SIGNAL TYPE DEFINITION

@dataclass
class SignalTypeDefinition:
    signal_type: str
    category: str
    description: str = ""
    data_type: str = "float"
    default_unit: Optional[str] = None
    valid_range: Optional[tuple] = None
    related_patterns: List[str] = field(default_factory=list)
    tags: List[str] = field(default_factory=list)

# SIGNAL TYPES

SIGNAL_TYPES: Dict[str, SignalTypeDefinition] = {

    # HUMAN SIGNALS

    "stress": SignalTypeDefinition(
        signal_type="stress",

        category="human_behavior",

        description="Measures stress level of a human unit.",

        data_type="float",

        valid_range=(0.0, 1.0),

        related_patterns=[
            "burnout_risk",
            "conflict_behavior",
            "fatigue_cycle"
        ],

        tags=[
            "psychological",
            "behavioral"
        ]
    ),

    "motivation": SignalTypeDefinition(
        signal_type="motivation",

        category="human_behavior",

        description="Represents motivation or drive level.",

        data_type="float",

        valid_range=(0.0, 1.0),

        related_patterns=[
            "goal_persistence",
            "productivity_growth"
        ]
    ),

    "belief_shift": SignalTypeDefinition(
        signal_type="belief_shift",

        category="human_behavior",

        description="Represents change in beliefs or ideology.",

        data_type="dict",

        related_patterns=[
            "ideological_transition"
        ]
    ),

    # ECONOMIC SIGNALS

    "revenue_growth": SignalTypeDefinition(
        signal_type="revenue_growth",

        category="economic",

        description="Represents increase in revenue.",

        data_type="float",

        default_unit="percentage",

        related_patterns=[
            "market_expansion",
            "growth_cycle"
        ],

        tags=[
            "financial"
        ]
    ),

    "debt_stress": SignalTypeDefinition(
        signal_type="debt_stress",

        category="economic",

        description="Represents financial debt pressure.",

        data_type="float",

        valid_range=(0.0, 1.0),

        related_patterns=[
            "bankruptcy_risk",
            "capital_instability"
        ]
    ),

    "capital_flow": SignalTypeDefinition(
        signal_type="capital_flow",

        category="economic",

        description="Represents movement of capital.",

        data_type="float",

        default_unit="currency",

        related_patterns=[
            "investment_shift",
            "economic_growth"
        ]
    ),

    # CITY / COUNTRY SIGNALS

    "population_growth": SignalTypeDefinition(
        signal_type="population_growth",

        category="demographic",

        description="Population growth trend.",

        data_type="float",

        default_unit="percentage",

        related_patterns=[
            "urban_expansion",
            "resource_stress"
        ]
    ),

    "migration": SignalTypeDefinition(
        signal_type="migration",

        category="demographic",

        description="Movement of people between regions.",

        data_type="dict",

        related_patterns=[
            "urbanization",
            "economic_shift"
        ]
    ),

    "traffic_stress": SignalTypeDefinition(
        signal_type="traffic_stress",

        category="infrastructure",

        description="Traffic congestion intensity.",

        data_type="float",

        valid_range=(0.0, 1.0),

        related_patterns=[
            "infrastructure_failure",
            "economic_delay"
        ]
    ),

    "pollution": SignalTypeDefinition(
        signal_type="pollution",

        category="environment",

        description="Environmental pollution level.",

        data_type="float",

        related_patterns=[
            "health_risk",
            "urban_decay"
        ]
    ),

    # MARKET SIGNALS

    "bullish": SignalTypeDefinition(
        signal_type="bullish",

        category="market",

        description="Positive market sentiment.",

        data_type="float",

        valid_range=(0.0, 1.0),

        related_patterns=[
            "market_rally"
        ]
    ),

    "bearish": SignalTypeDefinition(
        signal_type="bearish",

        category="market",

        description="Negative market sentiment.",

        data_type="float",

        valid_range=(0.0, 1.0),

        related_patterns=[
            "market_decline"
        ]
    ),

    "high_volatility": SignalTypeDefinition(
        signal_type="high_volatility",

        category="market",

        description="High fluctuation in market movement.",

        data_type="float",

        valid_range=(0.0, 1.0),

        related_patterns=[
            "market_instability"
        ]
    ),

    # AI / KNOWLEDGE SIGNALS

    "pattern_detected": SignalTypeDefinition(
        signal_type="pattern_detected",

        category="cognitive",

        description="New pattern identified by system.",

        data_type="dict",

        related_patterns=[
            "knowledge_growth"
        ]
    ),

    "contradiction_detected": SignalTypeDefinition(
        signal_type="contradiction_detected",

        category="cognitive",

        description="Contradiction found in knowledge.",

        data_type="dict",

        related_patterns=[
            "hypothesis_revision"
        ]
    ),

    "confidence_change": SignalTypeDefinition(
        signal_type="confidence_change",

        category="cognitive",

        description="Confidence score updated.",

        data_type="float",

        valid_range=(0.0, 1.0),

        related_patterns=[
            "belief_update"
        ]
    )
}

# HELPER FUNCTIONS

def get_signal_type(
    signal_type: str
) -> Optional[SignalTypeDefinition]:

    return SIGNAL_TYPES.get(signal_type)

def signal_type_exists(signal_type: str) -> bool:
    return signal_type in SIGNAL_TYPES

def list_signal_types() -> List[str]:
    return list(SIGNAL_TYPES.keys())

def get_signal_types_by_category(
    category: str
) -> List[str]:

    return [
        name
        for name, definition in SIGNAL_TYPES.items()
        if definition.category == category
    ]