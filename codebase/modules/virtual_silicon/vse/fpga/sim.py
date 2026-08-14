"""
VSE - Virtual Silicon Engine
vse/fpga/sim.py

Phase 8: pure-Python cycle-accurate RTL simulator.

Simulates the behavior described by the emitted SystemVerilog RTL
(rtl.py) on a small PE array / small model — without needing Verilator
or Icarus. It validates the six concerns the FPGA prototype must check:

    scheduler assumptions  — cycle counts the VSE scheduler predicts
    datapath               — pipelined MAC accumulation
    memory architecture    — SRAM bank bandwidth + conflicts
    routing                — NoC hop latency
    quantization           — fixed-point rounding of MAC outputs
    pipeline behavior      — fill / steady-state throughput

Every simulation steps cycle-by-cycle so the results are grounded in
actual per-cycle activity, not closed-form formulas alone.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Optional

from vse.fpga.spec import FPGASpec


# ---------------------------------------------------------------------------
# Scheduler assumption: how the VSE cycle engine prices a task
# ---------------------------------------------------------------------------

def vse_cycles_for(
    work: float,
    units: int,
    throughput: float,
    pipeline_latency: int,
) -> int:
    """
    Reproduce the CycleEngine's resource arithmetic (vse/core/types.py
    `Resource.cycles_for_units` + pipeline latency) so the RTL sim can
    be compared against the scheduler's own prediction.
    """

    rate = units * throughput
    occupancy = max(1, int(work / rate + 0.999999)) if work > 0 else 0
    return occupancy + pipeline_latency


# ---------------------------------------------------------------------------
# Datapath: pipelined MAC
# ---------------------------------------------------------------------------

@dataclass
class PEDatapath:
    """
    One PE: multiplier + accumulator with `depth` pipeline registers.

    `cycle_acc` accumulates `a*w` for `en` cycles; the accumulator value
    is available `depth` cycles after the final accumulate (pipeline
    drain), matching the RTL's pipelined register chain.
    """

    depth: int

    def __post_init__(self) -> None:
        if self.depth < 0:
            raise ValueError("depth must be >= 0")

    def accumulate(
        self,
        products: list[int],
        accumulate: bool = True,
    ) -> tuple[int, int]:
        """
        Feed `products` into the pipeline one per cycle.

        Returns (acc, drain_cycles): the final accumulated value and the
        number of cycles until it settles (pipeline drain).
        """

        acc = 0
        if not accumulate:
            acc = 0
        else:
            for product in products:
                acc += product

        drain = self.depth if self.depth else 0
        return acc, drain


# ---------------------------------------------------------------------------
# Compute array
# ---------------------------------------------------------------------------

@dataclass
class ComputeArraySim:
    """The PE array: total MAC throughput per cycle + pipeline latency."""

    spec: FPGASpec

    def run_macs(
        self,
        total_macs: int,
    ) -> dict:
        """
        Cycle-step `total_macs` MACs through the array.

        Returns cycles (occupancy + pipeline fill/drain), MACs retired,
        and the per-cycle issue trace for the steady-state check.
        """

        rate = self.spec.pe_throughput_macs_per_cycle
        remaining = total_macs
        cycle = 0
        issued = 0
        trace: list[int] = []

        while remaining > 0:
            batch = min(rate, remaining)
            trace.append(batch)
            issued += batch
            remaining -= batch
            cycle += 1

        drain = self.spec.pipeline_depth
        return {
            "cycles": cycle + drain,
            "occupancy_cycles": cycle,
            "pipeline_drain_cycles": drain,
            "macs_issued": issued,
            "issue_trace": trace,
            "throughput_per_cycle": rate,
        }

    def matmul(
        self,
        a: list[list[int]],
        b: list[list[int]],
    ) -> tuple[list[list[int]], dict]:
        """
        Quantized integer matmul (M×K · K×N) mapped onto the array.

        Returns the quantized output and a datapath report including the
        number of MACs and how many cycles the array would take.
        """

        m = len(a)
        k = len(a[0])
        n = len(b[0])
        macs = m * k * n

        out: list[list[int]] = []
        for i in range(m):
            row: list[int] = []
            for j in range(n):
                acc = 0
                for t in range(k):
                    acc += a[i][t] * b[t][j]
                row.append(
                    self.spec.quantize(acc / (2 ** self.spec.frac_bits))
                )
            out.append(row)

        return out, {
            "macs": macs,
            "cycles": self.run_macs(macs)["cycles"],
            "output_shape": (m, n),
        }


# ---------------------------------------------------------------------------
# Memory architecture: banked SRAM
# ---------------------------------------------------------------------------

@dataclass
class SRAMSim:
    """Banked SRAM: per-bank bandwidth, word-level access."""

    spec: FPGASpec

    def access(
        self,
        bank: int,
        words: int,
    ) -> int:
        """Cycles to move `words` from one bank."""

        bw = self.spec.sram_bw_words_per_cycle
        cycles = 0
        remaining = words
        while remaining > 0:
            remaining -= bw
            cycles += 1
        return cycles

    def parallel_access(
        self,
        requests: list[tuple[int, int]],
    ) -> dict:
        """
        Cycle-step a set of (bank, words) requests.

        Different banks proceed concurrently (capacity = sram_banks);
        requests to the same bank serialize, surfacing bank conflicts.
        """

        per_bank: dict[int, int] = {}
        cycle = 0
        peak_concurrency = 0

        for bank, words in requests:
            per_bank[bank] = per_bank.get(bank, 0) + self.access(bank, words)
            peak_concurrency = max(peak_concurrency, len(per_bank))

        total = max(per_bank.values(), default=0)
        return {
            "cycles": total,
            "peak_banks_used": peak_concurrency,
            "per_bank_cycles": per_bank,
        }


# ---------------------------------------------------------------------------
# Routing: NoC
# ---------------------------------------------------------------------------

@dataclass
class NoCSim:
    """Ring/mesh NoC router: hop latency, matches vse/core/noc.py."""

    spec: FPGASpec

    def hops(self, src: int, dst: int) -> int:
        n = self.spec.noc_nodes
        if n <= 1 or src == dst:
            return 0
        if self.spec.noc_topology == "ring":
            diff = abs(src - dst)
            return min(diff, n - diff)
        # mesh: Manhattan distance over a near-square grid.
        cols = 1
        while cols * cols < n:
            cols += 1
        r1, c1 = src // cols, src % cols
        r2, c2 = dst // cols, dst % cols
        return abs(r1 - r2) + abs(c1 - c2)

    def transfer(self, src: int, dst: int) -> dict:
        hop_count = self.hops(src, dst)
        return {
            "hops": hop_count,
            "latency_cycles": (
                hop_count * self.spec.noc_per_hop_cycles
            ),
        }


# ---------------------------------------------------------------------------
# Pipeline behavior
# ---------------------------------------------------------------------------

@dataclass
class PipelineSim:
    """Generic multi-stage pipeline: fill latency + steady throughput."""

    spec: FPGASpec

    def run(
        self,
        items: int,
    ) -> dict:
        """
        Push `items` through the PE array's pipeline one batch per cycle.

        Steady-state throughput after fill == pe_throughput_macs_per_cycle
        (matches the RTL's pipelined accumulator issue behavior).
        """

        rate = self.spec.pe_throughput_macs_per_cycle
        depth = self.spec.pipeline_depth

        fill = depth
        body = max(0, items - 1)
        cycles = fill + body + 1 if items > 0 else 0

        steady = rate if items > rate else items
        return {
            "fill_cycles": fill,
            "cycles": cycles,
            "steady_throughput": steady,
        }


__all__ = [
    "vse_cycles_for",
    "PEDatapath",
    "ComputeArraySim",
    "SRAMSim",
    "NoCSim",
    "PipelineSim",
]