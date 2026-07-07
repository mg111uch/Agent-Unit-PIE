from dataclasses import dataclass, field
from typing import Dict, List, Optional

# BEHAVIOR TYPE DEFINITION

@dataclass
class BehaviorTypeDefinition:
    behavior_type: str
    category: str
    description: str = ""
    required_resources: List[str] = field(default_factory=list)
    generated_signals: List[str] = field(default_factory=list)
    generated_events: List[str] = field(default_factory=list)
    compatible_unit_types: List[str] = field(default_factory=list)
    tags: List[str] = field(default_factory=list)

# BEHAVIOR TYPES

BEHAVIOR_TYPES: Dict[str, BehaviorTypeDefinition] = {

    # HUMAN BEHAVIORS

    "move": BehaviorTypeDefinition(
        behavior_type="move",

        category="physical",

        description="Movement between locations.",

        required_resources=[
            "energy",
            "time"
        ],

        generated_signals=[
            "location_change"
        ],

        generated_events=[
            "movement_event"
        ],

        compatible_unit_types=[
            "human",
            "vehicle",
            "robot"
        ],

        tags=[
            "mobility"
        ]
    ),

    "learn": BehaviorTypeDefinition(
        behavior_type="learn",

        category="cognitive",

        description="Acquisition of knowledge.",

        required_resources=[
            "time",
            "energy",
            "knowledge"
        ],

        generated_signals=[
            "knowledge_gain",
            "belief_shift"
        ],

        generated_events=[
            "learning_event"
        ],

        compatible_unit_types=[
            "human",
            "ai_agent"
        ],

        tags=[
            "intelligence"
        ]
    ),

    "communicate": BehaviorTypeDefinition(
        behavior_type="communicate",

        category="social",

        description="Exchange of information.",

        required_resources=[
            "time",
            "knowledge"
        ],

        generated_signals=[
            "information_flow",
            "belief_shift"
        ],

        generated_events=[
            "communication_event"
        ],

        compatible_unit_types=[
            "human",
            "ai_agent",
            "organization"
        ]
    ),

    "work": BehaviorTypeDefinition(
        behavior_type="work",

        category="economic",

        description="Economic productivity activity.",

        required_resources=[
            "energy",
            "time"
        ],

        generated_signals=[
            "wealth_change",
            "fatigue"
        ],

        generated_events=[
            "work_event"
        ],

        compatible_unit_types=[
            "human"
        ]
    ),

    "invest": BehaviorTypeDefinition(
        behavior_type="invest",

        category="financial",

        description="Capital allocation activity.",

        required_resources=[
            "money",
            "knowledge"
        ],

        generated_signals=[
            "capital_flow",
            "risk_exposure"
        ],

        generated_events=[
            "investment_event"
        ],

        compatible_unit_types=[
            "human",
            "company",
            "fund",
            "country"
        ],

        tags=[
            "finance"
        ]
    ),

    "trade": BehaviorTypeDefinition(
        behavior_type="trade",

        category="economic",

        description="Exchange of goods or services.",

        required_resources=[
            "money",
            "inventory"
        ],

        generated_signals=[
            "capital_flow",
            "market_activity"
        ],

        generated_events=[
            "trade_event"
        ],

        compatible_unit_types=[
            "human",
            "company",
            "city",
            "country"
        ]
    ),

    # ORGANIZATION BEHAVIORS

    "hire": BehaviorTypeDefinition(
        behavior_type="hire",

        category="organizational",

        description="Recruitment of workforce.",

        required_resources=[
            "capital"
        ],

        generated_signals=[
            "employment_growth"
        ],

        generated_events=[
            "hiring_event"
        ],

        compatible_unit_types=[
            "company",
            "organization"
        ]
    ),

    "produce": BehaviorTypeDefinition(
        behavior_type="produce",

        category="industrial",

        description="Production of goods/services.",

        required_resources=[
            "energy",
            "labor",
            "infrastructure"
        ],

        generated_signals=[
            "inventory_growth",
            "resource_consumption"
        ],

        generated_events=[
            "production_event"
        ],

        compatible_unit_types=[
            "company",
            "factory",
            "country"
        ]
    ),

    "research": BehaviorTypeDefinition(
        behavior_type="research",

        category="knowledge",

        description="Creation of new knowledge.",

        required_resources=[
            "knowledge",
            "time",
            "compute"
        ],

        generated_signals=[
            "innovation_growth",
            "pattern_detected"
        ],

        generated_events=[
            "research_event"
        ],

        compatible_unit_types=[
            "company",
            "organization",
            "ai_agent"
        ]
    ),

    # GOVERNANCE BEHAVIORS

    "govern": BehaviorTypeDefinition(
        behavior_type="govern",

        category="governance",

        description="Governance and policy actions.",

        required_resources=[
            "budget",
            "authority"
        ],

        generated_signals=[
            "policy_shift",
            "resource_allocation"
        ],

        generated_events=[
            "governance_event"
        ],

        compatible_unit_types=[
            "state",
            "country",
            "government"
        ]
    ),

    "allocate_budget": BehaviorTypeDefinition(
        behavior_type="allocate_budget",

        category="governance",

        description="Budget/resource distribution.",

        required_resources=[
            "budget"
        ],

        generated_signals=[
            "capital_flow",
            "infrastructure_growth"
        ],

        generated_events=[
            "budget_event"
        ],

        compatible_unit_types=[
            "city",
            "state",
            "country"
        ],

        tags=[
            "public_finance"
        ]
    ),

    "regulate": BehaviorTypeDefinition(
        behavior_type="regulate",

        category="governance",

        description="Regulation/control of systems.",

        required_resources=[
            "authority"
        ],

        generated_signals=[
            "policy_shift",
            "market_restriction"
        ],

        generated_events=[
            "regulation_event"
        ],

        compatible_unit_types=[
            "state",
            "country",
            "government"
        ]
    ),

    # CITY / COUNTRY BEHAVIORS

    "expand": BehaviorTypeDefinition(
        behavior_type="expand",

        category="growth",

        description="Expansion of influence or territory.",

        required_resources=[
            "capital",
            "infrastructure",
            "population"
        ],

        generated_signals=[
            "population_growth",
            "economic_growth"
        ],

        generated_events=[
            "expansion_event"
        ],

        compatible_unit_types=[
            "city",
            "company",
            "country"
        ]
    ),

    "develop_infrastructure": BehaviorTypeDefinition(
        behavior_type="develop_infrastructure",

        category="infrastructure",

        description="Infrastructure development activity.",

        required_resources=[
            "budget",
            "materials",
            "energy"
        ],

        generated_signals=[
            "infrastructure_growth",
            "traffic_stress"
        ],

        generated_events=[
            "infrastructure_event"
        ],

        compatible_unit_types=[
            "city",
            "state",
            "country"
        ]
    ),

    # AI / KNOWLEDGE BEHAVIORS

    "observe": BehaviorTypeDefinition(
        behavior_type="observe",

        category="cognitive",

        description="Observation and data ingestion.",

        required_resources=[
            "compute",
            "memory"
        ],

        generated_signals=[
            "signal_detected"
        ],

        generated_events=[
            "observation_event"
        ],

        compatible_unit_types=[
            "ai_agent"
        ]
    ),

    "reason": BehaviorTypeDefinition(
        behavior_type="reason",

        category="cognitive",

        description="Inference and reasoning process.",

        required_resources=[
            "compute",
            "knowledge"
        ],

        generated_signals=[
            "hypothesis_generated",
            "confidence_change"
        ],

        generated_events=[
            "reasoning_event"
        ],

        compatible_unit_types=[
            "ai_agent"
        ]
    ),

    "simulate": BehaviorTypeDefinition(
        behavior_type="simulate",

        category="simulation",

        description="Simulation of possible futures.",

        required_resources=[
            "compute",
            "knowledge",
            "memory"
        ],

        generated_signals=[
            "prediction_generated",
            "risk_projection"
        ],

        generated_events=[
            "simulation_event"
        ],

        compatible_unit_types=[
            "ai_agent"
        ],

        tags=[
            "digital_twin"
        ]
    ),

    "debate": BehaviorTypeDefinition(
        behavior_type="debate",

        category="cognitive",

        description="Argumentative reasoning process.",

        required_resources=[
            "knowledge",
            "compute"
        ],

        generated_signals=[
            "contradiction_detected",
            "hypothesis_revision"
        ],

        generated_events=[
            "debate_event"
        ],

        compatible_unit_types=[
            "ai_agent"
        ],

        tags=[
            "argumentation"
        ]
    ),

    "predict": BehaviorTypeDefinition(
        behavior_type="predict",

        category="prediction",

        description="Prediction of future states.",

        required_resources=[
            "knowledge",
            "compute",
            "memory"
        ],

        generated_signals=[
            "forecast",
            "risk_projection"
        ],

        generated_events=[
            "prediction_event"
        ],

        compatible_unit_types=[
            "ai_agent"
        ]
    )
}

# HELPER FUNCTIONS

def get_behavior_type(
    behavior_type: str
) -> Optional[BehaviorTypeDefinition]:

    return BEHAVIOR_TYPES.get(behavior_type)

def behavior_type_exists(
    behavior_type: str
) -> bool:

    return behavior_type in BEHAVIOR_TYPES

def list_behavior_types() -> List[str]:
    return list(BEHAVIOR_TYPES.keys())

def get_behaviors_by_category(
    category: str
) -> List[str]:

    return [
        name
        for name, definition in BEHAVIOR_TYPES.items()
        if definition.category == category
    ]

def get_behaviors_for_unit_type(
    unit_type: str
) -> List[str]:

    results = []

    for name, definition in BEHAVIOR_TYPES.items():

        if unit_type in definition.compatible_unit_types:
            results.append(name)

    return results