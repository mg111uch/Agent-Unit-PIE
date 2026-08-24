"""
VSE - Virtual Silicon Engine
vse/search.py

Phase 6: hardware architecture search.

Iterates a design space of `ArchitectureSpec` candidates, compiles and
simulates the target workload on each, scores by tokens/sec, and returns
the best candidates plus the Pareto frontier (tokens/sec vs a silicon
cost proxy).
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Optional

from vse.silicon.area import estimate_area
from vse.search.architecture import ArchitectureSpec, SearchSpace
from vse.compiler.compiler import execute
from vse.silicon.power import estimate_power
from vse.report.result import EndToEndResult


@dataclass
class SearchResult:
    """One candidate chip + its simulated outcome."""

    spec: ArchitectureSpec
    result: EndToEndResult
    plausible: bool = True
    gate: Optional[object] = None
    gate_result: Optional[object] = None

    def __post_init__(self):
        # keep gate and gate_result synced for backward compat
        if self.gate is not None and self.gate_result is None:
            object.__setattr__(self, "gate_result", self.gate)
        elif self.gate_result is not None and self.gate is None:
            object.__setattr__(self, "gate", self.gate_result)

    @property
    def tokens_per_second(self) -> float:
        return self.result.tokens_per_second

    @property
    def total_cycles(self) -> int:
        return self.result.total_cycles

    @property
    def area_proxy(self) -> float:
        return self.spec.area_proxy

    @property
    def power_proxy(self) -> float:
        return self.spec.power_proxy

    @property
    def area_mm2(self) -> float:
        """Real Phase-7 die-area estimate (total, mm²)."""
        return estimate_area(
            self.spec,
            tech=self.spec.technology,
        ).total_area_mm2

    @property
    def power_watts(self) -> float:
        """Real Phase-7 average-power estimate (W, incl. leakage)."""
        return estimate_power(
            self.result,
            tech=self.spec.technology,
            chip=self.spec,
        ).average_power_watts

    @property
    def energy_per_token_uj(self) -> float:
        return estimate_power(
            self.result,
            tech=self.spec.technology,
            chip=self.spec,
        ).energy_per_token_uj

    @property
    def tokens_per_watt(self) -> float:
        return estimate_power(
            self.result,
            tech=self.spec.technology,
            chip=self.spec,
        ).tokens_per_watt

    def report(self) -> dict:
        out = {
            "arch": self.spec.label(),
            "num_pes": self.spec.num_pes,
            "macs_per_pe": self.spec.macs_per_pe,
            "frequency_hz": self.spec.frequency_hz,
            "sram_bytes": self.spec.sram_bytes,
            "hbm_bytes_per_cycle": self.spec.hbm_bytes_per_cycle,
            "weight_bits": self.spec.weight_bits,
            "total_cycles": self.total_cycles,
            "tokens_per_second": self.tokens_per_second,
            "compute_utilization": self.result.compute_utilization,
            "memory_utilization": self.result.memory_utilization,
            "area_proxy": self.area_proxy,
            "power_proxy": self.power_proxy,
            "area_mm2": self.area_mm2,
            "power_watts": self.power_watts,
            "energy_per_token_uj": (
                self.energy_per_token_uj
            ),
            "tokens_per_watt": self.tokens_per_watt,
            "plausible": self.plausible,
        }
        g = self.gate if self.gate is not None else self.gate_result
        if g is not None:
            try:
                checks = [
                    {
                        "name": getattr(c, "name", "?"),
                        "passed": bool(getattr(c, "passed", False)),
                        "expected": getattr(c, "expected", None),
                        "measured": getattr(c, "measured", None),
                        "unit": getattr(c, "unit", ""),
                    }
                    for c in getattr(g, "checks", [])
                ]
                out["physics"] = {
                    "plausible": bool(getattr(g, "plausible", getattr(g, "overall_pass", True))),
                    "overall_pass": bool(getattr(g, "overall_pass", getattr(g, "plausible", True))),
                    "checks": checks,
                }
            except Exception:
                out["physics"] = {"plausible": self.plausible, "overall_pass": self.plausible, "checks": []}
        elif not self.plausible:
            out["physics"] = {"plausible": False, "overall_pass": False, "checks": []}
        # also include inner result physics if present for deep inspect
        try:
            inner = getattr(self.result, "_gate_dict", None)
            if callable(inner):
                gd = inner()
                if gd and "physics" not in out:
                    out["physics"] = gd
            elif hasattr(self.result, "gate") and getattr(self.result, "gate", None) is not None:
                gd = self.result._gate_dict() if hasattr(self.result, "_gate_dict") else None
                if gd and "physics" not in out:
                    out["physics"] = gd
        except Exception:
            pass
        return out


def _check_gate(outcome, spec):
    """Lazy PhysicsGate check; returns (plausible, gate_result)."""
    try:
        from vse.physics.gate import PhysicsGate  # lazy

        gate = PhysicsGate.check(outcome, spec)
        return bool(gate.plausible), gate
    except Exception:
        return True, None


def run_search(
    space: SearchSpace,
    build_program,
    base: Optional[ArchitectureSpec] = None,
    physics: str = "off",
) -> list[SearchResult]:
    """
    Compile and simulate every candidate in `space`.

    `build_program(spec) -> CompiledProgram` is supplied by the caller
    (it owns the model + workload definition).
    physics: off|warn|fail — gate implausible candidates.
    """

    if physics not in ("off", "warn", "fail"):
        raise ValueError(f"physics must be off/warn/fail, got {physics}")
    if base is None:
        base = ArchitectureSpec()

    results: list[SearchResult] = []

    for spec in space.specs(base):
        program = build_program(spec)
        outcome = execute(program)
        plausible = True
        gate = None
        if physics != "off":
            plausible, gate = _check_gate(outcome, spec)
            try:
                outcome.gate = gate  # type: ignore
                outcome.gate_result = gate  # type: ignore
            except Exception:
                pass
            if physics == "fail" and not plausible:
                continue
        results.append(
            SearchResult(spec=spec, result=outcome, plausible=plausible, gate=gate, gate_result=gate)
        )

    return results


def run_random_search(
    space: SearchSpace,
    build_program,
    n: int,
    base: Optional[ArchitectureSpec] = None,
    seed: Optional[int] = None,
    physics: str = "off",
) -> list[SearchResult]:
    """
    Sample `n` random candidates from `space` and simulate each.

    Lets a search explore far more of a large design space than the
    full explicit grid, at a fixed cost (`n` simulations).
    physics: off|warn|fail — gate implausible candidates.
    """

    if physics not in ("off", "warn", "fail"):
        raise ValueError(f"physics must be off/warn/fail, got {physics}")
    if base is None:
        base = ArchitectureSpec()

    results: list[SearchResult] = []

    for spec in space.sample_specs(n, base, seed):
        program = build_program(spec)
        outcome = execute(program)
        plausible = True
        gate = None
        if physics != "off":
            plausible, gate = _check_gate(outcome, spec)
            try:
                outcome.gate = gate  # type: ignore
                outcome.gate_result = gate  # type: ignore
            except Exception:
                pass
            if physics == "fail" and not plausible:
                continue
        results.append(
            SearchResult(spec=spec, result=outcome, plausible=plausible, gate=gate, gate_result=gate)
        )

    return results


def _get_val(obj, attr: str) -> float:
    """Resolve attribute to float; handles callables & AccuracyEstimate."""
    if hasattr(obj, attr):
        v = getattr(obj, attr)
        if callable(v):
            try:
                v = v()
            except Exception:
                pass
        if v is not None and v.__class__.__name__ == "AccuracyEstimate":
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
    # accuracy aliases -> accuracy_score
    if attr in ("accuracy", "acc", "coding_score", "pass_at_k", "accuracy_score"):
        for cand in ("accuracy_score", "accuracy", "acc"):
            if hasattr(obj, cand):
                try:
                    v = getattr(obj, cand)
                    if callable(v):
                        v = v()
                    if v is not None and v.__class__.__name__ == "AccuracyEstimate":
                        for k in ("coding_score", "pass_at_k"):
                            if hasattr(v, k):
                                return float(getattr(v, k))
                        return 0.0
                    return float(v)
                except Exception:
                    continue
        return 0.0
    if hasattr(obj, "result") and hasattr(obj.result, attr):
        try:
            return float(getattr(obj.result, attr))
        except Exception:
            pass
    return 0.0


def _normalize_objectives(objectives=None, maximize=None, minimize=None):
    """Convert various forms to list of (attr, direction)."""
    if objectives is not None:
        # objectives: list of (attr, "max"/"min") or dict
        norm = []
        for item in objectives:
            if isinstance(item, (list, tuple)) and len(item) == 2:
                attr, direction = item
                d = str(direction).lower()
                if d not in ("max", "min", "maximize", "minimize"):
                    raise ValueError(f"unknown direction: {direction}")
                norm.append((attr, "max" if d.startswith("max") else "min"))
            elif isinstance(item, dict):
                for k, v in item.items():
                    d = str(v).lower()
                    norm.append((k, "max" if d.startswith("max") else "min"))
            else:
                raise ValueError(f"bad objective entry: {item}")
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


def pareto_frontier(
    results: list[SearchResult],
    maximize: str | list[str] = "tokens_per_second",
    minimize: str | list[str] = "area_mm2",
) -> list[SearchResult]:
    """
    Keep only Pareto-optimal candidates: no other result is at least as
    good on all objectives and strictly better on one.

    Accepts single attr or list for maximize/minimize (backward compatible).
    For more than 2 objectives use pareto_frontier_multi.
    Input order is preserved.
    """
    # fast path for classic 2-objective case
    if isinstance(maximize, str) and isinstance(minimize, str):
        def get(item: SearchResult) -> tuple:
            return (
                _get_val(item, minimize),
                _get_val(item, maximize),
            )

        frontier: list[SearchResult] = []

        for item in results:
            area, tokens = get(item)
            dominated = False

            for other in results:
                if other is item:
                    continue
                other_area, other_tokens = get(other)
                if (
                    other_area <= area
                    and other_tokens >= tokens
                    and (
                        other_area < area
                        or other_tokens > tokens
                    )
                ):
                    dominated = True
                    break

            if not dominated:
                frontier.append(item)

        return frontier

    # multi-objective path
    objectives = _normalize_objectives(maximize=maximize, minimize=minimize)
    return pareto_frontier_multi(results, objectives=objectives)


def pareto_frontier_multi(
    results: list,
    objectives: list[tuple[str, str]] | None = None,
    *,
    maximize: list[str] | str | None = None,
    minimize: list[str] | str | None = None,
) -> list:
    """
    Generic multi-objective Pareto frontier.

    Args:
        results: list of any objects with numeric attributes.
        objectives: list of (attr, direction) where direction is
            "max"/"maximize" or "min"/"minimize".
            e.g. [("tokens_per_second","max"), ("area_mm2","min")]
        maximize/minimize: alternative kwargs (list or single attr).

    A result is dominated if another result is >= on all maximize
    and <= on all minimize and strictly better on at least one.
    """
    objs = _normalize_objectives(objectives, maximize, minimize)
    frontier: list = []
    for item in results:
        vals = {attr: _get_val(item, attr) for attr, _ in objs}
        dominated = False
        for other in results:
            if other is item:
                continue
            better_or_eq = True
            strictly_better = False
            for attr, direction in objs:
                v = vals[attr]
                ov = _get_val(other, attr)
                if direction == "max":
                    if ov < v:
                        better_or_eq = False
                        break
                    if ov > v:
                        strictly_better = True
                else:  # min
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


__all__ = [
    "SearchResult",
    "run_search",
    "run_random_search",
    "pareto_frontier",
    "pareto_frontier_multi",
]
