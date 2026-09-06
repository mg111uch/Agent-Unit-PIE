"""Epoch model for popula_dyn (FixesIssues #12-18, Phase 3-4).

Causal realism over chronological realism: explicit societal regimes,
constraint-gated transitions, multi-scale/event-driven time, epoch compiler,
calibration vs scenario modes. Pure functions over SimulationModel; no new store.
"""
from __future__ import annotations
from typing import Any, Dict, List

EPOCHS: List[str] = ["Agricultural", "Pre-industrial", "Industrial",
                     "Urban-industrial", "Modern"]

# constraint-gated transition thresholds on macro vars (all 0..~1+)
TRANSITIONS: List[Dict[str, Any]] = [
    {"from": "Agricultural", "to": "Pre-industrial",
     "need": {"surplus": 0.3, "density": 0.2, "specialization": 0.05}},
    {"from": "Pre-industrial", "to": "Industrial",
     "need": {"surplus": 0.5, "energy": 0.3, "knowledge": 0.3, "trade": 0.2}},
    {"from": "Industrial", "to": "Urban-industrial",
     "need": {"surplus": 0.6, "energy": 0.5, "density": 0.5}},
    {"from": "Urban-industrial", "to": "Modern",
     "need": {"knowledge": 0.6, "energy": 0.6, "specialization": 0.3}},
]


def macro_state(model) -> Dict[str, float]:
    """Derive macro vars from model summary. Cheap, no behaviour change."""
    try:
        s = model.summary()
    except Exception:
        s = {}
    pop = float(s.get("population", 0) or 0)
    wealth = float(s.get("total_wealth", 0) or 0)
    skill = float(s.get("avg_skill", 0) or 0)
    spatial = s.get("spatial", {}) or {}
    occ = float(spatial.get("human_occupied_cells", spatial.get("occupied_cells", 0)) or 0)
    cells = max(1, model.params.get("grid_width", 1) * model.params.get("grid_height", 1))
    return {
        "surplus": min(2.0, wealth / max(1.0, pop)),
        "density": min(1.0, occ / cells + pop / max(1.0, cells * 4)),
        "specialization": min(1.0, (getattr(model, "tools_produced", 0)
                                    + getattr(model, "successful_healings", 0)) / max(1.0, pop)),
        "trade": min(2.0, getattr(model, "trades_executed", 0) / max(1.0, pop)),
        "energy": min(2.0, getattr(model, "tools_produced", 0) / max(1.0, pop) + 0.1),
        "knowledge": min(2.0, skill + getattr(model, "tools_produced", 0) / max(1.0, pop)),
    }


def transition_ready(epoch: str, macro: Dict[str, float]) -> Dict[str, Any]:
    """Constraint gate: all needs met → ready with target epoch."""
    for t in TRANSITIONS:
        if t["from"] == epoch and all(macro.get(k, 0) >= v for k, v in t["need"].items()):
            return {"ready": True, "to": t["to"], "need": t["need"]}
    need = next((t["need"] for t in TRANSITIONS if t["from"] == epoch), {})
    return {"ready": False, "to": "", "need": need}


def run_until_transition(model, max_steps: int = 500, fast_n: int = 10) -> Dict[str, Any]:
    """Event-driven multi-scale: accelerate (fast_n steps) when far, slow near gate."""
    epoch = getattr(model, "epoch", "Agricultural")
    for i in range(max_steps):
        m = macro_state(model)
        r = transition_ready(epoch, m)
        if r["ready"]:
            return {"transition": True, "from": epoch, "to": r["to"],
                    "steps": i, "macro": m}
        # far from gate → leap; near → single step (grounded around transitions)
        gap = sum(max(0.0, v - m.get(k, 0)) for k, v in r.get("need", {}).items())
        for _ in range(fast_n if gap > 0.5 else 1):
            model.step()
            if getattr(model, "epoch", epoch) != epoch:
                epoch = getattr(model, "epoch", epoch)
                break
    m = macro_state(model)
    return {"transition": False, "from": epoch, "to": "", "steps": max_steps, "macro": m}


def compile_epoch(epoch: str, mode: str = "calibration",
                  base: Dict[str, Any] | None = None) -> Dict[str, Any]:
    """Epoch compiler: epoch name (+mode) → world params. Calibration = stable
    plausible history; scenario = same base + counterfactual lever."""
    p = dict(base or {})
    table = {
        "Agricultural": {"initial_pop": 500, "birth_rate": 0.04, "initial_traders": 2,
                         "initial_toolmakers": 2, "toolmaker_production_rate": 0.05},
        "Pre-industrial": {"initial_pop": 1500, "birth_rate": 0.045, "initial_traders": 10,
                           "initial_toolmakers": 10, "toolmaker_production_rate": 0.1},
        "Industrial": {"initial_pop": 4000, "birth_rate": 0.05, "initial_traders": 30,
                       "initial_toolmakers": 40, "toolmaker_production_rate": 0.2},
        "Urban-industrial": {"initial_pop": 8000, "birth_rate": 0.045, "initial_traders": 60,
                             "initial_toolmakers": 60, "toolmaker_production_rate": 0.25},
        "Modern": {"initial_pop": 12000, "birth_rate": 0.03, "initial_traders": 100,
                   "initial_toolmakers": 80, "toolmaker_production_rate": 0.3},
    }
    if epoch not in table:
        raise ValueError(f"unknown epoch {epoch}")
    p.update(table[epoch])
    p["epoch"] = epoch
    p["epoch_mode"] = mode  # calibration: stabilize; scenario: branch counterfactuals
    return p
