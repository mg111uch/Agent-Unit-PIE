"""CityState: every field = value+timestamp+source+quality+confidence+geography."""
from __future__ import annotations

import copy
from datetime import datetime, timezone
from typing import Any, Dict

# TWN-01: the ten series worth collecting per city. Coverage is measured on
# this list, so adding a field makes the gap visible instead of optional.
FIELDS = (
    "population",
    "employment_rate",
    "industrial_units",
    "industrial_capacity",
    "water_supply_mld",
    "energy_reliability",
    "power_supply_hours",
    "air_quality_pm25",
    "road_km",
    "municipal_budget_cr",
)

TRUTH = (
    "OBSERVED",
    "TRANSACTION_DERIVED",
    "THIRD_PARTY_VERIFIED",
    "OWNER_REPORTED",
    "AI_INFERRED",
    "SIMULATED",
)


def infer_truth(source: str) -> str:
    s = str(source or "").lower()
    if "placeholder" in s or "slice" in s or "survey" in s:
        return "AI_INFERRED"
    if "census" in s or "cpcb" in s or "plfs" in s:
        return "THIRD_PARTY_VERIFIED"
    if "fireflow" in s or "kernel" in s or "observation" in s or "sensor" in s:
        return "OBSERVED"
    if "tx" in s or "ledger" in s or "transaction" in s:
        return "TRANSACTION_DERIVED"
    if "sim" in s:
        return "SIMULATED"
    if "kmc" in s or "djb" in s or "discom" in s or "dda" in s:
        return "OWNER_REPORTED"
    return "AI_INFERRED"


def utc_now() -> str:
    return datetime.now(timezone.utc).isoformat()


def field(
    value: Any,
    source: str,
    quality: str = "reported",
    confidence: float = 0.5,
    geography: Any = None,
    timestamp: str = "",
    truth: str = "",
    **extra: Any,
) -> Dict[str, Any]:
    tier = truth if truth in TRUTH else infer_truth(source)
    return {
        "value": value,
        "timestamp": timestamp or utc_now(),
        "source": source,
        "quality": quality,
        "confidence": float(confidence),
        "geography": geography or {},
        "truth": tier,
        **extra,
    }


PLACEHOLDER_PREFIX = "placeholder:"


def is_placeholder(value: Dict[str, Any]) -> bool:
    """A field is a placeholder when its source says so, or it is AI_INFERRED."""
    src = str((value or {}).get("source", ""))
    return src.startswith(PLACEHOLDER_PREFIX) or \
        (value or {}).get("truth") == "AI_INFERRED"


def coverage(state: Dict[str, Any]) -> Dict[str, Any]:
    """TWN-01 answer: how much of a city is observed vs placeholder.

    Counts are over `FIELDS`, so a missing series is reported as missing rather
    than silently lowering the denominator.
    """
    fields = (state or {}).get("fields") or {}
    by_field, counts = {}, {"observed": 0, "placeholder": 0, "missing": 0}
    for name in FIELDS:
        v = fields.get(name)
        if not v:
            by_field[name] = "missing"
            counts["missing"] += 1
        elif is_placeholder(v):
            by_field[name] = "placeholder"
            counts["placeholder"] += 1
        else:
            by_field[name] = "observed"
            counts["observed"] += 1
    total = len(FIELDS)
    return {"city_id": (state or {}).get("city_id", ""),
            "series": total, **counts,
            "coverage": round(counts["observed"] / total, 3) if total else 0.0,
            "by_field": by_field,
            "complete": counts["observed"] == total}


def build_state(city_id: str, values: Dict[str, Dict[str, Any]]) -> Dict[str, Any]:
    return {
        "city_id": city_id,
        "fields": {
            k: field(**v) for k, v in (values or {}).items() if k in FIELDS
        },
    }


def snapshot_state(
    city_id: str, version_id: str, state: Dict[str, Any]
) -> Dict[str, Any]:
    return {
        "city_id": city_id,
        "version_id": version_id,
        "snapshot_at": utc_now(),
        "state": copy.deepcopy(state),
    }
