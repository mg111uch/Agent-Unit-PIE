from __future__ import annotations

from typing import Dict, List, Optional, Callable, Any
from collections import defaultdict
import traceback

from kernel.utils.logger import get_child_logger
from kernel.memory.memory_engine import memory_engine
from kernel.memory.working_memory import working_memory

from kernel.schemas.signal_schema import SignalSchema
from kernel.schemas.event_schema import EventSchema

from kernel.ontology.signal_types import (
    signal_type_exists,
    get_signal_type
)


logger = get_child_logger("signal_engine")


# =========================================================
# SIGNAL HANDLER
# =========================================================

SignalHandler = Callable[[SignalSchema], Optional[Any]]


# =========================================================
# SIGNAL ENGINE
# =========================================================

class SignalEngine:

    def __init__(self):

        # signal_type -> handlers
        self.signal_handlers: Dict[
            str,
            List[SignalHandler]
        ] = defaultdict(list)

        # signal history
        self.signal_history: List[str] = []

        # recent signals
        self.recent_signals: List[
            SignalSchema
        ] = []

        self.max_recent_signals = 1000

    # =====================================================
    # SIGNAL EMISSION
    # =====================================================

    def emit_signal(
        self,
        signal: SignalSchema,
        persist: bool = True,
        trigger_handlers: bool = True,
        add_to_working_memory: bool = True,
    ) -> SignalSchema:

        # -------------------------------------------------
        # VALIDATION
        # -------------------------------------------------

        if not signal_type_exists(
            signal.signal_type
        ):

            logger.warning(
                f"Unknown signal type: "
                f"{signal.signal_type}"
            )

        # -------------------------------------------------
        # SAVE SIGNAL
        # -------------------------------------------------

        if persist:

            memory_engine.save_signal(
                signal=signal,
                memory_type="episodic"
            )

        # -------------------------------------------------
        # WORKING MEMORY
        # -------------------------------------------------

        if add_to_working_memory:

            working_memory.add_memory(
                memory_id=signal.signal_id,
                memory_type="signal",
                content=signal.to_dict(),
                importance=signal.metrics.importance,
                confidence=signal.metrics.confidence,
                tags=[
                    signal.signal_type,
                    signal.category
                ],
                metadata={
                    "source_unit_id":
                    signal.source_unit_id
                },
                ttl_seconds=3600,
            )

        # -------------------------------------------------
        # HISTORY
        # -------------------------------------------------

        self.signal_history.append(
            signal.signal_id
        )

        self.recent_signals.append(signal)

        if (
            len(self.recent_signals)
            > self.max_recent_signals
        ):
            self.recent_signals.pop(0)

        logger.info(
            f"Signal emitted: "
            f"{signal.signal_id}"
        )

        # -------------------------------------------------
        # HANDLERS
        # -------------------------------------------------

        if trigger_handlers:

            self._trigger_handlers(signal)

        return signal

    # =====================================================
    # SIGNAL CREATION
    # =====================================================

    def create_signal(
        self,
        signal_type: str,
        source_unit_id: str,
        value: Any,
        category: str = "general",
        subtype: str = "generic",
        title: str = "",
        description: str = "",
        confidence: float = 1.0,
        importance: float = 0.5,
        tags: Optional[List[str]] = None,
        metadata: Optional[Dict] = None,
        persist: bool = True,
        trigger_handlers: bool = True,
    ) -> SignalSchema:

        signal = SignalSchema.create(
            signal_type=signal_type,
            source_unit_id=source_unit_id,
            value=value,
            category=category,
            subtype=subtype,
            title=title,
            description=description,
        )

        signal.metrics.confidence = confidence

        signal.metrics.importance = importance

        signal.metadata.tags.extend(
            tags or []
        )

        signal.metadata.extra.update(
            metadata or {}
        )

        return self.emit_signal(
            signal=signal,
            persist=persist,
            trigger_handlers=trigger_handlers,
        )

    # =====================================================
    # HANDLERS
    # =====================================================

    def register_handler(
        self,
        signal_type: str,
        handler: SignalHandler
    ):

        self.signal_handlers[
            signal_type
        ].append(handler)

        logger.info(
            f"Registered signal handler: "
            f"{signal_type}"
        )

    def unregister_handler(
        self,
        signal_type: str,
        handler: SignalHandler
    ):

        if (
            signal_type
            not in self.signal_handlers
        ):
            return

        if (
            handler
            in self.signal_handlers[
                signal_type
            ]
        ):

            self.signal_handlers[
                signal_type
            ].remove(handler)

            logger.info(
                f"Unregistered handler: "
                f"{signal_type}"
            )

    # =====================================================
    # HANDLER EXECUTION
    # =====================================================

    def _trigger_handlers(
        self,
        signal: SignalSchema
    ):

        handlers = (
            self.signal_handlers.get(
                signal.signal_type,
                []
            )
        )

        for handler in handlers:

            try:

                handler(signal)

            except Exception as e:

                logger.error(
                    f"Signal handler failed: "
                    f"{str(e)}"
                )

                traceback.print_exc()

    # =====================================================
    # SEARCH
    # =====================================================

    def get_recent_signals(
        self,
        limit: int = 10,
        signal_type: Optional[str] = None
    ) -> List[SignalSchema]:

        signals = self.recent_signals

        if signal_type:

            signals = [
                s for s in signals
                if s.signal_type == signal_type
            ]

        return signals[-limit:]

    def search_signals_by_source(
        self,
        source_unit_id: str
    ) -> List[SignalSchema]:

        return [
            signal
            for signal
            in self.recent_signals
            if (
                signal.source_unit_id
                == source_unit_id
            )
        ]

    def search_signals_by_tag(
        self,
        tag: str
    ) -> List[SignalSchema]:

        results = []

        for signal in self.recent_signals:

            if (
                tag
                in signal.metadata.tags
            ):
                results.append(signal)

        return results

    # =====================================================
    # AGGREGATION
    # =====================================================

    def aggregate_signal_values(
        self,
        signal_type: str
    ) -> Dict[str, Any]:

        signals = [
            s for s in self.recent_signals
            if s.signal_type == signal_type
        ]

        if not signals:

            return {
                "count": 0,
                "average": None,
            }

        numeric_values = []

        for signal in signals:

            if isinstance(
                signal.value,
                (int, float)
            ):
                numeric_values.append(
                    signal.value
                )

        if not numeric_values:

            return {
                "count": len(signals),
                "average": None,
            }

        avg = (
            sum(numeric_values)
            / len(numeric_values)
        )

        return {
            "count": len(signals),
            "average": avg,
            "min": min(numeric_values),
            "max": max(numeric_values),
        }

    # =====================================================
    # SIGNAL -> EVENT
    # =====================================================

    def signal_to_event(
        self,
        signal: SignalSchema,
        event_type: str,
        title: str = "",
        description: str = ""
    ) -> EventSchema:

        event = EventSchema.create(
            event_type=event_type,
            title=title,
            description=description,
            source_unit_id=signal.source_unit_id,
        )

        event.add_signal_reference(
            signal.signal_id
        )

        logger.info(
            f"Signal converted to event: "
            f"{signal.signal_id}"
        )

        return event

    # =====================================================
    # STATS
    # =====================================================

    def stats(self) -> Dict[str, Any]:

        return {
            "total_signal_history":
            len(self.signal_history),

            "recent_signals":
            len(self.recent_signals),

            "registered_signal_types":
            len(self.signal_handlers),

            "total_handlers":
            sum(
                len(v)
                for v in self.signal_handlers.values()
            ),
        }

    # =====================================================
    # CLEAR
    # =====================================================

    def clear_recent_signals(self):

        self.recent_signals.clear()

        logger.warning(
            "Recent signals cleared"
        )


# =========================================================
# GLOBAL ENGINE
# =========================================================

signal_engine = SignalEngine()