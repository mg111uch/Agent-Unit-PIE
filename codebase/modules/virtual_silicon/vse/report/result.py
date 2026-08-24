"""
VSE - Virtual Silicon Engine
vse/result.py

Combined end-to-end simulation result.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, Optional

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

    gate: Optional[Any] = None
    gate_result: Optional[Any] = None

    def __post_init__(self) -> None:
        if self.gate is not None and self.gate_result is None:
            object.__setattr__(self, "gate_result", self.gate)
        elif self.gate_result is not None and self.gate is None:
            object.__setattr__(self, "gate", self.gate_result)

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

    def _gate_dict(self) -> Optional[dict]:
        g = self.gate if self.gate is not None else self.gate_result
        if g is None:
            return None
        # support dict form
        if isinstance(g, dict):
            return g
        try:
            checks = []
            for c in getattr(g, "checks", []):
                checks.append({
                    "name": getattr(c, "name", "?"),
                    "passed": bool(getattr(c, "passed", False)),
                    "expected": getattr(c, "expected", None),
                    "measured": getattr(c, "measured", None),
                    "unit": getattr(c, "unit", ""),
                })
            return {
                "plausible": bool(getattr(g, "plausible", getattr(g, "overall_pass", True))),
                "overall_pass": bool(getattr(g, "overall_pass", getattr(g, "plausible", True))),
                "checks": checks,
            }
        except Exception:
            return None

    def report(self) -> dict:
        out = {
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
        gd = self._gate_dict()
        if gd is not None:
            out["physics"] = gd
        return out

    def to_json(self) -> dict:
        return self.report()
