"""JF-3 fit engine: hard gates + description-based skill match -> verdict.

Gates kill first (remote-only, employment type, comp floor when parseable,
junior/intern titles). Survivors score on twin-skill coverage in the actual
description text (employer tags are noisy — never trusted alone), title
seniority fit, and remote/India eligibility signals. Verdicts: APPLY (clean),
TAILOR (fit but needs variant), OUTREACH (network-first), SKIP (gated).
Pure functions, no DB.
"""
from __future__ import annotations
import re
from typing import Any, Dict, List

USD_TO_INR = 83.0
APPLY_AT = 0.70
TAILOR_AT = 0.45

_JUNIOR = re.compile(r"\b(junior|intern|trainee|graduate|entry[ -]?level|fresher)\b", re.I)
_SENIOR = re.compile(r"\b(senior|sr\.?|staff|lead|principal|head|director|architect)\b", re.I)
_INDIA_OK = re.compile(r"\b(india|indian|ist|asia/kolkata|apac|worldwide|global|anywhere)\b", re.I)
_INDIA_NO = re.compile(r"\b(us (only|citizens?)|eu (only|citizens?)|uk only|no india|except india|must (reside|be (based|located)) in (the )?(us|usa|eu|uk|europe))\b", re.I)
_US_TZ = re.compile(r"\b(pst|est|cst|mst|pacific|eastern|us hours|us timezone)\b", re.I)
_RELOCATE = re.compile(r"\b(hybrid|onsite|on-site|in-office|in office|work from office)\b", re.I)
_INDIA_HIRE = re.compile(r"\b(india|bangalore|bengaluru|hyderabad|pune|chennai|noida|gurgaon|mumbai|delhi|kolkata|ahmedabad|kochi|ist\b|asia/kolkata)\b", re.I)
_WORLDWIDE = re.compile(r"\b(worldwide|anywhere|global team|globally|remote.?first|fully remote|distributed team|work from anywhere)\b", re.I)


def _india_signal(job: Dict[str, Any]) -> bool:
    """Hire-in-India evidence: policy, eligible list, or description text."""
    if (job.get("remote_policy") or "").lower() == "india":
        return True
    if any("india" in str(c).lower() for c in (job.get("eligible_countries") or [])):
        return True
    d = _desc(job)
    return bool(_INDIA_HIRE.search(d) or _WORLDWIDE.search(d))


def _money_to_monthly_inr(comp: Any, currency: str) -> float | None:
    """Best-effort annual-or-monthly figure -> INR/month. None if unparseable."""
    if comp is None or comp == "" or comp == 0:
        return None
    if isinstance(comp, (int, float)):
        v = float(comp)
    else:
        m = re.search(r"([\d,]+(?:\.\d+)?)\s*(k)?", str(comp).replace("$", "").replace(",", ""))
        if not m:
            return None
        v = float(m.group(1)) * (1000 if m.group(2) else 1)
    if currency and currency.upper() == "USD":
        v *= USD_TO_INR
    if v <= 0:
        return None  # undisclosed comp never rejects — penalized, not gated
    # Heuristic: >500k is annual -> /12; else treat as monthly already.
    return v / 12 if v > 500000 else v


def _desc(job: Dict[str, Any]) -> str:
    return f"{job.get('title', '')} {job.get('description', '')}".lower()


def hard_gates(job: Dict[str, Any], prefs: Dict[str, Any]) -> Dict[str, Any]:
    """Fail-fast rejections with reasons. Unknown comp never rejects."""
    fails = []
    pol = (job.get("remote_policy") or "").lower()
    if pol and "remote" not in pol and "india" not in pol:
        fails.append("not remote")
    if job.get("employment_type") and job["employment_type"] not in prefs.get("employment", ["full_time", "contract"]):
        fails.append(f"employment {job['employment_type']}")
    if _JUNIOR.search(job.get("title") or ""):
        fails.append("junior-level title")
    if _INDIA_NO.search(_desc(job)):
        fails.append("india-excluded")
    monthly = _money_to_monthly_inr(job.get("compensation"), job.get("currency") or "")
    floor = float(prefs.get("min_comp_monthly", 0) or 0)
    if monthly is not None and monthly < floor:
        fails.append(f"comp {monthly:.0f}/mo < floor {floor:.0f}")
    return {"pass": not fails, "reasons": fails, "comp_monthly_inr": monthly}


def skill_match(job: Dict[str, Any], twin: Dict[str, Any]) -> Dict[str, Any]:
    """Twin skills (minus meta keys) vs description text + title boost."""
    d = _desc(job)
    skills = [s for s in (twin.get("skills") or {}) if s != "oss_evidence"]
    matched = [s for s in skills
               if any(h in d for h in _skill_hints(s))]
    title_hits = sum(1 for s in matched if s.replace("_", " ") in (job.get("title") or "").lower())
    coverage = len(matched) / max(1, len(skills))
    return {"matched": matched, "title_hits": title_hits,
            "coverage": round(coverage, 3)}


def _skill_hints(skill: str) -> List[str]:
    from modules.economy.jobs.candidate import SKILL_HINTS
    return SKILL_HINTS.get(skill, [skill.replace("_", " ")])


def score_job(job: Dict[str, Any], twin: Dict[str, Any],
              prefs: Dict[str, Any] | None = None) -> Dict[str, Any]:
    """Gate -> score -> verdict + confidence + evidence. Never hallucinates."""
    prefs = prefs or {}
    gate = hard_gates(job, prefs)
    if not gate["pass"]:
        return {"score": 0.0, "verdict": "SKIP", "confidence": 0.9,
                "reasons": gate["reasons"], "matched": [], "evidence": []}
    m = skill_match(job, twin)
    d = _desc(job)
    india_sig = 0.5 + (0.5 if _INDIA_OK.search(d) else 0.0)
    senior_fit = 1.0 if _SENIOR.search(job.get("title") or "") else 0.6
    us_only_tz = bool(_US_TZ.search(d))
    tz_fit = 0.5 if us_only_tz else 1.0
    comp_known = 1.0 if gate["comp_monthly_inr"] else 0.5
    score = round(0.5 * m["coverage"] + 0.15 * min(1.0, m["title_hits"] / 2)
                  + 0.1 * india_sig + 0.1 * senior_fit + 0.075 * tz_fit
                  + 0.075 * comp_known, 3)
    if score >= APPLY_AT and not us_only_tz and comp_known == 1.0:
        verdict = "APPLY"
    elif score >= TAILOR_AT:
        verdict = "TAILOR"
    elif score >= 0.25:
        verdict = "OUTREACH"
    else:
        verdict = "SKIP"
    reasons: List[str] = []
    if prefs.get("india_first") and verdict in ("APPLY", "TAILOR") and not _india_signal(job):
        verdict = "OUTREACH"
        reasons.append("india-first: no hire-in-India signal")
    if (not prefs.get("relocate", False) and verdict in ("APPLY", "TAILOR")
            and _RELOCATE.search(d) and "remote" not in d):
        verdict = "OUTREACH"
        reasons.append("requires relocation")
    conf = round(0.5 + 0.3 * m["coverage"] + (0.2 if comp_known == 1.0 else 0.0), 2)
    ev = [f"matched: {', '.join(m['matched']) or 'none'}",
          f"comp: {gate['comp_monthly_inr']:.0f}/mo" if gate["comp_monthly_inr"] else "comp: undisclosed"]
    return {"score": score, "verdict": verdict, "confidence": conf,
            "reasons": reasons, "matched": m["matched"], "evidence": ev}
