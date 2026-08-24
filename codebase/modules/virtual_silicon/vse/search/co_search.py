"""Model ↔ hardware co-search — Phase E.

Jointly enumerates ModelArchSpec × ArchitectureSpec, compiles and executes
each pair, and scores accuracy + perf + area + power.

Provides CoSearchResult, run_co_search, run_random_co_search, pareto helpers.
"""

from __future__ import annotations

import random
from dataclasses import dataclass
from itertools import product
from typing import Callable, List, Optional

from vse.compiler.compiler import CompiledProgram, execute
from vse.report.result import EndToEndResult
from vse.search.architecture import ArchitectureSpec, SearchSpace
from vse.search.model_space import ModelArchSpec, ModelSearchSpace
from vse.silicon.area import estimate_area
from vse.silicon.power import estimate_power


def _accuracy_for(model_spec: ModelArchSpec, arch_spec: ArchitectureSpec, precision_map=None):
    # Prefer explicit precision_map, else arch_spec.precision_map, else model weight_bits uniform
    pm = precision_map
    if pm is None and getattr(arch_spec, "precision_map", None) is not None:
        pm = getattr(arch_spec, "precision_map")
    try:
        return model_spec.estimate_accuracy(pm)
    except Exception:
        from vse.models.accuracy import estimate_accuracy as _ea

        return _ea(pm)


def _get_numeric(obj, attr: str) -> float:
    """Resolve attribute to float; handles AccuracyEstimate and nested."""
    # direct attr on result wrapper
    if hasattr(obj, attr):
        v = getattr(obj, attr)
        if callable(v):
            try:
                v = v()
            except Exception:
                pass
        # AccuracyEstimate -> scalar coding_score
        if v is not None and v.__class__.__name__ == "AccuracyEstimate":
            # prefer coding_score then pass_at_k
            for k in ("coding_score", "pass_at_k", "bits_avg"):
                if hasattr(v, k):
                    try:
                        return float(getattr(v, k))
                    except Exception:
                        continue
            return 0.0
        try:
            return float(v)
        except Exception:
            return 0.0
    # accuracy special
    if attr in ("accuracy", "acc", "coding_score", "pass_at_k"):
        acc = getattr(obj, "accuracy", None)
        if acc is None:
            return 0.0
        if isinstance(acc, (int, float)):
            return float(acc)
        for k in ("coding_score", "pass_at_k", "bits_avg", "ppl_delta"):
            if hasattr(acc, k):
                try:
                    return float(getattr(acc, k))
                except Exception:
                    continue
        try:
            return float(acc)
        except Exception:
            return 0.0
    # fallback via result
    if hasattr(obj, "result") and hasattr(obj.result, attr):
        try:
            return float(getattr(obj.result, attr))
        except Exception:
            pass
    return 0.0


