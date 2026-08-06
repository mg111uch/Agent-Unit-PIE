from __future__ import annotations

import os
import threading
from dataclasses import dataclass
from agent_core.config import WORKSPACE_BASE, EXCLUDE_DIRS

WORKSPACE_ROOT = os.path.abspath(
    os.getenv("AGENT_WORKSPACE_ROOT", os.getcwd())
)
os.makedirs(WORKSPACE_ROOT, exist_ok=True)

_user_context = threading.local()


def set_user_workspace(user_id: str) -> str:
    if user_id == "local":
        _user_context.root = WORKSPACE_ROOT
        return WORKSPACE_ROOT
    root = os.path.join(WORKSPACE_BASE, str(user_id))
    os.makedirs(root, exist_ok=True)
    _user_context.root = root
    return root


def get_user_workspace_root() -> str | None:
    return getattr(_user_context, "root", None)


def clear_user_context():
    _user_context.root = None


class PathEscapeError(ValueError):
    pass


def resolve(path: str) -> str:
    if path is None:
        raise PathEscapeError("path is required")

    root = get_user_workspace_root() or WORKSPACE_ROOT
    cleaned = path.strip()

    # Absolute path — use directly if within workspace
    if os.path.isabs(cleaned):
        real_path = os.path.realpath(cleaned)
        real_root = os.path.realpath(root)
        if os.path.commonpath([real_path, real_root]) != real_root:
            raise PathEscapeError(
                f"'{path}' resolves outside the workspace ({root}). "
                f"Use a path relative to the workspace root, e.g. 'src/app.py'."
            )
        return real_path

    cleaned = cleaned.lstrip("/\\")
    if cleaned in ("", "."):
        cleaned = "."

    full_path = os.path.abspath(os.path.join(root, cleaned))

    if os.path.commonpath([full_path, root]) != root:
        raise PathEscapeError(
            f"'{path}' resolves outside the workspace ({root}). "
            f"Use a path relative to the workspace root, e.g. 'src/app.py'."
        )
    return full_path


def to_relative(full_path: str) -> str:
    root = get_user_workspace_root() or WORKSPACE_ROOT
    return os.path.relpath(full_path, root)


_EXCLUDE_SET = set(EXCLUDE_DIRS)


@dataclass
class PathResolution:
    ok: bool
    full: str = ""
    rel: str = ""
    message: str = ""


def _matches_expect(full: str, expect: str) -> bool:
    if expect == "file":
        return os.path.isfile(full)
    if expect == "dir":
        return os.path.isdir(full)
    return os.path.exists(full)


def _ends_with_suffix(rel: str, suffix: str) -> bool:
    if rel == suffix:
        return True
    return rel.endswith("/" + suffix)


def _fuzzy_suffix_search(root: str, cleaned: str, expect: str) -> PathResolution | None:
    """Find an existing entry whose relative path ends with the given path.

    Depth-wise: only the shallowest depth group is considered. A single match
    wins; multiple matches at the shallowest depth fail with a candidate list.
    """
    parts = [p for p in cleaned.split("/") if p not in ("", ".")]
    if not parts:
        return None
    suffix = "/".join(parts)
    min_depth = len(parts)
    max_depth = min(16, min_depth + 8)
    matches: dict[int, set[str]] = {}
    for dirpath, dirnames, filenames in os.walk(root):
        dirnames[:] = [d for d in sorted(dirnames) if d not in _EXCLUDE_SET]
        depth = 0 if dirpath == root else dirpath[len(root.rstrip(os.sep)):].count(os.sep)
        for fn in filenames:
            rel = os.path.relpath(os.path.join(dirpath, fn), root)
            if _ends_with_suffix(rel, suffix):
                matches.setdefault(len(rel.split(os.sep)), set()).add(rel)
        if expect in ("dir", "any"):
            for dn in dirnames:
                rel = os.path.relpath(os.path.join(dirpath, dn), root)
                if _ends_with_suffix(rel, suffix):
                    matches.setdefault(len(rel.split(os.sep)), set()).add(rel)
        if depth > max_depth:
            dirnames[:] = []
    if not matches:
        return None
    shallowest = min(matches)
    candidates = sorted(matches[shallowest])
    if len(candidates) == 1:
        full = os.path.join(root, candidates[0])
        if expect != "any" and not _matches_expect(full, expect):
            return None
        return PathResolution(ok=True, full=full, rel=candidates[0])
    return PathResolution(
        ok=False,
        message=(
            f"Multiple matches for '{cleaned}' — be more specific:\n"
            + "\n".join(f"  {c}" for c in candidates)
        ),
    )


def resolve_for_tool(path, expect: str = "any") -> PathResolution:
    """Tolerantly resolve a user-supplied path for tool calls.

    expect: 'file' | 'dir' | 'any' (must exist) | 'target' (need not exist,
    no fuzzy search — used for create).
    """
    if path is None or not str(path).strip():
        return PathResolution(ok=False, message="path is required")
    cleaned = str(path).strip()
    root = get_user_workspace_root() or WORKSPACE_ROOT
    base = os.path.basename(root)
    full = None
    try:
        full = resolve(cleaned)
    except PathEscapeError:
        full = None

    if expect == "target":
        if full is not None:
            return PathResolution(ok=True, full=full, rel=to_relative(full))
        stripped = cleaned[len(base) + 1:] if cleaned.startswith(base + "/") else None
        try:
            best = resolve(stripped or cleaned)
            return PathResolution(ok=True, full=best, rel=to_relative(best))
        except PathEscapeError as e:
            return PathResolution(ok=False, message=str(e))

    if full is not None and _matches_expect(full, expect):
        return PathResolution(ok=True, full=full, rel=to_relative(full))

    if cleaned.startswith(base + "/"):
        try:
            sfull = resolve(cleaned[len(base) + 1:])
        except PathEscapeError:
            sfull = None
        if sfull is not None and _matches_expect(sfull, expect):
            return PathResolution(ok=True, full=sfull, rel=to_relative(sfull))
        full = full or sfull

    found = _fuzzy_suffix_search(root, cleaned, expect)
    if found is not None:
        return found

    if full is not None and os.path.exists(full):
        kind = "a directory" if os.path.isdir(full) else "a file"
        return PathResolution(
            ok=False,
            message=f"'{path}' resolves to {to_relative(full)} which is {kind}, expected {expect}.",
        )
    return PathResolution(
        ok=False,
        message=not_found_message(
            path, full or os.path.join(root, cleaned), to_relative(full or os.path.join(root, cleaned))
        ),
    )


def root_basename_hint(path: str) -> str:
    """If path starts with workspace root basename, suggest corrected version."""
    root = get_user_workspace_root() or WORKSPACE_ROOT
    basename = os.path.basename(root)
    cleaned = path.strip().lstrip("/\\")
    if cleaned == basename or cleaned.startswith(basename + "/"):
        alt = cleaned[len(basename):].lstrip("/\\")
        if not alt:
            alt = "."
        return f"\n(Hint: paths are relative to the workspace root. Try '{alt}' instead of '{cleaned}'.)"
    return ""


def not_found_message(path: str, full: str, rel: str) -> str:
    """Standard 'file not found' error block shared by read/edit tools."""
    parent = os.path.dirname(full) or WORKSPACE_ROOT
    nearby = []
    if os.path.isdir(parent):
        nearby = sorted(os.listdir(parent))[:20]
    hint = root_basename_hint(path)
    return (
        f"file not found: {path}\n"
        f"Resolved to: {rel} (workspace-relative)\n"
        f"Files in that directory: {nearby if nearby else '(directory does not exist)'}"
        f"{hint}"
    )
