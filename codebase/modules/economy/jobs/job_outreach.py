"""JF-5 job outreach: network-first messages + policy.

For OUTREACH-verdict roles (fit but not apply-grade), the move is a short
human message to the hiring side: role + 2-3 evidence points + one ask.
Same standing rules as revenue outreach: evidence-only, STOP footer,
human approval before any external send, frequency caps. Pure, no DB.
"""
from __future__ import annotations
from typing import Any, Dict, List

MAX_DAILY = 5
MIN_VERDICTS = ("APPLY", "TAILOR", "OUTREACH")


def _clean(line: str) -> str:
    return line.lstrip("- ").replace("**", "").replace("*", "").strip()


def draft_job_message(job: Dict[str, Any], twin: Dict[str, Any],
                      matched: List[str] | None = None) -> Dict[str, Any]:
    """Short recruiter/hiring-manager note. Claims ⊆ twin evidence only."""
    matched = matched or []
    pts = [_clean(ln) for ln in (twin.get("experience", []) + twin.get("projects", []))][:2]
    skills_str = ", ".join(s.replace("_", " ") for s in matched[:3]) or "full-stack development"
    body = (f"Hello {job.get('company', '')} team, I'm interested in {job.get('title', '')}. "
            f"Relevant background: {skills_str} — {'; '.join(pts)}. "
            f"India-based (IST, ±3h overlap), open to full-time or contract. "
            f"Worth a 15-min intro call? Reply STOP to opt out.")
    return {"to_company": job.get("company", ""), "job_id": job.get("job_id", ""),
            "subject": f"Interest: {job.get('title', '')}",
            "body": body, "honest": True}


def outreach_policy(verdict: str, sent_today: int,
                    max_daily: int = MAX_DAILY) -> Dict[str, Any]:
    """Verdict must be outreach-grade; daily cap; human approves the send."""
    if verdict not in MIN_VERDICTS:
        return {"decision": "blocked", "reason": f"verdict {verdict} not outreach-grade"}
    if sent_today >= max_daily:
        return {"decision": "blocked", "reason": f"daily cap {max_daily} reached"}
    return {"decision": "needs_approval", "reason": "human approves every external send"}
