"""
kernel/retrieval/unit_retriever.py

Unit retrieval engine.

Purpose
-------
Provides intelligent retrieval of units from:

- active registry
- local storage
- memory systems
- relation graphs
- simulation systems
- digital twins

Core Responsibilities
---------------------
- retrieve units
- retrieve related units
- retrieve by type
- retrieve by pattern
- retrieve by behavior
- retrieve by relation
- retrieve by metadata
- retrieve by timeline proximity
- retrieve by semantic similarity
- retrieve for LLM context building

Core Philosophy
----------------
Units are first-class cognition entities.

Retrieval is NOT simple database querying.

Retrieval should support:

- cognition
- forecasting
- simulation
- digital twins
- financial analysis
- behavior prediction
"""

from __future__ import annotations

import logging
from typing import Dict, Any, List, Optional

logger = logging.getLogger(__name__)

class UnitRetriever:
    """
    Unified unit retrieval layer.
    """
    # INIT
    def __init__(
        self,
        unit_registry=None,
        unit_storage=None,
        pattern_storage=None,
        relation_engine=None,
        embedding_engine=None,
        config: Optional[
            Dict[str, Any]
        ] = None,
    ):
        self.unit_registry = (
            unit_registry
        )
        self.unit_storage = (
            unit_storage
        )
        self.pattern_storage = (
            pattern_storage
        )
        self.relation_engine = (
            relation_engine
        )
        self.embedding_engine = (
            embedding_engine
        )
        self.config = config or {}
    # GET UNIT
    def get_unit(
        self,
        unit_id: str,
    ) -> Optional[Dict[str, Any]]:
        """
        Retrieve single unit.
        """
        # ACTIVE REGISTRY
        if self.unit_registry:
            unit = (
                self.unit_registry.get_unit(
                    unit_id
                )
            )
            if unit:
                return unit
        # STORAGE
        if self.unit_storage:
            try:
                return (
                    self.unit_storage.get_unit(
                        unit_id
                    )
                )
            except Exception:
                logger.exception(
                    "Failed retrieving unit."
                )
        return None
    # GET BY TYPE
    def get_units_by_type(
        self,
        unit_type: str,
        limit: Optional[int] = None,
    ) -> List[Dict[str, Any]]:
        """
        Retrieve units by type.
        """
        units = []
        # REGISTRY
        if self.unit_registry:
            units.extend(
                self.unit_registry
                .get_units_by_type(
                    unit_type
                )
            )
        # STORAGE FALLBACK
        elif self.unit_storage:
            try:
                units.extend(
                    self.unit_storage
                    .get_units_by_type(
                        unit_type
                    )
                )
            except Exception:
                logger.exception(
                    "Failed retrieving "
                    "units by type."
                )
        # LIMIT
        if limit:
            units = units[:limit]
        return units
    # QUERY
    def query_units(
        self,
        filters: Dict[str, Any],
        limit: Optional[int] = None,
    ) -> List[Dict[str, Any]]:
        """
        Query units using filters.
        """
        results = []
        # REGISTRY
        if self.unit_registry:
            results.extend(
                self.unit_registry.query_units(
                    filters
                )
            )
        # STORAGE
        elif self.unit_storage:
            try:
                results.extend(
                    self.unit_storage.query_units(
                        filters
                    )
                )
            except Exception:
                logger.exception(
                    "Unit query failed."
                )
        # LIMIT
        if limit:
            results = results[:limit]
        return results
    # RELATED UNITS
    def get_related_units(
        self,
        unit_id: str,
        relation_type: Optional[
            str
        ] = None,
    ) -> List[Dict[str, Any]]:
        """
        Retrieve related units.
        """
        related = []
        # UNIT REGISTRY
        if self.unit_registry:
            resolved = (
                self.unit_registry
                .resolve_related_units(
                    unit_id
                )
            )
            for item in resolved:
                relation = item.get(
                    "relation",
                    {}
                )
                if (
                    relation_type
                    and relation.get(
                        "relation_type"
                    )
                    != relation_type
                ):
                    continue
                related.append(item)
        return related
    # PATTERN RETRIEVAL
    def get_units_by_pattern(
        self,
        pattern_type: str,
        limit: Optional[int] = None,
    ) -> List[Dict[str, Any]]:
        """
        Retrieve units linked to pattern.
        """
        if self.pattern_storage is None:
            return []
        try:
            patterns = (
                self.pattern_storage
                .get_patterns_by_type(
                    pattern_type
                )
            )
            units = []
            seen = set()
            for pattern in patterns:
                linked_units = pattern.get(
                    "linked_units",
                    [],
                )
                for unit_id in linked_units:
                    if unit_id in seen:
                        continue
                    unit = self.get_unit(
                        unit_id
                    )
                    if unit:
                        units.append(unit)
                        seen.add(unit_id)
            if limit:
                units = units[:limit]
            return units
        except Exception:
            logger.exception(
                "Pattern retrieval failed."
            )
            return []
    # BEHAVIOR RETRIEVAL
    def get_units_by_behavior(
        self,
        behavior_name: str,
    ) -> List[Dict[str, Any]]:
        """
        Retrieve units using behavior.
        """
        matches = []
        all_units = self.get_all_units()
        for unit in all_units:
            behaviors = unit.get(
                "behaviors",
                [],
            )
            if (
                behavior_name
                in behaviors
            ):
                matches.append(unit)
        return matches
    # SEMANTIC SEARCH
    def semantic_search(
        self,
        query: str,
        limit: int = 10,
    ) -> List[Dict[str, Any]]:
        """
        Semantic similarity retrieval.
        """
        if self.embedding_engine is None:
            logger.warning(
                "Embedding engine missing."
            )
            return []
        # PLACEHOLDER
        # Future:
        # embedding similarity
        # hybrid retrieval
        # graph retrieval
        # --------------------------------------------------------
        return []
    # TIMELINE RETRIEVAL
    def retrieve_near_timeline(
        self,
        timestamp: str,
        window_size: int = 10,
    ) -> List[Dict[str, Any]]:
        """
        Retrieve units near timeline.
        """
        # PLACEHOLDER
        return []
    # GET ALL
    def get_all_units(
        self,
    ) -> List[Dict[str, Any]]:
        """
        Retrieve all active units.
        """
        if self.unit_registry is None:
            return []
        return list(
            self.unit_registry.units.values()
        )
    # DIGITAL TWIN RETRIEVAL
    def get_digital_twin(
        self,
        unit_id: str,
    ) -> Optional[Dict[str, Any]]:
        """
        Retrieve digital twin state.
        """
        unit = self.get_unit(
            unit_id
        )
        if not unit:
            return None
        return unit.get(
            "digital_twin"
        )
    # RETRIEVE FOR CONTEXT
    def retrieve_for_context(
        self,
        query: str,
        unit_id: Optional[
            str
        ] = None,
        limit: int = 20,
    ) -> Dict[str, Any]:
        """
        Retrieve optimized cognition packet.
        """
        results = {
            "units": [],
            "related_units": [],
            "patterns": [],
        }
        # PRIMARY UNIT
        if unit_id:
            unit = self.get_unit(
                unit_id
            )
            if unit:
                results["units"].append(
                    unit
                )
                results[
                    "related_units"
                ] = self.get_related_units(
                    unit_id
                )
        # SEMANTIC
        semantic = self.semantic_search(
            query=query,
            limit=limit,
        )
        results["units"].extend(
            semantic
        )
        return results
    # HEALTH CHECK
    def health_check(
        self,
    ) -> Dict[str, Any]:
        return {
            "unit_registry": (
                self.unit_registry
                is not None
            ),
            "unit_storage": (
                self.unit_storage
                is not None
            ),
            "pattern_storage": (
                self.pattern_storage
                is not None
            ),
            "relation_engine": (
                self.relation_engine
                is not None
            ),
            "embedding_engine": (
                self.embedding_engine
                is not None
            ),
        }