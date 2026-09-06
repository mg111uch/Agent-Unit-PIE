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


# Phase 1 (FixesIssues #3): baseline ladder L0-L2. Higher levels (ML/deep) only
# activate when lower-level evidence justifies escalation.
BASELINE_LADDER: List[Dict[str, str]] = [
    {"level": "L0", "name": "buy_hold",
     "question": "Does buy-and-hold on {universe} beat cash over each regime?"},
    {"level": "L1", "name": "momentum",
     "question": "Does cross-sectional momentum (top-N by ret_20) beat L0 on {universe}?"},
    {"level": "L1", "name": "reversal",
     "question": "Does short-run reversal (bottom-N by ret_5) beat L0 on {universe}?"},
    {"level": "L2", "name": "momentum_liquidity",
     "question": "Does momentum × liquidity filter (vol_ratio) survive costs on {universe}?"},
    {"level": "L2", "name": "momentum_vol_regime",
     "question": "Does momentum conditioned on vol_20 regime persist on {universe}?"},
]


def baseline_ladder(universe: str = "MY_RESEARCH_UNIVERSE") -> List[Dict[str, Any]]:
    """Ordered L0-L2 directed questions; climb before trying ML."""
    return [{"kind": "directed", "level": b["level"], "baseline": b["name"],
             "universe": universe,
             "question": b["question"].format(universe=universe)}
            for b in BASELINE_LADDER]
