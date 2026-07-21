from kernel.extractors.signal_extractor import signal_extractor

ARGU_GOD_UNIT_ID = "argu_god"


def emit_belief_signal(
    argument_name: str,
    stance: str,
    confidence: float,
    topic: str,
) -> None:
    signal_extractor.extract_and_emit(
        input_data={
            "argument_name": argument_name,
            "stance": stance,
            "confidence": confidence,
            "topic": topic,
        },
        source_unit_id=ARGU_GOD_UNIT_ID,
        signal_type_hint="belief_shift",
    )


def emit_confidence_signal(
    argument_name: str,
    old_confidence: float,
    new_confidence: float,
    topic: str,
) -> None:
    signal_extractor.extract_and_emit(
        input_data={
            "delta": new_confidence - old_confidence,
            "argument_name": argument_name,
            "confidence": new_confidence,
            "topic": topic,
        },
        source_unit_id=ARGU_GOD_UNIT_ID,
        signal_type_hint="confidence_change",
    )


def emit_contradiction_signal(
    contradicted_arguments: list,
    topic: str,
) -> None:
    signal_extractor.extract_and_emit(
        input_data={
            "contradicted_arguments": contradicted_arguments,
            "topic": topic,
        },
        source_unit_id=ARGU_GOD_UNIT_ID,
        signal_type_hint="contradiction_detected",
    )
