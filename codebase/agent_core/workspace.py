from __future__ import annotations

import os
import threading
from agent_core.config import WORKSPACE_BASE

WORKSPACE_ROOT = os.path.abspath(
    os.getenv("AGENT_WORKSPACE_ROOT", os.getcwd())
)
os.makedirs(WORKSPACE_ROOT, exist_ok=True)

_user_context = threading.local()


def set_user_workspace(user_id: str) -> str:
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
