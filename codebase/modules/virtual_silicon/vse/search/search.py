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
        return {
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
        }


def run_search(
    space: SearchSpace,
    build_program,
    base: Optional[ArchitectureSpec] = None,
) -> list[SearchResult]:
    """
    Compile and simulate every candidate in `space`.

    `build_program(spec) -> CompiledProgram` is supplied by the caller
    (it owns the model + workload definition).
    """

    if base is None:
        base = ArchitectureSpec()

    results: list[SearchResult] = []

    for spec in space.specs(base):
        program = build_program(spec)
        outcome = execute(program)
        results.append(
            SearchResult(spec=spec, result=outcome)
        )

    return results


def run_random_search(
    space: SearchSpace,
    build_program,
    n: int,
    base: Optional[ArchitectureSpec] = None,
    seed: Optional[int] = None,
) -> list[SearchResult]:
    """
    Sample `n` random candidates from `space` and simulate each.

    Lets a search explore far more of a large design space than the
    full explicit grid, at a fixed cost (`n` simulations).
    """

    if base is None:
        base = ArchitectureSpec()

    results: list[SearchResult] = []

    for spec in space.sample_specs(n, base, seed):
        program = build_program(spec)
        outcome = execute(program)
        results.append(
            SearchResult(spec=spec, result=outcome)
        )

    return results


def pareto_frontier(
    results: list[SearchResult],
    maximize: str = "tokens_per_second",
    minimize: str = "area_mm2",
) -> list[SearchResult]:
    """
    Keep only Pareto-optimal candidates: no other result is at least as
    good on both objectives and strictly better on one.

    Input order is preserved.
    """

    def get(item: SearchResult) -> tuple:
        return (
            getattr(item, minimize),
            getattr(item, maximize),
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


__all__ = [
    "SearchResult",
    "run_search",
    "run_random_search",
    "pareto_frontier",
]
