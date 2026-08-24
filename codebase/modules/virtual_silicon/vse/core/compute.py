"""
VSE - Virtual Silicon Engine
vse/compute.py - configurable compute fabric.
"""
from __future__ import annotations
from dataclasses import dataclass
from typing import Callable, Optional
from vse.core.core import HardwareComponent, Simulator

@dataclass
class ComputeConfig:
    """Config for parallel compute array. Family knobs default to scalar."""
    num_pes: int
    macs_per_pe_per_cycle: int = 1
    frequency_hz: float = 1e9
    pipeline_latency: int = 1
    data_bits: int = 4
    family: str = "scalar"
    vector_width: int = 1
    systolic_dim: int = 0
    simd_lanes: int = 1
    dataflow: str = "weight_stationary"

    def __post_init__(self) -> None:
        if self.num_pes <= 0:
            raise ValueError("num_pes must be > 0")
        if self.macs_per_pe_per_cycle <= 0:
            raise ValueError("macs_per_pe_per_cycle must be > 0")
        if self.frequency_hz <= 0:
            raise ValueError("frequency_hz must be > 0")
        if self.pipeline_latency <= 0:
            raise ValueError("pipeline_latency must be > 0")
        if self.data_bits <= 0:
            raise ValueError("data_bits must be > 0")
        fam_val = self.family.value if hasattr(self.family, "value") else self.family
        allowed = {"scalar","simd","vector","systolic","weight_stationary","output_stationary","cim","near_memory"}
        if fam_val not in allowed:
            raise ValueError(f"family must be one of {sorted(allowed)}, got {fam_val!r}")
        self.family = str(fam_val)
        if not 1 <= self.vector_width <= 16:
            raise ValueError("vector_width must be 1..16")
        if not 0 <= self.systolic_dim <= 64:
            raise ValueError("systolic_dim must be 0..64")
        if not 1 <= self.simd_lanes <= 8:
            raise ValueError("simd_lanes must be 1..8")
        if self.dataflow not in ("weight_stationary","output_stationary"):
            raise ValueError(f"dataflow must be weight_stationary or output_stationary, got {self.dataflow!r}")

@dataclass
class ComputeStats:
    operations_submitted: int = 0
    operations_completed: int = 0
    macs_requested: int = 0
    macs_completed: int = 0
    busy_cycles: int = 0
    peak_parallel_macs: int = 0
    rejected_operations: int = 0

@dataclass
class ComputeOperation:
    operation_id: int
    macs: int
    start_cycle: int
    completion_cycle: int

