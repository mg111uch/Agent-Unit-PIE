"""Shared configuration and defaults for agent CLI and server."""

from __future__ import annotations

import json
import os
import re

# codebase/ (parent of agent_core/)
CODEBASE_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))

# config.md is the single user-facing config file: readable Markdown where each
# setting is a "### dotted.key = value" heading. config.json beside it is the
# LEGACY fallback, used only when the markdown file is missing or unparseable.
CONFIG_MD_PATH = os.path.join(CODEBASE_ROOT, "config.md")
CONFIG_PATH = os.path.join(CODEBASE_ROOT, "config.json")

JWT_SECRET = os.getenv("JWT_SECRET", "your_jwt_secret")
AGENT_PORT = int(os.getenv("AGENT_PORT", "8001"))
CORS_ORIGINS = os.getenv("CORS_ORIGINS", "http://localhost:3000,http://localhost:8001").split(",")
WORKSPACE_BASE = os.getenv("AGENT_WORKSPACE_BASE",
    os.path.abspath(os.path.join(CODEBASE_ROOT, "..", "data", "workspaces")))


def _read_config_md() -> dict:
    """Parse config.md: each line ``### dotted.key = <json value>`` becomes a
    nested dict entry; prose and other Markdown are ignored."""
    cfg: dict = {}
    with open(CONFIG_MD_PATH, "r", encoding="utf-8") as _f:
        for line in _f:
            m = re.match(r"^### ([a-zA-Z_][\w.]*)\s*=\s*(.+)$", line.strip())
            if not m:
                continue
            key, raw = m.group(1), m.group(2).strip()
            try:
                val = json.loads(raw)
            except ValueError:
                val = raw
            node = cfg
            *parts, leaf = key.split(".")
            for p in parts:
                node = node.setdefault(p, {})
            node[leaf] = val
    return cfg


def _write_config_json(cfg: dict) -> None:
    """Mirror cfg into the legacy config.json so it never goes stale."""
    with open(CONFIG_PATH, "w", encoding="utf-8") as _f:
        json.dump(cfg, _f, indent=2)
        _f.write("\n")


def _load_config_file() -> dict:
    if os.path.exists(CONFIG_MD_PATH):
        try:
            cfg = _read_config_md()
            if cfg:
                if cfg.get("generate_config_json"):
                    _write_config_json(cfg)
                return cfg
        except Exception:
            pass  # fall back to legacy config.json below
    with open(CONFIG_PATH, "r", encoding="utf-8") as _f:
        return json.load(_f)


_CONFIG = _load_config_file()

PROVIDER_DEFAULTS: dict[str, str] = {
    name: data.get("default_model", list(data.get("models", []))[0] if data.get("models") else name)
    for name, data in _CONFIG.get("providers", {}).items()
}

CLI_STEP_DELAY = 5.0
SERVER_STEP_DELAY = 2.0

# Single source of truth for the sandbox allowlist is config.md
# (agent_core/tools/exec_ops.py enforces it at runtime).
ALLOWED_COMMANDS: list[str] = _CONFIG.get("allowed_commands", [
    "ls", "cat", "mkdir", "cd", "pwd", "python", "python3", "pytest",
])

TOOL_MODES: dict[str, set[str]] = {
    "read_only": {"Read", "glob_search", "grep_search"},
    "shell_only": {"execute_command"},
}

GIT_TOOLS_ENABLED: bool = _CONFIG.get("git_tools_enabled", False)
SUBAGENT_TASK_ENABLED: bool = _CONFIG.get("subagent_task_enabled", False)
ENABLE_CHECKPOINTS: bool = _CONFIG.get("enable_checkpoints", False)
MAX_CHECKPOINTS: int = _CONFIG.get("max_checkpoints", 50)
AGENTS_MD_ENABLED: bool = _CONFIG.get("agents_md_enabled", False)
EXCLUDE_DIRS: list[str] = _CONFIG.get("exclude_dirs", [])
SANDBOX_ENABLED: bool = _CONFIG.get("sandbox_enabled", False)
POST_EDIT_IMPORT_CHECK: bool = _CONFIG.get("post_edit_import_check", True)
SECRETS_PATTERNS: list[str] = _CONFIG.get("secrets_patterns", [])
RATE_LIMIT_LLM_CALLS: int = _CONFIG.get("rate_limits", {}).get("llm_calls_per_minute", 10)
RATE_LIMIT_TOOL_WRITES: int = _CONFIG.get("rate_limits", {}).get("tool_writes_per_minute", 30)

DEBUG_DUMP_ENABLED: bool = _CONFIG.get("debug_dump_enabled", False)
DEBUG_DUMP_APPEND_MODE: bool = bool(_CONFIG.get("debug_dump_append_mode", False))

