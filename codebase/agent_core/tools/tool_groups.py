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

_READ = {"read_file", "list_files"}
_LIST = {"list_files", "read_file"}
_FIND = {"glob_search", "list_files", "read_file"}
_GREP = {"grep_search", "read_file"}
_WRITE = {"read_file", "edit_file", "write_to_file"}
_EXEC = {"execute_command", "read_file"}
_EXISTS = {"check_path_exists", "read_file"}
_BASE = {
    "read_file", "list_files", "grep_search", "glob_search",
    "execute_command", "edit_file", "write_to_file",
}

SIDE_EFFECT_TOOLS = {
    "execute_command", "edit_file", "write_to_file",
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
    (e.g. "list codebase/temp" -> list_files only). Fuzzy or multi-intent
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