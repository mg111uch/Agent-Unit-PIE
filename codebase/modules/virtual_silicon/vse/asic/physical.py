"""
VSE - Virtual Silicon Engine
vse/asic/physical.py

Phase 10: physical implementation estimator (synthesis → P&R → timing).

Models the real silicon cost of the RTL generated in Phase 9 without a
commercial toolchain:

    - gate count       — from PE / SRAM / NoC / DMA / dispatch blocks
    - die area         — gates × gate density (µm²) per process node
    - critical path    — longest combinational delay (logic + wire)
    - achievable freq  — 1 / critical path
    - timing closure   — achievable freq vs the requested clock
    - power            — reuses the Phase-7 energy model

The estimates are first-order and grounded in `ProcessTechnology`
constants, so extreme-throughput claims must still clear them before
being accepted as physically plausible silicon (roadmap "missing
physics").
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Optional

from vse.silicon.process import DEFAULT, ProcessTechnology


@dataclass
class PhysicalEstimate:
    """Physical cost of one generated RTL design."""

    gates: int
    logic_area_um2: float
    die_area_mm2: float
    critical_path_ns: float
    wire_delay_ns: float
    achievable_freq_hz: float
    requested_freq_hz: float
    timing_slack_ps: float
    timing_closed: bool
    utilization: float

    def report(self) -> dict:
        return {
            "gates": self.gates,
            "logic_area_um2": self.logic_area_um2,
            "die_area_mm2": self.die_area_mm2,
            "critical_path_ns": self.critical_path_ns,
            "wire_delay_ns": self.wire_delay_ns,
            "achievable_freq_hz": self.achievable_freq_hz,
            "requested_freq_hz": self.requested_freq_hz,
            "timing_slack_ps": self.timing_slack_ps,
            "timing_closed": self.timing_closed,
            "utilization": self.utilization,
        }


# ---------------------------------------------------------------------------
# Gate budgets (NAND2-equivalent gates per building block).
# ---------------------------------------------------------------------------

GATES_PER_MAC = 8              # multiply + partial add
GATES_PER_PE_OVERHEAD = 120    # accumulator + quantizer + control
GATES_PER_SRAM_BIT = 2
GATES_PER_NOC_NODE = 400
GATES_PER_DMA = 800
GATES_PER_DISPATCH = 600
GATES_PER_ACCUM = 200
GATES_PER_ACTIVATION = 150


def _sram_bytes(chip) -> int:
    """SRAM capacity in bytes for both ArchitectureSpec/HardwareConfig
    (`sram_bytes`) and FPGASpec (`sram_words_per_bank × banks × words`)."""

    if hasattr(chip, "sram_bytes"):
        return int(getattr(chip, "sram_bytes"))

    return int(
        getattr(chip, "sram_words_per_bank", 0)
        * getattr(chip, "sram_banks", 0)
        * getattr(chip, "sram_word_bits", 0)
        // 8
    )


def estimate_gates(
    chip,
) -> int:
    """First-order gate count of the generated RTL for a chip spec."""

    macs = (
        chip.num_pes
        * getattr(
            chip,
            "macs_per_pe",
            getattr(
                chip,
                "macs_per_pe_per_cycle",
                1,
            ),
        )
    )

    sram_bits = _sram_bytes(chip) * 8

    return int(
        macs * GATES_PER_MAC
        + chip.num_pes * GATES_PER_PE_OVERHEAD
        + sram_bits * GATES_PER_SRAM_BIT
        + chip.noc_nodes * GATES_PER_NOC_NODE
        + GATES_PER_DMA
        + GATES_PER_DISPATCH
        + GATES_PER_ACCUM
        + GATES_PER_ACTIVATION
    )


def _combinational_depth(
    chip,
) -> tuple[int, int]:
    """
    Logic depth (gate levels) and effective fan-out of the critical path.

    The longest path runs through a PE's MAC chain, the SRAM access, and
    (when the NoC is enabled) a router hop. Pipeline registers split the
    MAC chain, so `pipeline_latency` stages divide the combinational
    depth of the datapath.
    """

    macs = getattr(
        chip,
        "macs_per_pe",
        getattr(
            chip,
            "macs_per_pe_per_cycle",
            1,
        ),
    )

    pipeline = max(
        getattr(chip, "pipeline_latency", 0),
        1,
    )

    mac_depth = (
        macs * GATES_PER_MAC // pipeline
    )

    sram_depth = 12 if _sram_bytes(chip) > 0 else 0
    noc_depth = (
        chip.noc_nodes * 4
        if getattr(chip, "noc_nodes", 1) > 1
        else 0
    )

    return max(mac_depth, sram_depth, noc_depth), macs


def _wire_delay_ns(
    chip,
    tech: ProcessTechnology,
) -> float:
    """
    RC wire delay across the die. Grows with die edge (sqrt of gates)
    and shrinks with process node (narrower wires).
    """

    gates = max(estimate_gates(chip), 1)
    edge = gates ** 0.5

    per_unit = 0.5 * (tech.node_nm / 7.0)

    return per_unit * edge * 1e-3


def estimate_physical(
    chip,
    tech: ProcessTechnology = DEFAULT,
    requested_freq_hz: Optional[float] = None,
) -> PhysicalEstimate:
    """
    Estimate the physical cost of `chip` (an `ArchitectureSpec`,
    `HardwareConfig`, or `FPGASpec` — anything exposing `num_pes`,
    `sram_bytes`, `noc_nodes`, and a frequency).

    `requested_freq_hz` defaults to the chip's own clock; timing closes
    when the achievable frequency is at least the requested one.
    """

    if requested_freq_hz is None:
        requested_freq_hz = float(
            getattr(chip, "frequency_hz", 1e9)
        )

    gates = estimate_gates(chip)

    per_gate_um2 = (
        tech.mac_area_um2 / GATES_PER_MAC
    )
    logic_area_um2 = gates * per_gate_um2
    die_area_mm2 = (
        logic_area_um2 * tech.routing_overhead / 1e6
    )

    depth, _ = _combinational_depth(chip)

    gate_delay_ns = 0.05 * (tech.node_nm / 7.0)
    wire_delay = _wire_delay_ns(chip, tech)
    critical_path_ns = depth * gate_delay_ns + wire_delay

    achievable_freq_hz = (
        1e9 / critical_path_ns
        if critical_path_ns > 0
        else float("inf")
    )

    slack_ps = (
        (1.0 / requested_freq_hz - 1.0 / achievable_freq_hz)
        * 1e12
        if requested_freq_hz > 0 and achievable_freq_hz > 0
        else float("inf")
    )

    util = min(
        1.0,
        requested_freq_hz / achievable_freq_hz,
    )

    return PhysicalEstimate(
        gates=gates,
        logic_area_um2=logic_area_um2,
        die_area_mm2=die_area_mm2,
        critical_path_ns=critical_path_ns,
        wire_delay_ns=wire_delay,
        achievable_freq_hz=achievable_freq_hz,
        requested_freq_hz=requested_freq_hz,
        timing_slack_ps=slack_ps,
        timing_closed=(
            slack_ps >= 0
        ),
        utilization=util,
    )


__all__ = [
    "PhysicalEstimate",
    "estimate_gates",
    "estimate_physical",
]