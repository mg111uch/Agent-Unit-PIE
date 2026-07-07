"""
kernel/unit_registry.py

Unified active unit registry.

Purpose
-------
Tracks all active units across the entire
agent_unit_pie ecosystem.

Supported Units
---------------
- humans
- organizations
- companies
- cities
- states
- countries
- simulations
- digital twins
- markets
- ecosystems
- AI agents

Core Responsibilities
---------------------
- load units
- register units
- unregister units
- query units
- resolve relations
- cache active units
- search by metadata
- retrieve by type
- graph connectivity support

Core Philosophy
----------------
Everything is treated as a unit.

Units are dynamic cognition entities capable of:

- behaviors
- relations
- events
- patterns
- memory
- simulations
"""

from __future__ import annotations

import logging
from datetime import datetime, timezone
from typing import Dict, Any, List, Optional

logger = logging.getLogger(__name__)

class UnitRegistry:
    """
    Global runtime unit registry.
    """
    # INIT
    def __init__(
        self,
        unit_storage=None,
        ontology_registry=None,
        config: Optional[
            Dict[str, Any]
        ] = None,
    ):
        self.unit_storage = (
            unit_storage
        )
        self.ontology_registry = (
            ontology_registry
        )
        self.config = config or {}
        # ACTIVE CACHE
        self.units: Dict[
            str,
            Dict[str, Any]
        ] = {}
        # TYPE INDEX
        self.unit_type_index: Dict[
            str,
            set
        ] = {}
        # RELATION GRAPH
        self.relations: Dict[
            str,
            List[Dict[str, Any]]
        ] = {}
        # STATS
        self.total_registered = 0
        self.total_removed = 0
    # REGISTER
    def register_unit(
        self,
        unit: Dict[str, Any],
    ) -> bool:
        """
        Register active unit.
        """
        unit_id = unit.get("unit_id")
        if not unit_id:
            logger.warning(
                "Unit missing unit_id."
            )
            return False
        unit_type = unit.get(
            "unit_type",
            "unknown",
        )
        # CACHE
        self.units[unit_id] = unit
        # TYPE INDEX
        if (
            unit_type
            not in self.unit_type_index
        ):
            self.unit_type_index[
                unit_type
            ] = set()
        self.unit_type_index[
            unit_type
        ].add(unit_id)
        # RELATIONS
        self.relations.setdefault(
            unit_id,
            [],
        )
        self.total_registered += 1
        logger.info(
            f"Registered unit: "
            f"{unit_id} ({unit_type})"
        )
        return True
    # UNREGISTER
    def unregister_unit(
        self,
        unit_id: str,
    ) -> bool:
        """
        Remove unit from active registry.
        """
        unit = self.units.get(unit_id)
        if unit is None:
            return False
        unit_type = unit.get(
            "unit_type",
            "unknown",
        )
        # REMOVE FROM CACHE
        del self.units[unit_id]
        # REMOVE TYPE INDEX
        if (
            unit_type
            in self.unit_type_index
        ):
            self.unit_type_index[
                unit_type
            ].discard(unit_id)
        # REMOVE RELATIONS
        if unit_id in self.relations:
            del self.relations[unit_id]
        for _, relation_list in (
            self.relations.items()
        ):
            relation_list[:] = [
                r
                for r in relation_list
                if r.get("target_unit_id")
                != unit_id
            ]
        self.total_removed += 1
        logger.info(
            f"Removed unit: {unit_id}"
        )
        return True
    # LOAD UNIT
    def load_unit(
        self,
        unit_id: str,
    ) -> Optional[Dict[str, Any]]:
        """
        Load unit from storage if absent.
        """
        # CACHE HIT
        if unit_id in self.units:
            return self.units[unit_id]
        # STORAGE LOAD
        if self.unit_storage is None:
            return None
        try:
            unit = (
                self.unit_storage.get_unit(
                    unit_id
                )
            )
            if unit:
                self.register_unit(unit)
            return unit
        except Exception:
            logger.exception(
                "Failed loading unit."
            )
            return None
    # GET UNIT
    def get_unit(
        self,
        unit_id: str,
    ) -> Optional[Dict[str, Any]]:
        """
        Retrieve active unit.
        """
        return self.units.get(unit_id)
    # UNIT EXISTS
    def unit_exists(
        self,
        unit_id: str,
    ) -> bool:
        return (
            unit_id
            in self.units
        )
    # GET BY TYPE
    def get_units_by_type(
        self,
        unit_type: str,
    ) -> List[Dict[str, Any]]:
        """
        Retrieve units by type.
        """
        ids = self.unit_type_index.get(
            unit_type,
            set(),
        )
        return [
            self.units[uid]
            for uid in ids
            if uid in self.units
        ]
    # QUERY
    def query_units(
        self,
        filters: Dict[str, Any],
    ) -> List[Dict[str, Any]]:
        """
        Query units using metadata filters.
        """
        results = []
        for unit in self.units.values():
            matched = True
            for key, value in (
                filters.items()
            ):
                if (
                    unit.get(key)
                    != value
                ):
                    matched = False
                    break
            if matched:
                results.append(unit)
        return results
    # RELATIONS
    def add_relation(
        self,
        source_unit_id: str,
        target_unit_id: str,
        relation_type: str,
        metadata: Optional[
            Dict[str, Any]
        ] = None,
    ) -> bool:
        """
        Add relation between units.
        """
        if (
            source_unit_id
            not in self.units
        ):
            return False
        relation = {
            "source_unit_id": (
                source_unit_id
            ),
            "target_unit_id": (
                target_unit_id
            ),
            "relation_type": (
                relation_type
            ),
            "metadata": (
                metadata or {}
            ),
            "created_at": (
                self.utc_now()
            ),
        }
        self.relations.setdefault(
            source_unit_id,
            [],
        )
        self.relations[
            source_unit_id
        ].append(relation)
        return True
    # GET RELATIONS
    def get_relations(
        self,
        unit_id: str,
    ) -> List[Dict[str, Any]]:
        """
        Get unit relations.
        """
        return self.relations.get(
            unit_id,
            [],
        )
    # RESOLVE RELATED UNITS
    def resolve_related_units(
        self,
        unit_id: str,
    ) -> List[Dict[str, Any]]:
        """
        Resolve connected units.
        """
        related = []
        relations = self.get_relations(
            unit_id
        )
        for relation in relations:
            target_id = relation.get(
                "target_unit_id"
            )
            target_unit = self.get_unit(
                target_id
            )
            if target_unit:
                related.append(
                    {
                        "relation": relation,
                        "unit": target_unit,
                    }
                )
        return related
    # SEARCH
    def search_units(
        self,
        text: str,
    ) -> List[Dict[str, Any]]:
        """
        Lightweight text search.
        """
        text = text.lower()
        results = []
        for unit in self.units.values():
            serialized = str(
                unit
            ).lower()
            if text in serialized:
                results.append(unit)
        return results
    # CACHE CONTROL
    def clear_cache(
        self,
    ) -> None:
        """
        Clear active cache.
        """
        self.units.clear()
        self.unit_type_index.clear()
        self.relations.clear()
        logger.info(
            "Unit registry cache cleared."
        )
    # EXPORT
    def export_registry(
        self,
    ) -> Dict[str, Any]:
        """
        Export lightweight registry metadata.
        """
        return {
            "unit_count": len(
                self.units
            ),
            "unit_types": {
                key: len(value)
                for key, value in (
                    self.unit_type_index.items()
                )
            },
            "relations": sum(
                len(v)
                for v in (
                    self.relations.values()
                )
            ),
        }
    # SUMMARY
    def summary(
        self,
    ) -> Dict[str, Any]:
        return {
            "active_units": len(
                self.units
            ),
            "unit_types": len(
                self.unit_type_index
            ),
            "total_registered": (
                self.total_registered
            ),
            "total_removed": (
                self.total_removed
            ),
        }
    # HELPERS
    @staticmethod
    def utc_now() -> str:
        return datetime.now(
            timezone.utc
        ).isoformat()