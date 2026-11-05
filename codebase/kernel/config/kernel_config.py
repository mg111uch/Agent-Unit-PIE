import os
from pathlib import Path

# OPS-06: paths come from env so tests and deployments never share a store.
_DEFAULT_DATA_ROOT = Path(__file__).resolve().parent.parent.parent.parent / "data"
DATA_ROOT = Path(os.environ.get("PIE_DATA_ROOT", str(_DEFAULT_DATA_ROOT)))

# Working memory TTLs (seconds)
BELIEF_SHIFT_TTL = 7200
CONTRADICTION_TTL = 14400
CONFIDENCE_CHANGE_TTL = 3600

# Pattern detection defaults
PATTERN_IMPORTANCE = 0.9
PATTERN_CONFIDENCE = 0.9

# Hypothesis confidence nudges
HYPOTHESIS_CONFIDENCE_BUMP = 0.05
HYPOTHESIS_CONFIDENCE_PENALTY = 0.05