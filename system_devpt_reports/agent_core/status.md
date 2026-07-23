# Agent Core Status
_Last verified: 2026-07-23_

> Capability claims are hypotheses. Re-validate: `python scripts/validate_capabilities.py`

## Current Capability
- Agent loop with multi-tool turns, streaming, cancel support — `agent_core/loop/engine.py:iter_agent_events()`
- Tool registry with category filtering, middleware, MCP export — `agent_core/tools/__init__.py:_register_all()`
- MCP stdio server exposing kernel/sim tools — `agent_core/mcp_server.py:main()`
- LLM orchestration with provider abstraction — `agent_core/providers_setup.py:build_orchestrator()`
- File operations with sandbox and path resolution — `agent_core/tools/file_ops.py:read_file()`
- Code RAG tools for atlas queries — `agent_core/tools/context_dump.py:minimal_context_dump()`
- Kernel ops tools (retrieve, emit, store, create_event) — `agent_core/tools/kernel_ops.py:kernel_retrieve()`
- Capability-aware prompt fragments assembled by pack config — `agent_core/prompts.py:load_system_prompt()`

## Known Gaps
- Embed-mode packaging not finalized — med
- Circular import around debate question_ops — blocker
- Test coverage for agent loop edge cases — low

## Recent Changes (newest first, max 10)
- (No recent changes tracked in this format yet)
