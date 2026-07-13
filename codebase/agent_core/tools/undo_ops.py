"""Checkpoint/undo system: save file snapshots before destructive edits."""

from __future__ import annotations

import hashlib
import json
import os
import shutil
from pathlib import Path
from agent_core.config import ENABLE_CHECKPOINTS, MAX_CHECKPOINTS
from agent_core.workspace import WORKSPACE_ROOT, resolve, to_relative, PathEscapeError

CHECKPOINT_DIR = os.path.join(WORKSPACE_ROOT, ".agent_checkpoints")
CHECKPOINT_INDEX = os.path.join(CHECKPOINT_DIR, "index.json")


def _ensure_checkpoint_dir():
    os.makedirs(CHECKPOINT_DIR, exist_ok=True)


def _load_index() -> list[dict]:
    _ensure_checkpoint_dir()
    if not os.path.exists(CHECKPOINT_INDEX):
        return []
    try:
        with open(CHECKPOINT_INDEX, "r") as f:
            return json.load(f)
    except Exception:
        return []


def _save_index(index: list[dict]):
    _ensure_checkpoint_dir()
    with open(CHECKPOINT_INDEX, "w") as f:
        json.dump(index, f, indent=2)


def _trim_index(index: list[dict]):
    while len(index) > MAX_CHECKPOINTS:
        oldest = index.pop(0)
        ckpt_path = os.path.join(CHECKPOINT_DIR, oldest.get("file", ""))
        if os.path.exists(ckpt_path):
            try:
                os.remove(ckpt_path)
            except Exception:
                pass


def _hash_file(path: str) -> str:
    try:
        with open(path, "rb") as f:
            return hashlib.md5(f.read()).hexdigest()
    except Exception:
        return ""


def save_checkpoint(file_path: str) -> str | None:
    """Save a checkpoint of the given file before modifying it.
    Returns the checkpoint filename if saved, None if skipped.
    """
    if not ENABLE_CHECKPOINTS:
        return None
    try:
        full = resolve(file_path)
        if not os.path.exists(full):
            return None

        _ensure_checkpoint_dir()
        rel_path = to_relative(full)
        file_hash = _hash_file(full)
        ckpt_name = f"{rel_path.replace('/', '__')}__{file_hash[:12]}.ckpt"
        ckpt_path = os.path.join(CHECKPOINT_DIR, ckpt_name)

        if os.path.exists(ckpt_path):
            return ckpt_name

        shutil.copy2(full, ckpt_path)

        index = _load_index()
        index.append({
            "file": rel_path,
            "checkpoint": ckpt_name,
            "hash": file_hash,
            "timestamp": __import__("time").time(),
        })
        _trim_index(index)
        _save_index(index)
        return ckpt_name
    except PathEscapeError:
        return None
    except Exception:
        return None


def undo_last_edit(file_path: str | None = None) -> str:
    """Restore the most recent checkpoint for a file, or the most recent overall.

    input_data = {"path": "optional/path"} — if omitted, returns latest checkpoint info.
    """
    if not ENABLE_CHECKPOINTS:
        return "Checkpoints are disabled. Set enable_checkpoints: true in config.json."

    index = _load_index()
    if not index:
        return "No checkpoints available."

    if file_path:
        try:
            rel = to_relative(resolve(file_path))
        except PathEscapeError as e:
            return f"Error: {e}"

        candidates = [c for c in reversed(index) if c["file"] == rel]
        if not candidates:
            return f"No checkpoint found for: {file_path}"
        entry = candidates[0]
    else:
        entry = index[-1]

    ckpt_path = os.path.join(CHECKPOINT_DIR, entry["checkpoint"])
    if not os.path.exists(ckpt_path):
        return f"Checkpoint file not found: {entry['checkpoint']}"

    try:
        target = resolve(entry["file"])
        os.makedirs(os.path.dirname(target), exist_ok=True)
        shutil.copy2(ckpt_path, target)
        return f"Restored {entry['file']} from checkpoint {entry['checkpoint'][:20]}..."
    except PathEscapeError as e:
        return f"Error: {e}"
    except Exception as e:
        return f"Error restoring checkpoint: {e}"


def checkpoint_info() -> str:
    """Return summary of available checkpoints."""
    index = _load_index()
    if not index:
        return "No checkpoints yet."
    lines = [f"Checkpoints ({len(index)}):"]
    for entry in reversed(index[-10:]):
        lines.append(f"  {entry['file']} @ {entry['checkpoint'][:20]}...")
    return "\n".join(lines)
