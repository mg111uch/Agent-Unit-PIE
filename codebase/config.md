# Agent Configuration

This single file is the configuration for the agent — no second file to
reference. It is written as plain Markdown: every setting is a `###` heading
holding the dotted key and its value, followed by a short explanation of what
the setting does and how to change it. The agent reads the headings; the
prose is for you.

## How this file is read

- Each setting line has the form `### key = value`. Change a value, save, and
  the next agent launch picks it up.
- Nested settings use dotted keys, e.g. `### providers.gemini.default_model`
  is the same as `providers -> gemini -> default_model`.
- Values use plain JSON syntax: `"text"`, `123`, `true`/`false`, and lists
  like `["a", "b"]`.
- A legacy `config.json` beside this file is only used as a fallback if this
  file is missing or its settings can't be read — you should not need to edit
  it, and `config.md` always wins when both parse.
- Per-launch `AGENT_*` environment variables override this file. Common ones:
  `AGENT_PROVIDER`, `AGENT_MODEL`, `AGENT_TOOL_MODE`, `AGENT_TOOL_PACKS`,
  `AGENT_WORKSPACE_BASE`.

## What the sections cover

| Section | What it controls |
|---------|------------------|
| Context budget and tokens | When history is compacted, token reserves, output caps |
| Conversation history | How far back the model sees, and what can be dropped |
| Models and providers | Default provider/model, provider lists, Gemini/OpenRouter tuning |
| Request routing | Three tiers: deterministic fast path, small router, cloud reasoning |
| Tooling behavior | Command allowlist, tool packs, tool mode, edit self-checks |
| Checkpoints and safety | Undo snapshots, sandbox, excluded dirs, secret redaction, debug dumps |
| System prompt and learning | Core-only prompt, self-evolving chains and workflow graph |

---

## Config regeneration

### generate_config_json = true

When true, every load regenerates the legacy `config.json` beside this file
from the headings in this file. The Markdown file remains the source of truth; `config.json` is only a mirror.

---

## Context budget and tokens

### compaction_trigger_tokens = 8000

Estimated model-visible input tokens that trigger compaction. When the
assembled message history crosses this many tokens, older turns are folded
into a short summary so each model call stays cheap.

### model_output_token_budget = 1200

Token reserve carved out of the context window for the model's answer.

### model_reasoning_token_budget = 800

Token reserve carved out for the model's reasoning tokens.

### model_tool_result_headroom = 2500

Token reserve left empty for tool results arriving later in the turn. These
three reserves are subtracted before compaction decides what to trim.

### model_context_window_tokens = 131072

Assumed context window of the model, used for token-budget math.

### model_tool_result_max_chars = 2500

Maximum characters of a single tool result sent to the model. Larger results
are truncated in the model-facing payload.

### tool_decision_max_tokens = 512

Output cap for a step that only picks a tool. A tool-decision call needs a
small JSON envelope, not a long answer.

### final_answer_max_tokens = 1024

Output cap for the final answer, which gets room to explain.

### complex_reasoning_max_tokens = 2048

Output cap for steps that need complex reasoning.

### gemini_chain_restart_tokens = 40000

When estimated billed context crosses this, a stateful Gemini chain is
restarted with the compacted client history as a fresh first message, bounding
per-call cost.

### context_digest_enabled = true

Keep an in-context digest (workspace root, cached files, active plan) across
turns so the model does not re-discover what it already knows. `false`
disables the digest.

### show_tool_token_usage = true

Show per-step token usage in each tool box header in the frontend.

---

## Conversation history

### history_relevance.enabled = true

Master switch for the irrelevant-history filter: completed turns that share no
significant word or path with the current request are dropped from the model
payload to save tokens in long chats. `false` restores identical legacy
behavior.

### history_relevance.keep_recent = 1

Number of newest completed turns that are ALWAYS kept, regardless of whether
they overlap the current request.

### history_relevance.min_overlap = 1

Older completed turns survive only when at least this many significant tokens
of the current request appear in the turn's text (words plus file paths such
as `fib.py`).

---

## Models and providers

### default_provider = "mock"

Provider used by default. Override per-launch with `AGENT_PROVIDER`.

### default_model = "mock"

Fallback model when nothing more specific is chosen. `AGENT_MODEL` or a
provider's `default_model` wins over this.

### providers.gemini.default_model = "gemini-3.5-flash-lite"

Default Gemini model used when no explicit model is chosen.

### providers.gemini.models = ["gemini-3.5-flash-lite", "gemini-3.7-flash", "gemma-4-26b-a4b-it"]

Model list offered for Gemini in the UI.

### providers.openrouter.default_model = "openai/gpt-oss-20b:free"

Default OpenRouter model used when no explicit model is chosen.

