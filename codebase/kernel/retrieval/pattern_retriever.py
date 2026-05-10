"""
kernel/retrieval/pattern_retriever.py

Pattern retrieval engine.

Purpose
-------
Provides intelligent retrieval of patterns across:

- humans
- organizations
- companies
- cities
- countries
- simulations
- financial systems
- digital twins
- behavioral systems

Core Responsibilities
---------------------
- retrieve patterns by type
- retrieve patterns by unit
- retrieve patterns by confidence
- retrieve anomaly patterns
- retrieve recurring patterns
- retrieve causal patterns
- retrieve temporal patterns
- retrieve opportunity patterns
- retrieve risk patterns
- retrieve cross-unit patterns

Core Philosophy
----------------
Patterns are one of the highest cognition layers.

signals
    →
events
    →
relations
    →
patterns
    →
insights
    →
predictions

Pattern retrieval is essential for:

- forecasting
- financial opportunity detection
- corruption analysis
- behavior prediction
- simulation intelligence
"""

from __future__ import annotations

import logging
from typing import Dict, Any, List, Optional


logger = logging.getLogger(__name__)


class PatternRetriever:
    """
    Unified pattern retrieval engine.
    """

    # ============================================================
    # INIT
    # ============================================================

    def __init__(
        self,
        pattern_storage=None,
        pattern_engine=None,
        timeline_retriever=None,
        relation_engine=None,
        embedding_engine=None,
        config: Optional[
            Dict[str, Any]
        ] = None,
    ):

        self.pattern_storage = (
            pattern_storage
        )

        self.pattern_engine = (
            pattern_engine
        )

        self.timeline_retriever = (
            timeline_retriever
        )

        self.relation_engine = (
            relation_engine
        )

        self.embedding_engine = (
            embedding_engine
        )

        self.config = config or {}

    # ============================================================
    # GET PATTERN
    # ============================================================

    def get_pattern(
        self,
        pattern_id: str,
    ) -> Optional[Dict[str, Any]]:
        """
        Retrieve single pattern.
        """

        if self.pattern_storage is None:

            return None

        try:

            return (
                self.pattern_storage
                .get_pattern(
                    pattern_id
                )
            )

        except Exception:

            logger.exception(
                "Failed retrieving pattern."
            )

            return None

    # ============================================================
    # GET BY TYPE
    # ============================================================

    def get_patterns_by_type(
        self,
        pattern_type: str,
        limit: int = 100,
    ) -> List[Dict[str, Any]]:
        """
        Retrieve patterns by type.
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

            return patterns[:limit]

        except Exception:

            logger.exception(
                "Pattern type retrieval failed."
            )

            return []

    # ============================================================
    # GET BY CATEGORY
    # ============================================================

    def get_patterns_by_category(
        self,
        category: str,
        limit: int = 100,
    ) -> List[Dict[str, Any]]:
        """
        Retrieve patterns by ontology category.
        """

        if self.pattern_storage is None:

            return []

        try:

            patterns = (
                self.pattern_storage
                .get_patterns_by_category(
                    category
                )
            )

            return patterns[:limit]

        except Exception:

            logger.exception(
                "Pattern category retrieval "
                "failed."
            )

            return []

    # ============================================================
    # GET UNIT PATTERNS
    # ============================================================

    def get_unit_patterns(
        self,
        unit_id: str,
        limit: int = 100,
    ) -> List[Dict[str, Any]]:
        """
        Retrieve patterns linked to unit.
        """

        if self.pattern_storage is None:

            return []

        try:

            patterns = (
                self.pattern_storage
                .get_patterns_by_unit(
                    unit_id
                )
            )

            return patterns[:limit]

        except Exception:

            logger.exception(
                "Unit pattern retrieval failed."
            )

            return []

    # ============================================================
    # CONFIDENCE FILTER
    # ============================================================

    def get_high_confidence_patterns(
        self,
        threshold: float = 0.8,
        limit: int = 100,
    ) -> List[Dict[str, Any]]:
        """
        Retrieve high-confidence patterns.
        """

        patterns = self.get_all_patterns()

        results = []

        for pattern in patterns:

            confidence = float(
                pattern.get(
                    "confidence",
                    0.0,
                )
            )

            if confidence >= threshold:

                results.append(pattern)

        results = sorted(
            results,
            key=lambda x: x.get(
                "confidence",
                0.0,
            ),
            reverse=True,
        )

        return results[:limit]

    # ============================================================
    # ANOMALIES
    # ============================================================

    def get_anomaly_patterns(
        self,
        limit: int = 100,
    ) -> List[Dict[str, Any]]:
        """
        Retrieve anomaly patterns.
        """

        anomaly_keywords = {
            "anomaly",
            "outlier",
            "collapse",
            "instability",
            "unexpected",
            "rare",
        }

        patterns = self.get_all_patterns()

        results = []

        for pattern in patterns:

            pattern_type = str(
                pattern.get(
                    "pattern_type",
                    ""
                )
            ).lower()

            if any(
                keyword in pattern_type
                for keyword in anomaly_keywords
            ):

                results.append(pattern)

        return results[:limit]

    # ============================================================
    # OPPORTUNITIES
    # ============================================================

    def get_opportunity_patterns(
        self,
        limit: int = 100,
    ) -> List[Dict[str, Any]]:
        """
        Retrieve opportunity patterns.
        """

        keywords = {
            "opportunity",
            "growth",
            "investment",
            "market_gap",
            "optimization",
            "emerging",
        }

        patterns = self.get_all_patterns()

        results = []

        for pattern in patterns:

            pattern_type = str(
                pattern.get(
                    "pattern_type",
                    ""
                )
            ).lower()

            if any(
                keyword in pattern_type
                for keyword in keywords
            ):

                results.append(pattern)

        return results[:limit]

    # ============================================================
    # RISKS
    # ============================================================

    def get_risk_patterns(
        self,
        limit: int = 100,
    ) -> List[Dict[str, Any]]:
        """
        Retrieve risk patterns.
        """

        keywords = {
            "risk",
            "collapse",
            "fragility",
            "instability",
            "conflict",
            "crash",
        }

        patterns = self.get_all_patterns()

        results = []

        for pattern in patterns:

            pattern_type = str(
                pattern.get(
                    "pattern_type",
                    ""
                )
            ).lower()

            if any(
                keyword in pattern_type
                for keyword in keywords
            ):

                results.append(pattern)

        return results[:limit]

    # ============================================================
    # TEMPORAL PATTERNS
    # ============================================================

    def get_temporal_patterns(
        self,
        start_time: Optional[
            str
        ] = None,
        end_time: Optional[
            str
        ] = None,
        limit: int = 100,
    ) -> List[Dict[str, Any]]:
        """
        Retrieve timeline-bound patterns.
        """

        if self.timeline_retriever is None:

            return []

        return (
            self.timeline_retriever
            .retrieve_patterns(
                start_time=start_time,
                end_time=end_time,
                limit=limit,
            )
        )

    # ============================================================
    # RECURRING PATTERNS
    # ============================================================

    def get_recurring_patterns(
        self,
        limit: int = 100,
    ) -> List[Dict[str, Any]]:
        """
        Retrieve recurring patterns.
        """

        patterns = self.get_all_patterns()

        recurring_keywords = {
            "recurring",
            "cycle",
            "seasonal",
            "habit",
            "loop",
        }

        results = []

        for pattern in patterns:

            pattern_type = str(
                pattern.get(
                    "pattern_type",
                    ""
                )
            ).lower()

            if any(
                keyword in pattern_type
                for keyword in recurring_keywords
            ):

                results.append(pattern)

        return results[:limit]

    # ============================================================
    # CROSS UNIT
    # ============================================================

    def get_cross_unit_patterns(
        self,
        min_units: int = 2,
        limit: int = 100,
    ) -> List[Dict[str, Any]]:
        """
        Retrieve patterns spanning multiple units.
        """

        patterns = self.get_all_patterns()

        results = []

        for pattern in patterns:

            linked_units = pattern.get(
                "linked_units",
                [],
            )

            if (
                len(linked_units)
                >= min_units
            ):

                results.append(pattern)

        return results[:limit]

    # ============================================================
    # CAUSAL PATTERNS
    # ============================================================

    def get_causal_patterns(
        self,
        limit: int = 100,
    ) -> List[Dict[str, Any]]:
        """
        Retrieve causal relation patterns.
        """

        keywords = {
            "causal",
            "dependency",
            "feedback",
            "correlation",
            "reinforcement",
        }

        patterns = self.get_all_patterns()

        results = []

        for pattern in patterns:

            pattern_type = str(
                pattern.get(
                    "pattern_type",
                    ""
                )
            ).lower()

            if any(
                keyword in pattern_type
                for keyword in keywords
            ):

                results.append(pattern)

        return results[:limit]

    # ============================================================
    # SEMANTIC SEARCH
    # ============================================================

    def semantic_search(
        self,
        query: str,
        limit: int = 20,
    ) -> List[Dict[str, Any]]:
        """
        Semantic pattern retrieval.
        """

        if self.embedding_engine is None:

            return []

        # --------------------------------------------------------
        # PLACEHOLDER
        # --------------------------------------------------------
        # Future:
        # vector search
        # graph retrieval
        # hybrid retrieval
        # --------------------------------------------------------

        return []

    # ============================================================
    # GET ALL
    # ============================================================

    def get_all_patterns(
        self,
    ) -> List[Dict[str, Any]]:
        """
        Retrieve all patterns.
        """

        if self.pattern_storage is None:

            return []

        try:

            return (
                self.pattern_storage
                .get_all_patterns()
            )

        except Exception:

            logger.exception(
                "Failed retrieving all "
                "patterns."
            )

            return []

    # ============================================================
    # PATTERN SUMMARY
    # ============================================================

    def summarize_patterns(
        self,
    ) -> Dict[str, Any]:
        """
        Generate pattern statistics.
        """

        patterns = self.get_all_patterns()

        categories = {}

        for pattern in patterns:

            category = pattern.get(
                "pattern_category",
                "unknown",
            )

            categories.setdefault(
                category,
                0,
            )

            categories[category] += 1

        return {
            "total_patterns": len(
                patterns
            ),
            "categories": categories,
        }

    # ============================================================
    # RETRIEVE FOR CONTEXT
    # ============================================================

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
            "patterns": [],
            "opportunities": [],
            "risks": [],
            "anomalies": [],
        }

        # --------------------------------------------------------
        # UNIT PATTERNS
        # --------------------------------------------------------

        if unit_id:

            results[
                "patterns"
            ] = self.get_unit_patterns(
                unit_id=unit_id,
                limit=limit,
            )

        # --------------------------------------------------------
        # SPECIALIZED
        # --------------------------------------------------------

        results[
            "opportunities"
        ] = self.get_opportunity_patterns(
            limit=10
        )

        results[
            "risks"
        ] = self.get_risk_patterns(
            limit=10
        )

        results[
            "anomalies"
        ] = self.get_anomaly_patterns(
            limit=10
        )

        return results

    # ============================================================
    # HEALTH CHECK
    # ============================================================

    def health_check(
        self,
    ) -> Dict[str, Any]:

        return {
            "pattern_storage": (
                self.pattern_storage
                is not None
            ),
            "pattern_engine": (
                self.pattern_engine
                is not None
            ),
            "timeline_retriever": (
                self.timeline_retriever
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