"""Cross-turn session state: file cache, workspace digest, message compaction."""

from __future__ import annotations

import hashlib
import re
from contextvars import ContextVar
from dataclasses import dataclass, field
from typing import Any, Optional

# Soft budget for in-memory message payload size (chars ≈ tokens*4)
COMPACTION_TRIGGER_CHARS = 48_000
KEEP_RAW_TAIL = 6  # keep last N messages verbatim after compaction

_current: ContextVar[Optional["SessionState"]] = ContextVar("session_state", default=None)


def get_session_state() -> Optional["SessionState"]:
    return _current.get()


def set_session_state(state: Optional["SessionState"]):
    return _current.set(state)


def reset_session_state(token) -> None:
    _current.reset(token)


@dataclass
class FileCacheEntry:
    content: str
    sha256: str
    turn: int
    stale: bool = False


@dataclass
class SessionState:
    workspace_root: Optional[str] = None
    top_level_entries: Optional[list[str]] = None
    file_cache: dict[str, FileCacheEntry] = field(default_factory=dict)
    dir_cache: dict[str, str] = field(default_factory=dict)
    todo_plan: Optional[list[str]] = None
    turn_count: int = 0
    tool_calls_this_turn: int = 0
    files_touched: list[str] = field(default_factory=list)
    edits_log: list[str] = field(default_factory=list)
    outcomes: list[str] = field(default_factory=list)
    cache_hits: int = 0
    cache_misses: int = 0

    def begin_turn(self) -> None:
        self.turn_count += 1
        self.tool_calls_this_turn = 0

    def note_tool_call(self) -> None:
        self.tool_calls_this_turn += 1

    def build_digest(self) -> str:
        lines = ["[session context — do not re-fetch unless marked stale]"]
        if self.workspace_root:
            lines.append(f"workspace_root: {self.workspace_root}")
            if self.top_level_entries is not None:
                top = self.top_level_entries[:40]
                extra = len(self.top_level_entries) - len(top)
                suffix = f" (+{extra} more)" if extra > 0 else ""
                lines.append(f"top_level: {top}{suffix}")
        fresh = [p for p, e in self.file_cache.items() if not e.stale]
        stale = [p for p, e in self.file_cache.items() if e.stale]
        if fresh:
            lines.append(
                "already-read files (cached, do NOT re-read unless task needs a fresh view): "
                + ", ".join(fresh[:30])
            )
        if stale:
            lines.append("stale after edit (re-read only if you need current content): " + ", ".join(stale[:20]))
        if self.todo_plan:
            lines.append("active plan: " + " | ".join(self.todo_plan[:12]))
        if self.edits_log:
            lines.append("recent edits: " + "; ".join(self.edits_log[-5:]))
        return "\n".join(lines)

    def set_workspace(self, root: str, entries: list[str]) -> None:
        self.workspace_root = root
        self.top_level_entries = list(entries)

    def get_cached_file(self, path: str) -> Optional[str]:
        ent = self.file_cache.get(path)
        if ent and not ent.stale:
            self.cache_hits += 1
            return ent.content
        self.cache_misses += 1
        return None

    def put_file(self, path: str, content: str) -> None:
        digest = hashlib.sha256(content.encode("utf-8", errors="replace")).hexdigest()[:16]
        self.file_cache[path] = FileCacheEntry(
            content=content, sha256=digest, turn=self.turn_count, stale=False
        )
        if path not in self.files_touched:
            self.files_touched.append(path)

    def mark_stale(self, path: str) -> None:
        ent = self.file_cache.get(path)
        if ent:
            ent.stale = True
        self.dir_cache.pop(path, None)
        # parent dir listing may be stale if create/delete
        parent = path.rsplit("/", 1)[0] if "/" in path else "."
        self.dir_cache.pop(parent, None)
        if path not in self.files_touched:
            self.files_touched.append(path)

    def record_edit(self, path: str, summary: str) -> None:
        self.edits_log.append(f"{path}: {summary[:80]}")
        if len(self.edits_log) > 20:
            self.edits_log = self.edits_log[-20:]

    def record_outcome(self, text: str) -> None:
        if text:
            self.outcomes.append(text[:200])
            if len(self.outcomes) > 10:
                self.outcomes = self.outcomes[-10:]

    def history_summary(self) -> str:
        return (
            f"Files touched: {self.files_touched[-30:]}\n"
            f"Edits: {self.edits_log[-10:]}\n"
            f"Outcomes: {self.outcomes[-5:]}"
        )


def estimate_message_chars(messages: list[dict]) -> int:
    n = 0
    for m in messages:
        c = m.get("content")
        if isinstance(c, str):
            n += len(c)
        tr = m.get("tool_results")
        if tr:
            for r in tr:
                n += len(str(r.get("result", "")))
        tc = m.get("tool_calls")
        if tc:
            n += len(str(tc))
    return n


