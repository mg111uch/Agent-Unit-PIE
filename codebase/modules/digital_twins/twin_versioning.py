"""Twin versioning via kernel-validity semantics (ACTIVE->HISTORICAL).

Mirrors kernel/validity.py status blocks on twin version records:
bump records changed_variables + source_changes and retires the
previous version to HISTORICAL. mark_stale_findings itself stays
sim-scoped; twins reuse the invalidation convention, not a rewrite.
"""
from __future__ import annotations

from typing import Any, Dict, List

STATUS_ACTIVE = "ACTIVE"
STATUS_HISTORICAL = "HISTORICAL"


def version_id(city_id: str, n: int) -> str:
    return f"{city_id}_twin_v{n}"


def initial_version(city_id: str) -> Dict[str, Any]:
    return {
        "version_id": version_id(city_id, 1),
        "city_id": city_id,
        "changed_variables": [],
        "source_changes": [],
        "validity": {"status": STATUS_ACTIVE},
    }


def bump_version(
    city_id: str,
    current_n: int,
    changed_variables: List[str],
    source_changes: List[str],
) -> Dict[str, Any]:
    """Retire vN as HISTORICAL, open vN+1 as ACTIVE. Returns both."""
    old_id = version_id(city_id, current_n)
    new_id = version_id(city_id, current_n + 1)
    superseded = {
        "version_id": old_id,
        "city_id": city_id,
        "validity": {
            "status": STATUS_HISTORICAL,
            "invalidated_by": new_id,
            "changed_variables": list(changed_variables),
            "source_changes": list(source_changes),
        },
    }
    current = {
        "version_id": new_id,
        "city_id": city_id,
        "changed_variables": list(changed_variables),
        "source_changes": list(source_changes),
        "validity": {"status": STATUS_ACTIVE, "supersedes": old_id},
    }
    return {"current": current, "superseded": superseded}
