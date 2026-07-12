"""CLI slash-command parsing."""

from __future__ import annotations

from typing import Any


def parse_command(user_input: str) -> dict[str, Any]:
    if not user_input.startswith("/"):
        return {"type": "default", "input": user_input}

    parts = user_input.strip()[1:].split(None, 1)
    command = "/" + parts[0]
    rest = parts[1] if len(parts) > 1 else ""

    if command == "/argu":
        mode_topic = rest.split(None, 1)
        mode = mode_topic[0] if mode_topic else None
        topic = mode_topic[1] if len(mode_topic) > 1 else None
        return {"type": "argu", "mode": mode, "topic": topic}

    if command == "/auto":
        return {"type": "auto", "goal": rest}

    return {"type": "unknown", "input": user_input}