@dataclass
class CoSearchResult:
    """One model×hardware candidate plus its simulated outcome."""

    model_spec: ModelArchSpec
    arch_spec: ArchitectureSpec
    result: EndToEndResult
    accuracy: object = None  # AccuracyEstimate

    @property
    def tokens_per_second(self) -> float:
        return self.result.tokens_per_second

    @property
    def total_cycles(self) -> int:
        return self.result.total_cycles

    @property
    def area_proxy(self) -> float:
        return self.arch_spec.area_proxy

    @property
    def power_proxy(self) -> float:
        return self.arch_spec.power_proxy

    @property
    def area_mm2(self) -> float:
        try:
            return estimate_area(self.arch_spec, tech=self.arch_spec.technology).total_area_mm2
        except Exception:
            try:
                return estimate_area(self.arch_spec).total_area_mm2
            except Exception:
                return float(self.area_proxy)

    @property
    def power_watts(self) -> float:
        try:
            return estimate_power(self.result, tech=self.arch_spec.technology, chip=self.arch_spec).average_power_watts
        except Exception:
            try:
                return estimate_power(self.result, chip=self.arch_spec).average_power_watts
            except Exception:
                return float(self.power_proxy)

    @property
    def energy_per_token_uj(self) -> float:
        try:
            return estimate_power(self.result, tech=self.arch_spec.technology, chip=self.arch_spec).energy_per_token_uj
        except Exception:
            return 0.0

    @property
    def tokens_per_watt(self) -> float:
        try:
            return estimate_power(self.result, tech=self.arch_spec.technology, chip=self.arch_spec).tokens_per_watt
        except Exception:
            pw = self.power_watts
            return self.tokens_per_second / pw if pw > 0 else 0.0

    @property
    def tokens_per_mm2(self) -> float:
        a = self.area_mm2
        return self.tokens_per_second / a if a > 0 else 0.0

    @property
    def parameter_count(self) -> int:
        return self.model_spec.parameter_count()

    @property
    def accuracy_score(self) -> float:
        if self.accuracy is None:
            return 0.0
        if isinstance(self.accuracy, (int, float)):
            return float(self.accuracy)
        for k in ("coding_score", "pass_at_k"):
            if hasattr(self.accuracy, k):
                try:
                    return float(getattr(self.accuracy, k))
                except Exception:
                    continue
        try:
            return float(self.accuracy)  # type: ignore
        except Exception:
            return 0.0

    def model_label(self) -> str:
        return self.model_spec.label()

    def arch_label(self) -> str:
        return self.arch_spec.label()

    def label(self) -> str:
        return f"{self.model_label()} | {self.arch_label()}"

    def report(self) -> dict:
        acc_rep = None
        if self.accuracy is not None:
            if hasattr(self.accuracy, "report"):
                try:
                    acc_rep = self.accuracy.report()  # type: ignore
                except Exception:
                    acc_rep = str(self.accuracy)
            else:
                acc_rep = self.accuracy
        out = {
            "model": self.model_label(),
            "arch": self.arch_label(),
            "layers": self.model_spec.layers,
            "hidden_dim": self.model_spec.hidden_dim,
            "num_heads": self.model_spec.num_heads,
            "intermediate_dim": self.model_spec.intermediate_dim,
            "parameter_count": self.parameter_count,
            "accuracy": acc_rep,
            "accuracy_score": self.accuracy_score,
            "total_cycles": self.total_cycles,
            "tokens_per_second": self.tokens_per_second,
            "area_mm2": self.area_mm2,
            "power_watts": self.power_watts,
            "tokens_per_watt": self.tokens_per_watt,
            "tokens_per_mm2": self.tokens_per_mm2,
            "energy_per_token_uj": self.energy_per_token_uj,
        }
        # include physics if attached to inner result
        try:
            g = getattr(self.result, "gate", None) or getattr(self.result, "gate_result", None)
            if g is not None:
                out["physics"] = {
                    "plausible": bool(getattr(g, "plausible", getattr(g, "overall_pass", True))),
                    "overall_pass": bool(getattr(g, "overall_pass", getattr(g, "plausible", True))),
                    "checks": [
                        {"name": getattr(c, "name", "?"), "passed": bool(getattr(c, "passed", False)), "expected": getattr(c, "expected", None), "measured": getattr(c, "measured", None), "unit": getattr(c, "unit", "")}
                        for c in getattr(g, "checks", [])
                    ],
                }
            elif hasattr(self.result, "_gate_dict"):
                gd = self.result._gate_dict()  # type: ignore
                if gd:
                    out["physics"] = gd
        except Exception:
            pass
        return out


def run_co_search(
    model_space: ModelSearchSpace,
    hw_space: SearchSpace,
    build_fn: Callable[[ModelArchSpec, ArchitectureSpec], CompiledProgram],
    base_model: Optional[ModelArchSpec] = None,
    base_arch: Optional[ArchitectureSpec] = None,
) -> List[CoSearchResult]:
    """Enumerate cross-product of model×hardware specs, compile+execute each."""
    if base_model is None:
        base_model = ModelArchSpec()
    if base_arch is None:
        base_arch = ArchitectureSpec()
    model_specs = model_space.specs(base_model)
    hw_specs = hw_space.specs(base_arch)
    results: List[CoSearchResult] = []
    for m_spec, a_spec in product(model_specs, hw_specs):
        program = build_fn(m_spec, a_spec)
        outcome = execute(program)
        acc = _accuracy_for(m_spec, a_spec, getattr(program, "plan", {}).get("precision", {}).get("map") if hasattr(program, "plan") else None)
        results.append(CoSearchResult(model_spec=m_spec, arch_spec=a_spec, result=outcome, accuracy=acc))
    return results