def compact_messages(
    messages: list[dict],
    state: Optional[SessionState] = None,
    trigger_chars: int = COMPACTION_TRIGGER_CHARS,
    keep_tail: int = KEEP_RAW_TAIL,
) -> list[dict]:
    """Rule-based compaction: shrink old tool results when history grows large."""
    if not messages or estimate_message_chars(messages) < trigger_chars:
        return messages

    if len(messages) <= keep_tail + 2:
        return _shrink_tool_payloads(messages, aggressive=False)

    head, tail = messages[:-keep_tail], messages[-keep_tail:]
    summary_bits = []
    if state:
        summary_bits.append(state.history_summary())
    files = set()
    tools_used = set()
    for m in head:
        for tc in m.get("tool_calls") or []:
            tools_used.add(tc.get("name", "?"))
            args = tc.get("arguments") or {}
            if isinstance(args, dict) and args.get("path"):
                files.add(str(args["path"]))
        for tr in m.get("tool_results") or []:
            tools_used.add(tr.get("tool", "?"))
            # scrape path-like tokens from short results
            res = str(tr.get("result", ""))[:300]
            for p in re.findall(r"[\w./-]+\.(?:py|js|ts|md|json|txt)", res):
                files.add(p)

    summary = {
        "role": "user",
        "content": (
            "[compacted earlier turns]\n"
            + (summary_bits[0] + "\n" if summary_bits else "")
            + f"Tools used: {sorted(tools_used)}\n"
            f"Paths seen: {sorted(files)[:40]}\n"
            "Raw tool payloads for those turns were dropped to save context."
        ),
    }
    # Keep first user message if present
    prefix = []
    if head and head[0].get("role") == "user":
        first = dict(head[0])
        content = first.get("content") or ""
        if len(content) > 500:
            first["content"] = content[:500] + "…[truncated]"
        prefix = [first]

    compacted = prefix + [summary] + _shrink_tool_payloads(tail, aggressive=False)
    return compacted


def _shrink_tool_payloads(messages: list[dict], *, aggressive: bool) -> list[dict]:
    out = []
    limit = 400 if aggressive else 1200
    for m in messages:
        nm = dict(m)
        if nm.get("tool_results"):
            shrunk = []
            for r in nm["tool_results"]:
                rr = dict(r)
                res = str(rr.get("result", ""))
                if len(res) > limit:
                    rr["result"] = res[:limit] + f"…[truncated {len(res) - limit} chars]"
                shrunk.append(rr)
            nm["tool_results"] = shrunk
        c = nm.get("content")
        if isinstance(c, str) and len(c) > 2000 and aggressive:
            nm["content"] = c[:2000] + "…[truncated]"
        out.append(nm)
    return out


def observe_tool_result(state: SessionState, tool: str, arguments: Any, result: str, ok: bool) -> None:
    """Update caches from a completed tool call."""
    state.note_tool_call()
    path = _extract_path(arguments)
    if tool == "get_workspace_info" and ok:
        root, entries = _parse_workspace_info(result)
        if root:
            state.set_workspace(root, entries or [])
    elif tool == "read_file" and ok and path:
        # Don't cache partial reads as full-file truth if offset/limit present
        if not _is_partial_read(arguments):
            state.put_file(path, result)
    elif tool == "list_files" and ok and path:
        state.dir_cache[path or "."] = result
    elif tool in ("edit_file", "write_to_file") and path:
        if ok:
            state.mark_stale(path)
            state.record_edit(path, result.split("\n", 1)[0][:100])
            # If edit returned full content somehow we don't have it; leave stale
        else:
            state.mark_stale(path)
    elif tool == "todo_write" and ok:
        plan = _parse_todo(arguments)
        if plan is not None:
            state.todo_plan = plan
    elif tool == "todo_read" and ok and result and not result.startswith("(No plan"):
        lines = [ln.strip() for ln in result.splitlines() if ln.strip().startswith("[")]
        if lines:
            state.todo_plan = lines


def _extract_path(arguments: Any) -> Optional[str]:
    if isinstance(arguments, str):
        # bare path string
        if arguments and "\n" not in arguments and len(arguments) < 400:
            return arguments.strip()
        return None
    if isinstance(arguments, dict):
        p = arguments.get("path") or arguments.get("file") or arguments.get("input")
        return str(p) if p else None
    return None


def _is_partial_read(arguments: Any) -> bool:
    if not isinstance(arguments, dict):
        return False
    return bool(arguments.get("offset") or arguments.get("limit"))


def _parse_workspace_info(text: str) -> tuple[Optional[str], Optional[list[str]]]:
    root = None
    entries = None
    m = re.search(r"Workspace root[^:]*:\s*(.+)", text)
    if m:
        root = m.group(1).strip()
    m2 = re.search(r"Top-level entries:\s*(\[.*\])", text, re.S)
    if m2:
        try:
            import ast
            entries = list(ast.literal_eval(m2.group(1)))
        except Exception:
            entries = None
    return root, entries


def _parse_todo(arguments: Any) -> Optional[list[str]]:
    if not isinstance(arguments, dict):
        return None
    items = arguments.get("items")
    if isinstance(items, list):
        return [str(i) for i in items]
    return None
