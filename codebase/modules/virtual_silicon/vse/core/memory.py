"""
VSE - Virtual Silicon Engine
vse/memory.py

Architectural memory model for the Virtual Silicon Engine.

Models:
    - Capacity
    - Read/write latency
    - Read/write bandwidth
    - Concurrent transfers
    - Busy cycles
    - Bandwidth utilization

This is intentionally technology-neutral. It can represent:
    - SRAM
    - eDRAM
    - HBM
    - LPDDR
    - DDR
    - chiplet-local memory
    - hypothetical future memory

It does NOT simulate transistor-level memory behavior.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Callable, Optional

from vse.core.core import HardwareComponent, Simulator


# ---------------------------------------------------------------------------
# Memory configuration
# ---------------------------------------------------------------------------

@dataclass
class MemoryConfig:
    """
    Configuration of a memory subsystem.

    capacity_bytes:
        Total storage capacity.

    read_bandwidth_bytes_per_cycle:
        Maximum amount of data that can be read per cycle.

    write_bandwidth_bytes_per_cycle:
        Maximum amount of data that can be written per cycle.

    read_latency_cycles:
        Minimum latency before a read completes.

    write_latency_cycles:
        Minimum latency before a write completes.

    max_outstanding:
        Maximum number of simultaneous memory operations.
    """

    capacity_bytes: int

    read_bandwidth_bytes_per_cycle: int

    write_bandwidth_bytes_per_cycle: int

    read_latency_cycles: int

    write_latency_cycles: int

    max_outstanding: int = 1

    def __post_init__(self) -> None:
        if self.capacity_bytes <= 0:
            raise ValueError("capacity_bytes must be > 0")

        if self.read_bandwidth_bytes_per_cycle <= 0:
            raise ValueError(
                "read_bandwidth_bytes_per_cycle must be > 0"
            )

        if self.write_bandwidth_bytes_per_cycle <= 0:
            raise ValueError(
                "write_bandwidth_bytes_per_cycle must be > 0"
            )

        if self.read_latency_cycles <= 0:
            raise ValueError(
                "read_latency_cycles must be > 0"
            )

        if self.write_latency_cycles <= 0:
            raise ValueError(
                "write_latency_cycles must be > 0"
            )

        if self.max_outstanding <= 0:
            raise ValueError(
                "max_outstanding must be > 0"
            )


# ---------------------------------------------------------------------------
# Memory statistics
# ---------------------------------------------------------------------------

@dataclass
class MemoryStats:
    """Runtime statistics for a memory subsystem."""

    read_requests: int = 0
    write_requests: int = 0

    read_bytes: int = 0
    write_bytes: int = 0

    completed_reads: int = 0
    completed_writes: int = 0

    rejected_reads: int = 0
    rejected_writes: int = 0

    peak_outstanding: int = 0

    busy_read_cycles: int = 0
    busy_write_cycles: int = 0


# ---------------------------------------------------------------------------
# Memory request
# ---------------------------------------------------------------------------

@dataclass
class MemoryRequest:
    """Represents one memory transaction."""

    request_id: int
    address: int
    size_bytes: int
    is_write: bool
    start_cycle: int
    completion_cycle: int


# ---------------------------------------------------------------------------
# Memory
# ---------------------------------------------------------------------------

class Memory(HardwareComponent):
    """
    Generic architectural memory subsystem.

    Example:

        config = MemoryConfig(
            capacity_bytes=64 * 1024,
            read_bandwidth_bytes_per_cycle=64,
            write_bandwidth_bytes_per_cycle=64,
            read_latency_cycles=10,
            write_latency_cycles=10,
            max_outstanding=16,
        )

        memory = Memory(sim, "SRAM", config)

        memory.read(
            address=0,
            size_bytes=1024,
            callback=lambda data: print("read complete"),
        )

        sim.run()
    """

    def __init__(
        self,
        simulator: Simulator,
        name: str,
        config: MemoryConfig,
    ):
        super().__init__(simulator, name)

        self.config = config
        self.stats = MemoryStats()

        self._next_request_id = 0
        self._outstanding: dict[int, MemoryRequest] = {}

        # Track the simulated amount of data transferred.
        self.total_read_bytes = 0
        self.total_write_bytes = 0

    # ------------------------------------------------------------------
    # Properties
    # ------------------------------------------------------------------

    @property
    def capacity_bytes(self) -> int:
        return self.config.capacity_bytes

    @property
    def capacity_gb(self) -> float:
        return self.capacity_bytes / (1024 ** 3)

    @property
    def outstanding(self) -> int:
        return len(self._outstanding)

    @property
    def available_slots(self) -> int:
        return (
            self.config.max_outstanding
            - self.outstanding
        )

    @property
    def read_bandwidth_bytes_per_cycle(self) -> int:
        return self.config.read_bandwidth_bytes_per_cycle

    @property
    def write_bandwidth_bytes_per_cycle(self) -> int:
        return self.config.write_bandwidth_bytes_per_cycle

    # ------------------------------------------------------------------
    # Validation
    # ------------------------------------------------------------------

    def _validate_access(
        self,
        address: int,
        size_bytes: int,
    ) -> None:
        if address < 0:
            raise ValueError("address must be >= 0")

        if size_bytes <= 0:
            raise ValueError("size_bytes must be > 0")

        end_address = address + size_bytes

        if end_address > self.capacity_bytes:
            raise ValueError(
                f"Memory access exceeds capacity: "
                f"0x{address:x} + {size_bytes} bytes "
                f"> {self.capacity_bytes} bytes"
            )

    # ------------------------------------------------------------------
    # Latency calculation
    # ------------------------------------------------------------------

    @staticmethod
    def _transfer_cycles(
        size_bytes: int,
        bandwidth_bytes_per_cycle: int,
    ) -> int:
        """
        Number of cycles required to transfer size_bytes.

        Uses ceiling division.
        """

        return (
            size_bytes + bandwidth_bytes_per_cycle - 1
        ) // bandwidth_bytes_per_cycle

    # ------------------------------------------------------------------
    # Read
    # ------------------------------------------------------------------

    def read(
        self,
        address: int,
        size_bytes: int,
        callback: Optional[Callable[[], None]] = None,
    ) -> Optional[int]:
        """
        Schedule a memory read.

        Returns:
            Request ID if accepted.
            None if the memory has no available request slot.

        Total latency:

            read_latency + transfer_time
        """

        self._validate_access(address, size_bytes)

        self.stats.read_requests += 1

        if self.outstanding >= self.config.max_outstanding:
            self.stats.rejected_reads += 1
            return None

        transfer_cycles = self._transfer_cycles(
            size_bytes,
            self.config.read_bandwidth_bytes_per_cycle,
        )

        latency = (
            self.config.read_latency_cycles
            + transfer_cycles
        )

        request_id = self._next_request_id
        self._next_request_id += 1

        request = MemoryRequest(
            request_id=request_id,
            address=address,
            size_bytes=size_bytes,
            is_write=False,
            start_cycle=self.sim.cycle,
            completion_cycle=self.sim.cycle + latency,
        )

        self._outstanding[request_id] = request

        self.stats.read_bytes += size_bytes

        self.stats.peak_outstanding = max(
            self.stats.peak_outstanding,
            self.outstanding,
        )

        self.stats.busy_read_cycles += transfer_cycles

        def complete() -> None:
            self._complete_request(
                request_id,
                callback,
            )

        self.schedule(
            latency,
            complete,
            operation_name="read",
        )

        return request_id

    # ------------------------------------------------------------------
    # Write
    # ------------------------------------------------------------------

    def write(
        self,
        address: int,
        size_bytes: int,
        callback: Optional[Callable[[], None]] = None,
    ) -> Optional[int]:
        """
        Schedule a memory write.

        Returns:
            Request ID if accepted.
            None if no outstanding-request slot exists.
        """

        self._validate_access(address, size_bytes)

        self.stats.write_requests += 1

        if self.outstanding >= self.config.max_outstanding:
            self.stats.rejected_writes += 1
            return None

        transfer_cycles = self._transfer_cycles(
            size_bytes,
            self.config.write_bandwidth_bytes_per_cycle,
        )

        latency = (
            self.config.write_latency_cycles
            + transfer_cycles
        )

        request_id = self._next_request_id
        self._next_request_id += 1

        request = MemoryRequest(
            request_id=request_id,
            address=address,
            size_bytes=size_bytes,
            is_write=True,
            start_cycle=self.sim.cycle,
            completion_cycle=self.sim.cycle + latency,
        )

        self._outstanding[request_id] = request

        self.stats.write_bytes += size_bytes

        self.stats.peak_outstanding = max(
            self.stats.peak_outstanding,
            self.outstanding,
        )

        self.stats.busy_write_cycles += transfer_cycles

        def complete() -> None:
            self._complete_request(
                request_id,
                callback,
            )

        self.schedule(
            latency,
            complete,
            operation_name="write",
        )

        return request_id

    # ------------------------------------------------------------------
    # Completion
    # ------------------------------------------------------------------

    def _complete_request(
        self,
        request_id: int,
        callback: Optional[Callable[[], None]],
    ) -> None:
        request = self._outstanding.pop(
            request_id,
            None,
        )

        if request is None:
            return

        if request.is_write:
            self.stats.completed_writes += 1
            self.total_write_bytes += request.size_bytes
        else:
            self.stats.completed_reads += 1
            self.total_read_bytes += request.size_bytes

        if callback is not None:
            callback()

    # ------------------------------------------------------------------
    # Utilization
    # ------------------------------------------------------------------

    def read_bandwidth_utilization(self) -> float:
        """
        Approximate read-bandwidth utilization.

        Returns:
            0.0 - 1.0
        """

        if self.sim.cycle == 0:
            return 0.0

        possible = (
            self.sim.cycle
            * self.config.read_bandwidth_bytes_per_cycle
        )

        if possible <= 0:
            return 0.0

        return min(
            1.0,
            self.total_read_bytes / possible,
        )

    def write_bandwidth_utilization(self) -> float:
        """Approximate write-bandwidth utilization."""

        if self.sim.cycle == 0:
            return 0.0

        possible = (
            self.sim.cycle
            * self.config.write_bandwidth_bytes_per_cycle
        )

        if possible <= 0:
            return 0.0

        return min(
            1.0,
            self.total_write_bytes / possible,
        )

    # ------------------------------------------------------------------
    # Reset
    # ------------------------------------------------------------------

    def reset_stats(self) -> None:
        """Reset runtime statistics without changing configuration."""

        self.stats = MemoryStats()

        self.total_read_bytes = 0
        self.total_write_bytes = 0

    # ------------------------------------------------------------------
    # Reporting
    # ------------------------------------------------------------------

    def report(self) -> dict:
        """Return a machine-readable performance report."""

        return {
            "name": self.name,
            "capacity_bytes": self.capacity_bytes,
            "capacity_gb": self.capacity_gb,
            "read_requests": self.stats.read_requests,
            "write_requests": self.stats.write_requests,
            "read_bytes": self.stats.read_bytes,
            "write_bytes": self.stats.write_bytes,
            "completed_reads": self.stats.completed_reads,
            "completed_writes": self.stats.completed_writes,
            "rejected_reads": self.stats.rejected_reads,
            "rejected_writes": self.stats.rejected_writes,
            "peak_outstanding": self.stats.peak_outstanding,
            "read_bandwidth_utilization": (
                self.read_bandwidth_utilization()
            ),
            "write_bandwidth_utilization": (
                self.write_bandwidth_utilization()
            ),
        }

    def __repr__(self) -> str:
        return (
            f"Memory("
            f"name={self.name!r}, "
            f"capacity={self.capacity_gb:.3f} GB, "
            f"outstanding={self.outstanding}/"
            f"{self.config.max_outstanding})"
        )