def run_random_co_search(
    model_space: ModelSearchSpace,
    hw_space: SearchSpace,
    build_fn: Callable[[ModelArchSpec, ArchitectureSpec], CompiledProgram],
    n: int,
    base_model: Optional[ModelArchSpec] = None,
    base_arch: Optional[ArchitectureSpec] = None,
    seed: Optional[int] = None,
) -> List[CoSearchResult]:
    """Sample n joint model×hardware candidates and simulate each."""
    if n < 1:
        raise ValueError("n must be >= 1")
    if base_model is None:
        base_model = ModelArchSpec()
    if base_arch is None:
        base_arch = ArchitectureSpec()
    rng = random.Random(seed)
    results: List[CoSearchResult] = []
    for _ in range(n):
        m_spec = model_space.sample_specs(1, base_model, seed=rng.randint(0, 2**31 - 1))[0]
        a_spec = hw_space.sample_specs(1, base_arch, seed=rng.randint(0, 2**31 - 1))[0]
        program = build_fn(m_spec, a_spec)
        outcome = execute(program)
        acc = _accuracy_for(m_spec, a_spec, getattr(program, "plan", {}).get("precision", {}).get("map") if hasattr(program, "plan") else None)
        results.append(CoSearchResult(model_spec=m_spec, arch_spec=a_spec, result=outcome, accuracy=acc))
    return results


def _normalize_objs(maximize, minimize, objectives=None):
    if objectives is not None:
        norm = []
        for item in objectives:
            if isinstance(item, (list, tuple)) and len(item) == 2:
                attr, direction = item
                d = str(direction).lower()
                norm.append((attr, "max" if d.startswith("max") else "min"))
            else:
                raise ValueError(f"bad objective: {item}")
        return norm
    norm = []
    if maximize is not None:
        items = maximize if isinstance(maximize, (list, tuple)) else [maximize]
        for a in items:
            norm.append((a, "max"))
    if minimize is not None:
        items = minimize if isinstance(minimize, (list, tuple)) else [minimize]
        for a in items:
            norm.append((a, "min"))
    if not norm:
        norm = [("tokens_per_second", "max"), ("area_mm2", "min")]
    return norm


def pareto_frontier_models(
    results: List[CoSearchResult],
    maximize: List[str] | str | None = None,
    minimize: List[str] | str | None = None,
    objectives: List[tuple[str, str]] | None = None,
) -> List[CoSearchResult]:
    """
    Multi-objective Pareto for models×hardware.

    Defaults: maximize tok/s + accuracy, minimize area.
    A result is dominated if another is >= on all maximize and <= on all
    minimize and strictly better on at least one.
    """
    if maximize is None and minimize is None and objectives is None:
        maximize = ["tokens_per_second", "accuracy_score"]
        minimize = ["area_mm2"]
    objs = _normalize_objs(maximize, minimize, objectives)
    frontier: List[CoSearchResult] = []
    for item in results:
        vals = {attr: _get_numeric(item, attr) for attr, _ in objs}
        dominated = False
        for other in results:
            if other is item:
                continue
            better_or_eq = True
            strictly_better = False
            for attr, direction in objs:
                v = vals[attr]
                ov = _get_numeric(other, attr)
                if direction == "max":
                    if ov < v:
                        better_or_eq = False
                        break
                    if ov > v:
                        strictly_better = True
                else:
                    if ov > v:
                        better_or_eq = False
                        break
                    if ov < v:
                        strictly_better = True
            if better_or_eq and strictly_better:
                dominated = True
                break
        if not dominated:
            frontier.append(item)
    return frontier


def pareto_frontier_multi(
    results: List[CoSearchResult],
    objectives: List[tuple[str, str]] | None = None,
    *,
    maximize: List[str] | str | None = None,
    minimize: List[str] | str | None = None,
) -> List[CoSearchResult]:
    """Alias to pareto_frontier_models with objectives list."""
    return pareto_frontier_models(results, maximize=maximize, minimize=minimize, objectives=objectives)


def pareto_models(
    results: List[CoSearchResult],
    maximize: str | List[str] = "tokens_per_second",
    minimize: str | List[str] = "area_mm2",
) -> List[CoSearchResult]:
    """Keep Pareto-optimal results (supports multi-objective)."""
    # single-objective backward compat -> delegate to multi
    return pareto_frontier_models(results, maximize=maximize, minimize=minimize)


# Alias for compatibility with search.pareto_frontier naming
def pareto_frontier(
    results: List[CoSearchResult],
    maximize: str | List[str] = "tokens_per_second",
    minimize: str | List[str] = "area_mm2",
) -> List[CoSearchResult]:
    return pareto_models(results, maximize=maximize, minimize=minimize)


# Generic pareto alias
pareto = pareto_models

__all__ = [
    "CoSearchResult",
    "run_co_search",
    "run_random_co_search",
    "pareto_models",
    "pareto_frontier",
    "pareto",
    "pareto_frontier_models",
    "pareto_frontier_multi",
]
