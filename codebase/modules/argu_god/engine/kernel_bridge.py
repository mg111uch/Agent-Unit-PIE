import os
import sys
import json
import uuid
from datetime import datetime

CODEBASE_PATH = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
if CODEBASE_PATH not in sys.path:
    sys.path.insert(0, CODEBASE_PATH)

from kernel.signals.signal_engine import signal_engine
from kernel.memory.working_memory import working_memory
from kernel.hypothesis.hypothesis_engine import hypothesis_engine
from kernel.events.event_engine import event_engine


ARGU_GOD_UNIT_ID = "argu_god"


BASE_PATH = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
SESSION_DIR = os.path.join(BASE_PATH, "mindmaps", "local_user", "sessions")
os.makedirs(SESSION_DIR, exist_ok=True)


def _get_session_path(session_id: str = None):
    if session_id:
        return os.path.join(SESSION_DIR, f"{session_id}.json")
    return SESSION_DIR


def save_debate_session(
    topic: str,
    state: dict,
    beliefs: dict,
    session_id: str = None,
) -> str:
    """Save debate session state."""
    if session_id is None:
        session_id = f"session_{datetime.now().strftime('%Y%m%d_%H%M%S')}"

    session_data = {
        "session_id": session_id,
        "topic": topic,
        "state": state,
        "beliefs": beliefs,
        "created_at": datetime.now().isoformat(),
        "last_updated": datetime.now().isoformat(),
        "argument_count": len(state.get("seen_arguments", [])),
        "response_count": len(state.get("responses", [])),
    }

    path = _get_session_path(session_id)
    with open(path, "w") as f:
        json.dump(session_data, f, indent=2)

    working_memory.add_memory(
        memory_id=f"debate_session_{session_id}",
        memory_type="debate_session",
        content={
            "session_id": session_id,
            "topic": topic,
            "arguments_seen": len(state.get("seen_arguments", [])),
        },
        importance=0.8,
        confidence=0.9,
        tags=["argu_god", "debate_session", topic],
        metadata={"session_id": session_id},
        ttl_seconds=86400,
    )

    signal_engine.create_signal(
        signal_type="observation",
        source_unit_id=ARGU_GOD_UNIT_ID,
        value={
            "action": "session_saved",
            "session_id": session_id,
            "topic": topic,
        },
        category="cognitive",
        subtype="session",
        title=f"Debate session saved",
        description=f"Session {session_id} for topic {topic}",
        confidence=0.9,
        importance=0.7,
        metadata={"session_id": session_id},
    )

    return session_id


def load_debate_session(session_id: str = None) -> dict:
    """Load debate session state. If session_id is None, loads most recent."""
    if session_id is None:
        sessions = list_debate_sessions()
        if sessions:
            session_id = sessions[0]["session_id"]
        else:
            return None

    path = _get_session_path(session_id)
    if not os.path.exists(path):
        return None

    with open(path, "r") as f:
        return json.load(f)


def list_debate_sessions() -> list:
    """List all saved debate sessions."""
    sessions = []
    for filename in os.listdir(SESSION_DIR):
        if filename.endswith(".json"):
            path = os.path.join(SESSION_DIR, filename)
            with open(path, "r") as f:
                sessions.append(json.load(f))
    return sorted(sessions, key=lambda x: x.get("last_updated", ""), reverse=True)


def get_current_session_info() -> dict:
    """Get info about current/most recent session."""
    sessions = list_debate_sessions()
    if sessions:
        return sessions[0]
    return {"session_id": None, "topic": None}


def emit_belief_signal(
    argument_name: str,
    stance: str,
    confidence: float,
    topic: str,
) -> None:

    signal_engine.create_signal(
        signal_type="belief_shift",
        source_unit_id=ARGU_GOD_UNIT_ID,
        value={
            "argument": argument_name,
            "stance": stance,
            "topic": topic,
        },
        category="cognitive",
        subtype="belief",
        title=f"Belief shift: {argument_name}",
        description=f"User stance changed to {stance} on topic {topic}",
        confidence=confidence,
        importance=0.7,
        tags=["argu_god", "belief"],
        metadata={
            "argument_name": argument_name,
            "topic": topic,
        },
    )


