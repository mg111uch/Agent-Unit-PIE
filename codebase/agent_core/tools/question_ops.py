import json
import threading
from typing import Any, Dict, List, Optional


_pending: Dict[str, Dict[str, Any]] = {}


def ask_user_question(raw_input: Any) -> str:
    if isinstance(raw_input, str):
        try:
            raw_input = json.loads(raw_input)
        except json.JSONDecodeError:
            return "Error: invalid JSON input"
    if not isinstance(raw_input, dict):
        return "Error: expected a JSON object with 'questions'"

    questions = raw_input.get("questions", [])
    _session_id = raw_input.get("_session_id", "")

    if not _session_id:
        return "Error: session_id is required"
    if not isinstance(questions, list) or len(questions) == 0:
        return "Error: at least one question is required"

    for i, q in enumerate(questions):
        if not isinstance(q, dict) or "question" not in q:
            return f"Error: question at index {i} must have a 'question' field"
        opts = q.get("options", [])
        if not isinstance(opts, list):
            return f"Error: options must be an array for question at index {i}"
        if len(opts) > 3:
            return f"Error: maximum 3 options per question (index {i})"

    event = threading.Event()
    _pending[_session_id] = {
        "questions": questions,
        "event": event,
        "answers": None,
    }
    event.wait()

    result = _pending[_session_id].get("answers")
    del _pending[_session_id]

    if result is None:
        return json.dumps({"answers": [], "cancelled": True})
    return json.dumps({"answers": result})


def resolve_all_questions(session_id: str, answers: List[str]) -> bool:
    if session_id not in _pending:
        return False
    _pending[session_id]["answers"] = answers
    _pending[session_id]["event"].set()
    return True


def cancel_questions(session_id: str) -> bool:
    if session_id not in _pending:
        return False
    _pending[session_id]["answers"] = None
    _pending[session_id]["event"].set()
    return True
