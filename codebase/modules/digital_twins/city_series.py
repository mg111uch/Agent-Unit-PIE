"""Real city series ingestion (TWN-01).

A human collects ten high-value series per city and writes them to JSON; this
module validates provenance (source, year, licence) and merges them into a
`CityState`, then reports placeholder vs observed counts.

No network, no scraping. A row without a source and a licence is rejected,
because an unsourced number is exactly the placeholder problem this fixes.

File shape (`data/twins/series/<city>.json`):

    {"city_id": "city_kanpur",
     "series": [
       {"field": "population", "value": 2767031, "source": "census_2011",
        "year": 2011, "license": "public-domain",
        "geography": {"wards": 110}},
       {"field": "road_km", "value": 1850, "source": "kmc_annual_2023",
        "year": 2023, "license": "govt-open"},
       ...]}
"""
from __future__ import annotations

import json
from pathlib import Path
from typing import Any, Dict, List, Optional

from modules.digital_twins import city_state

REQUIRED_KEYS = ("field", "value", "source", "year", "license")
MAX_PLACEHOLDER_AGE_YEARS = 12  # census-era data is fine; undated is not


def validate_row(row: Dict[str, Any],
                 current_year: int = 2026) -> Dict[str, Any]:
    missing = [k for k in REQUIRED_KEYS if row.get(k) in (None, "")]
    if missing:
        return {"ok": False, "reason": f"missing {','.join(missing)}"}
    if row["field"] not in city_state.FIELDS:
        return {"ok": False, "reason": f"unknown field {row['field']!r}"}
    try:
        year = int(row["year"])
    except (TypeError, ValueError):
        return {"ok": False, "reason": "year must be an integer"}
    if year > current_year + 1 or year < 1900:
        return {"ok": False, "reason": f"implausible year {year}"}
    try:
        float(row["value"])
    except (TypeError, ValueError):
        return {"ok": False, "reason": "value must be numeric"}
    if not str(row["license"]).strip():
        return {"ok": False, "reason": "licence is empty"}
    return {"ok": True, "stale": current_year - year > MAX_PLACEHOLDER_AGE_YEARS}


def load_file(path: str | Path, current_year: int = 2026) -> Dict[str, Any]:
    p = Path(path)
    if not p.exists():
        return {"ok": False, "error": f"{p} not found", "accepted": [],
                "rejected": []}
    try:
        doc = json.loads(p.read_text())
    except ValueError as e:
        return {"ok": False, "error": f"invalid JSON: {e}", "accepted": [],
                "rejected": []}
    city_id = doc.get("city_id") or p.stem
    accepted, rejected = [], []
    for i, row in enumerate(doc.get("series") or []):
        verdict = validate_row(row, current_year)
        if verdict["ok"]:
            accepted.append({**row, "stale": verdict.get("stale", False)})
        else:
            rejected.append({"index": i, "row": row, "reason": verdict["reason"]})
    if not accepted:
        return {"ok": False, "error": "no usable rows", "city_id": city_id,
                "accepted": [], "rejected": rejected}
    return {"ok": True, "city_id": city_id, "accepted": accepted,
            "rejected": rejected, "path": str(p)}


def _to_field(row: Dict[str, Any]) -> Dict[str, Any]:
    out = city_state.field(
        value=row["value"], source=row["source"],
        quality="observed" if not row.get("stale") else "dated",
        confidence=0.8 if not row.get("stale") else 0.6,
        geography=row.get("geography") or {},
        timestamp=f"{row['year']}-01-01T00:00:00+00:00",
        truth=row.get("truth") or "")
    # Keep provenance next to the value: a later reader must be able to check it.
    out["url"] = row.get("url", "")
    out["note"] = row.get("note", "")
    return out


def merge(city_id: str, base_values: Dict[str, Dict[str, Any]],
          rows: List[Dict[str, Any]]) -> Dict[str, Any]:
    """Real rows win over placeholders; placeholders survive where missing."""
    values = {k: dict(v) for k, v in (base_values or {}).items()}
    replaced = []
    for row in rows:
        if row["field"] in values and city_state.is_placeholder(values[row["field"]]):
            replaced.append(row["field"])
        values[row["field"]] = _to_field(row)
    state = city_state.build_state(city_id, values)
    return {"state": state, "replaced_placeholders": sorted(set(replaced)),
            "coverage": city_state.coverage(state)}


def ingest(path: str | Path, base_values: Dict[str, Dict[str, Any]],
           current_year: int = 2026) -> Dict[str, Any]:
    """File -> validated rows -> merged state + coverage report."""
    loaded = load_file(path, current_year)
    if not loaded["ok"]:
        base = city_state.build_state(Path(path).stem, base_values)
        return {**loaded, "coverage": city_state.coverage(base)}
    merged = merge(loaded["city_id"], base_values, loaded["accepted"])
    return {"ok": True, "city_id": loaded["city_id"],
            "rejected": loaded["rejected"],
            "series_loaded": len(loaded["accepted"]),
            **merged}


def coverage_table(states: Dict[str, Dict[str, Any]]) -> Dict[str, Any]:
    """One row per city: observed/placeholder/missing over the ten series."""
    rows = {city: city_state.coverage(state) for city, state in states.items()}
    return {"cities": rows,
            "total_observed": sum(r["observed"] for r in rows.values()),
            "total_placeholder": sum(r["placeholder"] for r in rows.values()),
            "total_missing": sum(r["missing"] for r in rows.values())}


def save_coverage_table(states: Dict[str, Dict[str, Any]], path: str | Path) -> Path:
    out = Path(path)
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(json.dumps(coverage_table(states), indent=1))
    return out
