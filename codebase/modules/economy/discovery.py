"""RA-2 prospect discovery: collectors + pain ranking.

Collectors normalize raw source rows into Prospects; rank() orders by
pain_score and attaches the decide() verdict. Pure functions, no DB,
no network — live portal connectors (Udyam/GeM/ONDC) are deferred stubs
that say so honestly; agents push finds via manual/signal collectors.
"""
from __future__ import annotations
from typing import Any, Dict, List

from modules.economy.prospects import decide, make_prospect, pain_score

SOURCES = ("manual", "signal", "udyam", "gem", "ondc")
LIVE_DEFERRED = ("udyam", "gem", "ondc")


def normalize_raw(source: str, items: List[Dict[str, Any]]) -> List[Any]:
    """Raw dicts -> Prospects, source-stamped. Skips invalid rows."""
    if source not in SOURCES:
        raise ValueError(f"source must be one of {SOURCES}")
    out = []
    for it in items or []:
        try:
            out.append(make_prospect(
                company=str(it.get("company", "") or ""),
                problem=str(it.get("problem", "") or ""),
                region=str(it.get("region", "") or ""),
                industry=str(it.get("industry", "") or ""),
                evidence=list(it.get("evidence") or []),
                triggers=list(it.get("triggers") or []),
                estimated_monthly_value=float(it.get("estimated_monthly_value", 0) or 0),
                recommended_pilot=float(it.get("recommended_pilot", 0) or 0),
                contactability=float(it.get("contactability", 0.5)),
                confidence=float(it.get("confidence", 0.5)),
                source=source))
        except (ValueError, TypeError):
            continue
    return out


def from_signals(rows: List[Dict[str, Any]]) -> List[Any]:
    """market_signals rows -> raw prospect dicts (title=problem, region fallback)."""
    raws = []
    for r in rows or []:
        raws.append({
            "company": r.get("company") or r.get("region") or "open market",
            "problem": r.get("title", ""),
            "region": r.get("region", ""),
            "evidence": [r.get("detail")] if r.get("detail") else [f"signal:{r.get('signal_type', '')}"],
            "triggers": [],
            "estimated_monthly_value": 0.0,
            "contactability": 0.5, "confidence": 0.4,
        })
    return normalize_raw("signal", raws)


def collect(source: str, items: List[Dict[str, Any]] | None = None) -> Dict[str, Any]:
    """Dispatch to a collector. Live portals deferred — no fake data."""
    if source in LIVE_DEFERRED:
        return {"items": [], "note": f"{source} live connector deferred; push via manual import"}
    if source == "signal":
        return {"items": from_signals(items or []), "note": ""}
    return {"items": normalize_raw("manual", items or []), "note": ""}


def rank(prospects: List[Any], unit: Any = None, limit: int = 20) -> List[Dict[str, Any]]:
    """Dedup by id, score, attach decision, top-N by pain desc."""
    seen, rows = set(), []
    for p in prospects or []:
        pid = getattr(p, "prospect_id", None) or (p.get("prospect_id") if isinstance(p, dict) else None)
        if not pid or pid in seen:
            continue
        seen.add(pid)
        d = dict(p) if isinstance(p, dict) else {
            "prospect_id": p.prospect_id, "company": p.company, "problem": p.problem,
            "region": p.region, "industry": p.industry, "evidence": p.evidence,
            "triggers": p.triggers, "estimated_monthly_value": p.estimated_monthly_value,
            "recommended_pilot": p.recommended_pilot, "contactability": p.contactability,
            "confidence": p.confidence, "source": p.source,
            "no_contact": p.no_contact}
        s = pain_score(d, unit)
        rows.append({**d, "pain_score": s["score"],
                     "pain_breakdown": s["breakdown"], **decide(d, unit)})
    rows.sort(key=lambda r: r["pain_score"], reverse=True)
    return rows[:max(1, limit)]
