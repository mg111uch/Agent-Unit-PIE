"""QC primitives for research deliverables (REV-04).

Every batch can be checked before the customer sees it:
- duplicate **blind** assignment (the second analyst never knows it is a repeat)
- **gold records** with known truth injected and scored separately
- deterministic **spot-check sampling** for human review
- per-record **confidence** from agreement, plus an accuracy **SLA** that maps
  to a refund percentage.

Checkers are pure functions over plain dicts, so the same plan can be replayed
and audited later. No DB writes here — persistence stays in `ledger`.
"""
from __future__ import annotations

import hashlib
import math
import random
from typing import Any, Dict, Iterable, List, Optional

DEFAULT_DUPLICATE_RATIO = 0.10
DEFAULT_GOLD_RATIO = 0.05
DEFAULT_SPOTCHECK_RATIO = 0.20
DEFAULT_SLA = 0.90
SINGLE_SOURCE_CONFIDENCE = 0.6

# Promotion ladder: a value is only "verified" when two blind copies agree.
STATUSES = ("agreed", "disputed", "unverified")


def policy() -> Dict[str, Any]:
    """The published QC contract; also stored in the methodology note."""
    return {
        "duplicate_ratio": DEFAULT_DUPLICATE_RATIO,
        "gold_ratio": DEFAULT_GOLD_RATIO,
        "spotcheck_ratio": DEFAULT_SPOTCHECK_RATIO,
        "sla_accuracy": DEFAULT_SLA,
        "refund": [
            {"below": DEFAULT_SLA, "percent": 0},
            {"below": 0.85, "percent": 50},
            {"below": 0.75, "percent": 100},
        ],
        "statuses": list(STATUSES),
    }


def _blind_id(record_id: str, copy: int, seed: int) -> str:
    h = hashlib.sha1(f"{seed}|{record_id}|{copy}".encode()).hexdigest()[:10]
    return f"q_{h}"


def plan(record_ids: Iterable[str], analysts: List[str],
         duplicate_ratio: float = DEFAULT_DUPLICATE_RATIO,
         seed: int = 0) -> Dict[str, Any]:
    """Assign each record to an analyst; a share of them get a blind twin.

    Raises if there are no analysts — silence would look like a plan.
    """
    ids = [str(r) for r in record_ids]
    if not ids:
        return {"assignments": [], "duplicates": [], "analysts": list(analysts)}
    if not analysts:
        raise ValueError("at least one analyst is required")
    rng = random.Random(seed)
    order = list(analysts)
    rng.shuffle(order)

    assignments: List[Dict[str, Any]] = []
    for i, rid in enumerate(ids):
        analyst = order[i % len(order)]
        assignments.append({
            "blind_id": _blind_id(rid, 1, seed),
            "record_id": rid, "analyst": analyst, "copy": 1, "gold": False,
        })

    n_dup = min(len(ids), math.ceil(len(ids) * max(0.0, duplicate_ratio)))
    dup_ids = rng.sample(ids, n_dup) if n_dup else []
    duplicated = []
    for rid in dup_ids:
        primary = next(a for a in assignments
                       if a["record_id"] == rid and a["copy"] == 1)
        # A twin never goes to the same analyst: that is the whole control.
        choices = [a for a in order if a != primary["analyst"]] or order
        second = choices[rng.randrange(len(choices))]
        duplicated.append(rid)
        assignments.append({
            "blind_id": _blind_id(rid, 2, seed),
            "record_id": rid, "analyst": second, "copy": 2, "gold": False,
        })
    return {"assignments": assignments, "duplicates": duplicated,
            "analysts": list(analysts)}


def inject_gold(assignments: List[Dict[str, Any]],
                gold_records: List[Dict[str, Any]],
                analysts: List[str],
                gold_ratio: float = DEFAULT_GOLD_RATIO,
                seed: int = 0) -> Dict[str, Any]:
    """Add known-truth records under blind ids; return truth separately.

    Truth is returned in its own map so it can be scored but never shipped to
    the analyst doing the work.
    """
    if not gold_records or not analysts:
        return {"assignments": list(assignments), "truth": {}}
    rng = random.Random(seed + 7)
    n = max(1, math.ceil(len(assignments) * max(0.0, gold_ratio)))
    out = list(assignments)
    truth: Dict[str, Dict[str, Any]] = {}
    for i in range(n):
        g = gold_records[i % len(gold_records)]
        rid = f"gold::{g.get('record_id', i)}"
        bid = _blind_id(rid, 1, seed + 7 + i)
        out.append({"blind_id": bid, "record_id": rid,
                    "analyst": analysts[rng.randrange(len(analysts))],
                    "copy": 1, "gold": True})
        truth[bid] = dict(g.get("fields") or {})
    return {"assignments": out, "truth": truth}


def spotcheck(record_ids: Iterable[str],
              ratio: float = DEFAULT_SPOTCHECK_RATIO,
              seed: int = 0) -> List[str]:
    """Deterministic human-review sample (same seed -> same list)."""
    ids = [str(r) for r in record_ids]
    if not ids:
        return []
    k = min(len(ids), max(1, math.ceil(len(ids) * max(0.0, ratio))))
    return sorted(random.Random(seed).sample(ids, k))


