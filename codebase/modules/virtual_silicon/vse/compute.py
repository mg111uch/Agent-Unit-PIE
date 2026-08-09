"""
VSE - Virtual Silicon Engine
vse/compute.py

Configurable compute fabric for cycle-level architectural simulation.

MVP models:
    - Processing Elements (PEs)
    - INT4 MAC throughput
    - Parallel execution
    - Operation latency
    - Compute utilization
    - Arithmetic throughput

This intentionally does NOT perform real tensor arithmetic.
It models the amount of hardware required to perform the arithmetic.

The actual numerical model will be added later.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Callable, Optional

from .core import HardwareComponent, Simulator


# ---------------------------------------------------------------------------
# Compute configuration
# ---------------------------------------------------------------------------

@dataclass
class ComputeConfig:
    """
    Configuration for a parallel compute array.

    num_pes:
        Number of processing elements.

    macs_per_pe_per_cycle:
        Number of multiply-accumulate operations each PE can perform
        every cycle.

    frequency_hz:
        Clock frequency.

    pipeline_latency:
        Number of cycles before a submitted operation completes.

    data_bits:
        Operand precision. For our target architecture this will usually
        be 4 for INT4/FP4.
    """

    num_pes: int
    macs_per_pe_per_cycle: int = 1
    frequency_hz: float = 1e9
    pipeline_latency: int = 1
    data_bits: int = 4

    def __post_init__(self) -> None:
        if self.num_pes <= 0:
            raise ValueError("num_pes must be > 0")

        if self.macs_per_pe_per_cycle <= 0:
            raise ValueError(
                "macs_per_pe_per_cycle must be > 0"
            )

        if self.frequency_hz <= 0:
            raise ValueError("frequency_hz must be > 0")

        if self.pipeline_latency <= 0:
            raise ValueError(
                "pipeline_latency must be > 0"
            )

        if self.data_bits <= 0:
            raise ValueError("data_bits must be > 0")


# ---------------------------------------------------------------------------
# Compute statistics
# ---------------------------------------------------------------------------

@dataclass
class ComputeStats:
    """Runtime statistics for the compute fabric."""

    operations_submitted: int = 0
    operations_completed: int = 0

    macs_requested: int = 0
    macs_completed: int = 0

    busy_cycles: int = 0
    peak_parallel_macs: int = 0

    rejected_operations: int = 0


# ---------------------------------------------------------------------------
# Compute operation
# ---------------------------------------------------------------------------

@dataclass
class ComputeOperation:
    """Description of one submitted compute operation."""

    operation_id: int
    macs: int
    start_cycle: int
    completion_cycle: int


# ---------------------------------------------------------------------------
# Processing Element Array
# ---------------------------------------------------------------------------

class ComputeArray(HardwareComponent):
    """
    Parallel processing-element array.

    Example:

        config = ComputeConfig(
            num_pes=1024,
            macs_per_pe_per_cycle=1,
            frequency_hz=2e9,
            pipeline_latency=4,
        )

        compute = ComputeArray(
            sim,
            "INT4_ARRAY",
            config,
        )

        compute.submit(
            macs=1_000_000,
            callback=lambda: print("done"),
        )

        sim.run()

    The simulator determines how many cycles are needed based on the
    available parallel MAC throughput.
    """

    def __init__(
        self,
        simulator: Simulator,
        name: str,
        config: ComputeConfig,
    ):
        super().__init__(simulator, name)

        self.config = config
        self.stats = ComputeStats()

        self._next_operation_id = 0
        self._outstanding: dict[int, ComputeOperation] = {}

        # Maximum MAC throughput per cycle.
        self.macs_per_cycle = (
            self.config.num_pes
            * self.config.macs_per_pe_per_cycle
        )

    # ------------------------------------------------------------------
    # Properties
    # ------------------------------------------------------------------

    @property
    def num_pes(self) -> int:
        return self.config.num_pes

    @property
    def macs_per_cycle(self) -> int:
        return (
            self.config.num_pes
            * self.config.macs_per_pe_per_cycle
        )

    @property
    def peak_macs_per_second(self) -> float:
        return (
            self.macs_per_cycle
            * self.config.frequency_hz
        )

    @property
    def peak_tops(self) -> float:
        """
        Peak arithmetic throughput in TOPS.

        One MAC is counted as two operations:
            multiply + accumulate
        """

        return (
            self.peak_macs_per_second
            * 2
            / 1e12
        )

    @property
    def outstanding(self) -> int:
        return len(self._outstanding)

    # ------------------------------------------------------------------
    # Latency calculation
    # ------------------------------------------------------------------

    def cycles_for_macs(self, macs: int) -> int:
        """
        Calculate cycles required to perform a number of MACs.

        Pipeline latency is added after the arithmetic work.
        """

        if macs <= 0:
            raise ValueError("macs must be > 0")

        compute_cycles = (
            macs + self.macs_per_cycle - 1
        ) // self.macs_per_cycle

        return compute_cycles + self.config.pipeline_latency

    # ------------------------------------------------------------------
    # Submit operation
    # ------------------------------------------------------------------

    def submit(
        self,
        macs: int,
        callback: Optional[Callable[[], None]] = None,
    ) -> int:
        """
        Submit a compute workload.

        Args:
            macs:
                Number of MAC operations required.

            callback:
                Called when the workload completes.

        Returns:
            Operation ID.
        """

        if macs <= 0:
            raise ValueError("macs must be > 0")

        operation_id = self._next_operation_id
        self._next_operation_id += 1

        compute_cycles = (
            macs + self.macs_per_cycle - 1
        ) // self.macs_per_cycle

        latency = (
            compute_cycles
            + self.config.pipeline_latency
        )

        operation = ComputeOperation(
            operation_id=operation_id,
            macs=macs,
            start_cycle=self.sim.cycle,
            completion_cycle=self.sim.cycle + latency,
        )

        self._outstanding[operation_id] = operation

        self.stats.operations_submitted += 1
        self.stats.macs_requested += macs

        self.stats.busy_cycles += compute_cycles

        parallel_macs = min(
            macs,
            self.macs_per_cycle,
        )

        self.stats.peak_parallel_macs = max(
            self.stats.peak_parallel_macs,
            parallel_macs,
        )

        def complete() -> None:
            self._complete(
                operation_id,
                callback,
            )

        self.schedule(
            latency,
            complete,
            operation_name="compute",
        )

        return operation_id

    # ------------------------------------------------------------------
    # Completion
    # ------------------------------------------------------------------

    def _complete(
        self,
        operation_id: int,
        callback: Optional[Callable[[], None]],
    ) -> None:
        operation = self._outstanding.pop(
            operation_id,
            None,
        )

        if operation is None:
            return

        self.stats.operations_completed += 1
        self.stats.macs_completed += operation.macs

        if callback is not None:
            callback()

    # ------------------------------------------------------------------
    # Utilization
    # ------------------------------------------------------------------

    def utilization(self) -> float:
        """
        Estimate arithmetic-array utilization.

        This is a simple workload-level estimate:

            requested MACs
            -----------------------------
            cycles × peak MACs/cycle
        """

        if self.sim.cycle <= 0:
            return 0.0

        capacity = (
            self.sim.cycle
            * self.macs_per_cycle
        )

        if capacity <= 0:
            return 0.0

        return min(
            1.0,
            self.stats.macs_completed / capacity,
        )

    # ------------------------------------------------------------------
    # Throughput
    # ------------------------------------------------------------------

    def achieved_macs_per_second(self) -> float:
        """Measured MAC throughput."""

        if self.sim.time_seconds <= 0:
            return 0.0

        return (
            self.stats.macs_completed
            / self.sim.time_seconds
        )

    def achieved_tops(self) -> float:
        """Measured arithmetic throughput in TOPS."""

        return (
            self.achieved_macs_per_second()
            * 2
            / 1e12
        )

    # ------------------------------------------------------------------
    # Reset
    # ------------------------------------------------------------------

    def reset_stats(self) -> None:
        """Reset counters while keeping hardware configuration."""

        self.stats = ComputeStats()

    # ------------------------------------------------------------------
    # Report
    # ------------------------------------------------------------------

    def report(self) -> dict:
        """Return machine-readable performance information."""

        return {
            "name": self.name,
            "num_pes": self.config.num_pes,
            "macs_per_pe_per_cycle": (
                self.config.macs_per_pe_per_cycle
            ),
            "macs_per_cycle": self.macs_per_cycle,
            "frequency_hz": self.config.frequency_hz,
            "frequency_ghz": (
                self.config.frequency_hz / 1e9
            ),
            "data_bits": self.config.data_bits,
            "pipeline_latency": (
                self.config.pipeline_latency
            ),
            "peak_macs_per_second": (
                self.peak_macs_per_second
            ),
            "peak_tops": self.peak_tops,
            "operations_submitted": (
                self.stats.operations_submitted
            ),
            "operations_completed": (
                self.stats.operations_completed
            ),
            "macs_requested": self.stats.macs_requested,
            "macs_completed": self.stats.macs_completed,
            "utilization": self.utilization(),
            "achieved_macs_per_second": (
                self.achieved_macs_per_second()
            ),
            "achieved_tops": self.achieved_tops(),
        }

    def __repr__(self) -> str:
        return (
            f"ComputeArray("
            f"name={self.name!r}, "
            f"PEs={self.num_pes}, "
            f"MAC/cycle={self.macs_per_cycle}, "
            f"peak={self.peak_tops:.2f} TOPS)"
        )


# ---------------------------------------------------------------------------
# Convenience factory
# ---------------------------------------------------------------------------

def make_int4_array(
    simulator: Simulator,
    name: str,
    num_pes: int,
    frequency_ghz: float = 1.0,
    macs_per_pe_per_cycle: int = 1,
    pipeline_latency: int = 1,
) -> ComputeArray:
    """
    Convenience constructor for an INT4 compute array.
    """

    return ComputeArray(
        simulator=simulator,
        name=name,
        config=ComputeConfig(
            num_pes=num_pes,
            macs_per_pe_per_cycle=macs_per_pe_per_cycle,
            frequency_hz=frequency_ghz * 1e9,
            pipeline_latency=pipeline_latency,
            data_bits=4,
        ),
    )
