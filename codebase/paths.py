"""Workspace paths from the environment (OPS-06).

No personal absolute path belongs in code or docs. Everything derives from
`PIE_ROOT` (defaults to this repo) with `PIE_DATA_ROOT` / `FIREFLOW_ROOT`
overrides, so a copy of the repo runs anywhere.
"""
from __future__ import annotations

import os
from pathlib import Path

PIE_ROOT = Path(os.environ.get(
    "PIE_ROOT", str(Path(__file__).resolve().parent.parent))).resolve()
CODEBASE_ROOT = PIE_ROOT / "codebase"
DATA_ROOT = Path(os.environ.get("PIE_DATA_ROOT", str(PIE_ROOT / "data")))
FIREFLOW_ROOT = Path(os.environ.get(
    "FIREFLOW_ROOT", str(PIE_ROOT.parent / "reddit-clone")))
ATLAS_DIR = Path(os.environ.get("CODEBASE_ATLAS_DIR",
                                str(PIE_ROOT / "atlas_output")))


def resolve(value: str | Path) -> Path:
    """Expand `$VARS`/`~` and make relative paths relative to PIE_ROOT."""
    p = Path(os.path.expandvars(str(value))).expanduser()
    return p if p.is_absolute() else (PIE_ROOT / p)


def describe() -> dict:
    """What `doctor`/CI prints so a wrong root is obvious immediately."""
    return {"pie_root": str(PIE_ROOT), "codebase": str(CODEBASE_ROOT),
            "data": str(DATA_ROOT), "fireflow": str(FIREFLOW_ROOT),
            "atlas": str(ATLAS_DIR),
            "data_exists": DATA_ROOT.exists(),
            "fireflow_exists": FIREFLOW_ROOT.exists()}
