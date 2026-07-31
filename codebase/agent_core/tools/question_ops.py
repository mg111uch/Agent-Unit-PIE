import json
import os
import threading
from typing import Any, Dict, List, Optional

from agent_core.config import CODEBASE_ROOT


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
    answered = event.wait(timeout=300)
    if not answered:
        _pending.pop(_session_id, None)
        return json.dumps({"answers": [], "cancelled": True, "reason": "timeout"})

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


_PLAN: List[Dict[str, Any]] = []
_PLAN_FILE = os.path.join(CODEBASE_ROOT, "agent_plan.json")


def _load_plan() -> List[Dict[str, Any]]:
    global _PLAN
    try:
        with open(_PLAN_FILE, "r") as f:
            _PLAN = json.load(f)
    except (FileNotFoundError, json.JSONDecodeError):
        _PLAN = []
    return _PLAN


def _save_plan():
    with open(_PLAN_FILE, "w") as f:
        json.dump(_PLAN, f, indent=2)


def todo(input_data: Any = None) -> str:
    """Unified task-plan tool. Actions: read, create, update, mark_done, clear."""
    global _PLAN
    _load_plan()
    if isinstance(input_data, str):
        try:
            input_data = json.loads(input_data)
        except json.JSONDecodeError:
            input_data = {}
    elif not isinstance(input_data, dict):
        input_data = {}
    action = input_data.get("action", "create")

    if action == "read":
        if not _PLAN:
            return "(No plan set)"
        lines = ["Current plan:"]
        for t in _PLAN:
            status = "✓" if t["done"] else " "
            lines.append(f"  [{status}] {t['id']}. {t['text']}")
        return "\n".join(lines)

    elif action == "create":
        items = input_data.get("items", [])
        _PLAN = [{"id": i + 1, "text": item, "done": False} for i, item in enumerate(items)]
        _save_plan()
        return f"[PLAN] Created {len(items)} tasks"

    elif action == "update":
        items = input_data.get("items", [])
        existing_ids = {t["id"] for t in _PLAN}
        next_id = max(existing_ids) + 1 if existing_ids else 1
        for item in items:
            _PLAN.append({"id": next_id, "text": item, "done": False})
            next_id += 1
        _save_plan()
        return f"[PLAN] Added {len(items)} tasks"

    elif action == "mark_done":
        ids = input_data.get("ids", [])
        for t in _PLAN:
            if t["id"] in ids:
                t["done"] = True
        _save_plan()
        return f"[PLAN] Marked {len(ids)} tasks done"

    elif action == "clear":
        _PLAN = []
        _save_plan()
        return "[PLAN] Cleared"

    return f"Error: Unknown action '{action}'"
