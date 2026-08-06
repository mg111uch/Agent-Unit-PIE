---
name: provider-settings
description: Use this skill BEFORE touching anything related to LLM providers — reading the active provider/model, changing default provider or model in config.json, switching providers at runtime, setting API keys, or debugging provider-related failures (e.g. "provider not registered", "Active provider=...", model not found, or gemini 400 `UNKNOWN` type errors). It documents the single source of truth for provider settings and the hard rules to avoid breaking them.
---

# Provider Settings — Agent Notes

> [!IMPORTANT]
> These rules override your training data and any assumption that "editing config.json changes the running server".

## 1. Sources of truth (in precedence order)

| Source | Field / Env var | Resolved by |
|---|---|---|
| Explicit model argument | `model=...` passed to `generate()` | `resolve_default_model` (config.py:84) |
| `AGENT_MODEL` env var | `AGENT_MODEL` | `resolve_default_model` (config.py:87) |
| `AGENT_PROVIDER` env var | `AGENT_PROVIDER` | `resolve_active_provider` (config.py:116) |
| `codebase/config.json` → `default_provider` | top-level key | `resolve_active_provider` |
| `codebase/config.json` → `providers.<name>.default_model` (or first item of `providers.<name>.models`) | per-provider | `PROVIDER_DEFAULTS` (config.py:22) |
| API keys | `GEMINI_API_KEY`, `OPENROUTER_API_KEY` | `build_orchestrator` (providers_setup.py:17) |

- **The top-level `config.json` `default_model` field is effectively ignored.** The default model for a provider comes from `providers.<name>.default_model` (config.py:22-25) or `AGENT_MODEL`. Do not rely on the top-level `default_model`.
- Registered providers are only: `gemini`, `openrouter`, `mock`. A provider is registered only if its API-key env var is set (mock is always available with `include_mock=True`).

## 2. Hard rules — never break these

1. **`config.json` is read ONCE at process start.** `config.py` opens `config.json` at module import (config.py:19-20). Editing it while the server runs has **zero effect** until the server restarts. After editing, restart and confirm via `/api/status`.
2. **Do NOT edit `config.json` to "switch providers" as part of a code change.** Runtime switching is done with `POST /api/switch-provider` (`agent_core/server/routes.py:58`) → `switch_active` (providers_setup.py:72), which mutates only the in-memory `_srv.active_provider` / `_srv.active_model` and orchestrator defaults. It never writes back to `config.json`.
3. **Never hardcode a provider/model string in provider code, the loop, or tool code.** Always resolve through `resolve_active_provider()` / `resolve_default_model()`, or read `_srv.active_provider` / `_srv.active_model`. The loop already threads `provider=_srv.active_provider, model=_srv.active_model` into every turn (ws_handler.py:224-225).
4. **Never touch API keys or secrets.** Keys are env-driven. Never put keys in `config.json`, source files, or commit them.
5. **Do not invent a second provider-state store.** Active provider/model is in-memory + `config.json` defaults; message history is SQLite-only (`MessageStore`). Keep one persistence path.
6. **If the requested model is not in `config.json` → `providers.<name>.models`, it is not offered by the catalog** (`/api/providers`). To add a model, edit `config.json` **and** restart (rule 1). The server does not fetch new model names at runtime.

## 3. Provider behavioral differences (design constraints)

- **gemini** — stateful Interactions API (`google-genai` SDK). Supports `previous_interaction_id` chaining. Two request modes in `gemini_provider.py`:
  - `_generate_initial_from_messages` — first turn / no conversation_id: sends full message history as steps.
  - `_generate_stateful` — when a conversation_id exists: chains the latest turn only.
  - The latest conversation_id is propagated to the client via loop events → `ws_handler` `conv_id` threading. Do not "simplify" this by removing the propagation; that is what keeps subsequent turns chaining.
  - **Gemini `steps` schema pitfall:** `function_call` steps require `arguments` as a dict. If a tool call's `arguments` ever arrives as a string (e.g. Python repr), the SDK silently downgrades the step to `type: UNKNOWN` and the API returns `400 The value 'UNKNOWN' is not supported for 'type'`. Never convert `tool_calls[].arguments` to a string when persisting (see `MessageStore.get_messages`, message_store.py:114-115).
- **openrouter** — stateless. Always sends full `messages` history every turn; `conversation_id` is always `None`. Never rely on conversation_id for openrouter, and do not break the stateless `messages` path when changing gemini chaining.
- **mock** — no API key; used when no real provider key is present or for testing. Keep it last / fallback only.

## 4. Verification (do this before diagnosing or after changing)

```bash
# live runtime state (what the loop actually uses)
curl -s http://localhost:8001/api/status

# registered providers + model catalog
curl -s -H "Authorization: Bearer <token>" http://localhost:8001/api/providers

# env-driven config
cd /home/manigupt/Hello/Agentic_Unit_PIE/codebase && cat config.json
echo "provider=$AGENT_PROVIDER model=$AGENT_MODEL gemini_key=${GEMINI_API_KEY:+set} openrouter_key=${OPENROUTER_API_KEY:+set}"
```

Read `/api/status` first. If it reports `Active provider=mock`, the configured provider's API key is missing (server/__init__.py:75-85).

## 5. Common mistakes to avoid

- "I edited config.json but the server still uses the old model" → restart needed (rule 1).
- "Provider not found: X" → X isn't in `_PROVIDER_CONFIGS` (providers_setup.py:17) or its API key env var is unset.
- Editing `default_model` at the top level of config.json expecting it to change the model → it won't (see section 1).
- Sending `system_instruction`/`tools` incorrectly on gemini chained turns → `_generate_stateful` deliberately does not resend `system_instruction` (gemini_provider.py:331); tools are re-specified per turn.
- **Token-saving tool skip**: `gemini_skip_tools_on_chain=true` (config) means chained turns do NOT re-send the tool schema, to avoid re-uploading it every turn (the 78k-token blowup). This is safe because the schema is persisted server-side on the conversation. **Defense in depth**: after a skipped-tools turn, `_tool_calls_valid()` validates the model's tool calls against the schema; if it hallucinated unknown tool names or omitted required args (e.g. `file_path`/`instructions`/`target_content` instead of `path`/`mode`), the provider retries once WITH tools attached. If you see wrong tool-call args in a log, check whether `skip_tools` was true for that turn.
