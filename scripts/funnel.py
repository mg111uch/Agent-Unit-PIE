"""Funnel CLI (REV-01). Local sources by default; pass a captured FireFlow
payload with --ff to fill contacted/responses/proposals/pilots/won.

    conda run -n myenv python scripts/funnel.py
    conda run -n myenv python scripts/funnel.py --json
"""
from __future__ import annotations

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "codebase"))

from modules.economy.funnel_report import main  # noqa: E402

if __name__ == "__main__":
    raise SystemExit(main())
