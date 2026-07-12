"""Shared configuration and defaults for agent CLI and server."""

from __future__ import annotations

import json
import os

# codebase/ (parent of agent_core/)
CODEBASE_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))

SYSTEM_INSTRUCTION_PATH = os.path.join(CODEBASE_ROOT, "system_instruction.md")
CONFIG_PATH = os.path.join(CODEBASE_ROOT, "config.json")

JWT_SECRET = os.getenv("JWT_SECRET", "your_jwt_secret")
AGENT_PORT = int(os.getenv("AGENT_PORT", "8001"))

with open(CONFIG_PATH, "r", encoding="utf-8") as _f:
    _CONFIG = json.load(_f)

PROVIDER_DEFAULTS: dict[str, str] = {
    name: data.get("default_model", list(data.get("models", []))[0] if data.get("models") else name)
    for name, data in _CONFIG.get("providers", {}).items()
}

MAX_AGENT_STEPS = 30
CLI_STEP_DELAY = 5.0
SERVER_STEP_DELAY = 2.0


def load_config() -> dict:
    return _CONFIG


def get_provider_catalog() -> dict[str, dict]:
    return _CONFIG.get("providers", {})


def resolve_default_model(provider: str, explicit_model: str | None = None) -> str:
    if explicit_model:
        return explicit_model
    env_model = os.getenv("AGENT_MODEL")
    if env_model:
        return env_model
    return PROVIDER_DEFAULTS.get(provider, PROVIDER_DEFAULTS.get("gemini", "gemini-3.1-flash-lite"))


def resolve_active_provider() -> str:
    return os.getenv("AGENT_PROVIDER", _CONFIG.get("default_provider", "gemini"))