def emit_confidence_signal(
    argument_name: str,
    old_confidence: float,
    new_confidence: float,
    topic: str,
) -> None:

    signal_engine.create_signal(
        signal_type="confidence_change",
        source_unit_id=ARGU_GOD_UNIT_ID,
        value=new_confidence - old_confidence,
        category="cognitive",
        subtype="confidence",
        title=f"Confidence change: {argument_name}",
        description=f"Confidence updated from {old_confidence} to {new_confidence}",
        confidence=new_confidence,
        importance=0.6,
        tags=["argu_god", "confidence"],
        metadata={
            "argument_name": argument_name,
            "old_confidence": old_confidence,
            "new_confidence": new_confidence,
            "topic": topic,
        },
    )


def emit_contradiction_signal(
    contradicted_arguments: list,
    topic: str,
) -> None:

    signal_engine.create_signal(
        signal_type="contradiction_detected",
        source_unit_id=ARGU_GOD_UNIT_ID,
        value={
            "contradicted_arguments": contradicted_arguments,
            "topic": topic,
        },
        category="cognitive",
        subtype="contradiction",
        title=f"Contradiction detected",
        description=f"User agreed with contradictory arguments: {contradicted_arguments}",
        confidence=0.9,
        importance=0.9,
        tags=["argu_god", "contradiction"],
        metadata={
            "arguments": contradicted_arguments,
            "topic": topic,
        },
    )


def emit_topic_signal(
    topic: str,
    argument_count: int,
    action: str,
) -> None:

    signal_engine.create_signal(
        signal_type="observation",
        source_unit_id=ARGU_GOD_UNIT_ID,
        value={
            "topic": topic,
            "argument_count": argument_count,
            "action": action,
        },
        category="cognitive",
        subtype="debate",
        title=f"ArguGod topic: {action}",
        description=f"Topic {topic} - {action} with {argument_count} arguments",
        confidence=0.8,
        importance=0.5,
        tags=["argu_god", "topic"],
        metadata={
            "topic": topic,
            "action": action,
        },
    )


def create_belief_hypothesis(
    argument_name: str,
    stance: str,
    confidence: float,
    topic: str,
) -> str:
    """Create hypothesis from user belief stance."""
    hypothesis_id = f"hyp_{argument_name}_{int(datetime.now().timestamp())}"

    stance_description = f"User believes {stance} on: {argument_name}"

    hypothesis = hypothesis_engine.create_hypothesis(
        hypothesis_id=hypothesis_id,
        title=f"Belief: {argument_name}",
        description=stance_description,
        hypothesis_type="belief_position",
        category=topic,
        confidence=confidence,
        plausibility=confidence,
        novelty=0.6,
        related_concepts=[argument_name, topic],
        metadata={
            "argument": argument_name,
            "stance": stance,
            "topic": topic,
        },
    )

    signal_engine.create_signal(
        signal_type="observation",
        source_unit_id=ARGU_GOD_UNIT_ID,
        value={
            "action": "hypothesis_created",
            "hypothesis_id": hypothesis_id,
            "argument": argument_name,
        },
        category="cognitive",
        subtype="hypothesis",
        title=f"Hypothesis created",
        description=f"Hypothesis for {argument_name}",
        confidence=confidence,
        importance=0.6,
        metadata={
            "hypothesis_id": hypothesis_id,
            "argument": argument_name,
        },
    )

    return hypothesis_id


def add_belief_evidence(
    hypothesis_id: str,
    argument_name: str,
    supports: bool,
) -> None:
    """Add supporting or contradicting evidence to hypothesis."""
    evidence_id = f"evidence_{argument_name}_{int(datetime.now().timestamp())}"

    if supports:
        hypothesis_engine.add_supporting_evidence(
            hypothesis_id, evidence_id
        )
    else:
        hypothesis_engine.add_contradicting_evidence(
            hypothesis_id, evidence_id
        )


def validate_belief_hypothesis(
    hypothesis_id: str,
) -> dict:
    """Validate a belief hypothesis."""
    result = hypothesis_engine.validate_hypothesis(hypothesis_id)
    return result


