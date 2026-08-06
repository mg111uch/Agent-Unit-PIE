"""AST-based navigation tools: file_skeleton (structure) + who_imports (import graph).

Both are atlas-free (pure stdlib `ast` on on-disk files) — complements the code_rag
tools which read the stale-able atlas DB. Both accept `paths` as a single string
or a list of strings.
"""

from __future__ import annotations

import ast
import os
import re

from agent_core.config import EXCLUDE_DIRS
from agent_core.workspace import WORKSPACE_ROOT, resolve, resolve_for_tool, to_relative, PathEscapeError
from agent_core.tools.types import ToolResult

_exclude_set = set(EXCLUDE_DIRS)
_CAP = 15
_DEF_RE = re.compile(r"^\s*(?:def|fn|function|func|class|struct|interface|trait)\s+(\w+)")


def _get_paths(params) -> list[str] | None:
    paths = (params or {}).get("paths")
    if isinstance(paths, str):
        paths = [paths]
    if not paths or not isinstance(paths, list) or not all(isinstance(p, str) and p for p in paths):
        return None
    return paths


def _fmt_import(node) -> str:
    if isinstance(node, ast.Import):
        parts = []
        for alias in node.names:
            name = alias.name
            if alias.asname:
                name += f" as {alias.asname}"
            parts.append(name)
        return ", ".join(parts)
    module = node.module or ""
    prefix = "." * node.level
    if node.level:
        module = prefix + module
    if not node.names:
        return module
    names = ", ".join(a.name + (f" as {a.asname}" if a.asname else "") for a in node.names)
    return f"{module} import {names}"


def _collect_imports(tree) -> tuple[list[str], list[str]]:
    """Return (eager, lazy) import statements as compact strings.

    eager = imports directly at module level; lazy = imports nested inside any
    def/class body (run at call time, not import time).
    """
    eager = []
    lazy = []
    seen_e = set()
    seen_l = set()

    def add(dest, seen, s):
        if s not in seen:
            seen.add(s)
            dest.append(s)

    for node in tree.body:
        if isinstance(node, (ast.Import, ast.ImportFrom)):
            add(eager, seen_e, _fmt_import(node))
        elif isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef, ast.ClassDef)):
            for n in ast.walk(node):
                if isinstance(n, (ast.Import, ast.ImportFrom)):
                    add(lazy, seen_l, _fmt_import(n))
    return eager, lazy


def _sig(node) -> str:
    try:
        args = ast.unparse(node.args)
    except Exception:
        args = ""
    ret = ""
    if node.returns is not None:
        try:
            ret = " -> " + ast.unparse(node.returns)
        except Exception:
            pass
    return f"({args}){ret}"


def _clip(items: list[str], cap: int = _CAP) -> str:
    if not items:
        return "none"
    shown = ", ".join(items[:cap])
    if len(items) > cap:
        shown += f" (+{len(items) - cap} more)"
    return shown


def _doc_hint(node) -> str:
    doc = ast.get_docstring(node)
    if not doc:
        return ""
    first = doc.splitlines()[0].strip()
    if len(first) > 60:
        first = first[:60] + "..."
    return f"  —  {first}"


def _skeleton_py(source: str, rel: str) -> list[str]:
    try:
        tree = ast.parse(source)
    except SyntaxError as e:
        return [f"--- {rel} ---", f"ERROR: syntax error (line {e.lineno}): {e.msg}"]

    eager, lazy = _collect_imports(tree)
    lines = [
        f"--- {rel} ({len(source.splitlines())} lines) ---",
        f"imports eager ({len(eager)}): {_clip(eager)}",
        f"imports lazy  ({len(lazy)}): {_clip(lazy)}",
    ]
    globals_ = []
    for node in tree.body:
        if isinstance(node, ast.Assign):
            globals_.extend(t.id for t in node.targets if isinstance(t, ast.Name))
        elif isinstance(node, (ast.AnnAssign, ast.AugAssign)) and isinstance(node.target, ast.Name):
            globals_.append(node.target.id)
    lines.append(f"globals ({len(globals_)}): {_clip(globals_)}")

    classes = []
    functions = []
    for node in tree.body:
        if isinstance(node, ast.ClassDef):
            methods = [n.name for n in node.body
                       if isinstance(n, (ast.FunctionDef, ast.AsyncFunctionDef))]
            line = f"  {node.name}  L{node.lineno}-{node.end_lineno}  ({len(methods)} methods)"
            if methods:
                line += ": " + _clip(methods, 8)
            line += _doc_hint(node)
            classes.append(line)
        elif isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)):
            line = f"  {node.name}{_sig(node)}  L{node.lineno}-{node.end_lineno}"
            line += _doc_hint(node)
            functions.append(line)

    if classes:
        lines.append(f"classes ({len(classes)}):")
        lines.extend(classes)
    if functions:
        lines.append(f"functions ({len(functions)}):")
        lines.extend(functions)
    return lines


def _skeleton_other(source: str, rel: str) -> list[str]:
    total = len(source.splitlines())
    defs = [(i + 1, m.group(1)) for i, line in enumerate(source.splitlines())
            if (m := _DEF_RE.search(line))]
    lines = [f"--- {rel} ({total} lines, non-Python skeleton) ---"]
    if defs:
        lines.append(f"definitions ({len(defs)}):")
        lines.extend(f"  {name}  L{ln}" for ln, name in defs[:_CAP])
        if len(defs) > _CAP:
            lines.append(f"  ... (+{len(defs) - _CAP} more)")
    else:
        lines.append("definitions (0): none detected")
    return lines


