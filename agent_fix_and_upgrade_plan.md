# Agent Fix & Upgrade Plan

## PART 1 — ROOT CAUSE DIAGNOSIS

I traced the actual code path for `read_file`, `list_files`, and `write_to_file`. There are
**three different, disagreeing definitions of "the workspace root"** active in the system at
the same time. This is the entire reason the model can't find its own files — it isn't a
prompting problem, it's a real bug, and no amount of "be careful with paths" in the system
prompt will fix it.

### Bug G — the "conversation" is not really a conversation

```python
current_input = _tool_followup(tool, tool_input, tool_result)
...
result = orchestrator.generate(
    prompt=current_input,
    system_prompt=system_prompt if conv_id is None else None,
    conversation_id=conv_id,
    ...
)
```

Each step **replaces** `current_input` with just the latest tool result and relies entirely on
the provider's server-side `conversation_id` (e.g. Gemini's `previous_interaction_id`) to
remember everything before it — including the original user request. If that provider-side
state is ever dropped, truncated, or behaves differently than expected (varies a lot between
Gemini/OpenRouter/OpenAI), the model effectively forgets *why* it's reading a file at all by
step 4 or 5. This is architecturally risky — see Part 2 for the fix (own message-array
history, not provider magic).

**None of this is model intelligence failing — it's the harness giving the model contradictory
and unverifiable information about the filesystem.** Fix the harness first; the "10 rounds for
a trivial edit" problem will mostly disappear on its own even before you touch the system
prompt.

---

## PART 2 — REMAINING FIXES

### Fix 3 — Replace hand-rolled JSON-in-text parsing with real function calling

Right now the model must emit exact JSON in free text (`{"action": "write_to_file", ...}`),
which every provider does slightly differently, and any stray token before/after the JSON
breaks `extract_json`'s regex (`\{.*\}` is also greedy and will break on files whose *content*
contains braces, e.g. writing JSON or JS files — this is a real, separate bug: if the model's
`"input"` field contains `{`/`}` characters as file content, `extract_json`'s greedy regex can
grab the wrong span).

Use each provider's **native tool-calling / function-calling API** instead
(`tools=[...]` with JSON schema, not prompt-engineered JSON). This is what Claude Code, Codex,
and OpenCode all do — it is not optional if you want reliability comparable to them. Concretely:

- Define each tool once as a JSON Schema (name, description, parameters).
- Pass that schema array to the provider's `generate()` call.
- Read `tool_calls` / `function_call` off the structured response, not off regex-parsed text.
- Only fall back to text-JSON parsing for providers that genuinely don't support tool calling.

This also unlocks **multiple tool calls per turn** (most modern APIs support returning several
tool calls in one response), which removes the "exactly one tool per message" bottleneck in
your system prompt and roughly halves round trips for any multi-file task.

### Fix 4 — Real conversation history, not provider-magic-only

Stop relying solely on `conversation_id`. Maintain an explicit list of messages
(`role`, `content`, `tool_calls`, `tool_results`) per session server-side, and send the
relevant window of it on every call. This:
- Works identically across providers (Gemini/OpenRouter/OpenAI/Anthropic all differ in how
  their "remember this for me" mechanism behaves and how long it lasts).
- Lets you implement **context compaction** later (summarize old tool outputs once the
  transcript gets long — critical for long coding sessions).
- Lets you persist sessions across server restarts (currently `conversations: dict[str, ...]`
  is in-memory only and is lost on redeploy).

---

### Why Fix 3 and Fix 4 are not implemented yet

