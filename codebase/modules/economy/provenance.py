"""Economic finding provenance (INT-06).

A conversion or margin finding is only valid for the regime that produced it.
Fee policy is runtime-changeable, so every economic finding carries the
versions it was learned under:

    stamp() -> {"app_commit", "fee_policy_version", "offer_template_version"}

    finding = stamped({"kind": "conversion", "value": 0.11})
    needs_invalidation(finding, current)  # policy bumped since -> True
    mark_historical(finding)              # validity ACTIVE -> HISTORICAL

Versions are read from `data/economy/provenance.json` (or env), because the
authoritative values live in FireFlow's fee_config, not in PIE.
"""
from __future__ import annotations

import json
import os
from pathlib import Path
from typing import Any, Dict, Optional

FINDING_MEMORY_TYPE = "economic_findings"
_UNKNOWN = "unversioned"


def _root() -> Path:
    return Path(os.environ.get("PIE_DATA_ROOT",
                               Path(__file__).resolve().parents[3] / "data"))


def _versions() -> Dict[str, str]:
    p = _root() / "economy" / "provenance.json"
    data: Dict[str, Any] = {}
    if p.exists():
        try:
            data = json.loads(p.read_text() or "{}")
        except ValueError:
            data = {}
    return {
        "fee_policy_version": str(os.environ.get(
            "PIE_FEE_POLICY_VERSION",
            data.get("fee_policy_version", _UNKNOWN))),
        "offer_template_version": str(os.environ.get(
            "PIE_OFFER_TEMPLATE_VERSION",
            data.get("offer_template_version", _UNKNOWN))),
    }


def _app_commit() -> str:
    env = os.environ.get("PIE_APP_COMMIT")
    if env:
        return env
    try:
        from kernel.git_version import current_commit
        return str(current_commit() or _UNKNOWN)
    except Exception:
        return _UNKNOWN


def stamp() -> Dict[str, str]:
    """The three version tags every economic finding must carry."""
    s = {"app_commit": _app_commit()}
    s.update(_versions())
    return s


def stamped(payload: Dict[str, Any]) -> Dict[str, Any]:
    """Return `payload` with a `provenance` block (never mutates the input)."""
    out = dict(payload or {})
    out["provenance"] = {**stamp(), **(out.get("provenance") or {})}
    out.setdefault("validity", {"status": "ACTIVE"})
    return out


def needs_invalidation(finding: Dict[str, Any],
                       current: Optional[Dict[str, str]] = None) -> Dict[str, Any]:
    """Compare a finding's regime with today's. Returns drift, empty = valid."""
    want = current or stamp()
    have = (finding or {}).get("provenance") or {}
    drift = {k: {"was": have.get(k, _UNKNOWN), "now": want.get(k, _UNKNOWN)}
             for k in want if have.get(k, _UNKNOWN) != want.get(k, _UNKNOWN)}
    return drift


def mark_historical(finding: Dict[str, Any], reason: str = "regime changed") -> Dict[str, Any]:
    """Flip a stored finding to HISTORICAL (persisted if it has an id)."""
    out = dict(finding or {})
    out["validity"] = {"status": "HISTORICAL", "reason": reason, **stamp()}
    fid = out.get("finding_id")
    if fid:
        from kernel.memory.memory_engine import memory_engine
        memory_engine.save_object(FINDING_MEMORY_TYPE, str(fid), out)
    return out


def apply_invalidation(findings, current: Optional[Dict[str, str]] = None):
    """Mark every finding whose regime drifted. Returns (changed, kept)."""
    changed, kept = [], []
    for f in findings or []:
        if needs_invalidation(f, current):
            changed.append(mark_historical(f))
        else:
            kept.append(f)
    return changed, kept
