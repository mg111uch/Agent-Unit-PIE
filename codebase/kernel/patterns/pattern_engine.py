from __future__ import annotations

from typing import Dict, List, Optional, Any
from collections import defaultdict
import statistics
import time

from kernel.utils.logger import get_child_logger

from kernel.schemas.pattern_schema import PatternSchema
from kernel.schemas.signal_schema import SignalSchema
from kernel.schemas.event_schema import EventSchema

from kernel.memory.memory_engine import memory_engine
from kernel.memory.working_memory import working_memory

from kernel.utils.ids import generate_pattern_id


logger = get_child_logger("pattern_engine")


# =========================================================
# PATTERN ENGINE
# =========================================================

class PatternEngine:

    def __init__(self):

        self.patterns: Dict[
            str,
            PatternSchema
        ] = {}

        self.pattern_index = defaultdict(list)

        self.source_index = defaultdict(list)

        self.detected_pattern_history = []

    # =====================================================
    # PATTERN STORAGE
    # =====================================================

    def register_pattern(
        self,
        pattern: PatternSchema,
        persist: bool = True,
        add_to_memory: bool = True,
    ) -> PatternSchema:

        self.patterns[
            pattern.pattern_id
        ] = pattern

        self.pattern_index[
            pattern.pattern_type
        ].append(
            pattern.pattern_id
        )

        for source_id in pattern.source_ids:

            self.source_index[
                source_id
            ].append(
                pattern.pattern_id
            )

        # -------------------------------------------------
        # PERSIST
        # -------------------------------------------------

        if persist:

            memory_engine.save_pattern(
                pattern=pattern,
                memory_type="pattern"
            )

        # -------------------------------------------------
        # WORKING MEMORY
        # -------------------------------------------------

        if add_to_memory:

            working_memory.add_memory(
                memory_id=pattern.pattern_id,
                memory_type="pattern",
                content=pattern.to_dict(),
                importance=pattern.metrics.importance,
                confidence=pattern.metrics.confidence,
                tags=[
                    pattern.pattern_type,
                    pattern.category,
                ],
                metadata={
                    "source_count":
                    len(pattern.source_ids)
                },
                ttl_seconds=7200,
            )

        self.detected_pattern_history.append(
            pattern.pattern_id
        )

        logger.info(
            f"Pattern registered: "
            f"{pattern.pattern_id}"
        )

        return pattern

    # =====================================================
    # CREATE PATTERN
    # =====================================================

    def create_pattern(
        self,
        pattern_type: str,
        title: str,
        description: str,
        source_ids: List[str],
        category: str = "general",
        subtype: str = "generic",
        confidence: float = 1.0,
        importance: float = 0.5,
        tags: Optional[List[str]] = None,
        metadata: Optional[Dict] = None,
    ) -> PatternSchema:

        pattern = PatternSchema.create(
            pattern_type=pattern_type,
            title=title,
            description=description,
            source_ids=source_ids,
            category=category,
            subtype=subtype,
        )

        pattern.metrics.confidence = confidence

        pattern.metrics.importance = importance

        pattern.metadata.tags.extend(
            tags or []
        )

        pattern.metadata.extra.update(
            metadata or {}
        )

        return self.register_pattern(
            pattern
        )

    # =====================================================
    # TREND DETECTION
    # =====================================================

    def detect_numeric_trend(
        self,
        signals: List[SignalSchema],
        signal_name: str = "trend"
    ) -> Optional[PatternSchema]:

        numeric_values = []

        for signal in signals:

            if isinstance(
                signal.value,
                (int, float)
            ):

                numeric_values.append(
                    signal.value
                )

        if len(numeric_values) < 3:
            return None

        # -------------------------------------------------
        # TREND ANALYSIS
        # -------------------------------------------------

        first = numeric_values[0]

        last = numeric_values[-1]

        avg = statistics.mean(
            numeric_values
        )

        direction = "stable"

        if last > first:
            direction = "increasing"

        elif last < first:
            direction = "decreasing"

        volatility = (
            statistics.stdev(numeric_values)
            if len(numeric_values) > 1
            else 0.0
        )

        confidence = min(
            1.0,
            abs(last - first)
            / (abs(avg) + 1e-6)
        )

        source_ids = [
            s.signal_id
            for s in signals
        ]

        pattern = PatternSchema.create(
            pattern_type="trend_pattern",

            title=f"{signal_name} trend",

            description=(
                f"{signal_name} shows "
                f"{direction} behaviour"
            ),

            source_ids=source_ids,

            category="trend",

            subtype=direction,
        )

        pattern.metrics.confidence = confidence

        pattern.metrics.importance = min(
            1.0,
            volatility / 10.0
        )

        pattern.metadata.extra.update({

            "direction":
            direction,

            "average":
            avg,

            "volatility":
            volatility,

            "first_value":
            first,

            "last_value":
            last,
        })

        return self.register_pattern(
            pattern
        )

    # =====================================================
    # REPEATED EVENT DETECTION
    # =====================================================

    def detect_repeated_events(
        self,
        events: List[EventSchema],
        threshold: int = 3
    ) -> List[PatternSchema]:

        grouped_events = defaultdict(list)

        for event in events:

            grouped_events[
                event.event_type
            ].append(event)

        patterns = []

        for event_type, event_group in (
            grouped_events.items()
        ):

            if len(event_group) >= threshold:

                pattern = PatternSchema.create(
                    pattern_type="repeated_event",

                    title=(
                        f"Repeated "
                        f"{event_type}"
                    ),

                    description=(
                        f"{event_type} occurred "
                        f"{len(event_group)} times"
                    ),

                    source_ids=[
                        e.event_id
                        for e in event_group
                    ],

                    category="event_pattern",

                    subtype=event_type,
                )

                pattern.metrics.confidence = min(
                    1.0,
                    len(event_group) / 10
                )

                pattern.metrics.importance = 0.7

                pattern.metadata.extra.update({

                    "event_count":
                    len(event_group),

                    "event_type":
                    event_type,
                })

                patterns.append(
                    self.register_pattern(
                        pattern
                    )
                )

        return patterns

    # =====================================================
    # CORRELATION DETECTION
    # =====================================================

    def detect_shared_sources(
        self,
        patterns: List[PatternSchema]
    ) -> List[PatternSchema]:

        source_map = defaultdict(list)

        for pattern in patterns:

            for source_id in pattern.source_ids:

                source_map[
                    source_id
                ].append(
                    pattern.pattern_id
                )

        correlated_patterns = []

        for source_id, linked_patterns in (
            source_map.items()
        ):

            if len(linked_patterns) >= 2:

                correlation = PatternSchema.create(
                    pattern_type="correlation_pattern",

                    title="Shared source correlation",

                    description=(
                        "Multiple patterns "
                        "share same source"
                    ),

                    source_ids=linked_patterns,

                    category="correlation",

                    subtype="shared_source",
                )

                correlation.metrics.confidence = 0.8

                correlation.metrics.importance = 0.6

                correlation.metadata.extra.update({

                    "shared_source":
                    source_id,

                    "linked_patterns":
                    linked_patterns,
                })

                correlated_patterns.append(
                    self.register_pattern(
                        correlation
                    )
                )

        return correlated_patterns

    # =====================================================
    # SEARCH
    # =====================================================

    def get_pattern(
        self,
        pattern_id: str
    ) -> Optional[PatternSchema]:

        return self.patterns.get(
            pattern_id
        )

    def get_patterns_by_type(
        self,
        pattern_type: str
    ) -> List[PatternSchema]:

        pattern_ids = self.pattern_index.get(
            pattern_type,
            []
        )

        return [
            self.patterns[pid]
            for pid in pattern_ids
            if pid in self.patterns
        ]

    def get_patterns_by_source(
        self,
        source_id: str
    ) -> List[PatternSchema]:

        pattern_ids = self.source_index.get(
            source_id,
            []
        )

        return [
            self.patterns[pid]
            for pid in pattern_ids
            if pid in self.patterns
        ]

    def get_recent_patterns(
        self,
        limit: int = 20
    ) -> List[PatternSchema]:

        recent_ids = (
            self.detected_pattern_history[-limit:]
        )

        return [
            self.patterns[pid]
            for pid in recent_ids
            if pid in self.patterns
        ]

    # =====================================================
    # REMOVE
    # =====================================================

    def remove_pattern(
        self,
        pattern_id: str
    ) -> bool:

        if pattern_id not in self.patterns:
            return False

        pattern = self.patterns[
            pattern_id
        ]

        if (
            pattern_id
            in self.pattern_index[
                pattern.pattern_type
            ]
        ):

            self.pattern_index[
                pattern.pattern_type
            ].remove(pattern_id)

        for source_id in pattern.source_ids:

            if (
                pattern_id
                in self.source_index[
                    source_id
                ]
            ):

                self.source_index[
                    source_id
                ].remove(pattern_id)

        del self.patterns[
            pattern_id
        ]

        logger.info(
            f"Pattern removed: "
            f"{pattern_id}"
        )

        return True

    # =====================================================
    # STATS
    # =====================================================

    def stats(self) -> Dict[str, Any]:

        return {

            "total_patterns":
            len(self.patterns),

            "pattern_types":
            len(self.pattern_index),

            "source_links":
            len(self.source_index),

            "pattern_history":
            len(
                self.detected_pattern_history
            ),
        }

    # =====================================================
    # CLEAR
    # =====================================================

    def clear(self):

        self.patterns.clear()

        self.pattern_index.clear()

        self.source_index.clear()

        self.detected_pattern_history.clear()

        logger.warning(
            "Pattern engine cleared"
        )


# =========================================================
# GLOBAL ENGINE
# =========================================================

pattern_engine = PatternEngine()