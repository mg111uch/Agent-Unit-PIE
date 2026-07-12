"""System prompt loading."""

from __future__ import annotations

import os

from agent_core.config import SYSTEM_INSTRUCTION_PATH
from agent_core.tools import log_output

DEFAULT_SYSTEM_PROMPT = "You are a helpful assistant."


def load_system_prompt(path: str | None = None) -> str:
    prompt_path = path or SYSTEM_INSTRUCTION_PATH
    try:
        with open(prompt_path, "r", encoding="utf-8") as f:
            return f.read()
    except FileNotFoundError:
        log_output(f"ERROR: {os.path.basename(prompt_path)} not found. Using empty prompt.")
        return DEFAULT_SYSTEM_PROMPT
    except Exception as e:
        log_output(f"ERROR loading system prompt: {e}")
        return DEFAULT_SYSTEM_PROMPT
