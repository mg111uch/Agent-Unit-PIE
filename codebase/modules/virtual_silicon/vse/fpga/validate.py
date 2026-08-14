"""
VSE - Virtual Silicon Engine
vse/fpga/validate.py

Phase 8: FPGA prototype validation harness.

Runs a small model on a small PE array through the pure-Python RTL
simulator and checks the six assumptions the VSE scheduler relies on:

    scheduler assumptions  — RTL-simulated cycles == CycleEngine's own
                             prediction for the same work
    datapath               — quantized matmul MAC count matches
    memory architecture    — banked SRAM parallel-access cycles
    routing                — NoC hop latency matches vse/core/noc.py
    quantization           — fixed-point rounding is monotonic & bounded
    pipeline behavior      — steady throughput equals PE-array rate

Every concern gets a pass/fail with measured vs expected numbers so a
regression in any single assumption is immediately visible.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Optional

from vse.fpga.spec import FPGASpec
from vse.fpga.sim import (
    ComputeArraySim,
    NoCSim,
    PipelineSim,
    SRAMSim,
    vse_cycles_for,
)
from vse.workload import HardwareConfig


@dataclass
class _Concern:
    name: str
    passed: bool
    expected: object
    measured: object
    detail: str = ""

    def as_dict(self) -> dict:
        return {
            "name": self.name,
            "passed": self.passed,
            "expected": self.expected,
            "measured": self.measured,
            "detail": self.detail,
        }


@dataclass
class FpgaValidationResult:
    """Outcome of validating one prototype chip against the scheduler."""

    spec: FPGASpec
    macs: int
    concerns: list[_Concern] = field(default_factory=list)

    @property
    def all_passed(self) -> bool:
        return all(c.passed for c in self.concerns)

    def report(self) -> dict:
        return {
            "arch": self.spec.label(),
            "macs": self.macs,
            "all_passed": self.all_passed,
            "concerns": [
                c.as_dict() for c in self.concerns
            ],
        }


def validate_fpga(
    config: HardwareConfig,
    weight_bits: Optional[int] = None,
    activation_bits: Optional[int] = None,
    frac_bits: int = 8,
    macs: int = 256,
    banks: int = 4,
) -> FpgaValidationResult:
    """
    Validate a prototype chip (from `config`) on a small workload.

    Defaults keep everything tiny: `macs` MACs on the small PE array,
    `banks` SRAM banks, and a couple of NoC transfers.
    """

    spec = FPGASpec.from_hardware(
        config,
        weight_bits=weight_bits,
        activation_bits=activation_bits,
        frac_bits=frac_bits,
    )

    spec.sram_banks = banks
    spec.sram_bw_words_per_cycle = 1
    spec.noc_nodes = max(spec.noc_nodes, 4)

    concerns: list[_Concern] = []
    compute = ComputeArraySim(spec)
    sram = SRAMSim(spec)
    noc = NoCSim(spec)
    pipeline = PipelineSim(spec)

    # -- scheduler assumptions: RTL sim cycles vs CycleEngine's pricing --
    rtl = compute.run_macs(macs)
    scheduler_prediction = vse_cycles_for(
        work=macs,
        units=spec.num_pes,
        throughput=spec.macs_per_pe,
        pipeline_latency=spec.pipeline_depth,
    )
    concerns.append(
        _Concern(
            name="scheduler",
            passed=rtl["cycles"] == scheduler_prediction,
            expected=scheduler_prediction,
            measured=rtl["cycles"],
            detail=(
                "RTL-simulated occupancy + pipeline drain matches "
                "the CycleEngine's cycles_for_units + latency"
            ),
        )
    )

    # -- datapath: matmul MAC accounting --
    a = [[1, 2], [3, 4]]
    b = [[1, 0], [0, 1]]
    _, matmul_report = compute.matmul(a, b)
    expected_macs = 2 * 2 * 2
    concerns.append(
        _Concern(
            name="datapath",
            passed=matmul_report["macs"] == expected_macs,
            expected=expected_macs,
            measured=matmul_report["macs"],
            detail="2×2 · 2×2 quantized matmul retires exactly M·N·K MACs",
        )
    )

    # -- memory architecture: banked SRAM --
    distinct = [(bank, 8) for bank in range(banks)]
    parallel = sram.parallel_access(distinct)
    conflict = sram.parallel_access([(0, 8)] * banks)
    concerns.append(
        _Concern(
            name="memory",
            passed=(
                parallel["cycles"] < conflict["cycles"]
                and parallel["peak_banks_used"] == banks
            ),
            expected={
                "parallel_cycles < conflict_cycles": True,
                "peak_banks": banks,
            },
            measured={
                "parallel_cycles": parallel["cycles"],
                "conflict_cycles": conflict["cycles"],
                "peak_banks": parallel["peak_banks_used"],
            },
            detail=(
                f"{banks} distinct banks run concurrently; "
                f"{banks} accesses to one bank serialize "
                "(bank conflicts)"
            ),
        )
    )

    # -- routing: NoC hop latency --
    transfer = noc.transfer(0, 2)
    from vse.core.noc import NoC, NoCConfig

    vse_noc = NoC(
        NoCConfig(
            topology=spec.noc_topology,
            nodes=spec.noc_nodes,
            per_hop_cycles=spec.noc_per_hop_cycles,
        )
    )
    expected_hops = vse_noc.distance(0, 2)
    concerns.append(
        _Concern(
            name="routing",
            passed=(
                transfer["hops"] == expected_hops
                and transfer["latency_cycles"]
                == expected_hops * spec.noc_per_hop_cycles
            ),
            expected={
                "hops": expected_hops,
                "latency_cycles": (
                    expected_hops * spec.noc_per_hop_cycles
                ),
            },
            measured=transfer,
            detail="RTL router hop count matches vse/core/noc.py distance",
        )
    )

    # -- quantization: bounded, monotonic fixed-point rounding --
    values = [-1.0, -0.5, 0.0, 0.49, 0.5, 0.51, 1.0]
    quantized = [spec.quantize(v) for v in values]
    bounded = all(
        -2 ** (spec.activation_bits - 1)
        <= q
        <= 2 ** (spec.activation_bits - 1) - 1
        for q in quantized
    )
    monotonic = quantized == sorted(quantized)
    concerns.append(
        _Concern(
            name="quantization",
            passed=bounded and monotonic,
            expected={"bounded": True, "monotonic": True},
            measured={
                "values": quantized,
                "bounded": bounded,
                "monotonic": monotonic,
            },
            detail="Round-to-nearest fixed-point stays in range & order",
        )
    )

    # -- pipeline behavior: steady throughput after fill --
    pipe = pipeline.run(macs)
    steady_ok = pipe["steady_throughput"] == (
        min(macs, spec.pe_throughput_macs_per_cycle)
    )
    concerns.append(
        _Concern(
            name="pipeline",
            passed=(
                steady_ok
                and pipe["cycles"]
                == spec.pipeline_depth + (macs - 1) + 1
            ),
            expected={
                "fill": spec.pipeline_depth,
                "throughput_after_fill": (
                    min(macs, spec.pe_throughput_macs_per_cycle)
                ),
            },
            measured={
                "fill_cycles": pipe["fill_cycles"],
                "steady_throughput": pipe["steady_throughput"],
                "cycles": pipe["cycles"],
            },
            detail="Steady-state throughput == PE-array MAC rate",
        )
    )

    return FpgaValidationResult(
        spec=spec,
        macs=macs,
        concerns=concerns,
    )


def format_fpga_report(result: FpgaValidationResult) -> str:
    """Compact textual rendering of a validation report."""

    lines = [
        "VSE FPGA PROTOTYPE VALIDATION",
        "=" * 60,
        f"Architecture  : {result.spec.label()}",
        f"MACs          : {result.macs:,}",
        f"Frequency     : {result.spec.frequency_hz / 1e6:.0f} MHz",
        "",
        "CONCERN             STATUS   EXPECTED      MEASURED",
        "-" * 60,
    ]

    for concern in result.concerns:
        status = "PASS" if concern.passed else "FAIL"
        lines.append(
            f"{concern.name:<19} {status:<8} "
            f"{str(concern.expected):<14} {concern.measured}"
        )

    lines.append("")
    lines.append(
        "OVERALL: "
        + (
            "all assumptions validated on the RTL simulator"
            if result.all_passed
            else "FAILURE — see failing concerns above"
        )
    )

    return "\n".join(lines)


__all__ = [
    "FpgaValidationResult",
    "validate_fpga",
    "format_fpga_report",
]