### providers.openrouter.models = ["google/gemma-4-26b-a4b-it:free", "openai/gpt-oss-20b:free", "nvidia/nemotron-3-ultra-550b-a55b:free", "nvidia/nemotron-3-super-120b-a12b:free", "nvidia/nemotron-3-nano-omni-30b-a3b-reasoning:free", "nvidia/nemotron-3-nano-30b-a3b:free", "nvidia/nemotron-3.5-lightning:free", "nvidia/nemotron-3-embed-1b:free", "poolside/laguna-s-2.1:free", "poolside/laguna-xs-2.1:free", "inclusionai/ling-3.0-flash:free", "inclusionai/ling-3.0-tiny:free", "bytedance-seed/seedream-4.5"]

Model list offered for OpenRouter in the UI. OpenRouter model ids are free to
change at any time; `:free` suffixes mark no-cost endpoints.

### providers.mock.default_model = "mock"

Default mock model (used for offline testing and frontend development).

### providers.mock.models = ["mock"]

Model list offered for the mock provider.

### gemini_skip_tools_on_chain = true

Do not re-send unchanged tool schemas on Gemini chained calls. Schemas persist
server-side, so this cuts per-step token cost.

### gemini_stateless = false

Use stateless Gemini calls (store=false): the full, client-compacted history
is sent every call, bounding cost deterministically. `false` keeps stateful
chains.

### gemini_implicit_cache = true

Rely on Gemini's implicit caching of the stable system-instruction prefix.

### gemini_stateless_cache = false

Explicitly cache the static prefix and reference it on later stateless calls.
Only used when implicit caching is off.

### gemini_stateless_skip_schemas = false

Skip tool schemas on stateless chained turns, trusting gathered data. Risky;
there is retry logic when the model still asks for a tool. Off by default.

### gemini_prune_tools_on_chain = true

On chained Gemini turns, send only the tools already used plus a small base
set, instead of every tool schema.

### openrouter_skip_tools_on_chain = false

Skip re-sending tool schemas on OpenRouter chained turns. OpenAI-compatible
models usually will not emit tool calls without the schema, so keep this off.

### openrouter_prune_tools_on_chain = true

On chained OpenRouter turns, send only the tools already used plus a small
base set.

### openrouter_retry_skipped_chain = true

When a chained turn deliberately skipped tools, retry once WITH tools if the
reply looks like a tool attempt — never on a plain text answer.

---

## Request routing

### factories_enabled = false

Tier-1 deterministic fast path: a small set of obvious filesystem requests
(find/read/list/check/create-dir) run with zero LLM calls. `true` enables it.

### direct_final_tools = ["check_path_exists"]

Tools whose success on the first step of a turn produces a synthesized final
answer instead of a second model call. Empty list turns this off.

### tool_group_routing = true

Show the reasoning model only a small, request-matched subset of tools on the
first step, instead of every active tool schema.

### tool_search.enabled = false

Hybrid tool search: each turn, send only an always-on base set plus a
request-ranked subset of tool schemas, and expose `find_tool` / `get_tool_schema`
so the model can discover and call any enabled tool on demand (execution runs
against the full registry, so a discovered tool needs no schema re-injection).
`true` enables it; when off, behavior is unchanged (`tool_group_routing` / full
catalog).

### tool_search.base_tools = ["Read", "grep_search", "glob_search", "execute_command", "edit_file", "Write", "ask_user_question", "get_workspace_info"]

Tool names always sent to the model each turn (intersected with active packs and
`tool_mode`). `find_tool` / `get_tool_schema` are always included regardless of
this list.

### tool_search.top_k = 10

How many additional request-ranked tools (beyond the base set) to include per turn.

### tool_search.fallback = "base"

When no tool ranks above zero: `base` keeps only the base set, `full` falls
back to every enabled tool.

### mcp_always_expose = "meta"

Which category is always exposed over MCP (`find_tool` / `get_tool_schema`
are always exposed in either mode):
- `meta` — all CAT_META tools (workspace, diff, edit/undo, introspection) plus
  the two search tools.
- `search` — only `find_tool` / `get_tool_schema`. CAT_META tools (e.g.
  `get_workspace_info`, `tool_anatomy`, `undo_last_edit`, `cross_file_edit`)
  become unlisted and un-callable over MCP (they remain available in the native
  agent loop). Other tool packs are still exposed when enabled in `tool_packs`.

Overridable via the `AGENT_MCP_ALWAYS_EXPOSE` env var.

### tier2_model_router.enabled = false

Tier-2 routing model on/off. When disabled, ambiguous requests go straight to
the cloud reasoning model.

### tier2_model_router.backend = "openrouter"

Which backend routes ambiguous requests: `gemini`/`openrouter` for a small
cloud model, `ollama` for a local model.

### tier2_model_router.model = "inclusionai/ling-3.0-tiny:free"

