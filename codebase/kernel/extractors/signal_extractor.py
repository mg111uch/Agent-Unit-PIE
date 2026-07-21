from __future__ import annotations

from typing import Dict, List, Optional, Any, Callable
import re

from kernel.utils.logger import get_child_logger
from kernel.signals.signal_engine import signal_engine

logger = get_child_logger("signal_extractor")

ExtractedSignal = Dict[str, Any]

ExtractorFn = Callable[
    [Any, str],
    Optional[ExtractedSignal]
]

_RELEVANCE_KEYWORDS = {
    "belief": ["believe", "agree", "disagree", "stance", "opinion", "think"],
    "contradiction": [
        "contradict", "conflict", "inconsistent",
        "but", "however", "on the other hand",
    ],
    "confidence": [
        "confident", "certain", "sure", "uncertain",
        "maybe", "probably", "unsure",
    ],
}

class SignalExtractor:
    def __init__(self):
        self._extractors: Dict[str, List[ExtractorFn]] = {}

    def register(
        self,
        signal_type: str,
        extractor_fn: ExtractorFn,
    ):
        self._extractors.setdefault(
            signal_type, []
        ).append(extractor_fn)

    def extract(
        self,
        input_data: Any,
        source_unit_id: str,
        signal_type_hint: Optional[str] = None,
    ) -> Optional[ExtractedSignal]:
        if signal_type_hint:
            handlers = self._extractors.get(
                signal_type_hint, []
            )
            for fn in handlers:
                result = fn(input_data, source_unit_id)
                if result:
                    return result
            return None

        for signal_type, handlers in self._extractors.items():
            for fn in handlers:
                result = fn(input_data, source_unit_id)
                if result:
                    return result
        return None

    def extract_and_emit(
        self,
        input_data: Any,
        source_unit_id: str,
        signal_type_hint: Optional[str] = None,
    ) -> Optional[str]:
        extracted = self.extract(
            input_data,
            source_unit_id,
            signal_type_hint,
        )
        if not extracted:
            return None

        signal = signal_engine.create_signal(
            signal_type=extracted["signal_type"],
            source_unit_id=source_unit_id,
            value=extracted["value"],
            category=extracted.get("category", "general"),
            subtype=extracted.get("subtype", "generic"),
            title=extracted.get("title", ""),
            description=extracted.get("description", ""),
            confidence=extracted.get("confidence", 1.0),
            importance=extracted.get("importance", 0.5),
            tags=extracted.get("tags", []),
            metadata=extracted.get("metadata", {}),
        )
        return signal.signal_id


def _extract_belief_shift(
    data: Any, source_unit_id: str
) -> Optional[ExtractedSignal]:
    if isinstance(data, dict):
        argument = data.get("argument") or data.get("argument_name")
        stance = data.get("stance")
        topic = data.get("topic")
        confidence = data.get("confidence", 0.7)

        if argument and stance:
            return {
                "signal_type": "belief_shift",
                "value": {
                    "argument": argument,
                    "stance": stance,
                    "topic": topic or "general",
                },
                "category": "cognitive",
                "subtype": "belief",
                "title": f"Belief shift: {argument}",
                "description": f"Stance changed to {stance} on {topic or 'general'}",
                "confidence": confidence,
                "importance": 0.7,
                "tags": ["belief", source_unit_id],
                "metadata": {
                    "argument_name": argument,
                    "topic": topic or "general",
                },
            }
    return None


def _extract_confidence_change(
    data: Any, source_unit_id: str
) -> Optional[ExtractedSignal]:
    if isinstance(data, dict):
        delta = data.get("delta") or data.get("confidence_delta")
        argument = data.get("argument") or data.get("argument_name")
        topic = data.get("topic")

        if delta is not None:
            return {
                "signal_type": "confidence_change",
                "value": delta,
                "category": "cognitive",
                "subtype": "confidence",
                "title": f"Confidence change: {argument or 'unknown'}",
                "description": f"Confidence delta: {delta}",
                "confidence": data.get("confidence", 1.0),
                "importance": 0.6,
                "tags": ["confidence", source_unit_id],
                "metadata": {
                    "argument_name": argument or "",
                    "topic": topic or "",
                },
            }
    return None


def _extract_contradiction(
    data: Any, source_unit_id: str
) -> Optional[ExtractedSignal]:
    if isinstance(data, dict):
        contradicted = (
            data.get("contradicted_arguments")
            or data.get("contradictions")
        )
        topic = data.get("topic")

        if contradicted:
            return {
                "signal_type": "contradiction_detected",
                "value": {
                    "contradicted_arguments": contradicted,
                    "topic": topic or "general",
                },
                "category": "cognitive",
                "subtype": "contradiction",
                "title": "Contradiction detected",
                "description": f"Contradictory beliefs: {contradicted}",
                "confidence": data.get("confidence", 0.9),
                "importance": 0.9,
                "tags": ["contradiction", source_unit_id],
                "metadata": {
                    "arguments": contradicted,
                    "topic": topic or "general",
                },
            }
    return None


def _extract_observation(
    data: Any, source_unit_id: str
) -> Optional[ExtractedSignal]:
    if isinstance(data, str) and len(data.strip()) > 10:
        return {
            "signal_type": "observation",
            "value": {"text": data.strip()},
            "category": "cognitive",
            "subtype": "observation",
            "title": "User observation",
            "description": data.strip()[:200],
            "confidence": 0.8,
            "importance": 0.5,
            "tags": ["observation", source_unit_id],
            "metadata": {"source": "user_input"},
        }
    return None


signal_extractor = SignalExtractor()
signal_extractor.register("belief_shift", _extract_belief_shift)
signal_extractor.register("confidence_change", _extract_confidence_change)
signal_extractor.register("contradiction_detected", _extract_contradiction)
signal_extractor.register("observation", _extract_observation)
