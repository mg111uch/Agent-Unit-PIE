from __future__ import annotations

import json
from typing import Any

_PLAN: list[dict] = []
_PLAN_FILE = "agent_plan.json"


def _load_plan() -> list[dict]:
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


def todo_write(input_data: Any) -> str:
    global _PLAN
    _load_plan()
    data = json.loads(input_data) if isinstance(input_data, str) else input_data
    action = data.get("action", "create")

    if action == "create":
        items = data.get("items", [])
        _PLAN = [{"id": i + 1, "text": item, "done": False} for i, item in enumerate(items)]
        _save_plan()
        return f"[PLAN] Created {len(items)} tasks"

    elif action == "update":
        items = data.get("items", [])
        existing_ids = {t["id"] for t in _PLAN}
        next_id = max(existing_ids) + 1 if existing_ids else 1
        for item in items:
            _PLAN.append({"id": next_id, "text": item, "done": False})
            next_id += 1
        _save_plan()
        return f"[PLAN] Added {len(items)} tasks"

    elif action == "mark_done":
        ids = data.get("ids", [])
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


def todo_read(_input: Any = None) -> str:
    _load_plan()
    if not _PLAN:
        return "(No plan set)"
    lines = ["Current plan:"]
    for t in _PLAN:
        status = "✓" if t["done"] else " "
        lines.append(f"  [{status}] {t['id']}. {t['text']}")
    return "\n".join(lines)
