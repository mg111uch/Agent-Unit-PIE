"""
simulation_connector.py

Bridges popula_dyn simulation with kernel cognition.

Purpose
-------
- Runs simulation → extracts signals → stores in KB
- Compares simulation runs
- Enables policy injection experiments

Usage
-----
    from modules.simulators.simulation_connector import SimulationConnector
    
    conn = SimulationConnector()
    
    # Run simulation
    result = conn.run_and_extract(params, "run_001")
    
    # Compare runs
    diff = conn.compare_runs(["run_001", "run_002"])
"""

import json
import os
import yaml
from pathlib import Path
from datetime import datetime
from typing import Dict, Any, List, Optional

from modules.simulators.popula_dyn.core.simulation_model import SimulationModel
from modules.simulators.popula_dyn.constants import PARAMS


def _codebase_root():
    return os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))


def _workspace_root():
    return os.path.dirname(_codebase_root())


def _default_sim_base(simulator: str) -> str:
    return os.path.join(_workspace_root(), "data", "units", "simulations", simulator)


class SimulationConnector:
    """
    Bridge between simulators and kernel cognition — per-simulator isolated.
    """
    def __init__(
        self,
        base_path: str | None = None,
        emit_to_kernel: bool = True,
        simulator: str = "popula_dyn",
    ):
        self.simulator = simulator
        # default: data/units/simulations/{simulator} (single source; codebase path is legacy fallback)
        if base_path is None:
            base_path = _default_sim_base(simulator)
        elif not os.path.isabs(base_path):
            # legacy explicit "units/simulations" or "codebase/units/simulations" → map to legacy location for migration
            if base_path in ("units/simulations", "codebase/units/simulations"):
                root = os.path.join(_codebase_root(), "units", "simulations", simulator)
                base_path = root
            elif base_path == "data/units/simulations":
                base_path = os.path.join(_workspace_root(), "data", "units", "simulations", simulator)
            else:
                root = os.path.join(_codebase_root(), base_path)
                if base_path == "units/simulations":
                    root = os.path.join(root, simulator)
                base_path = root
        self.base_path = Path(base_path)
        self.base_path.mkdir(parents=True, exist_ok=True)
        self.emit_to_kernel = emit_to_kernel
        # legacy migration: move shared runs into sharded location once + migrate codebase → data/units
        self._migrate_legacy_shard()
        # resolve topic via registry
        try:
            from kernel.simulator_registry import sim_topic
            self.topic = sim_topic(simulator)
        except Exception:
            self.topic = "popu_sim" if simulator == "popula_dyn" else f"sim_{simulator}"
        self._signal_engine = None
        if emit_to_kernel:
            try:
                from kernel.signals.signal_engine import signal_engine
                self._signal_engine = signal_engine
            except ImportError:
                pass

    def _legacy_base(self) -> Path:
        return Path(_codebase_root()) / "units" / "simulations"

    def _data_base(self) -> Path:
        return Path(_workspace_root()) / "data" / "units" / "simulations" / self.simulator

    def _migrate_legacy_shard(self):
        try:
            # 1) legacy shared → sharded (inside codebase) for old layout
            legacy = self._legacy_base()
            if legacy.exists() and self.base_path != legacy:
                for child in list(legacy.iterdir()):
                    if not child.is_dir() or child.name.startswith("."):
                        continue
                    if child.name in ("popula_dyn", "eco_sim"):
                        continue
                    if self.simulator != "popula_dyn":
                        continue
                    dest = self.base_path / child.name
                    if dest.exists():
                        continue
                    # only migrate to data base if we are the data base; else to codebase sharded
                    if self.base_path == Path(_workspace_root()) / "data" / "units" / "simulations" / self.simulator:
                        dest = self.base_path / child.name
                    try:
                        import shutil
                        shutil.move(str(child), str(dest))
                    except Exception:
                        pass
            # 2) codebase sharded → data/units sharded (one-time)
            if self.base_path == self._data_base():
                codebase_sharded = self._legacy_base() / self.simulator
                if codebase_sharded.exists() and codebase_sharded != self.base_path:
                    for child in list(codebase_sharded.iterdir()):
                        if not child.is_dir():
                            continue
                        dest = self.base_path / child.name
                        if dest.exists():
                            continue
                        try:
                            import shutil
                            shutil.copytree(str(child), str(dest))
                        except Exception:
                            pass
        except Exception:
            pass
    def run_and_extract(
        self,
        params: Dict[str, Any],
        run_id: str,
        emit_signals: bool = True,
    ) -> str:
        """
        Run simulation, extract signals, store in KB.
        
        Args:
            params: Simulation parameters
            run_id: Unique identifier for this run
            emit_signals: Whether to emit to kernel (default: True)
            
        Returns:
            Summary string
        """
        params = {**PARAMS, **params}
        # coerce seed stored as string 'None' via yaml
        if params.get("seed") in ("None", "null", ""):
            params["seed"] = None
        model = SimulationModel(params)
        model.run()
        signals = self._extract_signals(model, params)
        self._store_run(run_id, params, model, signals)
        if emit_signals and self._signal_engine:
            self._emit_signals_to_kernel(run_id, signals)
        summary = self._generate_summary(run_id, model, signals)
        return summary
    def _emit_signals_to_kernel(
        self,
        run_id: str,
        signals: List[Dict[str, Any]],
    ) -> None:
        """Emit simulation signals to kernel."""
        for sig in signals:
            signal_type = sig.get("signal_type", "simulation_signal")
            value = sig.get("value")
            category = sig.get("category", "simulation")
            self._signal_engine.create_signal(
                signal_type=signal_type,
                source_unit_id=f"simulation_{run_id}",
                value=value,
                category=category,
                title=f"Sim {run_id}: {signal_type}",
                description=f"Simulation signal: {signal_type}",
                importance=sig.get("intensity", 5.0) / 10.0,
                confidence=0.8,
                tags=["simulation", run_id],
            )
    def _extract_signals(
        self,
        model: SimulationModel,
        params: Dict[str, Any],
    ) -> List[Dict[str, Any]]:
        """Extract signals from simulation results."""
        signals = []
        summary = model.summary()
        year = summary["step_count"]
        pop = summary["population"]
        total_wealth = summary["total_wealth"]
        deaths = summary["deaths"]
        births = summary["births"]
        if births > 0:
            signals.append({
                "signal_type": "population_growth",
                "value": births,
                "category": "demographic",
                "subtype": "birth_rate",
                "intensity": min(births / 10.0, 10.0),
                "trend": "increasing" if births > params.get("initial_pop", 50) * 0.1 else "stable",
            })
        if deaths > 0:
            signals.append({
                "signal_type": "mortality_event",
                "value": deaths,
                "category": "demographic",
                "subtype": "death_rate",
                "intensity": min(deaths / 10.0, 10.0),
                "trend": "significant" if deaths > births else "normal",
            })
        avg_wealth = total_wealth / max(pop, 1)
        if avg_wealth < 20:
            signals.append({
                "signal_type": "resource_scarcity",
                "value": avg_wealth,
                "category": "economic",
                "subtype": "wealth",
                "intensity": 7.0,
                "trend": "declining",
            })
        elif avg_wealth > 50:
            signals.append({
                "signal_type": "prosperity",
                "value": avg_wealth,
                "category": "economic",
                "subtype": "wealth",
                "intensity": 5.0,
                "trend": "increasing",
            })
        if pop < params.get("initial_pop", 50) * 0.5:
            signals.append({
                "signal_type": "population_decline",
                "value": pop,
                "category": "demographic",
                "subtype": "critical",
                "intensity": 8.0,
                "trend": "declining",
            })
        healers = summary.get("Healer_Count", 0)
        if healers == 0 and pop > 20:
            signals.append({
                "signal_type": "healthcare_gap",
                "value": healers,
                "category": "social",
                "subtype": "services",
                "intensity": 6.0,
                "trend": "deficit",
            })
        traders = summary.get("Trader_Count", 0)
        if traders == 0 and pop > 30:
            signals.append({
                "signal_type": "trade_gap",
                "value": traders,
                "category": "economic",
                "subtype": "services",
                "intensity": 4.0,
                "trend": "deficit",
            })
        df = model.get_dataframe()
        if len(df) > 10:
            pop_series = df["Population"].tolist()
            if len(pop_series) >= 5:
                recent = pop_series[-5:]
                if recent[-1] < recent[0]:
                    signals.append({
                        "signal_type": "population_trend_declining",
                        "value": pop_series[-1],
                        "category": "demographic",
                        "subtype": "trend",
                        "intensity": 5.0,
                        "trend": "declining",
                    })
        return signals
    def _resolve_run_path(self, run_id: str) -> Path:
        p = self.base_path / run_id
        if p.exists():
            return p
        # fallback legacy codebase sharded + shared
        for cand in [self._legacy_base() / self.simulator / run_id, self._legacy_base() / run_id, Path(_workspace_root()) / "data" / "units" / "simulations" / self.simulator / run_id]:
            if cand.exists():
                return cand
        return p

    def _store_run(
        self,
        run_id: str,
        params: Dict[str, Any],
        model: SimulationModel,
        signals: List[Dict[str, Any]],
    ) -> None:
        """Store run data in data/units/simulations/{simulator}/{run_id}/ + DB + episodic (legacy codebase fallback)."""
        run_path = self.base_path / run_id
        run_path.mkdir(parents=True, exist_ok=True)
        with open(run_path / "params.yaml", "w") as f:
            yaml.dump(params, f)
        with open(run_path / "signals.json", "w") as f:
            json.dump(signals, f, indent=2)
        df = model.get_dataframe()
        df.to_csv(run_path / "data.csv", index=False)
        summary = model.summary()
        summary["run_id"] = run_id
        summary["simulator"] = self.simulator
        summary["timestamp"] = datetime.utcnow().isoformat()
        with open(run_path / "summary.json", "w") as f:
            json.dump(summary, f, indent=2)
        # Phase 1: DB + episodic (per-sim isolated)
        self._persist_run_lineage(run_id, params, summary)

    def _persist_run_lineage(self, run_id: str, params: Dict[str, Any], summary: Dict[str, Any]):
        try:
            from kernel.simulation_version import sync_from_git
            v = sync_from_git(self.simulator)
            version_id = v["version_id"] if v else f"{self.simulator}@V0"
            horizon = int(summary.get("step_count", params.get("years", 0)) or 0)
            # DB
            from kernel.persistence.db import kernel_db
            kernel_db.save_simulation_run(run_id, version_id, params, None, summary, horizon=horizon, simulator=self.simulator)
            # Episodic memory (kernel) + filesystem data/memory/episodic
            try:
                from kernel.memory.episodic_memory import episodic_memory
                episodic_memory.create_episode(
                    episode_id=f"simrun_{self.simulator}_{run_id}",
                    episode_type="simulation_run",
                    summary=f"{self.simulator} {run_id} pop={summary.get('population')} wealth={summary.get('total_wealth',0):.1f}",
                    tags=["simulation", self.simulator, run_id, version_id],
                    metadata={"simulator": self.simulator, "version_id": version_id, "run_id": run_id, "parameters": params, "result": summary},
                    importance=0.7,
                )
            except Exception:
                pass
            # filesystem episodic as requested: data/memory/episodic/{simulator}_{run_id}.json
            try:
                epi_root = Path(_codebase_root()).parent / "data" / "memory" / "episodic"
                # _codebase_root is .../codebase, parent is workspace
                alt = Path(_codebase_root()) / ".." / "data" / "memory" / "episodic"
                for root in (epi_root, alt.resolve() if alt.exists() else None):
                    if root is None:
                        continue
                    root.mkdir(parents=True, exist_ok=True)
                    with open(root / f"{self.simulator}_{run_id}.json", "w") as f:
                        json.dump({"episode_id": f"simrun_{self.simulator}_{run_id}", "simulator": self.simulator, "version_id": version_id, "run_id": run_id, "parameters": params, "result": summary, "timestamp": summary.get("timestamp")}, f, indent=2)
            except Exception:
                pass
        except Exception:
            pass
    def _generate_summary(
        self,
        run_id: str,
        model: SimulationModel,
        signals: List[Dict[str, Any]],
    ) -> str:
        """Generate readable summary."""
        s = model.summary()
        signal_types = [sig["signal_type"] for sig in signals]
        lines = [
            f"=== Simulation Run: {run_id} ===",
            f"Years: {s['step_count']}",
            f"Population: {s['population']}",
            f"Wealth: {s['total_wealth']:.1f}",
            f"S births: {s['births']}",
            f"  Deaths: {s['deaths']}",
            f"Signals: {signal_types}",
        ]
        return "\n".join(lines)
    def get_signals(self, run_id: str) -> List[Dict[str, Any]]:
        """Read signals for a simulation run (per-sim sharded + legacy fallback)."""
        signals_path = self._resolve_run_path(run_id) / "signals.json"
        if not signals_path.exists():
            return []
        with open(signals_path) as f:
            return json.load(f)

    def get_params(self, run_id: str) -> Dict[str, Any]:
        """Read params for a simulation run."""
        params_path = self._resolve_run_path(run_id) / "params.yaml"
        if not params_path.exists():
            return {}
        with open(params_path) as f:
            data = yaml.safe_load(f) or {}
        if data.get("seed") in ("None", "null"):
            data["seed"] = None
        return data

    def compare_runs(
        self,
        run_ids: List[str],
    ) -> str:
        """
        Compare multiple simulation runs.
        
        Args:
            run_ids: List of run IDs to compare
            
        Returns:
            Comparison string
        """
        runs = []
        for run_id in run_ids:
            summary_path = self._resolve_run_path(run_id) / "summary.json"
            if summary_path.exists():
                with open(summary_path) as f:
                    runs.append(json.load(f))
        if not runs:
            return "No runs found"
        lines = ["=== Run Comparison ==="]
        headers = ["Run", "Pop", "Wealth", "Births", "Deaths"]
        lines.append(" | ".join(headers))
        lines.append("-" * 50)
        for r in runs:
            row = [
                r.get("run_id", "??"),
                str(r.get("population", 0)),
                f"{r.get('total_wealth', 0):.0f}",
                str(r.get("births", 0)),
                str(r.get("deaths", 0)),
            ]
            lines.append(" | ".join(row))
        return "\n".join(lines)
    def inject_policy(
        self,
        base_run_id: str,
        policy: Dict[str, Any],
        new_run_id: str,
    ) -> str:
        """
        Inject policy into base run and re-run.

        Args:
            base_run_id: Base run to modify
            policy: Policy params to inject ({param: value})
            new_run_id: New run ID
            
        Returns:
            Summary string
        """
        base_params = self.get_params(base_run_id)
        if not base_params:
            return f"Base run {base_run_id} not found"
        params = {**base_params, **policy}
        return self.run_and_extract(params, new_run_id)
    def list_runs(self) -> List[str]:
        """List all simulation runs (data/units + legacy codebase fallback)."""
        runs: set[str] = set()
        if self.base_path.exists():
            for p in self.base_path.iterdir():
                if p.is_dir():
                    runs.add(p.name)
        # include legacy codebase sharded/shared for backward compat
        for cand in [self._legacy_base() / self.simulator, self._legacy_base()]:
            if cand.exists() and cand != self.base_path:
                for p in cand.iterdir():
                    if p.is_dir() and p.name not in ("popula_dyn", "eco_sim") and (p / "summary.json").exists():
                        runs.add(p.name)
        return sorted(runs)

    def generate_structured_premise(
        self,
        run_id: str,
        baseline_run_id: str = None,
        all_runs: List[str] = None,
    ) -> str:
        """
        Generate contradiction-friendly structured premise.

        Format:
        Verdict: {IMPROVED|DEGRADED|STABLE|COLLAPSED}
        Change: {metric} {old}→{new} ({percent_change})
        Deaths: {count} ({trend} vs baseline {baseline})
        Interpretation: {why it happened based on signals}
        Contradicts: {prior runs with opposite outcomes}
        """
        summary = self._read_summary(run_id)
        signals = self.get_signals(run_id)
        params = self.get_params(run_id)

        pop = summary.get("population", 0)
        deaths = summary.get("deaths_total", summary.get("deaths", 0))
        births = summary.get("births_total", summary.get("births", 0))
        wealth = summary.get("total_wealth", 0)
        avg_skill = summary.get("avg_skill", 0)

        baseline = None
        baseline_deaths = 0
        baseline_pop = 0
        baseline_wealth = 0

        if baseline_run_id:
            baseline = self._read_summary(baseline_run_id)
            if baseline:
                baseline_deaths = baseline.get("deaths_total", baseline.get("deaths", 0))
                baseline_pop = baseline.get("population", 0)
                baseline_wealth = baseline.get("total_wealth", 0)

        pop_change_pct = 0
        if baseline_pop and baseline_pop > 0:
            pop_change_pct = ((pop - baseline_pop) / baseline_pop) * 100

        death_trend = "STABLE"
        if deaths < baseline_deaths * 0.8:
            death_trend = "REDUCED"
        elif deaths > baseline_deaths * 1.5:
            death_trend = "SPIKED"

        verdict = "STABLE"
        if pop_change_pct > 20:
            verdict = "IMPROVED"
        elif pop_change_pct < -20:
            verdict = "DEGRADED"
        if pop < 5:
            verdict = "COLLAPSED"

        signal_summary = []
        for sig in signals:
            st = sig.get("signal_type", "")
            intensity = sig.get("intensity", 0)
            if intensity >= 7:
                signal_summary.append(f"{st}={sig.get('value')} intensity={intensity}(HIGH)")
            elif intensity >= 5:
                signal_summary.append(f"{st}={sig.get('value')} intensity={intensity}")

        interpretation_parts = []
        if births == 0 and deaths > 0:
            interpretation_parts.append("Zero total births with deaths suggest fertile window or partner availability bottleneck")
        if deaths > baseline_deaths * 2 and baseline_deaths > 0:
            interpretation_parts.append("Death spike likely caused by wealth-based starvation multiplier")
        if wealth < baseline_wealth * 0.8 and baseline_wealth > 0:
            interpretation_parts.append("Wealth decline may indicate resource depletion")
        if not interpretation_parts:
            interpretation_parts.append("No obvious failure mode detected")

        lines = [
            f"Status: {verdict}",
            f"Population: {pop} (baseline {baseline_pop}) {pop_change_pct:+.1f}%",
            f"Deaths: {deaths} ({death_trend} vs baseline {baseline_deaths})",
            f" Births: {births}",
            f" Wealth: {wealth:.1f} (baseline {baseline_wealth:.1f})",
            f" AvgSkill: {avg_skill:.2f}",
            f" Signals: {'; '.join(signal_summary) if signal_summary else 'none'}",
            f" Interpretation: {'; '.join(interpretation_parts)}",
        ]

        return "\n".join(lines)

    def _read_summary(self, run_id: str) -> dict:
        summary_path = self._resolve_run_path(run_id) / "summary.json"
        if not summary_path.exists():
            return {}
        with open(summary_path) as f:
            return json.load(f)

    def build_observation(
        self,
        run_id: str,
        baseline_run_id: str = None,
    ) -> Dict[str, Any]:
        """Build typed observation for symbolic gate (FixesIssues.md)."""
        summary = self._read_summary(run_id)
        params = self.get_params(run_id)
        signals = self.get_signals(run_id)
        pop = summary.get("population", 0)
        wealth = summary.get("total_wealth", 0)
        deaths = summary.get("deaths_total", summary.get("deaths", 0))
        births = summary.get("births_total", summary.get("births", 0))
        years = params.get("years", summary.get("step_count", 0))

        baseline_pop = 0
        baseline_wealth = 0
        if baseline_run_id:
            b = self._read_summary(baseline_run_id)
            baseline_pop = b.get("population", 0)
            baseline_wealth = b.get("total_wealth", 0)

        pop_change_pct = ((pop - baseline_pop) / baseline_pop * 100) if baseline_pop else 0.0
        verdict = "STABLE"
        if pop_change_pct > 20:
            verdict = "IMPROVED"
        elif pop_change_pct < -20:
            verdict = "DEGRADED"
        if pop < 5:
            verdict = "COLLAPSED"

        direction = "STABLE"
        if verdict == "IMPROVED":
            direction = "INCREASE"
        elif verdict in ("DEGRADED", "COLLAPSED"):
            direction = "DECREASE"

        # scenario = delta vs baseline params (key params)
        scenario = {}
        if baseline_run_id:
            base_params = self.get_params(baseline_run_id)
            for k in ("birth_rate", "death_rate", "initial_pop", "years"):
                if params.get(k) != base_params.get(k):
                    scenario[k] = params.get(k)
        else:
            scenario = {k: params.get(k) for k in ("birth_rate", "death_rate") if k in params}

        # per-simulator version (git-scoped, strictly isolated)
        try:
            from kernel.simulation_version import sync_from_git
            v = sync_from_git(self.simulator)
            version_id = v["version_id"] if v else f"{self.simulator}@V0"
        except Exception:
            version_id = f"{self.simulator}@V0"
        return {
            "experiment": run_id,
            "simulator": self.simulator,
            "version_id": version_id,
            "scenario": scenario,
            "baseline": baseline_run_id or "none",
            "metric": "population",
            "baseline_value": baseline_pop,
            "observed_value": pop,
            "delta": round(pop_change_pct, 1),
            "direction": direction,
            "outcome": verdict,
            "horizon": years,
            "wealth": wealth,
            "wealth_delta": round(((wealth - baseline_wealth) / baseline_wealth * 100) if baseline_wealth else 0, 1),
            "deaths": deaths,
            "births": births,
            "signals": [s.get("signal_type") for s in signals],
        }

    def register_to_kernel(
        self,
        run_id: str,
        premise: str = None,
        baseline_run_id: str = None,
    ) -> dict:
        """
        Register simulation findings to kernel topic graph.
        Creates finding node with structured premise + typed observation metadata.
        Auto-creates contradicts edge via symbolic comparison.
        """
        if premise is None:
            premise = self.generate_structured_premise(run_id, baseline_run_id)
        obs = self.build_observation(run_id, baseline_run_id)
        verdict = obs.get("outcome", "STABLE")
        name = f"{run_id} Findings"
        # direct topic_store path to pass metadata (keeps subprocess fallback)
        try:
            import sys, pathlib, json as _json
            modules_path = str(pathlib.Path(__file__).resolve().parents[1])
            if modules_path not in sys.path:
                sys.path.insert(0, modules_path)
            codebase_path = str(pathlib.Path(__file__).resolve().parents[2].parent)
            # codebase is .../codebase, already via earlier import; ensure kernel importable
            if codebase_path not in sys.path:
                sys.path.insert(0, codebase_path + "/codebase")
                sys.path.insert(0, str(pathlib.Path(__file__).resolve().parents[3]))
            from argu_god.engine.topic_store import add_node, add_edge
            from kernel.hypothesis.contradiction_gate import check_observation_contradiction
            # strictly isolated per simulator: topic + validity
            meta = {"observation": obs, "baseline": obs.get("baseline"), "metric": obs.get("metric"), "outcome": verdict, "direction": obs.get("direction"), "horizon": obs.get("horizon"), "scenario": obs.get("scenario"), "simulator": obs.get("simulator"), "version_id": obs.get("version_id"), "validity": {"valid_for_version": obs.get("version_id"), "status": "ACTIVE", "simulator": obs.get("simulator")}}
            res = add_node(self.topic, {"name": name, "premise": premise, "side": "argument", "type": "observation", "metadata": meta}, force=False)
            edges_created = []
            if res.get("kind") == "node_added":
                blocked, sym = check_observation_contradiction(self.topic, obs)
                for c in sym:
                    target = c.get("title")
                    if target and target != name:
                        try:
                            e = add_edge(self.topic, name, target, "contradicts", force=True)
                            if e.get("kind") == "edge_added":
                                edges_created.append(f"{name} <-> {target}")
                        except Exception:
                            pass
            return {"run_id": run_id, "name": name, "verdict": verdict, "observation": obs, "topic_store_result": res, "edges_created": edges_created, "returncode": 0, "stdout": str(res), "stderr": ""}
        except Exception as e:
            import subprocess as sp, json as _js
            meta_json = _js.dumps({"observation": obs, "baseline": obs.get("baseline"), "metric": obs.get("metric"), "outcome": verdict, "direction": obs.get("direction"), "horizon": obs.get("horizon"), "simulator": obs.get("simulator"), "version_id": obs.get("version_id"), "validity": {"valid_for_version": obs.get("version_id"), "status": "ACTIVE", "simulator": obs.get("simulator")}})
            result = sp.run(["python", "scripts/topic_ops.py", "add-node", "--topic", self.topic, "--name", name, "--premise", premise, "--side", "argument", "--type", "observation", "--metadata", meta_json, "--json"], capture_output=True, text=True, cwd=str(self.base_path.parent.parent.parent))
            return {"run_id": run_id, "name": name, "verdict": verdict, "observation": obs, "returncode": result.returncode, "stdout": result.stdout, "stderr": result.stderr + f" direct_err:{e}"}