# Self-evolving tool chains: observe tool-call sequences, mine repeated patterns
# into new chains, auto-promote read-only chains, persist everything in SQLite.
_WF = _CONFIG.get("workflow_learn", {})
WORKFLOW_LEARN_ENABLED: bool = bool(_WF.get("enabled", True))
WORKFLOW_LEARN_MIN_OCCURRENCES: int = int(_WF.get("min_occurrences", 2))
WORKFLOW_LEARN_MAX_SEQUENCE: int = int(_WF.get("max_sequence_len", 4))
WORKFLOW_LEARN_IN_LOOP: bool = bool(_WF.get("in_loop", True))
WORKFLOW_LEARN_SESSION_END: bool = bool(_WF.get("session_end", True))
WORKFLOW_LEARN_GRAPH_EVOLVE: bool = bool(_WF.get("graph_evolve", True))
WORKFLOW_LEARN_CONTEXT_HINTS: bool = bool(_WF.get("context_hints", True))
WORKFLOW_LEARN_STALE_AFTER_DAYS: int = int(_WF.get("stale_after_days", 14))
WORKFLOW_LEARN_MIN_SAVINGS_TOKENS: int = int(_WF.get("min_savings_tokens", 0))

# Efficiency / context management
# Token-aware compaction trigger (Phase 7): compact the model-visible history
# once ESTIMATED INPUT TOKENS reach this many. Previously this was a raw
# character count; token math is more faithful to how models bill context.
COMPACTION_TRIGGER_TOKENS: int = int(_CONFIG.get("compaction_trigger_tokens", 8_000))
CONTEXT_DIGEST_ENABLED: bool = bool(_CONFIG.get("context_digest_enabled", True))

# Reserves carved out of the effective context window before a model call
# (Phase 7 §reserve): output budget, reasoning budget, and tool-result
# headroom. Compaction targets the visible-input budget that remains.
MODEL_OUTPUT_TOKEN_BUDGET: int = int(_CONFIG.get("model_output_token_budget", 1_200))
MODEL_REASONING_TOKEN_BUDGET: int = int(_CONFIG.get("model_reasoning_token_budget", 800))
MODEL_TOOL_RESULT_HEADROOM: int = int(_CONFIG.get("model_tool_result_headroom", 2_500))
MODEL_CONTEXT_WINDOW_TOKENS: int = int(_CONFIG.get("model_context_window_tokens", 131_072))

# Irrelevant-history classification (PlanFixes2): drop completed turns with no
# meaningful overlap with the current request from the model payload, saving
# tokens in long chats. Conservative by default: the last completed turn is
# always kept, and only zero-overlap turns are dropped.
HISTORY_RELEVANCE_ENABLED: bool = bool(_CONFIG.get("history_relevance", {}).get("enabled", False))
HISTORY_RELEVANCE_KEEP_RECENT: int = int(_CONFIG.get("history_relevance", {}).get("keep_recent", 1))
HISTORY_RELEVANCE_MIN_OVERLAP: int = int(_CONFIG.get("history_relevance", {}).get("min_overlap", 1))


def compaction_budget_tokens() -> int:
    """Model-visible input budget after reserving output + reasoning + tool
    results, the trigger for token-aware compaction (Phase 7)."""
    reserved = (
        MODEL_OUTPUT_TOKEN_BUDGET
        + MODEL_REASONING_TOKEN_BUDGET
        + MODEL_TOOL_RESULT_HEADROOM
    )
    return max(1, min(COMPACTION_TRIGGER_TOKENS, MODEL_CONTEXT_WINDOW_TOKENS - reserved))

# Gemini stateful chains retain the whole conversation server-side, so each
# chained call is billed against the accumulated context. When the estimated
# billed tokens pass this threshold, the chain is restarted with the compacted
# client history as a fresh first message to bound per-call cost.
GEMINI_CHAIN_RESTART_TOKENS: int = int(_CONFIG.get("gemini_chain_restart_tokens", 40_000))

# Deterministic, single-purpose tools whose successful result fully answers
# the request. When such a tool succeeds as the FIRST step of a turn, the loop
# emits a synthesized final instead of making a second LLM call. Empty = off.
DIRECT_FINAL_TOOLS: set[str] = set(_CONFIG.get("direct_final_tools", []) or [])

# First-step dynamic tool exposure: route the initial request to a small
# deterministic tool group (tool_groups.py) instead of exposing every active
# tool schema. Chained steps keep their own pruning. Off = current behavior.
TOOL_GROUP_ROUTING: bool = bool(_CONFIG.get("tool_group_routing", False))

