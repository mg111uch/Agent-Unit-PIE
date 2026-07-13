"""Shared configuration and defaults for agent CLI and server."""

from __future__ import annotations

import json
import os
import secrets

# codebase/ (parent of agent_core/)
CODEBASE_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))

CONFIG_PATH = os.path.join(CODEBASE_ROOT, "config.json")

JWT_SECRET = os.getenv("JWT_SECRET", secrets.token_hex(32))
AGENT_PORT = int(os.getenv("AGENT_PORT", "8001"))
CORS_ORIGINS = os.getenv("CORS_ORIGINS", "http://localhost:3000,http://localhost:8001").split(",")
WORKSPACE_BASE = os.getenv("AGENT_WORKSPACE_BASE",
    os.path.abspath(os.path.join(CODEBASE_ROOT, "..", "workspaces")))

with open(CONFIG_PATH, "r", encoding="utf-8") as _f:
    _CONFIG = json.load(_f)

PROVIDER_DEFAULTS: dict[str, str] = {
    name: data.get("default_model", list(data.get("models", []))[0] if data.get("models") else name)
    for name, data in _CONFIG.get("providers", {}).items()
}

MAX_AGENT_STEPS = 30
CLI_STEP_DELAY = 5.0
SERVER_STEP_DELAY = 2.0

ALLOWED_COMMANDS: list[str] = _CONFIG.get("allowed_commands", [
    "ls", "cat", "pwd", "echo", "python", "python3", "pytest",
    "pip", "pip3", "node", "npm", "npx", "git",
])

GIT_TOOLS_ENABLED: bool = _CONFIG.get("git_tools_enabled", False)
ENABLE_CHECKPOINTS: bool = _CONFIG.get("enable_checkpoints", False)
MAX_CHECKPOINTS: int = _CONFIG.get("max_checkpoints", 50)
AGENTS_MD_ENABLED: bool = _CONFIG.get("agents_md_enabled", False)
SANDBOX_ENABLED: bool = _CONFIG.get("sandbox_enabled", False)
SECRETS_PATTERNS: list[str] = _CONFIG.get("secrets_patterns", [])
RATE_LIMIT_LLM_CALLS: int = _CONFIG.get("rate_limits", {}).get("llm_calls_per_minute", 10)
RATE_LIMIT_TOOL_WRITES: int = _CONFIG.get("rate_limits", {}).get("tool_writes_per_minute", 30)


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
