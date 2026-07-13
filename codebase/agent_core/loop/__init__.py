"""Agent loop — shared multi-step tool-calling loop.

Supports native function calling, message store persistence, streaming,
cancel, and failure recovery.
"""

from agent_core.loop.engine import iter_agent_events, run_agent_turn

__all__ = ["iter_agent_events", "run_agent_turn"]