class ComputeArray(HardwareComponent):
    """Parallel PE array with family-aware MAC throughput."""
    def __init__(self, simulator: Simulator, name: str, config: ComputeConfig):
        super().__init__(simulator, name)
        self.config = config
        self.stats = ComputeStats()
        self._next_operation_id = 0
        self._outstanding: dict[int, ComputeOperation] = {}

    @property
    def num_pes(self) -> int:
        return self.config.num_pes

    def _pe_family_config(self):
        from vse.core.pe_families import ArchFamily, PEFamilyConfig
        fam = self.config.family
        if hasattr(fam, "value"):
            fam = fam.value
        return PEFamilyConfig(family=ArchFamily(fam), vector_width=self.config.vector_width, systolic_dim=self.config.systolic_dim, simd_lanes=self.config.simd_lanes, dataflow=self.config.dataflow)

    def _effective_macs_per_pe(self) -> int:
        from vse.core.pe_families import effective_macs_per_cycle
        return effective_macs_per_cycle(self.config.macs_per_pe_per_cycle, self._pe_family_config())

    def _latency_extra(self) -> int:
        from vse.core.pe_families import latency_extra
        return latency_extra(self._pe_family_config())

    @property
    def macs_per_cycle(self) -> int:
        return self.config.num_pes * self._effective_macs_per_pe()

    @property
    def peak_macs_per_second(self) -> float:
        return self.macs_per_cycle * self.config.frequency_hz

    @property
    def peak_tops(self) -> float:
        return self.peak_macs_per_second * 2 / 1e12

    @property
    def outstanding(self) -> int:
        return len(self._outstanding)

    def cycles_for_macs(self, macs: int) -> int:
        if macs <= 0:
            raise ValueError("macs must be > 0")
        compute_cycles = (macs + self.macs_per_cycle - 1) // self.macs_per_cycle
        return compute_cycles + self.config.pipeline_latency + self._latency_extra()

    def submit(self, macs: int, callback: Optional[Callable[[], None]] = None) -> int:
        if macs <= 0:
            raise ValueError("macs must be > 0")
        operation_id = self._next_operation_id
        self._next_operation_id += 1
        compute_cycles = (macs + self.macs_per_cycle - 1) // self.macs_per_cycle
        latency = compute_cycles + self.config.pipeline_latency + self._latency_extra()
        operation = ComputeOperation(operation_id=operation_id, macs=macs, start_cycle=self.sim.cycle, completion_cycle=self.sim.cycle + latency)
        self._outstanding[operation_id] = operation
        self.stats.operations_submitted += 1
        self.stats.macs_requested += macs
        self.stats.busy_cycles += compute_cycles
        parallel_macs = min(macs, self.macs_per_cycle)
        self.stats.peak_parallel_macs = max(self.stats.peak_parallel_macs, parallel_macs)
        def complete() -> None:
            self._complete(operation_id, callback)
        self.schedule(latency, complete, operation_name="compute")
        return operation_id

    def _complete(self, operation_id: int, callback: Optional[Callable[[], None]]) -> None:
        operation = self._outstanding.pop(operation_id, None)
        if operation is None:
            return
        self.stats.operations_completed += 1
        self.stats.macs_completed += operation.macs
        if callback is not None:
            callback()

    def utilization(self) -> float:
        if self.sim.cycle <= 0:
            return 0.0
        capacity = self.sim.cycle * self.macs_per_cycle
        if capacity <= 0:
            return 0.0
        return min(1.0, self.stats.macs_completed / capacity)

    def achieved_macs_per_second(self) -> float:
        if self.sim.time_seconds <= 0:
            return 0.0
        return self.stats.macs_completed / self.sim.time_seconds

    def achieved_tops(self) -> float:
        return self.achieved_macs_per_second() * 2 / 1e12

    def reset_stats(self) -> None:
        self.stats = ComputeStats()

    def report(self) -> dict:
        return {
            "name": self.name,
            "num_pes": self.config.num_pes,
            "macs_per_pe_per_cycle": self.config.macs_per_pe_per_cycle,
            "macs_per_cycle": self.macs_per_cycle,
            "frequency_hz": self.config.frequency_hz,
            "frequency_ghz": self.config.frequency_hz / 1e9,
            "data_bits": self.config.data_bits,
            "pipeline_latency": self.config.pipeline_latency,
            "family": self.config.family,
            "vector_width": self.config.vector_width,
            "systolic_dim": self.config.systolic_dim,
            "simd_lanes": self.config.simd_lanes,
            "dataflow": self.config.dataflow,
            "peak_macs_per_second": self.peak_macs_per_second,
            "peak_tops": self.peak_tops,
            "operations_submitted": self.stats.operations_submitted,
            "operations_completed": self.stats.operations_completed,
            "macs_requested": self.stats.macs_requested,
            "macs_completed": self.stats.macs_completed,
            "utilization": self.utilization(),
            "achieved_macs_per_second": self.achieved_macs_per_second(),
            "achieved_tops": self.achieved_tops(),
        }

    def __repr__(self) -> str:
        return f"ComputeArray(name={self.name!r}, PEs={self.num_pes}, MAC/cycle={self.macs_per_cycle}, peak={self.peak_tops:.2f} TOPS)"

def make_int4_array(simulator: Simulator, name: str, num_pes: int, frequency_ghz: float = 1.0, macs_per_pe_per_cycle: int = 1, pipeline_latency: int = 1) -> ComputeArray:
    return ComputeArray(simulator=simulator, name=name, config=ComputeConfig(num_pes=num_pes, macs_per_pe_per_cycle=macs_per_pe_per_cycle, frequency_hz=frequency_ghz * 1e9, pipeline_latency=pipeline_latency, data_bits=4))
