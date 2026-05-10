from __future__ import annotations

from typing import Dict, List, Optional, Callable, Any
from collections import defaultdict
import traceback

from kernel.utils.logger import get_child_logger

from kernel.memory.memory_engine import memory_engine
from kernel.memory.working_memory import working_memory
from kernel.memory.episodic_memory import episodic_memory

from kernel.schemas.event_schema import EventSchema
from kernel.schemas.signal_schema import SignalSchema

from kernel.utils.ids import generate_id


logger = get_child_logger("event_engine")


# =========================================================
# EVENT HANDLER
# =========================================================

EventHandler = Callable[[EventSchema], Optional[Any]]


# =========================================================
# EVENT ENGINE
# =========================================================

class EventEngine:

    def __init__(self):

        # event_type -> handlers
        self.event_handlers: Dict[
            str,
            List[EventHandler]
        ] = defaultdict(list)

        self.event_history: List[str] = []

        self.recent_events: List[
            EventSchema
        ] = []

        self.max_recent_events = 1000

    # =====================================================
    # EVENT EMISSION
    # =====================================================

    def emit_event(
        self,
        event: EventSchema,
        persist: bool = True,
        trigger_handlers: bool = True,
        add_to_working_memory: bool = True,
        create_episode: bool = True,
    ) -> EventSchema:

        # -------------------------------------------------
        # PERSIST
        # -------------------------------------------------

        if persist:

            memory_engine.save_event(
                event=event,
                memory_type="episodic"
            )

        # -------------------------------------------------
        # WORKING MEMORY
        # -------------------------------------------------

        if add_to_working_memory:

            working_memory.add_memory(
                memory_id=event.event_id,
                memory_type="event",
                content=event.to_dict(),
                importance=event.metrics.importance,
                confidence=event.metrics.confidence,
                tags=[
                    event.event_type,
                    event.category
                ],
                metadata={
                    "source_unit_id":
                    event.source_unit_id
                },
                ttl_seconds=7200,
            )

        # -------------------------------------------------
        # CREATE EPISODE
        # -------------------------------------------------

        if create_episode:

            episodic_memory.create_episode(
                episode_id=generate_id(
                    prefix="episode"
                ),

                episode_type=event.event_type,

                summary=event.description,

                entities=[
                    event.source_unit_id
                ] if event.source_unit_id else [],

                events=[
                    event.event_id
                ],

                signals=event.signal_references,

                patterns=event.pattern_references,

                tags=event.metadata.tags,

                importance=event.metrics.importance,

                confidence=event.metrics.confidence,

                metadata={
                    "event_category":
                    event.category
                },
            )

        # -------------------------------------------------
        # HISTORY
        # -------------------------------------------------

        self.event_history.append(
            event.event_id
        )

        self.recent_events.append(
            event
        )

        if (
            len(self.recent_events)
            > self.max_recent_events
        ):
            self.recent_events.pop(0)

        logger.info(
            f"Event emitted: "
            f"{event.event_id}"
        )

        # -------------------------------------------------
        # HANDLERS
        # -------------------------------------------------

        if trigger_handlers:

            self._trigger_handlers(event)

        return event

    # =====================================================
    # CREATE EVENT
    # =====================================================

    def create_event(
        self,
        event_type: str,
        title: str,
        description: str,
        source_unit_id: Optional[str] = None,
        category: str = "general",
        subtype: str = "generic",
        confidence: float = 1.0,
        importance: float = 0.5,
        urgency: float = 0.5,
        tags: Optional[List[str]] = None,
        metadata: Optional[Dict] = None,
        signal_references: Optional[List[str]] = None,
        persist: bool = True,
        trigger_handlers: bool = True,
    ) -> EventSchema:

        event = EventSchema.create(
            event_type=event_type,
            title=title,
            description=description,
            source_unit_id=source_unit_id,
            category=category,
            subtype=subtype,
        )

        event.metrics.confidence = confidence

        event.metrics.importance = importance

        event.metrics.urgency = urgency

        event.metadata.tags.extend(
            tags or []
        )

        event.metadata.extra.update(
            metadata or {}
        )

        if signal_references:

            for signal_id in signal_references:

                event.add_signal_reference(
                    signal_id
                )

        return self.emit_event(
            event=event,
            persist=persist,
            trigger_handlers=trigger_handlers,
        )

    # =====================================================
    # SIGNAL -> EVENT
    # =====================================================

    def create_event_from_signal(
        self,
        signal: SignalSchema,
        event_type: str,
        title: str,
        description: str,
        importance_multiplier: float = 1.0,
    ) -> EventSchema:

        event = EventSchema.create(
            event_type=event_type,
            title=title,
            description=description,
            source_unit_id=signal.source_unit_id,
            category=signal.category,
            subtype=signal.subtype,
        )

        event.metrics.confidence = (
            signal.metrics.confidence
        )

        event.metrics.importance = (
            signal.metrics.importance
            * importance_multiplier
        )

        event.metrics.urgency = (
            signal.metrics.urgency
        )

        event.add_signal_reference(
            signal.signal_id
        )

        event.metadata.tags.extend(
            signal.metadata.tags
        )

        return self.emit_event(
            event=event
        )

    # =====================================================
    # EVENT HANDLERS
    # =====================================================

    def register_handler(
        self,
        event_type: str,
        handler: EventHandler
    ):

        self.event_handlers[
            event_type
        ].append(handler)

        logger.info(
            f"Registered event handler: "
            f"{event_type}"
        )

    def unregister_handler(
        self,
        event_type: str,
        handler: EventHandler
    ):

        if (
            event_type
            not in self.event_handlers
        ):
            return

        if (
            handler
            in self.event_handlers[
                event_type
            ]
        ):

            self.event_handlers[
                event_type
            ].remove(handler)

            logger.info(
                f"Unregistered handler: "
                f"{event_type}"
            )

    # =====================================================
    # HANDLER EXECUTION
    # =====================================================

    def _trigger_handlers(
        self,
        event: EventSchema
    ):

        handlers = self.event_handlers.get(
            event.event_type,
            []
        )

        for handler in handlers:

            try:

                handler(event)

            except Exception as e:

                logger.error(
                    f"Event handler failed: "
                    f"{str(e)}"
                )

                traceback.print_exc()

    # =====================================================
    # SEARCH
    # =====================================================

    def get_recent_events(
        self,
        limit: int = 10,
        event_type: Optional[str] = None
    ) -> List[EventSchema]:

        events = self.recent_events

        if event_type:

            events = [
                e for e in events
                if e.event_type == event_type
            ]

        return events[-limit:]

    def search_events_by_source(
        self,
        source_unit_id: str
    ) -> List[EventSchema]:

        return [
            event
            for event in self.recent_events
            if (
                event.source_unit_id
                == source_unit_id
            )
        ]

    def search_events_by_tag(
        self,
        tag: str
    ) -> List[EventSchema]:

        results = []

        for event in self.recent_events:

            if (
                tag
                in event.metadata.tags
            ):
                results.append(event)

        return results

    # =====================================================
    # EVENT CHAINS
    # =====================================================

    def link_events(
        self,
        parent_event: EventSchema,
        child_event: EventSchema
    ):

        parent_event.add_related_event(
            child_event.event_id
        )

        logger.info(
            f"Linked events: "
            f"{parent_event.event_id} -> "
            f"{child_event.event_id}"
        )

    # =====================================================
    # STATS
    # =====================================================

    def stats(self) -> Dict[str, Any]:

        return {
            "total_event_history":
            len(self.event_history),

            "recent_events":
            len(self.recent_events),

            "registered_event_types":
            len(self.event_handlers),

            "total_handlers":
            sum(
                len(v)
                for v in self.event_handlers.values()
            ),
        }

    # =====================================================
    # CLEAR
    # =====================================================

    def clear_recent_events(self):

        self.recent_events.clear()

        logger.warning(
            "Recent events cleared"
        )


# =========================================================
# GLOBAL ENGINE
# =========================================================

event_engine = EventEngine()