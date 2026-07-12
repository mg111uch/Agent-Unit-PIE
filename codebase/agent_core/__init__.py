"""
agent_core - Shared agent runtime: LLM orchestration, loop, config, commands.

Entrypoints (agent.py CLI, server.py WebSocket) stay thin and import from here.
"""

from agent_core.config import CODEBASE_ROOT, MAX_AGENT_STEPS, PROVIDER_DEFAULTS
from agent_core.prompts import load_system_prompt
from agent_core.providers_setup import build_orchestrator
from agent_core.agent_loop import run_agent_turn, iter_agent_events
from agent_core.commands import parse_command

__all__ = [
    "CODEBASE_ROOT",
    "MAX_AGENT_STEPS",
    "PROVIDER_DEFAULTS",
    "load_system_prompt",
    "build_orchestrator",
    "run_agent_turn",
    "iter_agent_events",
    "parse_command",
]
