# PlanIssues2 — Token-Cost Reduction (consolidated)

> Consolidated 2026-08-06 from `Issues2.md` (problem), `Fixes2.md` (work done),
> and this file's original plan. Goal: cut per-task token cost from the
> **48.38k / 9 tasks** baseline toward OpenCode/Codex's **~12k**.

## Problem (Issues2)

Every LLM step re-sent the full tool schema (~2.1k tokens × each tool call) plus
system prompt + history, totaling ~48k for 9 tasks vs ~12k for production agents.

OpenCode/Codex/Claude Code avoid this via:
1. Server-side conversation state (`previous_response_id` / interaction IDs).
2. One-time tool registration per session.
3. Dynamic tool exposure (a few tools, not all).
4. Minimal incremental context after turn 1.
5. Direct execution for deterministic ops (skip the 2nd LLM call).

## Work done (Fixes2 + follow-up)

### Loop/stateful
- Digest/hints ephemeral per turn (never billed as user content).
- Stateful chain-restart bounds billed context (`gemini_chain_restart_tokens`=40000).
- Compaction engages (`compaction_trigger_chars`=8000); raw-tail trimmed, redundant
  assistant text dropped, corrective messages merged.
- OpenRouter message hardening (`tool_call_id` synth, `_coerce_arguments`, empty-input guard).
- Usage split into `prompt_tokens`/`completion_tokens`; `list_files` no longer cached.

### Gemini stateless
- Turn-local chained-turn detection (re-send at each new user prompt; omit on chains).
- System prompt sent at turn start only, never on tool chains.
- Explicit context cache (`gemini_cache.py`) + fresh-token reporting; **degrades inline**
  (`caches.create` rejected for `gemini-3.1-flash-lite`).
- msg_store tool-result bounding; stepper/compaction/debug-dump trimming.

### Dynamic tool exposure (pruning on chained turns)
- OpenRouter: `openrouter_prune_tools_on_chain` (default true) — chained turns send
  base set + tools used this turn (`_prune_tools_for_chain`).
- Gemini: `gemini_prune_tools_on_chain` (default true) — same via `_prune_gc_tools`
  in `_generate_stateless` + stateless `generate_stream`.
- Non-chained (new user prompt) turns always get the full set.
- Base set: `read_file, list_files, grep_search, glob_search, execute_command, edit_file, write_to_file`.

### Direct-final
- `direct_final_tools: ["check_path_exists"]` — moved the 424-byte tool from the
  disabled `meta` pack into the active `file` pack (now 10 tools / 7.4KB). When it
  succeeds as the first step, the loop skips the 2nd LLM call (`DIRECT FINAL`).

## Current config flags

| Key | Value |
| --- | --- |
| `gemini_stateless` / `gemini_stateless_cache` | true / true |
| `gemini_stateless_skip_schemas` | false |
| `gemini_prune_tools_on_chain` | true |
| `gemini_skip_tools_on_chain` (stateful) | true |
| `openrouter_skip_tools_on_chain` | false |
| `openrouter_prune_tools_on_chain` | true |
| `openrouter_retry_skipped_chain` | true |
| `compaction_trigger_chars` / `gemini_chain_restart_tokens` | 8000 / 40000 |
| `direct_final_tools` | [check_path_exists] |

## Verification

- Live (Gemini stateless): chained steps dropped **~4.2k → ~1.6–1.9k** after the
  system-prompt fix; cache contributed 0 (inline fallback for flash-lite).
- Synthetic (mocked): Gemini stateless (8 cases), OpenRouter (5 cases),
  pruning helpers (used+base kept, ask/todo dropped, no-op preserved),
  compaction, dump capping, tool-pack registration — all pass.

## Remaining / excluded

- **System-prompt size** (8.4k chars, ~2.1k tokens, resent per user prompt):
  **EXCLUDED by user** (target <2.5k chars estimated 25–40% of remaining cost).
- **OpenRouter server-side state**: not implementable — OpenRouter/OpenAI APIs are
  stateless and reject `store: true` / `previous_response_id`; only Gemini exposes
  `previous_interaction_id` (already wired).
- **Context cache on flash-lite**: still unverified on a cache-capable model
  (`gemini_cache_model` idea not pursued).
- **Intent-based per-task tool filtering** (plan Phase 2): not in scope; active set
  already limited via `tool_packs` (file only).
- **Stateful A/B** (plan Phase 5): not needed — stateless + cache + pruning already bound cost.
