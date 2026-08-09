"""
VSE - Virtual Silicon Engine
vse/benchmark.py

Architectural benchmarking and feasibility analysis.

The benchmark layer answers questions such as:

    - How many tokens/sec can this virtual chip produce?
    - Is the design compute-bound or memory-bound?
    - How much bandwidth is required?
    - How many compute operations are required per token?
    - Can the architecture reach 10K / 1M / 10M tok/s?
    - What happens when multiple tokens are decoded in parallel?

This is an analytical model, not cycle-accurate RTL simulation yet.

Later versions can replace individual estimates with the VSE scheduler
and eventually generated RTL.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Optional

from .compute import ComputeArray
from .memory import Memory
from .moe import MoE, MoECost
from .transformer import (
    TransformerModel,
    TransformerWorkloadCost,
)


# ---------------------------------------------------------------------------
# Benchmark result
# ---------------------------------------------------------------------------

@dataclass
class BenchmarkResult:
    """
    Result of one benchmark run.

    All throughput numbers refer to generated output tokens.
    """

    name: str

    tokens: int

    sequence_length: int

    compute_cycles: int
    memory_cycles: int

    compute_time_seconds: float
    memory_time_seconds: float

    latency_seconds: float
    throughput_tokens_per_second: float

    total_macs: int
    total_memory_bytes: int

    compute_bound: bool
    memory_bound: bool

    required_memory_bandwidth_bytes_per_second: float

    target_tokens_per_second: Optional[float] = None
    target_reached: Optional[bool] = None

    @property
    def latency_ms(self) -> float:
        return self.latency_seconds * 1000.0

    @property
    def throughput_mtok_per_second(self) -> float:
        return self.throughput_tokens_per_second / 1e6

    @property
    def required_bandwidth_gb_per_second(self) -> float:
        return (
            self.required_memory_bandwidth_bytes_per_second
            / 1e9
        )

    def report(self) -> dict:
        return {
            "name": self.name,
            "tokens": self.tokens,
            "sequence_length": self.sequence_length,
            "latency_ms": self.latency_ms,
            "tokens_per_second": (
                self.throughput_tokens_per_second
            ),
            "mtok_per_second": (
                self.throughput_mtok_per_second
            ),
            "total_macs": self.total_macs,
            "memory_bytes": self.total_memory_bytes,
            "compute_cycles": self.compute_cycles,
            "memory_cycles": self.memory_cycles,
            "compute_bound": self.compute_bound,
            "memory_bound": self.memory_bound,
            "required_bandwidth_GBps": (
                self.required_bandwidth_gb_per_second
            ),
            "target_tokens_per_second": (
                self.target_tokens_per_second
            ),
            "target_reached": self.target_reached,
        }


# ---------------------------------------------------------------------------
# Hardware statistics
# ---------------------------------------------------------------------------

@dataclass
class HardwareLimits:
    """
    Extracted limits from the virtual hardware.

    This abstraction allows benchmark.py to remain independent of the
    exact implementation of ComputeArray and Memory.
    """

    compute_macs_per_cycle: float

    frequency_hz: float

    memory_read_bytes_per_cycle: float
    memory_write_bytes_per_cycle: float

    @property
    def compute_macs_per_second(self) -> float:
        return (
            self.compute_macs_per_cycle
            * self.frequency_hz
        )

    @property
    def memory_read_bandwidth(self) -> float:
        return (
            self.memory_read_bytes_per_cycle
            * self.frequency_hz
        )

    @property
    def memory_write_bandwidth(self) -> float:
        return (
            self.memory_write_bytes_per_cycle
            * self.frequency_hz
        )

    @property
    def total_memory_bandwidth(self) -> float:
        return (
            self.memory_read_bandwidth
            + self.memory_write_bandwidth
        )


# ---------------------------------------------------------------------------
# Hardware extraction
# ---------------------------------------------------------------------------

def hardware_limits(
    compute: Optional[ComputeArray],
    memory: Optional[Memory],
    frequency_hz: Optional[float] = None,
) -> HardwareLimits:
    """
    Extract analytical hardware limits.

    The ComputeArray and Memory implementations may evolve, so this
    function keeps the benchmark interface stable.
    """

    if compute is None:
        compute_macs_per_cycle = 0.0
        compute_frequency = (
            frequency_hz or 1.0
        )
    else:
        num_pes = getattr(
            compute.config,
            "num_pes",
            0,
        )

        macs_per_pe = getattr(
            compute.config,
            "macs_per_pe_per_cycle",
            1,
        )

        compute_macs_per_cycle = (
            num_pes * macs_per_pe
        )

        compute_frequency = getattr(
            compute.config,
            "frequency_hz",
            frequency_hz or 1.0,
        )

    if memory is None:
        read_bandwidth = 0.0
        write_bandwidth = 0.0
    else:
        read_bandwidth = getattr(
            memory,
            "read_bandwidth_bytes_per_cycle",
            0,
        )

        write_bandwidth = getattr(
            memory,
            "write_bandwidth_bytes_per_cycle",
            0,
        )

    if frequency_hz is not None:
        compute_frequency = frequency_hz

    return HardwareLimits(
        compute_macs_per_cycle=float(
            compute_macs_per_cycle
        ),
        frequency_hz=float(
            compute_frequency
        ),
        memory_read_bytes_per_cycle=float(
            read_bandwidth
        ),
        memory_write_bytes_per_cycle=float(
            write_bandwidth
        ),
    )


# ---------------------------------------------------------------------------
# Analytical benchmark engine
# ---------------------------------------------------------------------------

class Benchmark:
    """
    Analytical VSE benchmark engine.

    Example:

        benchmark = Benchmark(
            compute=compute,
            memory=memory,
        )

        result = benchmark.transformer_decode(
            model,
            sequence_length=4096,
            target_tokens_per_second=1_000_000,
        )
    """

    def __init__(
        self,
        compute: Optional[ComputeArray] = None,
        memory: Optional[Memory] = None,
        frequency_hz: Optional[float] = None,
    ):
        self.compute = compute
        self.memory = memory

        self.limits = hardware_limits(
            compute=compute,
            memory=memory,
            frequency_hz=frequency_hz,
        )

    # ------------------------------------------------------------------
    # Generic workload
    # ------------------------------------------------------------------

    def workload(
        self,
        macs: int,
        memory_bytes: int,
        tokens: int = 1,
        name: str = "workload",
        target_tokens_per_second: Optional[float] = None,
    ) -> BenchmarkResult:
        """
        Benchmark an arbitrary workload.

        Uses a roofline-style estimate:

            compute time = MACs / compute throughput

            memory time = bytes / memory bandwidth

            latency = max(compute time, memory time)

        This assumes perfect scheduling/overlap.

        It therefore represents an optimistic architectural upper bound.
        """

        if macs < 0:
            raise ValueError("macs must be >= 0")

        if memory_bytes < 0:
            raise ValueError(
                "memory_bytes must be >= 0"
            )

        if tokens <= 0:
            raise ValueError(
                "tokens must be > 0"
            )

        compute_throughput = (
            self.limits.compute_macs_per_second
        )

        memory_bandwidth = (
            self.limits.total_memory_bandwidth
        )

        if compute_throughput > 0:
            compute_time = (
                macs
                / compute_throughput
            )
        else:
            compute_time = float("inf")

        if memory_bandwidth > 0:
            memory_time = (
                memory_bytes
                / memory_bandwidth
            )
        else:
            memory_time = float("inf")

        latency = max(
            compute_time,
            memory_time,
        )

        if latency == 0:
            throughput = float("inf")
        else:
            throughput = (
                tokens / latency
            )

        compute_cycles = 0

        if (
            self.limits.compute_macs_per_cycle
            > 0
        ):
            compute_cycles = int(
                (macs
                 / self.limits.compute_macs_per_cycle)
                + 0.999999
            )

        memory_cycles = 0

        memory_bytes_per_cycle = (
            self.limits.total_memory_bandwidth
            / self.limits.frequency_hz
            if self.limits.frequency_hz > 0
            else 0
        )

        if memory_bytes_per_cycle > 0:
            memory_cycles = int(
                (memory_bytes
                 / memory_bytes_per_cycle)
                + 0.999999
            )

        compute_bound = (
            compute_time >= memory_time
        )

        memory_bound = (
            memory_time >= compute_time
        )

        required_bandwidth = (
            memory_bytes / latency
            if latency > 0
            else float("inf")
        )

        target_reached = None

        if target_tokens_per_second is not None:
            target_reached = (
                throughput
                >= target_tokens_per_second
            )

        return BenchmarkResult(
            name=name,
            tokens=tokens,
            sequence_length=0,
            compute_cycles=compute_cycles,
            memory_cycles=memory_cycles,
            compute_time_seconds=compute_time,
            memory_time_seconds=memory_time,
            latency_seconds=latency,
            throughput_tokens_per_second=throughput,
            total_macs=macs,
            total_memory_bytes=memory_bytes,
            compute_bound=compute_bound,
            memory_bound=memory_bound,
            required_memory_bandwidth_bytes_per_second=(
                required_bandwidth
            ),
            target_tokens_per_second=(
                target_tokens_per_second
            ),
            target_reached=target_reached,
        )

    # ------------------------------------------------------------------
    # Transformer decode
    # ------------------------------------------------------------------

    def transformer_decode(
        self,
        model: TransformerModel,
        sequence_length: int,
        target_tokens_per_second: Optional[float] = None,
    ) -> BenchmarkResult:
        """
        Benchmark one-token Transformer decode.
        """

        workload = model.decode_cost(
            sequence_length
        )

        result = self.workload(
            macs=workload.macs,
            memory_bytes=workload.memory_bytes,
            tokens=1,
            name="transformer_decode",
            target_tokens_per_second=(
                target_tokens_per_second
            ),
        )

        result.sequence_length = sequence_length

        return result

    # ------------------------------------------------------------------
    # Transformer prefill
    # ------------------------------------------------------------------

    def transformer_prefill(
        self,
        model: TransformerModel,
        sequence_length: int,
    ) -> BenchmarkResult:
        """
        Benchmark processing an entire prompt.
        """

        workload = model.prefill_cost(
            sequence_length
        )

        return self.workload(
            macs=workload.macs,
            memory_bytes=workload.memory_bytes,
            tokens=sequence_length,
            name="transformer_prefill",
        )

    # ------------------------------------------------------------------
    # MoE benchmark
    # ------------------------------------------------------------------

    def moe(
        self,
        moe_model: MoE,
        tokens: int,
        target_tokens_per_second: Optional[float] = None,
    ) -> BenchmarkResult:
        """
        Benchmark an MoE workload.
        """

        workload = moe_model.cost(
            tokens=tokens
        )

        return self.workload(
            macs=workload.macs,
            memory_bytes=workload.total_memory_bytes,
            tokens=tokens,
            name="moe",
            target_tokens_per_second=(
                target_tokens_per_second
            ),
        )

    # ------------------------------------------------------------------
    # Roofline
    # ------------------------------------------------------------------

    def roofline(
        self,
        macs: int,
        memory_bytes: int,
    ) -> dict:
        """
        Return roofline information.

        Arithmetic intensity:

            MACs / byte

        Compute roof:

            hardware MAC/s

        Memory roof:

            bandwidth × arithmetic intensity

        Attainable performance:

            min(compute roof, memory roof)
        """

        if memory_bytes <= 0:
            intensity = float("inf")
        else:
            intensity = (
                macs / memory_bytes
            )

        compute_roof = (
            self.limits.compute_macs_per_second
        )

        if intensity == float("inf"):
            memory_roof = float("inf")
        else:
            memory_roof = (
                self.limits.total_memory_bandwidth
                * intensity
            )

        attainable = min(
            compute_roof,
            memory_roof,
        )

        return {
            "arithmetic_intensity": intensity,
            "compute_roof_macs_per_second": (
                compute_roof
            ),
            "memory_roof_macs_per_second": (
                memory_roof
            ),
            "attainable_macs_per_second": (
                attainable
            ),
            "compute_bound": (
                compute_roof <= memory_roof
            ),
            "memory_bound": (
                memory_roof <= compute_roof
            ),
        }


# ---------------------------------------------------------------------------
# Throughput target analysis
# ---------------------------------------------------------------------------

@dataclass
class TargetAnalysis:
    """
    Analysis of a requested token/s target.
    """

    target_tokens_per_second: float

    required_macs_per_second: float
    available_macs_per_second: float

    required_memory_bandwidth: float
    available_memory_bandwidth: float

    compute_utilization: float
    memory_utilization: float

    compute_feasible: bool
    memory_feasible: bool

    feasible: bool

    @property
    def required_memory_bandwidth_gbps(self) -> float:
        return (
            self.required_memory_bandwidth
            / 1e9
        )

    @property
    def available_memory_bandwidth_gbps(self) -> float:
        return (
            self.available_memory_bandwidth
            / 1e9
        )

    def report(self) -> dict:
        return {
            "target_tok_s": (
                self.target_tokens_per_second
            ),
            "required_macs_s": (
                self.required_macs_per_second
            ),
            "available_macs_s": (
                self.available_macs_per_second
            ),
            "required_memory_GB_s": (
                self.required_memory_bandwidth_gbps
            ),
            "available_memory_GB_s": (
                self.available_memory_bandwidth_gbps
            ),
            "compute_utilization": (
                self.compute_utilization
            ),
            "memory_utilization": (
                self.memory_utilization
            ),
            "compute_feasible": (
                self.compute_feasible
            ),
            "memory_feasible": (
                self.memory_feasible
            ),
            "feasible": self.feasible,
        }


def analyze_target(
    macs_per_token: int,
    memory_bytes_per_token: int,
    target_tokens_per_second: float,
    compute: Optional[ComputeArray],
    memory: Optional[Memory],
    frequency_hz: Optional[float] = None,
) -> TargetAnalysis:
    """
    Determine whether a target token/s rate is achievable.

    This is one of the most useful functions in the initial VSE.

    Example:

        analyze_target(
            macs_per_token=30_000_000_000,
            memory_bytes_per_token=20_000_000_000,
            target_tokens_per_second=1_000_000,
            ...
        )

    This immediately exposes the required silicon throughput and
    memory bandwidth.
    """

    if target_tokens_per_second <= 0:
        raise ValueError(
            "target_tokens_per_second must be > 0"
        )

    limits = hardware_limits(
        compute=compute,
        memory=memory,
        frequency_hz=frequency_hz,
    )

    required_macs = (
        macs_per_token
        * target_tokens_per_second
    )

    required_memory = (
        memory_bytes_per_token
        * target_tokens_per_second
    )

    available_macs = (
        limits.compute_macs_per_second
    )

    available_memory = (
        limits.total_memory_bandwidth
    )

    if available_macs > 0:
        compute_utilization = (
            required_macs
            / available_macs
        )
    else:
        compute_utilization = float("inf")

    if available_memory > 0:
        memory_utilization = (
            required_memory
            / available_memory
        )
    else:
        memory_utilization = float("inf")

    compute_feasible = (
        required_macs <= available_macs
    )

    memory_feasible = (
        required_memory <= available_memory
    )

    return TargetAnalysis(
        target_tokens_per_second=(
            target_tokens_per_second
        ),
        required_macs_per_second=required_macs,
        available_macs_per_second=available_macs,
        required_memory_bandwidth=required_memory,
        available_memory_bandwidth=available_memory,
        compute_utilization=compute_utilization,
        memory_utilization=memory_utilization,
        compute_feasible=compute_feasible,
        memory_feasible=memory_feasible,
        feasible=(
            compute_feasible
            and memory_feasible
        ),
    )


# ---------------------------------------------------------------------------
# Batch decode scaling
# ---------------------------------------------------------------------------

def batch_decode_analysis(
    macs_per_token: int,
    memory_bytes_per_token: int,
    batch_sizes: list[int],
    compute: Optional[ComputeArray],
    memory: Optional[Memory],
    frequency_hz: Optional[float] = None,
) -> list[BenchmarkResult]:
    """
    Estimate decode throughput for different batch sizes.

    MVP assumption:
        MACs and memory traffic scale linearly with batch.

    Later versions can model:
        - weight reuse
        - expert reuse
        - SRAM caching
        - batching efficiency
        - routing collisions
        - PE utilization
    """

    if not batch_sizes:
        raise ValueError(
            "batch_sizes cannot be empty"
        )

    results = []

    benchmark = Benchmark(
        compute=compute,
        memory=memory,
        frequency_hz=frequency_hz,
    )

    for batch in batch_sizes:

        if batch <= 0:
            raise ValueError(
                "batch sizes must be > 0"
            )

        result = benchmark.workload(
            macs=(
                macs_per_token
                * batch
            ),
            memory_bytes=(
                memory_bytes_per_token
                * batch
            ),
            tokens=batch,
            name=f"batch_decode_{batch}",
        )

        results.append(result)

    return results


# ---------------------------------------------------------------------------
# Formatting
# ---------------------------------------------------------------------------

def format_benchmark(
    result: BenchmarkResult,
) -> str:
    """
    Human-readable benchmark report.
    """

    return (
        f"{result.name}\n"
        f"  tokens:              "
        f"{result.tokens:,}\n"
        f"  sequence length:     "
        f"{result.sequence_length:,}\n"
        f"  MACs:                "
        f"{result.total_macs:,}\n"
        f"  memory:              "
        f"{result.total_memory_bytes:,} bytes\n"
        f"  compute cycles:      "
        f"{result.compute_cycles:,}\n"
        f"  memory cycles:       "
        f"{result.memory_cycles:,}\n"
        f"  latency:             "
        f"{result.latency_ms:.6f} ms\n"
        f"  throughput:          "
        f"{result.throughput_tokens_per_second:,.2f} tok/s\n"
        f"  bandwidth required:  "
        f"{result.required_bandwidth_gb_per_second:,.2f} GB/s\n"
        f"  compute bound:       "
        f"{result.compute_bound}\n"
        f"  memory bound:        "
        f"{result.memory_bound}\n"
        f"  target:              "
        f"{result.target_tokens_per_second}\n"
        f"  target reached:      "
        f"{result.target_reached}"
    )


def format_target(
    result: TargetAnalysis,
) -> str:
    """
    Human-readable target feasibility report.
    """

    return (
        f"Target: "
        f"{result.target_tokens_per_second:,.0f} tok/s\n"
        f"  Required compute:    "
        f"{result.required_macs_per_second / 1e15:.3f} P-MAC/s\n"
        f"  Available compute:   "
        f"{result.available_macs_per_second / 1e15:.3f} P-MAC/s\n"
        f"  Compute utilization: "
        f"{result.compute_utilization * 100:.2f}%\n"
        f"  Required bandwidth:  "
        f"{result.required_memory_bandwidth_gbps:.2f} GB/s\n"
        f"  Available bandwidth: "
        f"{result.available_memory_bandwidth_gbps:.2f} GB/s\n"
        f"  Memory utilization:  "
        f"{result.memory_utilization * 100:.2f}%\n"
        f"  Compute feasible:    "
        f"{result.compute_feasible}\n"
        f"  Memory feasible:     "
        f"{result.memory_feasible}\n"
        f"  OVERALL FEASIBLE:    "
        f"{result.feasible}"
    )