def consensus(submissions: List[Dict[str, Any]]) -> Dict[str, Any]:
    """Field-level agreement across blind copies.

    `submissions`: [{record_id, value: {field: value}}]. A record with one
    submission is `unverified` (confidence 0.6); unanimous copies are
    `agreed` (1.0); any field mismatch is `disputed` with the modal value kept
    so the batch is still usable.
    """
    groups: Dict[str, List[Dict[str, Any]]] = {}
    for s in submissions:
        groups.setdefault(str(s.get("record_id")), []).append(s.get("value") or {})

    records: Dict[str, Any] = {}
    for rid, vals in groups.items():
        n = len(vals)
        if n == 1:
            records[rid] = {"value": dict(vals[0]), "confidence":
                            SINGLE_SOURCE_CONFIDENCE, "status": "unverified",
                            "copies": 1, "disagreements": []}
            continue
        fields = sorted({k for v in vals for k in v})
        disagreements, total = [], 0.0
        merged: Dict[str, Any] = {}
        for f in fields:
            seen: Dict[str, int] = {}
            for v in vals:
                key = repr(v.get(f))
                seen[key] = seen.get(key, 0) + 1
            top = max(seen.items(), key=lambda kv: (kv[1], kv[0]))
            merged[f] = next(v.get(f) for v in vals if repr(v.get(f)) == top[0])
            total += top[1] / n
            if len(seen) > 1:
                disagreements.append(f)
        conf = round(total / len(fields), 3) if fields else 0.0
        records[rid] = {
            "value": merged, "confidence": conf, "copies": n,
            "status": "agreed" if not disagreements else "disputed",
            "disagreements": disagreements,
        }
    return {"records": records,
            "summary": summarize(records)}


def score_gold(submissions: List[Dict[str, Any]],
               truth: Dict[str, Dict[str, Any]]) -> Dict[str, Any]:
    """Accuracy on gold items only — the one number the SLA uses."""
    total = correct = 0
    misses = []
    for s in submissions:
        want = truth.get(str(s.get("blind_id")))
        if not want:
            continue
        got = s.get("value") or {}
        for f, expected in want.items():
            total += 1
            if got.get(f) == expected:
                correct += 1
            else:
                misses.append({"blind_id": s.get("blind_id"), "field": f,
                               "expected": expected, "got": got.get(f)})
    acc = round(correct / total, 3) if total else None
    return {"gold_fields": total, "correct": correct, "accuracy": acc,
            "misses": misses[:20]}


def summarize(records: Dict[str, Any]) -> Dict[str, Any]:
    if not records:
        return {"total": 0, "agreed": 0, "disputed": 0, "unverified": 0,
                "mean_confidence": None}
    counts = {s: 0 for s in STATUSES}
    for r in records.values():
        counts[r["status"]] += 1
    mean = round(sum(r["confidence"] for r in records.values())
                 / len(records), 3)
    return {"total": len(records), **counts, "mean_confidence": mean}


def evaluate(accuracy: Optional[float],
             sla: float = DEFAULT_SLA) -> Dict[str, Any]:
    """SLA verdict + refund. Unknown accuracy fails closed, never open."""
    if accuracy is None:
        return {"pass": False, "accuracy": None, "sla": sla,
                "reason": "no gold records scored",
                "refund": {"required": False, "percent": 0,
                           "policy": "hold payment until gold set is scored"}}
    if accuracy >= sla:
        return {"pass": True, "accuracy": accuracy, "sla": sla,
                "reason": "within SLA",
                "refund": {"required": False, "percent": 0,
                           "policy": "no refund"}}
    # Published rule: 75-90% -> 50% refund, below 75% -> full refund.
    pct = 50 if accuracy >= 0.75 else 100
    return {"pass": False, "accuracy": accuracy, "sla": sla,
            "reason": f"accuracy {accuracy} < SLA {sla}",
            "refund": {"required": True, "percent": pct,
                       "policy": "50% refund 75-90% accuracy, 100% below 75%"}}


def run(record_ids: Iterable[str], analysts: List[str],
        submissions: List[Dict[str, Any]],
        gold_records: Optional[List[Dict[str, Any]]] = None,
        truth: Optional[Dict[str, Dict[str, Any]]] = None,
        duplicate_ratio: float = DEFAULT_DUPLICATE_RATIO,
        seed: int = 0) -> Dict[str, Any]:
    """One call that produces the QC report attached to a deliverable."""
    p = plan(record_ids, analysts, duplicate_ratio, seed)
    gold = inject_gold(p["assignments"], gold_records or [], analysts, seed=seed)
    cons = consensus(submissions)
    gold_score = score_gold(submissions, truth or gold["truth"])
    return {
        "plan": {**p, "assignments": gold["assignments"]},
        "consensus": cons,
        "gold": gold_score,
        "verdict": evaluate(gold_score["accuracy"]),
        "spotcheck": spotcheck(record_ids, seed=seed),
        "policy": policy(),
    }
