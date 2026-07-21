import json
import os
import sys
import threading
from datetime import datetime
from typing import Any, Optional

from agent_core.tools.question_ops import _pending

from .loop import load_graph, get_next_argument
from .storage import load_state, save_state, add_response, load_beliefs, save_beliefs
from .debate_helpers import (
    _build_knowledge_context,
    _check_novelty,
    _store_user_knowledge,
    _generate_next_question,
    _get_untouched_knowledge,
)

_DEBATE_AGENT_DIR = os.path.join(
    os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))),
    "sub-agents",
)
if _DEBATE_AGENT_DIR not in sys.path:
    sys.path.insert(0, _DEBATE_AGENT_DIR)
from debate_agent import (
    emit_belief_signal,
    emit_confidence_signal,
    emit_contradiction_signal,
)

CHOICE_MAP = {1: ("agree", 0.7), 2: ("disagree", 0.7), 3: ("neutral", 0.5), 4: ("custom", 0.6)}
CHOICE_LABELS = {1: "Agree", 2: "Counter", 3: "Explore", 4: "Custom"}


def _populate_semantic_memory(graph: dict, topic: str):
    from kernel.memory.semantic_memory import semantic_memory

    nodes_map = {}
    for node in graph.get("nodes", []):
        name = node.get("name", "")
        node_id = f"argu_{topic}_{name.replace(' ', '_')}"
        if node_id not in semantic_memory.nodes:
            semantic_memory.create_node(
                node_id=node_id,
                node_type="argument",
                title=name,
                content=node.get("premise", ""),
                concepts=[node.get("side", "neutral")],
                tags=[topic, "debate", "argument"],
                confidence=1.0,
                importance=0.7,
            )
        nodes_map[name] = node_id

    for edge in graph.get("edges", []):
        rel = edge.get("relation", "")
        if rel != "refutes":
            continue
        src_name = edge.get("source", "")
        tgt_name = edge.get("target", "")
        src_id = nodes_map.get(src_name)
        tgt_id = nodes_map.get(tgt_name)
        if not src_id or not tgt_id:
            continue
        edge_id = f"edge_contra_{src_name}_{tgt_name}".replace(" ", "_")
        if edge_id not in semantic_memory.edges:
            semantic_memory.create_edge(
                edge_id=edge_id,
                source_node_id=src_id,
                target_node_id=tgt_id,
                relation_type="contradicts",
                weight=1.0,
                confidence=1.0,
                metadata={"topic": topic, "source_graph": "debate"},
            )

    from .vector_store import index_graph
    index_graph(graph)


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

    # --- Phase 1: Prepare ---
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

    _populate_semantic_memory(graph, topic)

    argument, counter = _generate_next_question(topic, state, beliefs, graph, raw_input)

    if not argument:
        return json.dumps({"done": True, "message": "All arguments explored"})

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

    # --- Phase 2: Wait for answer (blocking, with timeout) ---
    answered = event.wait(timeout=300)
    if not answered:
        _pending.pop(session_id, None)
        return json.dumps({"cancelled": True, "reason": "timeout"})
    entry = _pending.pop(session_id, {})
    answers = entry.get("answers")
    meta = entry.get("_debate_meta", {})

    if answers is None:
        return json.dumps({"cancelled": True})

    argument = meta.get("argument", {})
    state = meta.get("state", {})
    beliefs = meta.get("beliefs", {})
    graph = meta.get("graph", {})

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

    # --- Phase 3: Knowledge write-back ---
    _store_user_knowledge(
        argument_name=arg_name,
        stance=stance,
        confidence=confidence,
        topic=topic,
        user_text=custom_text,
    )

    # --- Phase 4: Contradiction detection & signal emission ---
    from kernel.patterns.contradiction_detector import detect_contradictions_for_beliefs
    raw = detect_contradictions_for_beliefs(
        beliefs["arguments"],
        claim_filter=arg_name,
    )
    contradictions = [(r.claim_a_title, r.claim_b_title) for r in raw]

    emit_belief_signal(arg_name, stance, confidence, topic)
    emit_confidence_signal(arg_name, 0.0, confidence, topic)

    if contradictions:
        for c in contradictions:
            emit_contradiction_signal(c, topic)

    next_arg, _ = _generate_next_question(topic, state, beliefs, graph, {})

    return json.dumps({
        "choice": choice_value,
        "choice_text": CHOICE_LABELS.get(choice_value, "Unknown"),
        "argument_name": arg_name,
        "stance": stance,
        "confidence": confidence,
        "contradictions": [list(c) for c in contradictions] if contradictions else [],
        "next_argument": next_arg.get("name") if next_arg else None,
        "done": next_arg is None,
    })