The small model used for tier-2 routing.

### tier2_model_router.timeout_s = 60

How long a routing call may take before the request escalates to the cloud.

---

## Tooling behavior

### allowed_commands = ["ls", "cat", "mkdir", "cd", "pwd", "python", "python3", "pytest"]

Sandbox allowlist: the ONLY commands `execute_command` may run. Enforced at
runtime — keep it minimal.

### tool_mode = "all"

Which tools are active: `all` (everything allowed by `tool_packs`), or a
`read-only` / `shell-only` subset.

### tool_packs.file = true

Expose the file operations pack (read, write, edit, list, search, execute).

### tool_packs.meta = false

Expose the meta/inspection pack (registry and tool introspection).

### tool_packs.kernel = false

Expose the kernel memory pack.

### tool_packs.debate = false

Expose the debate/simulation pack.

### tool_packs.sim = false

Expose the simulation connector pack.

### tool_packs.git = false

Expose the git pack (gated together with `git_tools_enabled`).

### tool_packs.code_rag = false

Expose the codebase-atlas retrieval pack.

### tool_packs.chain = false

Expose the tool-chain pack. Learned recipes are only ever hinted to the agent
when this pack is on.

### git_tools_enabled = false

Expose git-aware tools (they still obey the sandbox allowlist).

### subagent_task_enabled = false

Allow subagent task execution (used by the frontend for sub-tasks).

### post_edit_import_check = true

After editing a Python file, re-import-check that the edit did not break the
module.

### tool_nudge_threshold = 20

Nudge the model to wrap up after this many tool calls per step without a
final answer. Raise for legitimate long tool sequences.

---

## Checkpoints and safety

### enable_checkpoints = true

Snapshot the workspace before write-tool calls so changes can be rolled back.

### max_checkpoints = 50

Maximum number of rollback snapshots kept.

### agents_md_enabled = true

Inject workspace AGENTS.md guidance into the system prompt.

### sandbox_enabled = false

Sandbox the agent's filesystem access to the workspace. Off by default.

### exclude_dirs = [".git", ".agent_checkpoints", ".pytest_cache", ".adk", "node_modules", "__pycache__", ".venv", "children"]

Directories the agent treats as noise and skips when scanning and reading.

### secrets_patterns = ["sk-[A-Za-z0-9]{15,}", "gh[pousrx]_[A-Za-z0-9]{15,}", "xox[bpsa]-[A-Za-z0-9]{10,}", "AKIA[0-9A-Z]{16}", "-----BEGIN (RSA |EC |OPENSSH )PRIVATE KEY-----"]

Regex patterns for secrets that are redacted from stored messages and the UI.

### debug_dump_enabled = true

Dump per-call payloads for debugging and forensics.

### debug_dump_append_mode = true

Append each dump to the log (`true`) or overwrite per session (`false`).

### codebase_atlas_dir = "../atlas_output"

Relative path (from `codebase/`) to the codebase-atlas index used by code_rag.

### rate_limits.llm_calls_per_minute = 10

Maximum LLM calls allowed per minute.

### rate_limits.tool_writes_per_minute = 30

Maximum tool write operations allowed per minute.

---

## System prompt and learning

### system_prompt_core_only = false

Send only the immutable core system prompt (identity + workspace rules +
response contract). `false` also includes capability playbooks and AGENTS.md
(~1,288 tokens); core-only is ~831 tokens.

### system_prompt_devpt_fragments = false

Include the dev-report fragments (`onboarding.md` + `sys_devpt_reports.md`) in
the assembled system prompt. They point agents at `project_history`, capability
hypotheses (`list_capabilities`) and the report maintenance protocol. Set
`false` to drop this guidance while keeping the core fragments.

### workflow_learn.enabled = false

Master switch for self-evolving tool chains and the workflow graph: mining
repeated patterns into reusable chains and rebuilding the graph.

### workflow_learn.min_occurrences = 2

How often a tool-call sequence must appear to become a chain candidate.

### workflow_learn.max_sequence_len = 4

Longest learned recipe, in number of steps.

### workflow_learn.in_loop = true

Run lightweight mining mid-session.

### workflow_learn.session_end = true

Run full mining at the end of a session.

### workflow_learn.graph_evolve = true

Rebuild the workflow graph from chains, candidates, and session usage.

### workflow_learn.context_hints = true

Remind the agent of learned recipes and dos/don'ts in its context.

### workflow_learn.stale_after_days = 14

Retire learned chains unused for this many days.

### workflow_learn.min_savings_tokens = 0

Do not promote a recipe unless it saves at least this many tokens per use.

### workflow_learn.min_savings_ms = 0

Do not promote a recipe unless it saves at least this many milliseconds per use.
Promotion uses token OR time bar (whichever threshold is met). Default 0 (time
bar off) keeps the token-only behavior.