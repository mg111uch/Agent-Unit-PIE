from dataclasses import dataclass, field
from typing import Dict, List, Optional

# RELATION TYPE DEFINITION

@dataclass
class RelationTypeDefinition:
    relation_type: str
    category: str
    description: str = ""
    directed: bool = False
    symmetric: bool = False
    source_unit_types: List[str] = field(default_factory=list)
    target_unit_types: List[str] = field(default_factory=list)
    inverse_relation: Optional[str] = None
    tags: List[str] = field(default_factory=list)

# RELATION TYPES

RELATION_TYPES: Dict[str, RelationTypeDefinition] = {

    # HUMAN RELATIONS

    "friend": RelationTypeDefinition(
        relation_type="friend",

        category="social",

        description="Mutual friendship relation.",

        directed=False,

        symmetric=True,

        source_unit_types=["human"],

        target_unit_types=["human"],

        tags=[
            "social",
            "human_network"
        ]
    ),

    "family": RelationTypeDefinition(
        relation_type="family",

        category="social",

        description="Family relationship.",

        directed=False,

        symmetric=True,

        source_unit_types=["human"],

        target_unit_types=["human"],

        tags=[
            "kinship"
        ]
    ),

    "employee_of": RelationTypeDefinition(
        relation_type="employee_of",

        category="organizational",

        description="Human employed by organization.",

        directed=True,

        symmetric=False,

        source_unit_types=[
            "human"
        ],

        target_unit_types=[
            "company",
            "organization"
        ],

        inverse_relation="employs",

        tags=[
            "workforce"
        ]
    ),

    "employs": RelationTypeDefinition(
        relation_type="employs",

        category="organizational",

        description="Organization employs human.",

        directed=True,

        symmetric=False,

        source_unit_types=[
            "company",
            "organization"
        ],

        target_unit_types=[
            "human"
        ],

        inverse_relation="employee_of"
    ),

    "member_of": RelationTypeDefinition(
        relation_type="member_of",

        category="organizational",

        description="Membership relation.",

        directed=True,

        source_unit_types=[
            "human"
        ],

        target_unit_types=[
            "organization",
            "community",
            "group"
        ]
    ),

    # ECONOMIC RELATIONS

    "supplier_of": RelationTypeDefinition(
        relation_type="supplier_of",

        category="economic",

        description="Supplies goods/services to another unit.",

        directed=True,

        source_unit_types=[
            "company"
        ],

        target_unit_types=[
            "company"
        ],

        inverse_relation="customer_of",

        tags=[
            "supply_chain"
        ]
    ),

    "customer_of": RelationTypeDefinition(
        relation_type="customer_of",

        category="economic",

        description="Purchases from supplier.",

        directed=True,

        source_unit_types=[
            "company"
        ],

        target_unit_types=[
            "company"
        ],

        inverse_relation="supplier_of"
    ),

    "competitor_of": RelationTypeDefinition(
        relation_type="competitor_of",

        category="economic",

        description="Competes in same market.",

        directed=False,

        symmetric=True,

        source_unit_types=[
            "company"
        ],

        target_unit_types=[
            "company"
        ],

        tags=[
            "market"
        ]
    ),

    "investor_in": RelationTypeDefinition(
        relation_type="investor_in",

        category="financial",

        description="Investment relation.",

        directed=True,

        source_unit_types=[
            "human",
            "company",
            "fund"
        ],

        target_unit_types=[
            "company",
            "stock",
            "startup"
        ],

        inverse_relation="funded_by",

        tags=[
            "capital_flow"
        ]
    ),

    "funded_by": RelationTypeDefinition(
        relation_type="funded_by",

        category="financial",

        description="Entity funded by another entity.",

        directed=True,

        source_unit_types=[
            "company",
            "startup",
            "stock"
        ],

        target_unit_types=[
            "human",
            "company",
            "fund"
        ],

        inverse_relation="investor_in"
    ),

    # GEOGRAPHIC RELATIONS

    "located_in": RelationTypeDefinition(
        relation_type="located_in",

        category="geographic",

        description="Unit located inside geographic unit.",

        directed=True,

        source_unit_types=[
            "human",
            "company",
            "organization"
        ],

        target_unit_types=[
            "city",
            "state",
            "country"
        ],

        inverse_relation="contains",

        tags=[
            "spatial"
        ]
    ),

    "contains": RelationTypeDefinition(
        relation_type="contains",

        category="geographic",

        description="Geographic containment relation.",

        directed=True,

        source_unit_types=[
            "city",
            "state",
            "country"
        ],

        target_unit_types=[
            "human",
            "company",
            "organization",
            "city"
        ],

        inverse_relation="located_in"
    ),

    "connected_to": RelationTypeDefinition(
        relation_type="connected_to",

        category="infrastructure",

        description="Infrastructure or transport linkage.",

        directed=False,

        symmetric=True,

        source_unit_types=[
            "city",
            "state",
            "country"
        ],

        target_unit_types=[
            "city",
            "state",
            "country"
        ],

        tags=[
            "transport",
            "network"
        ]
    ),

    # GOVERNANCE RELATIONS

    "governed_by": RelationTypeDefinition(
        relation_type="governed_by",

        category="governance",

        description="Governance/control relation.",

        directed=True,

        source_unit_types=[
            "city",
            "state",
            "organization"
        ],

        target_unit_types=[
            "state",
            "country",
            "government"
        ],

        inverse_relation="governs"
    ),

    "governs": RelationTypeDefinition(
        relation_type="governs",

        category="governance",

        description="Governing authority relation.",

        directed=True,

        source_unit_types=[
            "government",
            "country",
            "state"
        ],

        target_unit_types=[
            "city",
            "state",
            "organization"
        ],

        inverse_relation="governed_by"
    ),

    # MARKET RELATIONS

    "belongs_to_sector": RelationTypeDefinition(
        relation_type="belongs_to_sector",

        category="market",

        description="Stock/company sector classification.",

        directed=True,

        source_unit_types=[
            "stock",
            "company"
        ],

        target_unit_types=[
            "sector"
        ]
    ),

    "issued_by": RelationTypeDefinition(
        relation_type="issued_by",

        category="market",

        description="Stock issued by company.",

        directed=True,

        source_unit_types=[
            "stock"
        ],

        target_unit_types=[
            "company"
        ]
    ),

    # KNOWLEDGE RELATIONS

    "supports": RelationTypeDefinition(
        relation_type="supports",

        category="knowledge",

        description="Supports a hypothesis or claim.",

        directed=True,

        tags=[
            "evidence"
        ]
    ),

    "contradicts": RelationTypeDefinition(
        relation_type="contradicts",

        category="knowledge",

        description="Contradicts another entity.",

        directed=True,

        tags=[
            "debate",
            "logic"
        ]
    ),

    "related_to": RelationTypeDefinition(
        relation_type="related_to",

        category="knowledge",

        description="Generic semantic relation.",

        directed=False,

        symmetric=True
    ),

    # AI SYSTEM RELATIONS

    "collaborates_with": RelationTypeDefinition(
        relation_type="collaborates_with",

        category="artificial",

        description="Collaboration between AI agents.",

        directed=False,

        symmetric=True,

        source_unit_types=[
            "ai_agent"
        ],

        target_unit_types=[
            "ai_agent"
        ]
    ),

    "derived_from": RelationTypeDefinition(
        relation_type="derived_from",

        category="knowledge",

        description="Knowledge/model derivation relation.",

        directed=True
    )
}

# HELPER FUNCTIONS

def get_relation_type(
    relation_type: str
) -> Optional[RelationTypeDefinition]:

    return RELATION_TYPES.get(relation_type)

def relation_type_exists(
    relation_type: str
) -> bool:

    return relation_type in RELATION_TYPES

def list_relation_types() -> List[str]:
    return list(RELATION_TYPES.keys())

def get_relation_types_by_category(
    category: str
) -> List[str]:

    return [
        name
        for name, definition in RELATION_TYPES.items()
        if definition.category == category
    ]

def get_inverse_relation(
    relation_type: str
) -> Optional[str]:

    definition = RELATION_TYPES.get(relation_type)

    if not definition:
        return None

    return definition.inverse_relation