# Phase 4 deterministic factory fast path (PlanFixes2 #8): run
# try_factory() before the first LLM call. Unambiguous asks (find/read/list/
# check/create-dir) execute one tool call with ZERO LLM calls. Ambiguous asks
# return None and fall through to the normal Gemini path.
FACTORY_ENABLED: bool = bool(_CONFIG.get("factories_enabled", True))

# Phase 6 — tier-2 model router (tier 2 of the three-tier classifier, after the
# deterministic factory and before the cloud model): when the factory declines
# an ambiguous request, a small model (config-driven backend: "gemini" /
# "openrouter" for cloud routing, "ollama" for a local model) maps it to
# one canonical validated action from a fixed vocabulary
# (planning/tier2_model_router.py). Disabled = ambiguous requests go straight
# to the cloud model.
TIER2_MODEL_ROUTER_ENABLED: bool = bool(_CONFIG.get("tier2_model_router", {}).get("enabled", False))
TIER2_MODEL_ROUTER_BACKEND: str = str(_CONFIG.get("tier2_model_router", {}).get("backend", "ollama"))
TIER2_MODEL_ROUTER_MODEL: str = str(_CONFIG.get("tier2_model_router", {}).get("model", "functiongemma"))
TIER2_MODEL_ROUTER_TIMEOUT: int = int(_CONFIG.get("tier2_model_router", {}).get("timeout_s", 60))

# Max characters of a tool result sent to the model (model-facing context),
# separate from the larger bound kept for storage/replay (Agent 2).
MODEL_TOOL_RESULT_MAX_CHARS: int = int(_CONFIG.get("model_tool_result_max_chars", 2500))

# Loop guard: nudge the LLM to wrap up only after this many tool calls per step
# without a final answer. Low values truncate legitimate long tool sequences.
TOOL_NUDGE_THRESHOLD: int = int(_CONFIG.get("tool_nudge_threshold", 12))

# Step-aware output budgets (PlanFixes2 #13): a tool-decision call only needs a
# small JSON envelope; a final answer gets room to explain.
MODEL_TOOL_DECISION_MAX_TOKENS: int = int(_CONFIG.get("tool_decision_max_tokens", 512))
MODEL_FINAL_MAX_TOKENS: int = int(_CONFIG.get("final_answer_max_tokens", 1024))
MODEL_COMPLEX_MAX_TOKENS: int = int(_CONFIG.get("complex_reasoning_max_tokens", 2048))

# System prompt split (PlanFixes2 #14): when true, the assembled system prompt
# is only the immutable core fragments (identity + workspace rules + response
# contract), dropping the optional capability playbooks and AGENTS.md, so the
# model-facing prefix stays ~700-1000 tokens.
SYSTEM_PROMPT_CORE_ONLY: bool = bool(_CONFIG.get("system_prompt_core_only", False))

# Dev-report fragments (onboarding.md + sys_devpt_reports.md) included in the
# assembled system prompt. When false, agents don't receive the project-history /
# report-maintenance guidance but the immutable core fragments still load.
SYSTEM_PROMPT_DEVPT_FRAGMENTS: bool = bool(_CONFIG.get("system_prompt_devpt_fragments", True))

# Frontend: display per-step token usage in each tool box header when true.
SHOW_TOOL_TOKEN_USAGE: bool = bool(_CONFIG.get("show_tool_token_usage", True))

# Gemini stateful turns: skip re-sending an unchanged tool schema on chained
# calls (schema persists server-side) to cut per-step token cost.
GEMINI_SKIP_TOOLS_ON_CHAIN: bool = bool(_CONFIG.get("gemini_skip_tools_on_chain", True))

# When true, Gemini uses store=False stateless calls: the full (client-compacted)
# history is sent on every call and the per-call cost is bounded deterministically
# by our compaction, instead of growing with Gemini's server-side chain retention.
GEMINI_STATELESS: bool = bool(_CONFIG.get("gemini_stateless", False))

# Stateless generateContent: rely on Gemini's IMPLICIT caching (2.5+/3.x auto
# cache a stable repeated request prefix) by preserving a byte-identical
# system_instruction prefix on every call. When false, fall back to the legacy
# explicit caches.create path (contributed ~zero in live tests, Phase 3).
GEMINI_IMPLICIT_CACHE: bool = bool(_CONFIG.get("gemini_implicit_cache", True))

# Stateless generateContent: explicitly cache the static prefix (system + tools)
# and reference it on later calls so the re-sent fixed overhead is billed at the
# discounted cached-input rate. Degrades to inline payloads on any failure.
# Only used when GEMINI_IMPLICIT_CACHE is off.
GEMINI_STATELESS_CACHE: bool = bool(_CONFIG.get("gemini_stateless_cache", False))

# Stateless chained turns: skip re-sending the tool schemas and let the model
# answer from the data it has already gathered. If it still emits a real tool
# call, the provider retries once WITH schemas available.
GEMINI_STATELESS_SKIP_SCHEMAS: bool = bool(_CONFIG.get("gemini_stateless_skip_schemas", False))