def _skeleton_for(full: str, rel: str) -> list[str]:
    try:
        with open(full, "r", encoding="utf-8", errors="replace") as f:
            source = f.read()
    except OSError as e:
        return [f"--- {rel} ---", f"ERROR: {e}"]
    if rel.endswith(".py"):
        return _skeleton_py(source, rel)
    return _skeleton_other(source, rel)


def file_skeleton(input_data=None) -> ToolResult:
    """Compact structural map of Python (or other) files via AST — imports, globals,
    classes, functions with line ranges. Atlas-free; use instead of full reads for orientation.
    input_data = {"paths": "engine.py"} or {"paths": ["a.py", "b.py"]}
    """
    try:
        params = input_data if isinstance(input_data, dict) else (input_data or {})
        paths = _get_paths(params)
        if not paths:
            return ToolResult(ok=False, message="'paths' is required: a single path string or list of paths.")
        blocks = []
        ok_count = 0
        for p in paths:
            res = resolve_for_tool(p, expect="file")
            if not res.ok:
                blocks.append(f"--- {p} ---\nERROR: {res.message}")
                continue
            full, rel = res.full, res.rel
            ok_count += 1
            blocks.append("\n".join(_skeleton_for(full, rel)))
        return ToolResult(ok=ok_count > 0, data="\n\n".join(blocks))
    except PathEscapeError as e:
        return ToolResult(ok=False, message=str(e))
    except Exception as e:
        return ToolResult(ok=False, message=f"file_skeleton error: {e}")


# ── who_imports ─────────────────────────────────────────────────────

_import_cache: dict[str, tuple[float, set[str]]] = {}


def _module_of(rel: str) -> str:
    parts = rel.split(os.sep)
    if parts[-1] == "__init__.py":
        parts = parts[:-1]
    else:
        parts[-1] = parts[-1][:-3]
    return ".".join(parts)


def _import_targets(full: str, rel: str) -> set[str]:
    """Set of module names this file imports (resolves relative imports)."""
    try:
        with open(full, "r", encoding="utf-8", errors="replace") as f:
            tree = ast.parse(f.read())
    except (OSError, SyntaxError):
        return set()
    own = _module_of(rel).split(".")
    targets: set[str] = set()

    def resolve_from(level: int, module: str, name: str = "") -> str:
        if level <= 0:
            base = module or ""
        else:
            base = ".".join(own[:-level] if level <= len(own) else [])
            if module:
                base = f"{base}.{module}" if base else module
        if name:
            return f"{base}.{name}" if base else name
        return base or name

    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            for alias in node.names:
                targets.add(alias.name.split(".")[0])
                targets.add(alias.name)
        elif isinstance(node, ast.ImportFrom):
            base = resolve_from(node.level, node.module or "")
            if base:
                targets.add(base)
            for alias in node.names:
                if base:
                    targets.add(f"{base}.{alias.name}")
                else:
                    targets.add(alias.name)
    return targets


def _targets_cached(full: str, rel: str) -> set[str]:
    try:
        mtime = os.path.getmtime(full)
    except OSError:
        return set()
    cached = _import_cache.get(rel)
    if cached and cached[0] == mtime:
        return cached[1]
    targets = _import_targets(full, rel)
    _import_cache[rel] = (mtime, targets)
    return targets


def _scan_workspace() -> dict[str, set[str]]:
    """module_name -> set of importer rel paths (workspace .py files only)."""
    index: dict[str, set[str]] = {}
    for root, dirs, files in os.walk(WORKSPACE_ROOT):
        dirs[:] = [d for d in sorted(dirs) if d not in _exclude_set and not d.startswith(".")]
        for fn in sorted(files):
            if not fn.endswith(".py"):
                continue
            fpath = os.path.join(root, fn)
            rel = os.path.relpath(fpath, WORKSPACE_ROOT)
            for target in _targets_cached(fpath, rel):
                index.setdefault(target, set()).add(rel)
    return index


def who_imports(input_data=None) -> ToolResult:
    """For each file: what it imports (eager/lazy) and which workspace files import it.
    Module-level import graph; complements symbol-level get_callers_callees.
    input_data = {"paths": "agent_core/loop/engine.py"} or {"paths": [...]}
    """
    try:
        params = input_data if isinstance(input_data, dict) else (input_data or {})
        paths = _get_paths(params)
        if not paths:
            return ToolResult(ok=False, message="'paths' is required: a single path string or list of paths.")
        index = _scan_workspace()
        blocks = []
        for p in paths:
            res = resolve_for_tool(p, expect="file")
            if not res.ok:
                blocks.append(f"--- {p} ---\nERROR: {res.message}")
                continue
            full, rel = res.full, res.rel
            if not rel.endswith(".py"):
                blocks.append(f"--- {rel} ---\n(non-Python file — no import graph)")
                continue
            try:
                with open(full, "r", encoding="utf-8", errors="replace") as f:
                    tree = ast.parse(f.read())
            except SyntaxError as e:
                blocks.append(f"--- {rel} ---\nERROR: syntax error (line {e.lineno}): {e.msg}")
                continue
            eager, lazy = _collect_imports(tree)
            module = _module_of(rel)
            leaf = module.rsplit(".", 1)[-1]
            importers = sorted(set(index.get(module, set())) | set(index.get(leaf, set())))
            blocks.append(
                f"--- {rel} ---\n"
                f"module: {module}\n"
                f"imports eager ({len(eager)}): {_clip(eager)}\n"
                f"imports lazy  ({len(lazy)}): {_clip(lazy)}\n"
                f"imported_by ({len(importers)}): {_clip(importers)}"
            )
        return ToolResult(ok=True, data="\n\n".join(blocks))
    except PathEscapeError as e:
        return ToolResult(ok=False, message=str(e))
    except Exception as e:
        return ToolResult(ok=False, message=f"who_imports error: {e}")
