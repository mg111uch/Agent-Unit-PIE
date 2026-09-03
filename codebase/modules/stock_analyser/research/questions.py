"""Research questions from objectives, observations, gaps, failures."""
from __future__ import annotations
from typing import Dict, List, Any


def from_objective(objective: str, universe: str = "MY_RESEARCH_UNIVERSE") -> Dict[str, Any]:
    return {"kind": "directed", "objective": objective, "universe": universe,
            "question": f"{objective} on {universe}?"}


def from_observation(note: str, universe: str = "MY_RESEARCH_UNIVERSE") -> Dict[str, Any]:
    return {"kind": "emergent", "universe": universe,
            "question": f"Is observed effect real and robust? {note[:200]}"}


def from_failure(failed: Dict[str, Any]) -> Dict[str, Any]:
    return {"kind": "mutation", "universe": failed.get("universe", "MY_RESEARCH_UNIVERSE"),
            "question": f"Why did {failed.get('name', '?')} fail; which regime/mutation fixes it?",
            "parent": failed.get("name")}


def next_questions(failures: List[Dict] = [], findings: List[Dict] = [],
                   gaps: List[str] = []) -> List[Dict[str, Any]]:
    out = [from_failure(f) for f in failures[:3]]
    out += [{"kind": "gap", "question": g} for g in gaps[:3]]
    if findings:
        out.append({"kind": "followup",
                    "question": f"Does {findings[0].get('claim', '?')[:120]} hold out-of-sample?"})
    return out
