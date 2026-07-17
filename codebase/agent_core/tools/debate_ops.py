import json
import os
import sys
import threading
from datetime import datetime
from typing import Any

# Ensure modules/ is on sys.path so debate engine modules can resolve
# each other via absolute imports (e.g. 'from argu_god.engine.xxx import yyy')
_modules_root = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(
    os.path.abspath(__file__)))), "modules")
if _modules_root not in sys.path:
    sys.path.insert(0, _modules_root)

from modules.argu_god.engine.loop import load_graph, get_next_argument
from modules.argu_god.engine.storage import load_state, save_state, add_response, load_beliefs, save_beliefs
from modules.argu_god.engine.analyzer import detect_contradictions
from modules.argu_god.engine.kernel_bridge import (
    emit_belief_signal,
    emit_confidence_signal,
    emit_contradiction_signal,
    create_belief_hypothesis,
    add_belief_evidence,
    validate_belief_hypothesis,
    get_hypothesis_for_argument,
)
from agent_core.tools.question_ops import _pending


CHOICE_MAP = {1: ("agree", 0.7), 2: ("disagree", 0.7), 3: ("neutral", 0.5), 4: ("custom", 0.6)}
CHOICE_LABELS = {1: "Agree", 2: "Counter", 3: "Explore", 4: "Custom"}


def _build_debate_question(argument: dict, counter: dict | None = None) -> dict:
    name = argument.get("name", "")
    premise = argument.get("premise", "")
    side_label = {"pro": "For", "con": "Against", "neutral": "Neutral"}.get(
        argument.get("side", ""), ""
    )

    question_text = f"Argument: {name} ({side_label})\n\n{premise}"
    if counter:
        question_text += f"\n\nOpposing view: {counter.get('premise', '')[:200]}..."

    return {
        "question": question_text,
        "options": [
            "Agree: I accept this argument",
            "Counter: I disagree",
            "Explore / unsure",
        ],
    }


def debate_step(raw_input: Any) -> str:
    if isinstance(raw_input, str):
        try:
            raw_input = json.loads(raw_input)
        except json.JSONDecodeError:
            return json.dumps({"error": "invalid JSON input"})
    if not isinstance(raw_input, dict):
        return json.dumps({"error": "expected a JSON object"})

    topic = raw_input.get("topic", "")
    session_id = raw_input.get("_session_id", "")
    prepare_only = raw_input.get("prepare_only", False)

    if not topic:
        return json.dumps({"error": "topic is required"})
    if not session_id:
        return json.dumps({"error": "_session_id is required"})

    # --- Phase 1: Prepare (non-blocking) ---
    graph = load_graph(topic)
    if not graph:
        return json.dumps({"error": f"Topic not found: {topic}"})

    state = load_state()
    beliefs = load_beliefs()

    if state["current_topic"] != topic:
        state["current_topic"] = topic
        state["seen_arguments"] = []
        state["responses"] = []
        save_state(state)

    argument = get_next_argument(topic, graph, state, beliefs)
    if not argument:
        return json.dumps({"done": True, "message": "All arguments explored"})

    try:
        from modules.argu_god.engine.retriever import get_best_counter
        counter = get_best_counter(argument)
    except Exception:
        counter = None
    question = _build_debate_question(argument, counter)

    event = threading.Event()
    _pending[session_id] = {
        "questions": [question],
        "event": event,
        "answers": None,
        "_debate_meta": {
            "topic": topic,
            "argument": argument,
            "state": state,
            "beliefs": beliefs,
            "graph": graph,
        },
    }

    if prepare_only:
        return json.dumps({"questions": [question]})

    # --- Phase 2: Wait for answer (blocking) ---
    event.wait()
    entry = _pending.pop(session_id, {})
    answers = entry.get("answers")
    meta = entry.get("_debate_meta", {})

    if answers is None:
        return json.dumps({"cancelled": True})

    argument = meta.get("argument", {})
    state = meta.get("state", {})
    beliefs = meta.get("beliefs", {})
    graph = meta.get("graph", {})

    # Parse answer — handle both index and label formats
    choice_raw = answers[0] if answers else "3"
    try:
        choice_value = int(choice_raw)
        if choice_value < 1 or choice_value > 4:
            choice_value = 3
    except (ValueError, TypeError):
        choice_value = 4

    custom_text = None
    if choice_value == 4:
        custom_text = choice_raw
    elif len(answers) > 1:
        custom_text = answers[1]

    stance, confidence = CHOICE_MAP.get(choice_value, ("neutral", 0.5))
    arg_name = argument.get("name", "unknown")

    # Update beliefs
    if arg_name not in beliefs["arguments"]:
        beliefs["arguments"][arg_name] = {
            "stance": stance,
            "confidence": confidence,
            "last_updated": "",
            "history": [],
        }

    beliefs["arguments"][arg_name]["history"].append({
        "stance": stance,
        "confidence": confidence,
        "timestamp": datetime.now().isoformat(),
    })
    beliefs["arguments"][arg_name]["stance"] = stance
    beliefs["arguments"][arg_name]["confidence"] = confidence
    beliefs["arguments"][arg_name]["last_updated"] = datetime.now().isoformat()
    save_beliefs(beliefs)

    add_response(state, arg_name, choice_value, custom_text)
    state["seen_arguments"].append(arg_name)
    save_state(state)

    contradictions = detect_contradictions(beliefs, graph)

    emit_belief_signal(arg_name, stance, confidence, topic)
    emit_confidence_signal(arg_name, 0.0, confidence, topic)

    try:
        create_belief_hypothesis(arg_name, stance, confidence, topic)
    except Exception:
        pass

    if contradictions:
        for c in contradictions:
            emit_contradiction_signal(c, topic)
            try:
                hyp_a = get_hypothesis_for_argument(c[0], topic)
                hyp_b = get_hypothesis_for_argument(c[1], topic)
                add_belief_evidence(hyp_a, c[1], supports=False)
                add_belief_evidence(hyp_b, c[0], supports=False)
                validate_belief_hypothesis(hyp_a)
                validate_belief_hypothesis(hyp_b)
            except Exception:
                pass

    next_arg = get_next_argument(topic, graph, state, beliefs)

    return json.dumps({
        "choice": choice_value,
        "choice_text": CHOICE_LABELS.get(choice_value, "Unknown"),
        "argument_name": arg_name,
        "stance": stance,
        "confidence": confidence,
        "contradictions": [list(c) for c in contradictions] if contradictions else [],
        "next_argument": next_arg["name"] if next_arg else None,
        "done": next_arg is None,
    })
