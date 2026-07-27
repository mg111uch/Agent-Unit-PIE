# Agent Core Status
_Last verified: 2026-07-27_

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
- Cross-turn SessionState with file cache, workspace cache, and context digest — `agent_core/loop/session_state.py:SessionState`
- Message compaction at 48K char threshold with rule-based summarization — `agent_core/loop/session_state.py:compact_messages()`
- Diff-based edit results with inline verification signal (avoids re-read) — `agent_core/tools/file_ops.py:edit_file()`
- Context digest injected at turn start for cached workspace/file state — `agent_core/loop/engine.py:iter_agent_events()`
- Prompts trimmed: removed redundant input-format table, trimmed tool list to behavioral rules — `agent_core/prompts.py:FRAGMENT_ORDER`
- Few-shot batching example in response contract — `prompt_fragments/60_response_contract.md`

## Known Gaps
- Embed-mode packaging not finalized — med
- Test coverage for agent loop edge cases — low

## Recent Changes (newest first, max 10)
- Efficiency P1-2: trimmed prompts (removed 50_tool_input_formats, trimmed 10_tool_list to behavior rules), added few-shot batching example, updated rule 6 for diff-as-verification — `agent_core/prompts.py`, `prompt_fragments/10_tool_list.md`, `prompt_fragments/20_file_ops_workflow.md`, `prompt_fragments/60_response_contract.md`
- Efficiency P0-1/P0-2/P1-1: SessionState, compaction, diff-based edit verification — `agent_core/loop/session_state.py`, `agent_core/loop/engine.py`, `agent_core/tools/file_ops.py`, `agent_core/config.py`
- LOW: deleted dead `_collect_blast_radius`; hoisted `_add_section` out of closure; collapsed raw/invalid_tool bookkeeping; added `LLMProvider` Protocol with `supports_stateful` — `agent_core/tools/context_dump.py`, `agent_core/loop/engine.py`, `agent_core/providers/__init__.py`
- Retry filtering in `LLMOrchestrator.generate()`; `_STRING_ARG_KEYS` completeness; `_run_interactive_tool` extracted; `execute_command` wrapped in `tc()` — `agent_core/llm_orchestrator.py`, `agent_core/loop/executor.py`, `agent_core/loop/engine.py`, `agent_core/tools/__init__.py`
- `stream_final` accepts `temperature`/`max_tokens`; double-call eliminated — `agent_core/loop/streaming.py`
- Cancellation: daemon thread + `stop_flag`; `cancel_flag` between retries — `agent_core/loop/_helpers.py:_generate_with_cancel()`, `agent_core/llm_orchestrator.py:LLMOrchestrator.generate()`
- Streaming: real `generate_stream` in `stream_final`; dropped fake chunks — `agent_core/loop/streaming.py:stream_final()`
- Executor: removed redundant `is_ok` double-check in all 3 branches — `agent_core/loop/executor.py:execute_tool_calls()`
- OpenRouter `tool_call_id`: capture `tc.id`; uuid fallbacks; removed name fallbacks — `agent_core/providers/openrouter_provider.py`, `agent_core/response_parse.py`, `agent_core/loop/messages.py`
- Fixed 3 BLOCKER issues: Gemini history/corrective-swallowing/circular import — `agent_core/providers/gemini_provider.py`, `agent_core/tools/__init__.py`
- Full audit: 18 issues found, categorized by severity (3 blockers, 4 high, 11 med/low) — `agent_core/loop/engine.py:iter_agent_events()`, `agent_core/providers/gemini_provider.py`, `agent_core/tools/__init__.py:tool_call()`
- Token reduction: category-filtered schemas, compact JSON, JSON-aware truncation, corrective compaction, optional line_numbers — `agent_core/tools/registry.py:get_schemas()`, `agent_core/loop/engine.py:iter_agent_events()`, `agent_core/tools/code_rag/tools.py`, `agent_core/tools/file_ops.py:read_file()`
- `--quiet` flag for seed_hypotheses/validate_capabilities suppresses per-item output — `scripts/seed_hypotheses.py`, `scripts/validate_capabilities.py`
- Fixed pre-existing `followup(` bug in `_handle_corrective_bookkeeping` that broke function boundary — `agent_core/loop/_helpers.py:_handle_corrective_bookkeeping()`
- Updated citations: `_generate_with_cancel`/`_handle_corrective_bookkeeping` moved to `_helpers.py`; `llm/` dir flattened to `providers/` and `llm_orchestrator.py` — `system_devpt_reports/agent_core/status.md`