def get_hypothesis_for_argument(
    argument_name: str,
    topic: str,
) -> str:
    """Get or create hypothesis for argument."""
    hypothesis_id = f"hyp_{argument_name}"

    existing = hypothesis_engine.get_hypothesis(hypothesis_id)
    if existing:
        return hypothesis_id

    hypothesis = hypothesis_engine.create_hypothesis(
        hypothesis_id=hypothesis_id,
        title=f"Position: {argument_name}",
        description=f"User position on {argument_name}",
        hypothesis_type="belief_position",
        category=topic,
        confidence=0.5,
        plausibility=0.5,
        novelty=0.5,
        related_concepts=[argument_name, topic],
        metadata={
            "argument": argument_name,
            "topic": topic,
        },
    )

    return hypothesis_id


def get_belief_summary(topic: str) -> list:
    """Get summary of all belief hypotheses for topic."""
    hypotheses = hypothesis_engine.get_by_category(topic)
    return [
        {
            "hypothesis_id": h.hypothesis_id,
            "title": h.title,
            "confidence": h.confidence,
            "status": h.status,
            "supporting_count": len(h.supporting_evidence),
            "contradicting_count": len(h.contradicting_evidence),
        }
        for h in hypotheses
    ]


DEBATE_EVENT_TYPES = [
    "session_start",
    "session_resume",
    "session_end",
    "argument_viewed",
    "user_responded",
    "belief_changed",
    "contradiction_detected",
    "hypothesis_validated",
]


def emit_debate_event(
    event_type: str,
    topic: str,
    description: str,
    metadata: dict = None,
) -> None:
    """Emit debate event for timeline tracking."""
    if event_type not in DEBATE_EVENT_TYPES:
        event_type = "debate_action"

    event_engine.create_event(
        event_type=event_type,
        title=f"Debate: {event_type}",
        description=description,
        source_unit_id=ARGU_GOD_UNIT_ID,
        category="debate",
        subtype=topic,
        confidence=0.9,
        importance=0.6,
        tags=["argu_god", "debate", topic],
        metadata=metadata or {},
    )


def emit_session_start_event(topic: str, is_resume: bool = False) -> None:
    """Emit session start or resume event."""
    event_type = "session_resume" if is_resume else "session_start"
    emit_debate_event(
        event_type=event_type,
        topic=topic,
        description=f"Debate session {'resumed' if is_resume else 'started'} for {topic}",
        metadata={"topic": topic, "is_resume": is_resume},
    )


def emit_argument_viewed_event(
    topic: str,
    argument_name: str,
) -> None:
    """Emit event when argument is shown to user."""
    emit_debate_event(
        event_type="argument_viewed",
        topic=topic,
        description=f"Argument viewed: {argument_name}",
        metadata={"argument": argument_name, "topic": topic},
    )


def emit_user_response_event(
    topic: str,
    argument_name: str,
    choice: int,
    stance: str,
) -> None:
    """Emit event when user responds."""
    emit_debate_event(
        event_type="user_responded",
        topic=topic,
        description=f"User responded: {choice} ({stance}) to {argument_name}",
        metadata={
            "argument": argument_name,
            "choice": choice,
            "stance": stance,
            "topic": topic,
        },
    )


def emit_belief_changed_event(
    topic: str,
    argument_name: str,
    old_stance: str,
    new_stance: str,
) -> None:
    """Emit event when belief changes."""
    emit_debate_event(
        event_type="belief_changed",
        topic=topic,
        description=f"Belief changed: {argument_name} from {old_stance} to {new_stance}",
        metadata={
            "argument": argument_name,
            "old_stance": old_stance,
            "new_stance": new_stance,
            "topic": topic,
        },
    )


def emit_contradiction_event(
    topic: str,
    arguments: list,
) -> None:
    """Emit event when contradiction detected."""
    emit_debate_event(
        event_type="contradiction_detected",
        topic=topic,
        description=f"Contradiction: {arguments}",
        metadata={"contradicted": arguments, "topic": topic},
    )


def emit_session_end_event(
    topic: str,
    arguments_seen: int,
    responses: int,
) -> None:
    """Emit session end event."""
    emit_debate_event(
        event_type="session_end",
        topic=topic,
        description=f"Session ended: {arguments_seen} arguments, {responses} responses",
        metadata={
            "topic": topic,
            "arguments_seen": arguments_seen,
            "responses": responses,
        },
    )