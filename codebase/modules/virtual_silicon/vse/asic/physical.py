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
GATES_PER_CIM = 500            # SRAM+MAC fused cell (CIM / near-memory)


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


def _is_cim_chip(chip) -> bool:
    """Lazy CIM check without hard dep on pe_families."""
    try:
        from vse.core.pe_families import ArchFamily  # noqa: WPS433

        for attr in ("arch_family", "family", "pe_family"):
            v = getattr(chip, attr, None)
            if isinstance(v, ArchFamily) and v in (ArchFamily.cim, ArchFamily.near_memory):
                return True
    except Exception:
        pass
    for attr in ("arch_family", "family", "pe_family", "cim"):
        v = getattr(chip, attr, None)
        if v is None:
            continue
        if isinstance(v, bool) and attr == "cim" and v:
            return True
        try:
            s = str(v).lower()
        except Exception:
            continue
        if s in ("cim", "near_memory", "near-memory"):
            return True
    return False


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

    base = int(
        macs * GATES_PER_MAC
        + chip.num_pes * GATES_PER_PE_OVERHEAD
        + sram_bits * GATES_PER_SRAM_BIT
        + chip.noc_nodes * GATES_PER_NOC_NODE
        + GATES_PER_DMA
        + GATES_PER_DISPATCH
        + GATES_PER_ACCUM
        + GATES_PER_ACTIVATION
    )
    if _is_cim_chip(chip):
        base += int(chip.num_pes * GATES_PER_CIM)
    return base


def _combinational_depth(
    chip,
    tech: ProcessTechnology = None,
) -> tuple[int, int]:
    """
    Logic depth (gate levels) and effective fan-out of the critical path.

    The longest path runs through a PE's MAC chain, the SRAM access, and
    (when the NoC is enabled) a router hop. Pipeline registers split the
    MAC chain, so `pipeline_latency` stages divide the combinational
    depth of the datapath.

    SRAM latency contribution is now physical: if sram_bytes>0,
        sram_depth = max(4, SRAMArray.latency_cycles(tech))
    which includes decode(1)+wordline/bitline(2)+wire_delay cycles.
    Falls back to 12 if array construction fails.

    Clock constraint: critical_path_ns = depth*gate_delay + wire_delay
        must be <= 1/achievable_freq; timing closes when
        achievable_freq >= requested_freq.
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

    sram_bytes = _sram_bytes(chip)
    if sram_bytes <= 0:
        sram_depth = 0
    else:
        try:
            from vse.silicon.sram.sram_array import SRAMArray
            from vse.silicon.process import DEFAULT as _DEFAULT

            t = tech if tech is not None else _DEFAULT
            banks = getattr(
                chip,
                "sram_banks",
                getattr(chip, "banks", 1),
            )
            ports = getattr(
                chip,
                "sram_ports",
                getattr(
                    chip,
                    "ports_per_bank",
                    getattr(
                        chip,
                        "sram_ports_per_bank",
                        1,
                    ),
                ),
            )
            bits = getattr(
                chip,
                "sram_word_bits",
                getattr(
                    chip,
                    "bits_per_access",
                    getattr(
                        chip,
                        "sram_bits_per_access",
                        32,
                    ),
                ),
            )
            freq = getattr(chip, "frequency_hz", 1e9)
            arr = SRAMArray(
                banks=int(banks),
                ports_per_bank=int(ports),
                bits_per_access=int(bits),
                frequency_hz=float(freq),
                capacity_bytes_total=int(sram_bytes),
            )
            lat = arr.latency_cycles(t)
            sram_depth = max(4, int(lat))
        except Exception:
            sram_depth = 12
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
    Per-SRAM-array + per-hop NoC aware: base is
        0.5 * (node/7) * sqrt(gates) * 1e-3
    plus SRAM wire contribution:
        sram_wire = SRAMArray(...).wire_delay_ns(tech) * 0.5
    (lazy import to avoid circular deps).
    """

    gates = max(estimate_gates(chip), 1)
    edge = gates ** 0.5

    per_unit = 0.5 * (tech.node_nm / 7.0)

    base = per_unit * edge * 1e-3

    # SRAM wire contribution (per-array)
    sram_bytes = _sram_bytes(chip)
    if sram_bytes > 0:
        try:
            from vse.silicon.sram.sram_array import SRAMArray

            banks = getattr(
                chip,
                "sram_banks",
                getattr(chip, "banks", 1),
            )
            ports = getattr(
                chip,
                "sram_ports",
                getattr(
                    chip,
                    "ports_per_bank",
                    getattr(
                        chip,
                        "sram_ports_per_bank",
                        1,
                    ),
                ),
            )
            bits = getattr(
                chip,
                "sram_word_bits",
                getattr(
                    chip,
                    "bits_per_access",
                    getattr(
                        chip,
                        "sram_bits_per_access",
                        32,
                    ),
                ),
            )
            freq = getattr(chip, "frequency_hz", 1e9)
            arr = SRAMArray(
                banks=int(banks),
                ports_per_bank=int(ports),
                bits_per_access=int(bits),
                frequency_hz=float(freq),
                capacity_bytes_total=int(sram_bytes),
            )
            sram_wire = arr.wire_delay_ns(tech) * 0.5
            return base + sram_wire
        except Exception:
            return base
    return base


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

    depth, _ = _combinational_depth(chip, tech)

    gate_delay_ns = 0.05 * (tech.node_nm / 7.0)
    wire_delay = _wire_delay_ns(chip, tech)
    # clock constraint: critical_path_ns = logic + wire
    # timing closes when 1/critical_path >= requested_freq
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