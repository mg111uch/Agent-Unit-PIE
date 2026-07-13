"""
Shared agent tool loop — now lives in agent_core/loop/ package.
This stub re-exports for backward compatibility.
"""

from agent_core.loop import iter_agent_events, run_agent_turn

__all__ = ["iter_agent_events", "run_agent_turn"]
