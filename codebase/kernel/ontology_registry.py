"""
kernel/ontology_registry.py

Unified ontology registry.

Purpose
-------
Central access layer for all ontology systems used in
agent_unit_pie.

This registry provides:

- validation
- lookup
- ontology discovery
- cross-ontology querying
- category resolution
- ontology extensibility

Supported Ontologies
--------------------
- event types
- pattern types
- signal types
- relation types
- entity types
- unit types
- resource types
- behavior types

Core Philosophy
----------------
All cognition layers should use standardized ontology
definitions instead of ad-hoc strings.

This prevents:

- schema drift
- inconsistent naming
- duplicate semantics
- invalid cognition artifacts
"""

from __future__ import annotations

import logging
from typing import Dict, Any, List, Optional


logger = logging.getLogger(__name__)


# ============================================================
# IMPORT ONTOLOGIES
# ============================================================

try:

    from kernel.ontology.event_types import (
        EVENT_TYPES,
        ALL_EVENT_TYPES,
        EVENT_CATEGORY_LOOKUP,
    )

except Exception:

    EVENT_TYPES = {}
    ALL_EVENT_TYPES = []
    EVENT_CATEGORY_LOOKUP = {}

try:

    from kernel.ontology.pattern_types import (
        PATTERN_TYPES,
        ALL_PATTERN_TYPES,
        PATTERN_CATEGORY_LOOKUP,
    )

except Exception:

    PATTERN_TYPES = {}
    ALL_PATTERN_TYPES = []
    PATTERN_CATEGORY_LOOKUP = {}

# ------------------------------------------------------------
# OPTIONAL FUTURE ONTOLOGIES
# ------------------------------------------------------------

try:

    from kernel.ontology.signal_types import (
        SIGNAL_TYPES,
        ALL_SIGNAL_TYPES,
        SIGNAL_CATEGORY_LOOKUP,
    )

except Exception:

    SIGNAL_TYPES = {}
    ALL_SIGNAL_TYPES = []
    SIGNAL_CATEGORY_LOOKUP = {}

try:

    from kernel.ontology.relation_types import (
        RELATION_TYPES,
        ALL_RELATION_TYPES,
        RELATION_CATEGORY_LOOKUP,
    )

except Exception:

    RELATION_TYPES = {}
    ALL_RELATION_TYPES = []
    RELATION_CATEGORY_LOOKUP = {}

try:

    from kernel.ontology.entity_types import (
        ENTITY_TYPES,
        ALL_ENTITY_TYPES,
        ENTITY_CATEGORY_LOOKUP,
    )

except Exception:

    ENTITY_TYPES = {}
    ALL_ENTITY_TYPES = []
    ENTITY_CATEGORY_LOOKUP = {}

try:

    from kernel.ontology.unit_types import (
        UNIT_TYPES,
        ALL_UNIT_TYPES,
        UNIT_CATEGORY_LOOKUP,
    )

except Exception:

    UNIT_TYPES = {}
    ALL_UNIT_TYPES = []
    UNIT_CATEGORY_LOOKUP = {}

try:

    from kernel.ontology.resource_types import (
        RESOURCE_TYPES,
        ALL_RESOURCE_TYPES,
        RESOURCE_CATEGORY_LOOKUP,
    )

except Exception:

    RESOURCE_TYPES = {}
    ALL_RESOURCE_TYPES = []
    RESOURCE_CATEGORY_LOOKUP = {}


# ============================================================
# ONTOLOGY REGISTRY
# ============================================================

