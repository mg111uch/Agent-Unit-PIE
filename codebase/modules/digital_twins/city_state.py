"""CityState: every field = value+timestamp+source+quality+confidence+geography."""
from __future__ import annotations

import copy
from datetime import datetime, timezone
from typing import Any, Dict

FIELDS = (
    "population",
    "employment_rate",
    "industrial_capacity",
    "water_supply_mld",
    "energy_reliability",
    "literacy_rate",
    "air_quality_pm25",
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
    }


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
