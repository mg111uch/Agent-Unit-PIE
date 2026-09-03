"""Simulator registry — per-simulator isolation (Phase 0 refactor).

Discovers `codebase/modules/simulators/*` as isolated simulators.
Strict isolation: findings, versions, lineage scoped per simulator.
"""
from __future__ import annotations

from pathlib import Path
from typing import Dict, List, Any, Optional
import yaml

_SIM_ROOT = Path(__file__).resolve().parents[1] / "modules" / "simulators"
_MOD_ROOT = Path(__file__).resolve().parents[1] / "modules"

def _is_simulator_dir(p: Path) -> bool:
    if not p.is_dir() or p.name.startswith("_") or p.name.startswith("."):
        return False
    # marker files that indicate a simulator module
    if (p / "simulation_connector.py").exists():
        return False  # that's the connector, not a sim
    # check for popula_dyn style
    if (p / "core").is_dir() or (p / "constants.py").exists() or (p / "manifest.yaml").exists():
        return True
    # fallback: any .py files
    return any(p.glob("*.py"))

def discover_simulators() -> Dict[str, Dict[str, Any]]:
    """Return {sim_name: {root, patterns, topic}}."""
    out: Dict[str, Dict[str, Any]] = {}
    if not _SIM_ROOT.exists():
        return out
    for child in sorted(_SIM_ROOT.iterdir()):
        if _is_simulator_dir(child):
            name = child.name
            # load manifest if exists for custom topics/patterns
            manifest = {}
            mpath = child / "manifest.yaml"
            if mpath.exists():
                try:
                    manifest = yaml.safe_load(mpath.read_text()) or {}
                except Exception:
                    pass
            patterns = manifest.get("patterns", [f"{name}/**"])
            topic = manifest.get("topic", f"sim_{name}" if name != "popula_dyn" else "popu_sim")
            out[name] = {
                "root": child,
                "patterns": patterns,
                "topic": topic,
                "manifest": manifest,
            }
    # domain engines: modules/stock_analyser with manifest.yaml (Plan M6)
    try:
        sa = _MOD_ROOT / "stock_analyser"
        if sa.is_dir() and (sa / "manifest.yaml").exists() and "stock_analyser" not in out:
            m: Dict[str, Any] = {}
            try:
                m = yaml.safe_load((sa / "manifest.yaml").read_text()) or {}
            except Exception:
                pass
            out["stock_analyser"] = {"root": sa,
                "patterns": m.get("patterns", ["codebase/modules/stock_analyser/**"]),
                "topic": m.get("topic", "sim_stock"), "manifest": m}
    except Exception:
        pass
    # fallback ensure popula_dyn always present for backward compat
    if "popula_dyn" not in out and (_SIM_ROOT / "popula_dyn").exists():
        out["popula_dyn"] = {
            "root": _SIM_ROOT / "popula_dyn",
            "patterns": ["popula_dyn/**"],
            "topic": "popu_sim",
            "manifest": {},
        }
    return out

def list_simulators() -> List[str]:
    return sorted(discover_simulators().keys())

def get_simulator(name: str) -> Optional[Dict[str, Any]]:
    return discover_simulators().get(name)

def sim_topic(sim_name: str) -> str:
    sim = get_simulator(sim_name)
    if sim:
        return sim["topic"]
    return f"sim_{sim_name}"

def sim_patterns(sim_name: str) -> List[str]:
    sim = get_simulator(sim_name)
    if sim:
        # honor absolute codebase/... patterns (stock_analyser manifest)
        pats = []
        for p in sim["patterns"]:
            pats.append(p if p.startswith("codebase/") else f"codebase/modules/simulators/{p}")
        return pats
    return [f"codebase/modules/simulators/{sim_name}/**"]
