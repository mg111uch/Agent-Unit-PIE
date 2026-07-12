from __future__ import annotations

import os

WORKSPACE_ROOT = os.path.abspath(
    os.getenv("AGENT_WORKSPACE_ROOT", os.getcwd())
)
os.makedirs(WORKSPACE_ROOT, exist_ok=True)


class PathEscapeError(ValueError):
    pass


def resolve(path: str) -> str:
    if path is None:
        raise PathEscapeError("path is required")

    cleaned = path.strip()
    cleaned = cleaned.lstrip("/\\")
    if cleaned in ("", "."):
        cleaned = "."

    full_path = os.path.abspath(os.path.join(WORKSPACE_ROOT, cleaned))

    if os.path.commonpath([full_path, WORKSPACE_ROOT]) != WORKSPACE_ROOT:
        raise PathEscapeError(
            f"'{path}' resolves outside the workspace ({WORKSPACE_ROOT}). "
            f"Use a path relative to the workspace root, e.g. 'src/app.py'."
        )
    return full_path


def to_relative(full_path: str) -> str:
    return os.path.relpath(full_path, WORKSPACE_ROOT)
