"""JF-1 candidate twin: resume.md -> structured profile + evidence pointers.

Every skill claim carries the resume line that proves it (anti-hallucination:
application variants may only cite this evidence). Preferences encode the
hard gates (min compensation, timezone overlap, employment types). Pure, no DB.
"""
from __future__ import annotations
import re
from typing import Any, Dict, List

SKILL_HINTS = {
    "python": ["python"], "typescript": ["typescript", "ts"],
    "javascript": ["javascript", "js", "node", "react", "next"],
    "web_frameworks": ["framework", "website", "web ", "next.js", "react", "node"],
    "game_dev": ["game"], "simulations": ["simulation"],
    "automation": ["automation", "workflow"],
    "iot_embedded": ["esp32", "raspberry", "raspi", "pill dispenser", "startup"],
    "llm_agents": ["llm", "agent", "agentic"],
    "ui_dev": ["ui development", "user interface", "frontend"],
    "process_engineering": ["process engineer", "reliance", "chemical"],
}

DEFAULT_PREFS = {
    "employment": ["full_time", "contract"],
    "remote": True, "india_eligible": True,
    "india_first": True, "relocate": False,
    "min_comp_monthly": 100000.0,
    "timezone_overlap_h": 3,
    "location": "Kanpur, India", "timezone": "Asia/Kolkata",
}


def parse_resume(text: str) -> Dict[str, List[str]]:
    """Split ## sections into line lists (header lines skipped)."""
    sections, cur = {}, None
    for line in (text or "").splitlines():
        m = re.match(r"##\s+(.+)", line.strip())
        if m:
            cur = m.group(1).strip().lower()
            sections[cur] = []
        elif cur is not None and line.strip() and not line.startswith("#"):
            sections[cur].append(line.strip())
    return sections


def extract_skills(sections: Dict[str, List[str]]) -> Dict[str, List[str]]:
    """Skill -> resume lines evidencing it. No line, no claim."""
    lines = [ln for ls in sections.values() for ln in ls]
    found = {}
    for skill, hints in SKILL_HINTS.items():
        ev = [ln for ln in lines if any(h in ln.lower() for h in hints)]
        if ev:
            found[skill] = ev
    return found


def make_twin(resume_text: str, prefs: Dict[str, Any] | None = None,
              github_repos: List[str] | None = None) -> Dict[str, Any]:
    """Resume + prefs + repo names -> candidate twin dict."""
    sections = parse_resume(resume_text)
    skills = extract_skills(sections)
    if github_repos:
        skills.setdefault("oss_evidence", github_repos)
    return {"skills": skills,
            "experience": sections.get("work experience", []),
            "projects": sections.get("projects", []),
            "education": sections.get("education", []),
            "preferences": {**DEFAULT_PREFS, **(prefs or {})}}


def validate_twin(t: Dict[str, Any]) -> Dict[str, Any]:
    if not t.get("skills"):
        raise ValueError("twin has no evidenced skills")
    p = t.get("preferences", {})
    if not p.get("employment"):
        raise ValueError("twin needs employment preferences")
    return t
