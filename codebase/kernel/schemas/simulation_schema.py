"""Simulation lineage schemas — Phase 0 refactored (Git-backed).

FixesIssues.md V2: use Git for syntactic lineage (commit/parent/diff).
Kernel keeps semantic validity (affected concepts, status).

Implements the 4 concepts:
 SimulationVersion (git_commit), SimulationRun, Finding, Validity
Maps to existing memory layers: episodic (raw), semantic (consolidated), pattern.

Design constraints:
 - <500 LOC, stdlib only
 - Single persistence path via kernel.persistence.db
 - Backwards compat: old V1_* / V0 treated as ACTIVE, new uses git short hash
"""
from __future__ import annotations

import hashlib
import time
from dataclasses import dataclass, field, asdict
from pathlib import Path
from typing import Dict, List, Any, Optional


def _utc_now() -> float:
    return time.time()


# --- helpers ---------------------------------------------------------------
def compute_code_hash(root: Path, patterns: Optional[List[str]] = None) -> str:
    """Hash relevant simulator source files (deterministic, short)."""
    patterns = patterns or [
        "popula_dyn/core/*.py",
        "popula_dyn/behaviours/*.py",
        "popula_dyn/constants.py",
    ]
    # root is codebase/modules/simulators
    h = hashlib.sha256()
    for pat in patterns:
        for p in sorted(root.glob(pat)):
            if p.is_file():
                h.update(p.name.encode())
                h.update(str(p.stat().st_mtime).encode())
                # content hash (first 4k to keep fast)
                try:
                    h.update(p.read_bytes()[:4096])
                except Exception:
                    pass
    return h.hexdigest()[:12]


# --- core schemas ----------------------------------------------------------
@dataclass
class SimulationVersion:
    version_id: str  # git short hash e.g. a83f91c, or {sim}@{commit} when scoped
    simulator: str = "popula_dyn"  # strictly isolated per simulator
    parent_version_id: Optional[str] = None  # git parent or None
    code_hash: str = ""  # full git commit or fallback hash (sim-scoped)
    git_branch: str = ""  # from git branch --show-current
    git_commit_msg: str = ""
    created_at: float = field(default_factory=_utc_now)
    change_reason: str = ""
    change_summary: str = ""
    affected_concepts: List[str] = field(default_factory=list)  # e.g. ["reproduction","mortality"]
    # SERIALIZATION
    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)

    @classmethod
    def from_dict(cls, d: Dict[str, Any]) -> "SimulationVersion":
        return cls(**{k: d.get(k, getattr(cls, k, None)) for k in cls.__dataclass_fields__ if k in d or hasattr(cls, k)})


@dataclass
class SimulationRun:
    run_id: str
    version_id: str
    simulator: str = "popula_dyn"
    parameters: Dict[str, Any] = field(default_factory=dict)
    baseline_run_id: Optional[str] = None
    result: Dict[str, Any] = field(default_factory=dict)  # summary.json subset
    status: str = "completed"  # completed|failed
    horizon: int = 0
    created_at: float = field(default_factory=_utc_now)
    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)


@dataclass
class Finding:
    finding_id: str  # == SemanticNode node_id (argu_popu_sim_...)
    run_id: str
    version_id: str
    simulator: str = "popula_dyn"
    claim: str = ""  # premise
    metrics: Dict[str, Any] = field(default_factory=dict)  # extracted deltas
    confidence: float = 1.0
    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)


@dataclass
class Validity:
    finding_id: str
    valid_for_version: str
    simulator: str = "popula_dyn"
    status: str = "ACTIVE"  # ACTIVE|HISTORICAL
    invalidated_by: Optional[str] = None
    affected_concepts: List[str] = field(default_factory=list)
    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)


# --- module-level registry for affected concepts ---------------------------
# changed module → concepts it touches (used for selective invalidation)
MODULE_CONCEPTS: Dict[str, List[str]] = {
    "reproduction": ["reproduction", "population_growth", "mortality"],
    "survival": ["mortality", "resource_scarcity"],
    "consume": ["resource_scarcity", "wealth"],
    "harvest": ["wealth", "resource_scarcity"],
    "regrow": ["terrain", "resource_scarcity"],
    "move": ["spatial", "population_decline"],
    "heal": ["healthcare_gap", "mortality"],
    "trade": ["trade_gap", "wealth"],
    "starvation": ["mortality", "population_decline"],
    "world_engine": ["population_growth", "wealth"],
    "simulation_model": ["population_growth", "wealth", "mortality"],
}


def _load_ontology_concepts() -> Dict[str, List[str]]:
    """Merge per-simulator ontology.yaml declared concepts with MODULE_CONCEPTS."""
    merged: Dict[str, List[str]] = dict(MODULE_CONCEPTS)
    try:
        from pathlib import Path as _P

        sim_root = _P(__file__).resolve().parents[2] / "modules" / "simulators"
        if sim_root.exists():
            for child in sim_root.iterdir():
                onto = child / "ontology.yaml"
                if not onto.exists():
                    onto = child / "ontology.yml"
                if onto.exists():
                    import yaml as _yaml

                    data = _yaml.safe_load(onto.read_text()) or {}
                    # support two shapes: {module: [concepts]} or {"modules": {module: {concepts: [...]}}}
                    mods = data.get("modules") if isinstance(data, dict) and "modules" in data else data
                    if isinstance(mods, dict):
                        for mod, cfg in mods.items():
                            if isinstance(cfg, dict):
                                conc = cfg.get("concepts") or cfg.get("affects") or []
                            elif isinstance(cfg, list):
                                conc = cfg
                            else:
                                continue
                            merged[mod.lower()] = sorted(set(conc))
                    elif isinstance(mods, list):
                        for entry in mods:
                            if not isinstance(entry, dict):
                                continue
                            mod = str(entry.get("module", "")).replace(".py", "").lower()
                            conc = entry.get("concepts", [])
                            if mod and conc:
                                merged[mod] = sorted(set(conc))
    except Exception:
        pass
    return merged


def concepts_for_changed_files(files: List[str], _ontology: Optional[Dict[str, List[str]]] = None) -> List[str]:
    registry = _ontology or _load_ontology_concepts()
    out: set[str] = set()
    for f in files:
        p = Path(f)
        stem = p.stem.lower()
        name = p.name.lower()
        # ontology.yaml change affects all declared concepts (declaration change)
        if "ontology" in stem or name in ("ontology.yaml", "ontology.yml"):
            for concs in registry.values():
                out.update(concs)
            continue
        for mod, concepts in registry.items():
            ml = mod.lower()
            # handle path keys like behaviours/reproduce
            mod_stem = Path(ml).stem.lower()
            mod_name = Path(ml).name.lower()
            if ml in stem or ml in name or mod_stem == stem or mod_name == name or stem in ml or name in ml:
                out.update(concepts)
            elif mod_stem in stem or stem == mod_stem:
                out.update(concepts)
    return sorted(out)


def module_concepts_for(module: str) -> List[str]:
    """Public helper: concepts declared for a simulator module (ontology-aware)."""
    return _load_ontology_concepts().get(module.lower(), MODULE_CONCEPTS.get(module.lower(), []))
