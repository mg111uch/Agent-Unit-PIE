from dataclasses import dataclass, field
from typing import Dict, List, Optional

# RESOURCE TYPE DEFINITION

@dataclass
class ResourceTypeDefinition:
    resource_type: str
    category: str
    description: str = ""
    unit: Optional[str] = None
    renewable: bool = False
    transferable: bool = True
    measurable: bool = True
    related_signals: List[str] = field(default_factory=list)
    tags: List[str] = field(default_factory=list)

# RESOURCE TYPES

RESOURCE_TYPES: Dict[str, ResourceTypeDefinition] = {

    # FINANCIAL RESOURCES

    "money": ResourceTypeDefinition(
        resource_type="money",

        category="financial",

        description="Liquid financial resource.",

        unit="currency",

        renewable=False,

        transferable=True,

        related_signals=[
            "wealth_change",
            "capital_flow"
        ],

        tags=[
            "economic"
        ]
    ),

    "capital": ResourceTypeDefinition(
        resource_type="capital",

        category="financial",

        description="Investment or productive capital.",

        unit="currency",

        transferable=True,

        related_signals=[
            "investment_shift",
            "debt_stress"
        ]
    ),

    "budget": ResourceTypeDefinition(
        resource_type="budget",

        category="financial",

        description="Allocated public/private spending pool.",

        unit="currency",

        transferable=False,

        related_signals=[
            "resource_allocation",
            "public_spending"
        ],

        tags=[
            "governance"
        ]
    ),

    # HUMAN RESOURCES

    "time": ResourceTypeDefinition(
        resource_type="time",

        category="human",

        description="Finite temporal resource.",

        unit="hours",

        renewable=True,

        transferable=False,

        related_signals=[
            "fatigue",
            "productivity_change"
        ]
    ),

    "energy": ResourceTypeDefinition(
        resource_type="energy",

        category="human",

        description="Physical or cognitive energy.",

        unit="energy_units",

        renewable=True,

        transferable=False,

        related_signals=[
            "fatigue",
            "stress"
        ]
    ),

    "knowledge": ResourceTypeDefinition(
        resource_type="knowledge",

        category="cognitive",

        description="Structured informational resource.",

        unit="knowledge_units",

        renewable=True,

        transferable=True,

        related_signals=[
            "knowledge_gain",
            "pattern_detected"
        ],

        tags=[
            "intelligence"
        ]
    ),

    "social_capital": ResourceTypeDefinition(
        resource_type="social_capital",

        category="social",

        description="Trust and network influence.",

        renewable=True,

        transferable=False,

        related_signals=[
            "influence_growth",
            "relationship_strength"
        ]
    ),

    # ORGANIZATIONAL RESOURCES

    "employees": ResourceTypeDefinition(
        resource_type="employees",

        category="organizational",

        description="Human workforce resource.",

        unit="people",

        transferable=False,

        related_signals=[
            "employment_growth"
        ]
    ),

    "inventory": ResourceTypeDefinition(
        resource_type="inventory",

        category="industrial",

        description="Stored goods/materials.",

        unit="inventory_units",

        transferable=True,

        related_signals=[
            "inventory_growth",
            "supply_shortage"
        ]
    ),

    "infrastructure": ResourceTypeDefinition(
        resource_type="infrastructure",

        category="physical",

        description="Built structural systems.",

        unit="infrastructure_units",

        renewable=False,

        transferable=False,

        related_signals=[
            "infrastructure_growth",
            "traffic_stress"
        ]
    ),

    "compute": ResourceTypeDefinition(
        resource_type="compute",

        category="digital",

        description="Computational processing capability.",

        unit="compute_units",

        renewable=True,

        transferable=True,

        related_signals=[
            "compute_load",
            "processing_latency"
        ],

        tags=[
            "ai"
        ]
    ),

    "memory": ResourceTypeDefinition(
        resource_type="memory",

        category="digital",

        description="Data storage and retrieval capacity.",

        unit="memory_units",

        renewable=True,

        transferable=False,

        related_signals=[
            "memory_pressure",
            "retrieval_efficiency"
        ],

        tags=[
            "ai"
        ]
    ),

    "data": ResourceTypeDefinition(
        resource_type="data",

        category="digital",

        description="Raw or processed informational data.",

        unit="data_units",

        renewable=True,

        transferable=True,

        related_signals=[
            "information_flow",
            "knowledge_growth"
        ]
    ),

    # GEOGRAPHIC / NATURAL RESOURCES

    "land": ResourceTypeDefinition(
        resource_type="land",

        category="geographic",

        description="Physical land area resource.",

        unit="sq_km",

        renewable=False,

        transferable=False,

        related_signals=[
            "urban_expansion",
            "resource_stress"
        ]
    ),

    "water": ResourceTypeDefinition(
        resource_type="water",

        category="natural",

        description="Water resource availability.",

        unit="liters",

        renewable=True,

        transferable=True,

        related_signals=[
            "water_shortage",
            "pollution"
        ]
    ),

    "population": ResourceTypeDefinition(
        resource_type="population",

        category="demographic",

        description="Population count resource.",

        unit="people",

        renewable=True,

        transferable=False,

        related_signals=[
            "population_growth",
            "migration"
        ]
    ),

    "materials": ResourceTypeDefinition(
        resource_type="materials",

        category="industrial",

        description="Raw material resource.",

        unit="material_units",

        transferable=True,

        related_signals=[
            "resource_consumption",
            "supply_shortage"
        ]
    ),

    # NATIONAL / MACRO RESOURCES

    "gdp": ResourceTypeDefinition(
        resource_type="gdp",

        category="macro_economic",

        description="Gross domestic product measure.",

        unit="currency",

        transferable=False,

        related_signals=[
            "economic_growth",
            "inflation"
        ]
    ),

    "technology": ResourceTypeDefinition(
        resource_type="technology",

        category="innovation",

        description="Technological capability resource.",

        renewable=True,

        transferable=True,

        related_signals=[
            "innovation_growth"
        ]
    ),

    "authority": ResourceTypeDefinition(
        resource_type="authority",

        category="governance",

        description="Administrative or governing authority.",

        renewable=True,

        transferable=False,

        related_signals=[
            "policy_shift",
            "governance_change"
        ]
    ),

    "military": ResourceTypeDefinition(
        resource_type="military",

        category="defense",

        description="Military capability resource.",

        transferable=False,

        related_signals=[
            "conflict_risk",
            "power_projection"
        ]
    )
}

# HELPER FUNCTIONS

def get_resource_type(
    resource_type: str
) -> Optional[ResourceTypeDefinition]:

    return RESOURCE_TYPES.get(resource_type)

def resource_type_exists(
    resource_type: str
) -> bool:

    return resource_type in RESOURCE_TYPES

def list_resource_types() -> List[str]:
    return list(RESOURCE_TYPES.keys())

def get_resources_by_category(
    category: str
) -> List[str]:

    return [
        name
        for name, definition in RESOURCE_TYPES.items()
        if definition.category == category
    ]

def get_related_signals(
    resource_type: str
) -> List[str]:

    definition = RESOURCE_TYPES.get(resource_type)

    if not definition:
        return []

    return definition.related_signals