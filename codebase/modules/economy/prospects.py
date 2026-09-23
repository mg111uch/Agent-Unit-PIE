"""RA-1 prospect model: customer evidence + pain score + decision.

Pure functions, no DB. A prospect is public-market evidence for one
concrete economic pain (PhasePlan: search pain, not companies).
IDs are content-hash (opp_/tsk_ style): pro_<12hex>, idempotent.
Ledger persistence lives in ledger.record_prospect (market.db).
"""
from __future__ import annotations
import hashlib
import json
import math
from dataclasses import asdict, dataclass, field
from typing import Any, Dict, List

DECISIONS = ("IGNORE", "RESEARCH", "OUTREACH", "PILOT")


def _hid(prefix: str, canon: Dict[str, Any]) -> str:
    return prefix + hashlib.sha256(
        json.dumps(canon, sort_keys=True, default=str).encode()).hexdigest()[:12]


@dataclass
class Prospect:
    prospect_id: str
    company: str
    problem: str
    region: str = ""
    industry: str = ""
    evidence: List[str] = field(default_factory=list)
    triggers: List[str] = field(default_factory=list)
    estimated_monthly_value: float = 0.0
    recommended_pilot: float = 0.0
    contactability: float = 0.5
    confidence: float = 0.5
    source: str = ""
    no_contact: bool = False


def validate_prospect(p: Dict[str, Any]) -> Dict[str, Any]:
    for k in ("company", "problem"):
        if not p.get(k) or not isinstance(p[k], str):
            raise ValueError(f"prospect missing/bad '{k}'")
    for k in ("contactability", "confidence"):
        v = p.get(k, 0.5)
        if not isinstance(v, (int, float)) or not 0.0 <= v <= 1.0:
            raise ValueError(f"prospect '{k}' must be in [0,1]")
    for k in ("estimated_monthly_value", "recommended_pilot"):
        v = p.get(k, 0.0)
        if not isinstance(v, (int, float)) or not v >= 0:
            raise ValueError(f"prospect '{k}' must be number >= 0")
    for k in ("evidence", "triggers"):
        if k in p and not isinstance(p[k], list):
            raise ValueError(f"prospect '{k}' must be a list")
    return p


def make_prospect(company: str, problem: str, region: str = "",
                  industry: str = "", evidence: List[str] | None = None,
                  triggers: List[str] | None = None,
                  estimated_monthly_value: float = 0.0,
                  recommended_pilot: float = 0.0,
                  contactability: float = 0.5, confidence: float = 0.5,
                  source: str = "") -> Prospect:
    d = {"company": company, "problem": problem, "region": region,
         "industry": industry, "evidence": list(evidence or []),
         "triggers": list(triggers or []),
         "estimated_monthly_value": float(estimated_monthly_value),
         "recommended_pilot": float(recommended_pilot),
         "contactability": float(contactability),
         "confidence": float(confidence), "source": source}
    validate_prospect(d)
    return Prospect(prospect_id=_hid("pro_", d), **d)


def _clamp(v: Any) -> float:
    try:
        return max(0.0, min(1.0, float(v)))
    except (TypeError, ValueError):
        return 0.0


def pain_score(p: Any, unit: Any = None) -> Dict[str, Any]:
    """Pain = evidence x value x fit x access x urgency x pilot_prob."""
    d = asdict(p) if not isinstance(p, dict) else dict(p)
    n_ev = len(d.get("evidence") or [])
    evidence = min(1.0, n_ev / 3.0)
    value = min(1.0, math.log10(1 + float(d.get("estimated_monthly_value", 0) or 0)) / 5.0)
    try:
        from modules.economy.scoring import capability_fit
        fit = capability_fit({"required_capabilities": d.get("required_capabilities", [])},
                             unit or {})
    except Exception:
        fit = 0.5
    access = _clamp(d.get("contactability", 0.5))
    urgency = min(1.0, (len(d.get("triggers") or []) + 1) / 3.0)
    pilot_prob = _clamp(d.get("confidence", 0.5))
    parts = {"evidence": round(evidence, 3), "value": round(value, 3),
             "fit": round(fit, 3), "access": round(access, 3),
             "urgency": round(urgency, 3), "pilot_prob": round(pilot_prob, 3)}
    score = round(math.prod(parts.values()) ** (1 / 6), 3)  # geometric mean
    return {"score": score, "breakdown": parts}


def decide(p: Any, unit: Any = None) -> Dict[str, Any]:
    """IGNORE / RESEARCH MORE / OUTREACH / PROPOSE PILOT."""
    d = asdict(p) if not isinstance(p, dict) else dict(p)
    if d.get("no_contact"):
        return {"decision": "IGNORE", "reason": "opt-out"}
    s = pain_score(d, unit)["score"]
    conf = _clamp(d.get("confidence", 0.5))
    n_ev = len(d.get("evidence") or [])
    if s >= 0.55 and conf >= 0.6 and n_ev >= 2:
        dec = "PILOT" if float(d.get("estimated_monthly_value", 0) or 0) >= 20000 else "OUTREACH"
    elif s >= 0.35:
        dec = "RESEARCH"
    else:
        dec = "IGNORE"
    return {"decision": dec, "pain_score": s,
            "reason": f"score={s} conf={conf} evidence={n_ev}"}