# Stateless chained turns: instead of re-sending the full tool schema on every
# tool-call follow-up, send only the tools already used this turn plus a small
# base set (read/list/grep/glob/edit/write/execute) — the Gemini analog of
# OPENROUTER_PRUNE_TOOLS_ON_CHAIN (Issues2.md: dynamic tool exposure).
GEMINI_PRUNE_TOOLS_ON_CHAIN: bool = bool(_CONFIG.get("gemini_prune_tools_on_chain", True))

# OpenRouter chained turns: skip re-sending the tool schemas so the model
# answers from gathered data. OpenAI-compatible models generally won't emit
# tool calls without the schema in the request, so enabling this can end
# multi-tool chains prematurely — keep OFF unless the chained step is known to
# be a final-answer step.
OPENROUTER_SKIP_TOOLS_ON_CHAIN: bool = bool(_CONFIG.get("openrouter_skip_tools_on_chain", False))

# OpenRouter chained turns: instead of re-sending the full tool schema on every
# tool-call follow-up, send only the tools already used this turn plus a small
# base set (read/list/grep/glob/edit/write/execute). This implements Issues2.md's
# "dynamic tool exposure": the per-call schema drops from ~1.6k tokens to a few
# hundred while keeping the model able to continue its chain.
OPENROUTER_PRUNE_TOOLS_ON_CHAIN: bool = bool(_CONFIG.get("openrouter_prune_tools_on_chain", True))

# When a chained turn deliberately skipped tools, retry once WITH tools only if
# the reply looks like a tool attempt (JSON action envelope / XML tool_call) —
# never on a plain final answer. Without this condition, a skipped chained turn
# ALWAYS retries (OpenAI-compatible models can't emit tool_calls sans schema),
# doubling every chained step and cancelling the token saving entirely.
OPENROUTER_RETRY_SKIPPED_CHAIN: bool = bool(_CONFIG.get("openrouter_retry_skipped_chain", True))

_raw_atlas_dir = _CONFIG.get("codebase_atlas_dir", "")
CODEBASE_ATLAS_DIR: str = os.path.abspath(os.path.join(CODEBASE_ROOT, _raw_atlas_dir)) if _raw_atlas_dir else ""


def load_config() -> dict:
    return _CONFIG


def get_provider_catalog() -> dict[str, dict]:
    return _CONFIG.get("providers", {})


def resolve_default_model(provider: str, explicit_model: str | None = None) -> str:
    if explicit_model:
        return explicit_model
    env_model = os.getenv("AGENT_MODEL")
    if env_model:
        return env_model
    return PROVIDER_DEFAULTS.get(provider, PROVIDER_DEFAULTS.get("gemini", "gemini-3.1-flash-lite"))


def resolve_active_tool_packs() -> list[str]:
    env_packs = os.getenv("AGENT_TOOL_PACKS")
    if env_packs:
        return [p.strip() for p in env_packs.split(",")]
    config_packs = _CONFIG.get("tool_packs")
    if isinstance(config_packs, dict):
        return [k for k, v in config_packs.items() if v]
    if isinstance(config_packs, list):
        return config_packs
    return ["file"]


def resolve_active_tool_mode() -> str:
    return os.getenv("AGENT_TOOL_MODE", _CONFIG.get("tool_mode", "all"))


def resolve_active_tool_names() -> set[str]:
    mode = resolve_active_tool_mode()
    if mode == "all":
        return set()
    return set(TOOL_MODES.get(mode, set()))


def resolve_active_provider() -> str:
    return os.getenv("AGENT_PROVIDER", _CONFIG.get("default_provider", "gemini"))


# Approximate model context windows (tokens), used to scale the session token
# usage bar. Prefix-matched per provider so newer model names still resolve.
MODEL_CONTEXT_WINDOWS: dict[str, dict[str, int]] = {
    "gemini": {
        "gemini": 1_000_000,
        "gemma": 8_192,
    },
    "openrouter": {
        "openai": 200_000,
        "google/": 1_000_000,
        "gpt-oss": 200_000,
        "nc-oss": 131_072,
        "nemotron": 131_072,
    },
    "mock": {
        "mock": 8_192,
    },
}

DEFAULT_CONTEXT_WINDOW: int = 200_000


def resolve_context_window(provider: str, model: str) -> int:
    table = MODEL_CONTEXT_WINDOWS.get((provider or "").lower(), {})
    for prefix, window in table.items():
        if (model or "").startswith(prefix.lower()):
            return window
    config_specific = (load_config().get("context_windows") or {}).get(provider, {}).get(model)
    return config_specific or DEFAULT_CONTEXT_WINDOW
