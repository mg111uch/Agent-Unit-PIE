"""Deterministic tool-group routing (Agent 2 — dynamic tool exposure).

Maps a user request to a small tool group using cheap lexical/structural
rules — no extra LLM call (PlanFixes2 #10/#11). Used only on the first
step of a turn to shrink the schema payload; chained steps keep their own
base-set pruning in the providers.

Fallbacks: low-confidence or unrecognized requests keep the full base set
so the model is never starved of a needed tool.
"""

from __future__ import annotations

import re

_READ = {"Read"}
_LIST = {"Read"}
_FIND = {"glob_search", "Read"}
_GREP = {"grep_search", "Read"}
_WRITE = {"Read", "edit_file", "Write"}
_EXEC = {"execute_command", "Read"}
_EXISTS = {"check_path_exists", "Read"}
_BASE = {
    "Read", "grep_search", "glob_search",
    "execute_command", "edit_file", "Write",
}

SIDE_EFFECT_TOOLS = {
    "execute_command", "edit_file", "Write",
    "cross_file_edit", "safe_edit", "git_commit", "undo_last_edit",
}

TOOL_GROUPS: dict[str, set[str]] = {
    "read": _READ,
    "list": _LIST,
    "find": _FIND,
    "grep": _GREP,
    "write": _WRITE,
    "execute": _EXEC,
    "exists": _EXISTS,
    "base": _BASE,
}

_READ_TOKENS = {"read", "show", "cat", "view", "display", "print", "open", "see", "inspect", "contents"}
_LIST_TOKENS = {"list", "ls", "dir", "tree"}
_FIND_TOKENS = {"find", "locate", "glob", "filepath", "which file", "where"}
_GREP_TOKENS = {"grep", "search", "occurrence", "references", "usage", "who uses", "who imports"}
_WRITE_TOKENS = {"write", "edit", "update", "create", "replace", "modify", "change", "rename", "append", "delete", "remove"}
_EXEC_TOKENS = {"run", "test", "pytest", "execute", "compile", "start", "build"}
_EXISTS_TOKENS = {"exists", "exist", "check", "verify", "confirm"}

_token_re: dict[frozenset, re.Pattern] = {}


def _has(text: str, tokens: set[str]) -> bool:
    key = frozenset(tokens)
    pat = _token_re.get(key)
    if pat is None:
        alt = "|".join(sorted(map(re.escape, tokens), key=len, reverse=True))
        pat = re.compile(r"(?<!\w)(?:%s)(?!\w)" % alt)
        _token_re[key] = pat
    return bool(pat.search(text))


def select_tools_for_request(user_input: str) -> set[str]:
    """Deterministically select a minimal tool group for a request.

    Single-purpose requests get the smallest group that can answer them
    (e.g. "list codebase/temp" -> Read only; Read lists directories). Fuzzy or multi-intent
    requests fall back to the base set so the model is never starved.
    """
    text = (user_input or "").strip().lower()
    if not text:
        return set(_BASE)
    if _has(text, _EXISTS_TOKENS) and len(text) < 80:
        return set(_EXISTS)
    if _has(text, _WRITE_TOKENS):
        return set(_WRITE)
    if _has(text, _LIST_TOKENS):
        return set(_LIST)
    if _has(text, _GREP_TOKENS):
        return set(_GREP)
    if _has(text, _FIND_TOKENS):
        return set(_FIND)
    if _has(text, _EXEC_TOKENS):
        return set(_EXEC)
    if _has(text, _READ_TOKENS):
        return set(_READ)
    return set(_BASE)


# ---------------------------------------------------------------------------
# Phase 4 — deterministic factory fast path (PlanFixes2 #8)
# ---------------------------------------------------------------------------
# Maps an unambiguous single-intent request to ONE deterministic tool call so
# the loop can skip the LLM entirely. Returns {"name": ..., "input": {...}},
# or None when nothing matches confidently (fall back to the LLM).

_CREATE_DIR_RE = re.compile(
    r"(?<!\w)(create|make|mkdir|new)(?!\w).{0,20}(?<!\w)(directory|dir|folder)(?!\w)", re.I)
_EXISTS_RE = re.compile(
    r"(?<!\w)(does|do|is|are|check|verify)(?!\w).{0,60}(?<!\w)(?:exists?|existed|existing|present)(?!\w)", re.I)
_FIND_RE = re.compile(
    r"(?<!\w)(find|locate)(?!\w)|(?<!\w)(where is|which file)(?!\w)", re.I)
_LIST_RE = re.compile(
    r"(?<!\w)(list|ls|dir|tree)(?!\w)|contents (of|in)|what'?s? in", re.I)
_READ_RE = re.compile(
    r"(?<!\w)(read|cat|print|open|view|show|display)(?!\w)", re.I)

_PATH_RE = re.compile(
    r"['\"]?([A-Za-z0-9_.+-]+(?:/[A-Za-z0-9_.+-]+)+|\./[A-Za-z0-9_.+-]+"
    r"(?:/[A-Za-z0-9_.+-]+)*|[A-Za-z0-9_+-]+\.(?:py|js|ts|jsx|tsx|txt|md|json|toml|cfg|yaml|yml))",
    re.I)

_FACTORY_VERBS = {
    "create", "make", "mkdir", "new", "list", "ls", "dir", "tree",
    "read", "cat", "print", "open", "view", "show", "display",
    "find", "locate", "check", "verify", "does", "do", "is", "are",
}


def _extract_path(text: str) -> str | None:
    m = _PATH_RE.search(text)
    if m:
        return m.group(1).strip("'\"")
    # Bare single target: "ls temp", "find fibonacci", "read Makefile".
    tokens = re.findall(r"[A-Za-z0-9_.+-]+", text)
    if len(tokens) == 2 and tokens[0].lower() in _FACTORY_VERBS:
        return tokens[1].strip("'\"")
    return None


def try_factory(user_input: str) -> dict | None:
    """Deterministic single-tool action for an unambiguous request, or None."""
    text = (user_input or "").strip()
    if not text or len(text) > 200:
        return None
    low = text.lower()
    if _CREATE_DIR_RE.search(low):
        path = _extract_path(text)
        if path:
            return {"name": "execute_command", "input": {"command": f"mkdir -p {path}"}}
    if _EXISTS_RE.search(low):
        path = _extract_path(text)
        if path:
            return {"name": "check_path_exists", "input": {"path": path}}
    if _FIND_RE.search(low):
        target = _extract_path(text)
        if target:
            return {"name": "glob_search", "input": {"pattern": f"**/{target}"}}
    if _LIST_RE.search(low):
        return {"name": "Read", "input": {"path": _extract_path(text) or "."}}
    if _READ_RE.search(low):
        path = _extract_path(text)
        if path:
            return {"name": "Read", "input": {"path": path}}
    return None