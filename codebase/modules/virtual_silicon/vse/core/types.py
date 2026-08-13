"""
VSE - Virtual Silicon Engine
vse/types.py

Shared scheduling data types for the cycle engine.

These are used by vse/engine.py (the cycle engine) and vse/scheduler.py
(the public API facade).
"""

from __future__ import annotations

from dataclasses import dataclass, field
from enum import Enum
from typing import Dict, List, Optional


# ---------------------------------------------------------------------------
# Resource types
# ---------------------------------------------------------------------------

class ResourceType(str, Enum):
    COMPUTE = "compute"
    MEMORY_READ = "memory_read"
    MEMORY_WRITE = "memory_write"
    ROUTER = "router"
    DMA = "dma"
    NOC = "noc"
    CUSTOM = "custom"


# ---------------------------------------------------------------------------
# Resource
# ---------------------------------------------------------------------------

@dataclass
class Resource:
    """
    A virtual hardware resource.

    capacity:
        Number of identical units available (e.g. PEs).

    throughput:
        Work units processed per unit per cycle.

    pipeline_latency:
        Extra cycles before a completed task's result is ready.

    banks:
        Number of independent banks (memory resources). Concurrent
        tasks that request banks more than this must wait.

    primary:
        If true, this resource is the default for its type when a
        task does not specify a memory level.
    """

    name: str
    resource_type: ResourceType

    capacity: int = 1
    throughput: float = 1.0

    pipeline_latency: int = 0

    banks: int = 1
    primary: bool = False

    available_cycle: int = 0

    busy_cycles: int = 0
    total_work: float = 0.0

    def __post_init__(self) -> None:
        if self.capacity <= 0:
            raise ValueError(
                "resource capacity must be > 0"
            )

        if self.throughput <= 0:
            raise ValueError(
                "resource throughput must be > 0"
            )

        if self.pipeline_latency < 0:
            raise ValueError(
                "pipeline_latency must be >= 0"
            )

        if self.banks <= 0:
            raise ValueError(
                "resource banks must be > 0"
            )

    def cycles_for_units(
        self,
        work: float,
        units: int,
    ) -> int:
        """
        Cycles for `work` using a subset of capacity units.
        """

        if work <= 0:
            return 0

        rate = units * self.throughput

        return max(
            1,
            int((work / rate) + 0.999999),
        )

    def cycles_for_work(
        self,
        work: float,
    ) -> int:
        """
        Cycles for `work` using the full resource.
        """

        return self.cycles_for_units(
            work,
            self.capacity,
        )

    def reset(self) -> None:
        self.available_cycle = 0
        self.busy_cycles = 0
        self.total_work = 0.0


# ---------------------------------------------------------------------------
# Task
# ---------------------------------------------------------------------------

@dataclass
class Task:
    """
    One executable unit in the virtual silicon graph.

    units:
        Number of capacity units this task occupies.
        0 (default) means "use the entire resource".

    mem_level:
        Memory-hierarchy level (e.g. "sram", "hbm") that this task
        accesses. None routes to the default resource for its type.

    banks:
        Number of banks this task touches simultaneously. 0 means no
        bank constraint.
    """

    task_id: str
    name: str

    resource_type: ResourceType

    work: float = 0.0

    dependencies: List[str] = field(
        default_factory=list
    )

    metadata: Dict[str, object] = field(
        default_factory=dict
    )

    units: int = 0

    mem_level: Optional[str] = None

    banks: int = 0

    pipeline_latency: Optional[int] = None

    start_cycle: Optional[int] = None
    end_cycle: Optional[int] = None

    resource_name: Optional[str] = None

    @property
    def duration(self) -> int:
        if (
            self.start_cycle is None
            or self.end_cycle is None
        ):
            return 0

        return (
            self.end_cycle
            - self.start_cycle
        )

    @property
    def scheduled(self) -> bool:
        return (
            self.start_cycle is not None
            and self.end_cycle is not None
        )


# ---------------------------------------------------------------------------
# Schedule event
# ---------------------------------------------------------------------------

@dataclass
class ScheduleEvent:
    task_id: str
    task_name: str

    resource_name: str

    start_cycle: int
    end_cycle: int

    work: float

    units: int = 0

    @property
    def duration(self) -> int:
        return (
            self.end_cycle
            - self.start_cycle
        )


# ---------------------------------------------------------------------------
# Cycle trace
# ---------------------------------------------------------------------------

@dataclass
class CycleTraceEntry:
    """
    Snapshot of one resource at one cycle boundary.
    """

    cycle: int
    resource: str

    busy_units: int
    capacity: int
    active_tasks: int


# ---------------------------------------------------------------------------
# Schedule result
# ---------------------------------------------------------------------------

@dataclass
class ScheduleResult:
    """
    Complete execution schedule.
    """

    events: List[ScheduleEvent]

    total_cycles: int

    resources: Dict[str, Resource]

    tasks: Dict[str, Task]

    frequency_hz: float = 1.0

    trace: List[CycleTraceEntry] = field(
        default_factory=list
    )

    peak_concurrency: Dict[str, int] = field(
        default_factory=dict
    )

    peak_banks: Dict[str, int] = field(
        default_factory=dict
    )

    @property
    def latency_seconds(self) -> float:
        if self.frequency_hz <= 0:
            return 0.0

        return (
            self.total_cycles
            / self.frequency_hz
        )

    @property
    def latency_us(self) -> float:
        return (
            self.latency_seconds
            * 1e6
        )

    def resource_utilization(
        self,
        resource_name: str,
    ) -> float:
        resource = self.resources[
            resource_name
        ]

        if self.total_cycles <= 0:
            return 0.0

        denominator = (
            self.total_cycles
            * resource.capacity
            * resource.throughput
        )

        if denominator <= 0:
            return 0.0

        return (
            resource.total_work
            / denominator
        )

    def all_utilization(self) -> dict[str, float]:
        return {
            name: self.resource_utilization(name)
            for name in self.resources
        }

    def report(self) -> dict:
        return {
            "total_cycles": self.total_cycles,
            "latency_us": self.latency_us,
            "latency_seconds": (
                self.latency_seconds
            ),
            "frequency_hz": self.frequency_hz,
            "events": len(self.events),
            "resource_utilization": (
                self.all_utilization()
            ),
            "peak_concurrency": (
                self.peak_concurrency
            ),
            "peak_banks": self.peak_banks,
        }