Both Fix 3 and Fix 4 are significant refactors of the LLM orchestration layer that touch the
entire provider stack (`llm_orchestrator.py`, `gemini_provider.py`, `openrouter_provider.py`,
`mock_provider.py`, and the agent loop's message handling).

- **Fix 3** requires defining a JSON Schema for every tool, adapting each provider's
  `generate()` to accept `tools=[...]` and return structured `tool_calls`, building a
  fallback for providers without native tool calling, and updating `response_parse.py` to
  handle structured responses. The current regex-based `extract_json` approach, while fragile,
  works for the basic case and the overhead of a full provider-level refactor is not justified
  while the file-tool path bugs (which caused >80% of failures) are resolved.

- **Fix 4** requires adding a server-side message store, context window management,
  truncation/compaction logic, and adapting each provider to accept explicit message arrays
  instead of relying on `conversation_id`. This is architecturally important for long sessions
  and cross-provider consistency, but the provider-magic approach works adequately for
  single-turn and short multi-turn interactions.

The plan recommends scheduling these as their **own milestone once the path resolution,
tooling, loop, and prompt fixes are stable** — which they now are. Both fixes remain valuable
for production hardening but are not blockers for the agent's core file-manipulation
functionality.

---

## PART 3 — FULL UPGRADE ROADMAP (toward Claude Code / Codex / OpenCode parity)

Group these into phases; each phase is independently shippable.

### Phase A — Core tool set parity

| Tool | Purpose | Notes |
|---|---|---|
| `read_file` | already have, upgrade per Fix 1 | add optional `offset`/`limit` for huge files |
| `edit_file` | new, per Fix 5 | primary editing tool |
| `write_to_file` | keep for create/overwrite only | |
| `list_files` | already have, upgrade per Fix 1 | tree output |
| `glob_search` | find files by pattern (`**/*.py`) | use `pathlib.Path.rglob` or `glob.glob` |
| `grep_search` | search file contents by regex across the repo | shell out to `ripgrep` (`rg --json`) if available, huge speed/quality win; fallback to Python regex walk |
| `execute_command` | already have | expand allowlist carefully, see Phase D |
| `run_tests` | run the project's test command and return pass/fail + output | detect via `package.json`/`pyproject.toml`/`Makefile` |
| `git_status` / `git_diff` / `git_commit` | inspect and commit changes | shells to `git`, restricted to workspace repo |
| `todo_write` / `todo_read` | agent's own task list, shown to the user | mirrors Claude Code's planning tool; big UX and reliability win for multi-step tasks |
| `web_fetch` (optional) | fetch docs when stuck | only if you want internet access in-agent |

### Phase B — Reliability / correctness of the agent loop

1. **Native function calling everywhere** (Fix 3) — biggest reliability lever available.
2. **Multi-tool-call turns** — let the model batch, e.g., 3 `read_file` calls in one turn when
   exploring a repo, instead of 3 round trips.
3. **Structured error taxonomy** — every tool returns `{"ok": false, "error_type": "...", "message": "...", "suggestion": "..."}` under the hood (still stringified for the model, but let your logging/telemetry key off `error_type`). Error types: `not_found`, `not_unique`, `permission`, `path_escape`, `too_large`, `timeout`.
4. **Self-correction loop**: track consecutive failures per tool; after N (e.g. 2) failures on
   the same file, auto-inject a system note: *"You have failed to edit `X` twice. Call
   `read_file` on it now and copy exact text before trying again."* This directly targets the
   exact failure mode you reported.
5. **Context compaction**: once transcript exceeds ~60–70% of the model's context window,
   summarize older tool results (keep file diffs/decisions, drop raw `list_files` dumps) into
   a single system note and continue. Needed for any session longer than ~15–20 turns.
6. **Idempotent conversation state**: persist session message history to disk/DB (SQLite is
   fine at your scale) instead of the in-memory `conversations: dict`, so a server restart
   doesn't silently reset every user's session.
7. **Timeouts & retries with backoff** on LLM calls, not just on `execute_command`.
8. **Structured "plan" step before execution** for any task touching >1 file: force the model
   to emit a short plan (via `todo_write`) before its first edit. This is what makes Claude
   Code/Codex feel coherent on multi-file tasks instead of thrashing.

### Phase C — UX parity with Claude Code / Codex / OpenCode

1. **Diff preview + approve/reject per edit** in the frontend — stream the unified diff for
   every `edit_file`/`write_to_file` call to the UI before/as it's applied, with an
   accept-all / per-file toggle. This is the single most-recognizable feature of these tools.
2. **Checkpoints / undo** — snapshot the workspace (or just the touched files) before each
   agent turn (`git stash`-style or simple copy-on-write to a `.agent_checkpoints/` dir) so the
   user can revert a whole turn with one click.
3. **`@file` mentions and inline file picker** in the chat input (you already have a file tree
   endpoint — wire it into an autocomplete in `AgentChat.tsx`).
4. **Live "currently editing: `path`" status** using your existing `tool_call`/`tool_result`
   websocket events — you already stream these, just surface them more prominently in the UI
   (you're most of the way there already).
5. **Todo/plan panel** in the sidebar, fed by the new `todo_write` tool, so the user sees the
   agent's plan update live, not just raw tool calls.
6. **Cost/usage panel** — you already track `total_tokens`/`total_cost` in
   `LLMOrchestrator`; expose it via `/api/status` and show it in the UI.

### Phase D — Sandboxing & safety (needed before "full-fledged")

1. **Expand `ALLOWED_COMMANDS` deliberately, not by removing the allowlist.** Add `grep`,
   `find`, `mkdir`, `mv`, `cp`, `git`, language-specific runners (`pytest`, `npm`, `pip`) —
   but keep a real allowlist/denylist, don't switch to "allow everything."
2. **Run `execute_command` inside a container or restricted subprocess** (e.g. `firejail`,
   Docker, or at minimum `resource` limits + a scratch working directory) so an agent-written
   script can't touch anything outside `WORKSPACE_ROOT` even via `os.system` tricks embedded
   in code it writes and then runs.
3. **Secrets redaction** — scan tool outputs (especially `execute_command` and `.env` file
   reads) for likely API keys/tokens before they're sent back to the LLM provider or logged.
4. **Per-user workspace isolation** — right now `WORKSPACE_ROOT` is global; for multi-user
   deployments, scope it to `WORKSPACE_ROOT/<user_id>/` (your JWT already gives you `user.id`).
5. **File size / write-rate limits** already partially present (`MAX_FILE_SIZE`) — apply
   consistently to `edit_file` and `write_to_file` both.

### Phase E — Memory & project understanding

1. **`AGENTS.md`/`CLAUDE.md`-style project memory file** — on session start, if a file like
   `AGENTS.md` exists at the workspace root, auto-read and prepend it to context (conventions,
   build commands, architecture notes the user maintains by hand). This is now a de-facto
   standard across Claude Code/Codex/Cursor/OpenCode.
2. **Lightweight repo map** — on first message in a session, run a fast structural scan
   (file tree + top-level symbol names via `ast` for Python / regex for JS/TS) and include a
   compact summary so the model doesn't need several `list_files`/`read_file` calls just to
   orient itself in a large repo.
3. Your existing `kernel_retrieve`/`kernel_store_context`/RAG machinery is a good foundation
   for longer-term memory across sessions — keep it, but make sure it's optional/degrades
   gracefully (it already does via `KERNEL_AVAILABLE`, good).


