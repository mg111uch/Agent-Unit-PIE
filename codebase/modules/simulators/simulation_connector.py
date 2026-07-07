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
import yaml
from pathlib import Path
from datetime import datetime
from typing import Dict, Any, List, Optional

from modules.simulators.popula_dyn.core.simulation_model import SimulationModel
from modules.simulators.popula_dyn.constants import PARAMS

class SimulationConnector:
    """
    Bridge between popula_dyn and kernel cognition.
    """
    def __init__(
        self,
        base_path: str = "units/simulations",
        emit_to_kernel: bool = True,
    ):
        self.base_path = Path(base_path)
        self.base_path.mkdir(parents=True, exist_ok=True)
        self.emit_to_kernel = emit_to_kernel
        self._signal_engine = None
        if emit_to_kernel:
            try:
                from kernel.signals.signal_engine import signal_engine
                self._signal_engine = signal_engine
            except ImportError:
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
    def _store_run(
        self,
        run_id: str,
        params: Dict[str, Any],
        model: SimulationModel,
        signals: List[Dict[str, Any]],
    ) -> None:
        """Store run data in units/simulations/{run_id}/"""
        run_path = self.base_path / run_id
        run_path.mkdir(parents=True, exist_ok=True)
        if "seed" in params:
            params["seed"] = str(params["seed"])
        with open(run_path / "params.yaml", "w") as f:
            yaml.dump(params, f)
        with open(run_path / "signals.json", "w") as f:
            json.dump(signals, f, indent=2)
        df = model.get_dataframe()
        df.to_csv(run_path / "data.csv", index=False)
        summary = model.summary()
        summary["run_id"] = run_id
        summary["timestamp"] = datetime.utcnow().isoformat()
        with open(run_path / "summary.json", "w") as f:
            json.dump(summary, f, indent=2)
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
        """Read signals for a simulation run."""
        signals_path = self.base_path / run_id / "signals.json"
        if not signals_path.exists():
            return []
        with open(signals_path) as f:
            return json.load(f)

    def get_params(self, run_id: str) -> Dict[str, Any]:
        """Read params for a simulation run."""
        params_path = self.base_path / run_id / "params.yaml"
        if not params_path.exists():
            return {}
        with open(params_path) as f:
            return yaml.safe_load(f)

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
            summary_path = self.base_path / run_id / "summary.json"
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
        """List all simulation runs."""
        if not self.base_path.exists():
            return []
        return [p.name for p in self.base_path.iterdir() if p.is_dir()]