"""JF-4 application packs: evidence-bound variants + submission policy gate.

build_pack() tailors WITHOUT inventing: it selects the twin's evidenced
lines most relevant to the job and fills a cover letter from matched
skills + repo evidence only. The master resume is never modified.
submit_gate() enforces the application policy (plan §11): routine
submits auto-pass, salary/legal/contract steps need the human.
Pure functions, no DB.
"""
from __future__ import annotations
from typing import Any, Dict, List

ALLOWED_VERDICTS = ("APPLY", "TAILOR")
NEEDS_HUMAN = ("salary_negotiation", "legal_attestation",
               "demographic_questions", "employment_contract", "external_submit")


def _clean(line: str) -> str:
    return line.lstrip("- ").replace("**", "").replace("*", "").strip()


def _relevance(line: str, matched: List[str]) -> int:
    ln = line.lower()
    return sum(1 for s in matched if s.replace("_", " ") in ln or s.replace("_", "") in ln.replace(" ", ""))


def build_pack(job: Dict[str, Any], twin: Dict[str, Any],
               matched: List[str] | None = None) -> Dict[str, Any]:
    """Job + twin -> {resume_md, cover_letter, evidence}. Claims ⊆ twin only."""
    matched = matched or []
    exp = twin.get("experience", []) + twin.get("projects", [])
    ranked = sorted(exp, key=lambda ln: _relevance(ln, matched), reverse=True)
    top = [_clean(ln) for ln in ranked if _relevance(ln, matched) > 0][:6] or \
        [_clean(ln) for ln in ranked[:3]]
    repos = (twin.get("skills") or {}).get("oss_evidence", [])
    skills_str = ", ".join(s.replace("_", " ") for s in matched) or "full-stack development"
    cover = (
        f"Hello {job.get('company', '')} team,\n\n"
        f"I'm applying for {job.get('title', '')}. "
        f"My strongest fit: {skills_str}.\n\n"
        f"Evidence:\n" +
        "".join(f"- {ln}\n" for ln in top[:3]) +
        (f"\nCode: {', '.join(repos[:3])}\n" if repos else "") +
        f"\nManish Gupta · Kanpur, India (IST, ±3h overlap) · manigupt317@gmail.com")
    evidence = {ln: "resume.md" for ln in top}
    for r in repos[:3]:
        evidence[r] = "github.com/mg111uch"
    resume_md = (f"# Manish Gupta — application for {job.get('title', '')} "
                 f"at {job.get('company', '')}\n\n"
                 f"## Matched strengths\n" +
                 "".join(f"- {ln}\n" for ln in top) +
                 f"\n## Full background\nSee canonical resume.md (never edited by tailoring).")
    return {"job_id": job.get("job_id", ""), "resume_md": resume_md,
            "cover_letter": cover, "evidence": evidence}


def submit_gate(pack: Dict[str, Any], verdict: str,
                pending_steps: List[str] | None = None) -> Dict[str, Any]:
    """Policy gate: verdict must be APPLY/TAILOR; human steps listed explicitly."""
    if verdict not in ALLOWED_VERDICTS:
        return {"decision": "blocked", "reason": f"verdict {verdict} not submittable"}
    human = [s for s in (pending_steps or []) if s in NEEDS_HUMAN]
    if human:
        return {"decision": "needs_approval", "reason": f"human steps: {', '.join(human)}"}
    return {"decision": "auto_ok", "reason": "routine submit"}
