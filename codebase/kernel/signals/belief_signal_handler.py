from kernel.signals.signal_engine import signal_engine
from kernel.patterns.pattern_engine import pattern_engine
from kernel.memory.working_memory import working_memory
from kernel.utils.logger import get_child_logger
from kernel.config.kernel_config import (
    BELIEF_SHIFT_TTL,
    CONTRADICTION_TTL,
    CONFIDENCE_CHANGE_TTL,
    PATTERN_IMPORTANCE,
    PATTERN_CONFIDENCE,
)

logger = get_child_logger("belief_signal_handler")

CONTRADICTION_PATTERN_ID = "belief_contradiction"
BELIEF_CHANGE_PATTERN_ID = "belief_change_frequency"

def handle_belief_shift_signal(signal):
    """Handler for belief_shift signals - tracks belief changes."""
    try:
        value = signal.value
        argument = value.get("argument", "")
        stance = value.get("stance", "")
        topic = value.get("topic", "")
        logger.info(
            f"Belief shift detected: {argument} -> {stance} on {topic}"
        )
        importance = signal.metrics.importance
        confidence = signal.metrics.confidence
        working_memory.add_memory(
            memory_id=f"belief_{signal.signal_id}",
            memory_type="belief_shift",
            content={
                "argument": argument,
                "stance": stance,
                "topic": topic,
            },
            importance=importance,
            confidence=confidence,
            tags=["belief", "argu_god", topic],
            metadata={
                "signal_id": signal.signal_id,
                "topic": topic,
            },
            ttl_seconds=BELIEF_SHIFT_TTL,
        )
        logger.info(
            f"Belief shift stored in working memory: {argument}"
        )
    except Exception as e:
        logger.error(f"Failed to handle belief shift: {e}")

def handle_contradiction_signal(signal):
    """Handler for contradiction_detected signals."""
    try:
        value = signal.value
        contradicted_args = value.get("contradicted_arguments", [])
        topic = value.get("topic", "")
        if contradicted_args:
            logger.warning(
                f"Contradiction detected: {contradicted_args} in {topic}"
            )
            working_memory.add_memory(
                memory_id=f"contradiction_{signal.signal_id}",
                memory_type="contradiction",
                content={
                    "contradicted_arguments": contradicted_args,
                    "topic": topic,
                },
                importance=PATTERN_IMPORTANCE,
                confidence=signal.metrics.confidence,
                tags=["contradiction", "argu_god", topic],
                metadata={
                    "signal_id": signal.signal_id,
                    "topic": topic,
                },
                ttl_seconds=CONTRADICTION_TTL,
            )
            from kernel.signals.signal_engine import signal_engine
            signal_engine.create_signal(
                signal_type="pattern_detected",
                source_unit_id="argu_god",
                value={
                    "pattern_type": CONTRADICTION_PATTERN_ID,
                    "contradicted_arguments": contradicted_args,
                    "topic": topic,
                },
                category="cognitive",
                subtype="pattern",
                title=f"Belief contradiction pattern",
                description=f"User holds contradictory beliefs on {topic}",
                confidence=PATTERN_CONFIDENCE,
                importance=PATTERN_IMPORTANCE,
                tags=["pattern", "contradiction"],
                metadata={
                    "arguments": contradicted_args,
                    "topic": topic,
                },
            )
            logger.info(
                f"Contradiction pattern detected and signal emitted"
            )
        else:
            logger.info("No contradictions in this response")
    except Exception as e:
        logger.error(f"Failed to handle contradiction: {e}")

def handle_confidence_change_signal(signal):
    """Handler for confidence_change signals."""
    try:
        value = signal.value
        confidence_delta = value if isinstance(value, (int, float)) else 0
        logger.info(
            f"Confidence change: {confidence_delta}"
        )
        working_memory.add_memory(
            memory_id=f"confidence_{signal.signal_id}",
            memory_type="confidence_change",
            content={
                "delta": confidence_delta,
            },
            importance=signal.metrics.importance,
            confidence=signal.metrics.confidence,
            tags=["confidence", "argu_god"],
            metadata={
                "signal_id": signal.signal_id,
            },
            ttl_seconds=CONFIDENCE_CHANGE_TTL,
        )
        logger.info(
            f"Confidence change stored"
        )
    except Exception as e:
        logger.error(f"Failed to handle confidence change: {e}")

def register_handlers():
    """Register all belief signal handlers."""
    signal_engine.register_handler(
        "belief_shift",
        handle_belief_shift_signal
    )
    signal_engine.register_handler(
        "contradiction_detected",
        handle_contradiction_signal
    )
    signal_engine.register_handler(
        "confidence_change",
        handle_confidence_change_signal
    )
    logger.info("Belief signal handlers registered")

def unregister_handlers():
    """Unregister all belief signal handlers."""
    signal_engine.unregister_handler(
        "belief_shift",
        handle_belief_shift_signal
    )
    signal_engine.unregister_handler(
        "contradiction_detected",
        handle_contradiction_signal
    )
    signal_engine.unregister_handler(
        "confidence_change",
        handle_confidence_change_signal
    )
    logger.info("Belief signal handlers unregistered")