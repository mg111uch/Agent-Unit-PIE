"""
VSE - Virtual Silicon Engine
vse/result.py

Combined end-to-end simulation result.
"""

from __future__ import annotations

from dataclasses import dataclass, field

from vse.benchmark.benchmark import BenchmarkResult
from vse.core.types import ScheduleResult


@dataclass
class EndToEndResult:
    """
    Combined result of one end-to-end simulation.
    """

    name: str
    tokens: int
    sequence_length: int

    schedule: ScheduleResult
    benchmark: BenchmarkResult

    total_macs: int
    total_memory_bytes: int

    memory_traffic: dict = field(
        default_factory=dict
    )

    noc: dict = field(
        default_factory=dict
    )

    plan: dict = field(
        default_factory=dict
    )

    power: dict = field(
        default_factory=dict
    )

    area: dict = field(
        default_factory=dict
    )

    @property
    def total_cycles(self) -> int:
        return self.schedule.total_cycles

    @property
    def latency_seconds(self) -> float:
        return self.schedule.latency_seconds

    @property
    def latency_us(self) -> float:
        return self.schedule.latency_us

    @property
    def tokens_per_second(self) -> float:
        if self.latency_seconds == 0:
            return 0.0

        return self.tokens / self.latency_seconds

    @property
    def compute_utilization(self) -> float:
        return self.schedule.resource_utilization(
            "compute"
        )

    @property
    def memory_utilization(self) -> float:
        """
        Utilization of the primary off-chip (HBM) memory resource.
        """

        names = (
            "hbm_read",
            "hbm_write",
            "memory_read",
            "memory_write",
        )

        values = [
            self.schedule.resource_utilization(name)
            for name in names
            if name in self.schedule.resources
        ]

        if not values:
            return 0.0

        return max(values)

    def report(self) -> dict:
        return {
            "name": self.name,
            "tokens": self.tokens,
            "sequence_length": self.sequence_length,
            "total_cycles": self.total_cycles,
            "latency_us": self.latency_us,
            "tokens_per_second": (
                self.tokens_per_second
            ),
            "total_macs": self.total_macs,
            "total_memory_bytes": (
                self.total_memory_bytes
            ),
            "compute_utilization": (
                self.compute_utilization
            ),
            "memory_utilization": (
                self.memory_utilization
            ),
            "schedule": self.schedule.report(),
            "benchmark": self.benchmark.report(),
            "memory": self.memory_traffic,
            "noc": self.noc,
            "plan": self.plan,
            "power": self.power,
            "area": self.area,
        }
