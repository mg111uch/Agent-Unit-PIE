# Agent Core Status
_Last verified: 2026-08-01_

> Capability claims are hypotheses. Re-validate: `python scripts/validate_capabilities.py`
> For a user-facing feature overview, see `README.md`.

## Current Capability
- Local model routing: FunctionGemma/Ollama handles simple file+meta tool calls, falls back to cloud — `agent_core/planning/local_planner.py:should_route_local()`, `agent_core/loop/engine.py:iter_agent_events()`
- Ollama provider compatible with LLMProvider protocol for local inference — `agent_core/providers/ollama_provider.py:generate()`
- Config-driven local model on/off via `local_model.enabled` in config.json — `agent_core/config.py:load_config()`
- Agent loop with multi-tool turns, streaming, cancel support — `agent_core/loop/engine.py:iter_agent_events()`
- Tool registry with category filtering, middleware, MCP export — `agent_core/tools/__init__.py:_register_all()`
- MCP stdio server exposure policy: CAT_META always, CAT_FILE never, other packs per config — `agent_core/mcp_server.py:_exposed_categories()`
- LLM orchestration with provider abstraction — `agent_core/providers_setup.py:build_orchestrator()`
- File operations with sandbox and path resolution — `agent_core/tools/file_ops.py:read_file()`
- Code RAG tools for atlas queries — `agent_core/tools/context_dump.py:minimal_context_dump()`
- Kernel ops tools (retrieve, emit, store, create_event) — `agent_core/tools/kernel_ops.py:kernel_retrieve()`
- Capability-aware prompt fragments assembled by pack config — `agent_core/prompts.py:load_system_prompt()`
- Cross-turn SessionState with file cache, workspace cache, and context digest — `agent_core/loop/session_state.py:build_digest()`
- Message compaction at 48K char threshold with rule-based summarization — `agent_core/loop/session_state.py:compact_messages()`
- Diff-based edit results with inline verification signal (avoids re-read) — `agent_core/tools/file_ops.py:edit_file()`
- Context digest injected at turn start for cached workspace/file state — `agent_core/loop/engine.py:iter_agent_events()`

## Known Gaps
- Embed-mode packaging not finalized — med
- Test coverage for agent loop edge cases — low

## Recent Changes (newest first, max 10)
- MCP exposure policy: CAT_META always, CAT_FILE never, other tool packs only when enabled in config — `agent_core/mcp_server.py:_exposed_categories()`
- `subagent_task` moved to CAT_FILE, gated by `subagent_task_enabled` config flag (default off) — `agent_core/tools/__init__.py:_register_file_tools()`, `agent_core/config.py:SUBAGENT_TASK_ENABLED`
- Local model routing: LocalPlanner + OllamaProvider for per-step delegation of file/meta tools to FunctionGemma, with config.json on/off toggle — `agent_core/planning/local_planner.py:should_route_local()`
- Efficiency P1-2: trimmed prompts (removed input-format table, trimmed tool list to behavior rules), added few-shot batching example, updated rule 6 for diff-as-verification — `agent_core/prompts.py:load_system_prompt()`
- Efficiency P0-1/P0-2/P1-1: SessionState, compaction, diff-based edit verification — `agent_core/loop/session_state.py:compact_messages()`
- LOW: deleted dead `_collect_blast_radius`; hoisted `_add_section` out of closure; collapsed raw/invalid_tool bookkeeping; added `LLMProvider` Protocol with `supports_stateful` — `agent_core/tools/context_dump.py:minimal_context_dump()`
- Retry filtering in `generate()`; `_STRING_ARG_KEYS` completeness; `_run_interactive_tool` extracted; `execute_command` wrapped in `tc()` — `agent_core/llm_orchestrator.py:generate()`
- Cancellation: daemon thread + `stop_flag`; `cancel_flag` between retries — `agent_core/loop/_helpers.py:_generate_with_cancel()`
- Streaming: real `generate_stream` in `stream_final`; dropped fake chunks — `agent_core/loop/streaming.py:stream_final()`
- Full audit: 18 issues found, categorized by severity (3 blockers, 4 high, 11 med/low) — `agent_core/loop/engine.py:iter_agent_events()`