class OntologyRegistry:
    """
    Unified ontology access layer.
    """

    # ========================================================
    # INIT
    # ========================================================

    def __init__(self):

        self.ontologies = {

            "event": {
                "types": EVENT_TYPES,
                "flat": set(
                    ALL_EVENT_TYPES
                ),
                "lookup": (
                    EVENT_CATEGORY_LOOKUP
                ),
            },

            "pattern": {
                "types": PATTERN_TYPES,
                "flat": set(
                    ALL_PATTERN_TYPES
                ),
                "lookup": (
                    PATTERN_CATEGORY_LOOKUP
                ),
            },

            "signal": {
                "types": SIGNAL_TYPES,
                "flat": set(
                    ALL_SIGNAL_TYPES
                ),
                "lookup": (
                    SIGNAL_CATEGORY_LOOKUP
                ),
            },

            "relation": {
                "types": RELATION_TYPES,
                "flat": set(
                    ALL_RELATION_TYPES
                ),
                "lookup": (
                    RELATION_CATEGORY_LOOKUP
                ),
            },

            "entity": {
                "types": ENTITY_TYPES,
                "flat": set(
                    ALL_ENTITY_TYPES
                ),
                "lookup": (
                    ENTITY_CATEGORY_LOOKUP
                ),
            },

            "unit": {
                "types": UNIT_TYPES,
                "flat": set(
                    ALL_UNIT_TYPES
                ),
                "lookup": (
                    UNIT_CATEGORY_LOOKUP
                ),
            },

            "resource": {
                "types": RESOURCE_TYPES,
                "flat": set(
                    ALL_RESOURCE_TYPES
                ),
                "lookup": (
                    RESOURCE_CATEGORY_LOOKUP
                ),
            },
        }

    # ========================================================
    # VALIDATION
    # ========================================================

    def is_valid(
        self,
        ontology_name: str,
        value: str,
    ) -> bool:
        """
        Validate ontology value.
        """

        ontology = self.ontologies.get(
            ontology_name
        )

        if ontology is None:
            return False

        return (
            value
            in ontology["flat"]
        )

    # ========================================================
    # CATEGORY LOOKUP
    # ========================================================

    def get_category(
        self,
        ontology_name: str,
        value: str,
    ) -> str:
        """
        Get category of ontology value.
        """

        ontology = self.ontologies.get(
            ontology_name
        )

        if ontology is None:
            return "unknown"

        return ontology[
            "lookup"
        ].get(
            value,
            "unknown",
        )

    # ========================================================
    # GET TYPES BY CATEGORY
    # ========================================================

    def get_types_by_category(
        self,
        ontology_name: str,
        category: str,
    ):
        """
        Get all types under category.
        """

        ontology = self.ontologies.get(
            ontology_name
        )

        if ontology is None:
            return set()

        return ontology[
            "types"
        ].get(
            category,
            set(),
        )

    # ========================================================
    # LIST ALL TYPES
    # ========================================================

    def list_types(
        self,
        ontology_name: str,
    ) -> List[str]:
        """
        List all ontology types.
        """

        ontology = self.ontologies.get(
            ontology_name
        )

        if ontology is None:
            return []

        return sorted(
            ontology["flat"]
        )

    # ========================================================
    # LIST CATEGORIES
    # ========================================================

    def list_categories(
        self,
        ontology_name: str,
    ) -> List[str]:
        """
        List ontology categories.
        """

        ontology = self.ontologies.get(
            ontology_name
        )

        if ontology is None:
            return []

        return sorted(
            ontology[
                "types"
            ].keys()
        )

    # ========================================================
    # REGISTER NEW ONTOLOGY
    # ========================================================

    def register_ontology(
        self,
        ontology_name: str,
        ontology_types: Dict[
            str,
            Any,
        ],
    ) -> None:
        """
        Dynamically register ontology.
        """

        flat = set()

        lookup = {}

        for category, values in (
            ontology_types.items()
        ):

            for value in values:

                flat.add(value)

                lookup[value] = category

        self.ontologies[
            ontology_name
        ] = {
            "types": ontology_types,
            "flat": flat,
            "lookup": lookup,
        }

        logger.info(
            f"Registered ontology: "
            f"{ontology_name}"
        )

    # ========================================================
    # REMOVE ONTOLOGY
    # ========================================================

    def remove_ontology(
        self,
        ontology_name: str,
    ) -> bool:
        """
        Remove ontology.
        """

        if (
            ontology_name
            not in self.ontologies
        ):
            return False

        del self.ontologies[
            ontology_name
        ]

        logger.info(
            f"Removed ontology: "
            f"{ontology_name}"
        )

        return True

    # ========================================================
    # GLOBAL SEARCH
    # ========================================================

    def search(
        self,
        value: str,
    ) -> Dict[str, Any]:
        """
        Search value across all ontologies.
        """

        matches = []

        for ontology_name, ontology in (
            self.ontologies.items()
        ):

            if value in ontology["flat"]:

                matches.append(
                    {
                        "ontology": (
                            ontology_name
                        ),
                        "category": ontology[
                            "lookup"
                        ].get(value),
                        "value": value,
                    }
                )

        return {
            "query": value,
            "matches": matches,
        }

    # ========================================================
    # EXPORT
    # ========================================================

    def export_registry(
        self,
    ) -> Dict[str, Any]:
        """
        Export ontology metadata.
        """

        exported = {}

        for name, ontology in (
            self.ontologies.items()
        ):

            exported[name] = {
                "categories": sorted(
                    ontology[
                        "types"
                    ].keys()
                ),
                "count": len(
                    ontology["flat"]
                ),
            }

        return exported

    # ========================================================
    # SUMMARY
    # ========================================================

    def summary(
        self,
    ) -> Dict[str, Any]:

        return {
            "ontology_count": len(
                self.ontologies
            ),
            "ontologies": (
                self.export_registry()
            ),
        }