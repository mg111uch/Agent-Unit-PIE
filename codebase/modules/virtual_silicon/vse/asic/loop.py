"""
VSE - Virtual Silicon Engine
vse/asic/loop.py

Phase 10: closed-loop ASIC exploration.

Closes the loop from the roadmap:

    Architecture → Simulation → RTL → Physical estimation
    → Updated architecture → Simulation

Starting from one candidate chip, the loop:

    1. compiles + simulates the workload (existing VSE pipeline),
    2. generates the Phase-9 RTL for the same chip,
    3. estimates its physical cost (gates, area, timing closure),
    4. if timing does not close (or the die is not feasible), updates
       the architecture (slower clock / deeper pipeline / smaller
       array) and re-simulates,
    5. stops when the design is physically plausible.

This makes the simulated performance a physically-achievable number
rather than a theoretical workload figure.
"""

from __future__ import annotations

from dataclasses import dataclass, field, replace
from typing import Callable, Optional

from vse.asic.physical import estimate_physical
from vse.fpga.spec import FPGASpec
from vse.report.result import EndToEndResult
from vse.rtl import generate_rtl
from vse.search.architecture import ArchitectureSpec
from vse.silicon.process import DEFAULT, ProcessTechnology


@dataclass
class LoopIteration:
    """One pass through Architecture → Simulation → RTL → Physical."""

    step: int
    spec: ArchitectureSpec
    result: EndToEndResult
    rtl_lines: int
    physical: object
    updated: bool
    note: str = ""

    def report(self) -> dict:
        return {
            "step": self.step,
            "arch": self.spec.label(),
            "tokens_per_second": self.result.tokens_per_second,
            "total_cycles": self.result.total_cycles,
            "rtl_lines": self.rtl_lines,
            "physical": self.physical.report(),
            "updated": self.updated,
            "note": self.note,
        }


@dataclass
class DesignLoopResult:
    """Final outcome of a closed-loop exploration."""

    iterations: list[LoopIteration] = field(
        default_factory=list
    )

    @property
    def converged(self) -> bool:
        return bool(self.iterations) and (
            self.iterations[-1].physical.timing_closed
        )

    @property
    def final_spec(self) -> Optional[ArchitectureSpec]:
        if not self.iterations:
            return None

        return self.iterations[-1].spec

    @property
    def final_result(self) -> Optional[EndToEndResult]:
        if not self.iterations:
            return None

        return self.iterations[-1].result

    def report(self) -> dict:
        return {
            "converged": self.converged,
            "iterations": [
                item.report()
                for item in self.iterations
            ],
            "final_arch": (
                self.final_spec.label()
                if self.final_spec
                else None
            ),
        }


def _update_for_timing(
    spec: ArchitectureSpec,
    physical,
    max_pipeline: int,
) -> tuple[ArchitectureSpec, str]:
    """
    Update the architecture to close timing.

    Prefer a deeper pipeline (splits the critical path) over a slower
    clock; if the pipeline is already deep enough, reduce the clock to
    the achievable frequency.
    """

    if spec.pipeline_latency < max_pipeline:
        return (
            replace(
                spec,
                pipeline_latency=spec.pipeline_latency + 1,
            ),
            "timing open: deepened pipeline",
        )

    target = physical.achievable_freq_hz * 0.95

    return (
        replace(
            spec,
            frequency_hz=target,
        ),
        "timing open: reduced clock to "
        f"{target / 1e6:.0f} MHz",
    )


def run_design_loop(
    build_program: Callable[[ArchitectureSpec], object],
    base: ArchitectureSpec,
    tech: ProcessTechnology = DEFAULT,
    max_iterations: int = 6,
    max_pipeline: int = 16,
) -> DesignLoopResult:
    """
    Close the design loop for one model.

    `build_program(spec) -> CompiledProgram` mirrors the search API and
    owns the model + workload.
    """

    from vse.compiler.compiler import execute

    result = DesignLoopResult()
    spec = base

    for step in range(max_iterations):
        program = build_program(spec)

        outcome = execute(program)

        fpgaspec = FPGASpec.from_hardware(
            spec.to_hardware_config(),
            weight_bits=spec.weight_bits,
            activation_bits=spec.activation_bits,
        )

        rtl_lines = len(
            generate_rtl(fpgaspec).splitlines()
        )

        physical = estimate_physical(
            spec,
            tech=tech,
        )

        if physical.timing_closed:
            result.iterations.append(
                LoopIteration(
                    step=step,
                    spec=spec,
                    result=outcome,
                    rtl_lines=rtl_lines,
                    physical=physical,
                    updated=False,
                    note="timing closed",
                )
            )
            break

        updated, note = _update_for_timing(
            spec,
            physical,
            max_pipeline,
        )

        result.iterations.append(
            LoopIteration(
                step=step,
                spec=spec,
                result=outcome,
                rtl_lines=rtl_lines,
                physical=physical,
                updated=True,
                note=note,
            )
        )

        spec = updated

    return result


def format_design_loop_report(
    result: DesignLoopResult,
) -> str:
    """Compact textual rendering of the closed-loop exploration."""

    lines = [
        "VSE ASIC EXPLORATION (closed loop)",
        "=" * 60,
    ]

    for item in result.iterations:
        p = item.physical
        lines.append("")
        lines.append(f"Step {item.step + 1}: {item.spec.label()}")
        lines.append("-" * 60)
        lines.append(
            f"Tokens/sec     : {item.result.tokens_per_second:,.3f}"
        )
        lines.append(
            f"Cycles         : {item.result.total_cycles:,}"
        )
        lines.append(f"RTL lines      : {item.rtl_lines:,}")
        lines.append(
            f"Gates          : {p.gates:,}"
        )
        lines.append(
            f"Die area       : {p.die_area_mm2:.3f} mm²"
        )
        lines.append(
            f"Critical path  : {p.critical_path_ns:.3f} ns "
            f"(wire {p.wire_delay_ns:.3f} ns)"
        )
        lines.append(
            f"Achievable f   : {p.achievable_freq_hz / 1e6:,.0f} MHz"
        )
        lines.append(
            f"Requested f    : {p.requested_freq_hz / 1e6:,.0f} MHz"
        )
        lines.append(
            f"Timing         : "
            f"{'CLOSED' if p.timing_closed else 'open'} "
            f"(slack {p.timing_slack_ps:+.0f} ps)"
        )

        if item.updated:
            lines.append(f"→ {item.note}")

    lines.append("")
    lines.append(
        "RESULT: "
        + (
            "physically plausible silicon after "
            f"{len(result.iterations)} iteration(s)"
            if result.converged
            else "did not converge — increase max iterations"
        )
    )

    return "\n".join(lines)


__all__ = [
    "DesignLoopResult",
    "LoopIteration",
    "run_design_loop",
    "format_design_loop_report",
]