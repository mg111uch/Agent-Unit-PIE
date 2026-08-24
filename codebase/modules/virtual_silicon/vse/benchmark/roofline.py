"""VSE roofline benchmark — split from benchmark.py."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Optional

from vse.core.compute import ComputeArray
from vse.core.memory import Memory
from vse.models.moe import MoE
from vse.models.transformer import TransformerModel


@dataclass
class BenchmarkResult:
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
        return self.required_memory_bandwidth_bytes_per_second / 1e9

    def report(self) -> dict:
        return {"name": self.name, "tokens": self.tokens, "sequence_length": self.sequence_length, "latency_ms": self.latency_ms, "tokens_per_second": self.throughput_tokens_per_second, "mtok_per_second": self.throughput_mtok_per_second, "total_macs": self.total_macs, "memory_bytes": self.total_memory_bytes, "compute_cycles": self.compute_cycles, "memory_cycles": self.memory_cycles, "compute_bound": self.compute_bound, "memory_bound": self.memory_bound, "required_bandwidth_GBps": self.required_bandwidth_gb_per_second, "target_tokens_per_second": self.target_tokens_per_second, "target_reached": self.target_reached}


@dataclass
class HardwareLimits:
    compute_macs_per_cycle: float
    frequency_hz: float
    memory_read_bytes_per_cycle: float
    memory_write_bytes_per_cycle: float

    @property
    def compute_macs_per_second(self) -> float:
        return self.compute_macs_per_cycle * self.frequency_hz

    @property
    def memory_read_bandwidth(self) -> float:
        return self.memory_read_bytes_per_cycle * self.frequency_hz

    @property
    def memory_write_bandwidth(self) -> float:
        return self.memory_write_bytes_per_cycle * self.frequency_hz

    @property
    def total_memory_bandwidth(self) -> float:
        return self.memory_read_bandwidth + self.memory_write_bandwidth


def hardware_limits(compute: Optional[ComputeArray], memory: Optional[Memory], frequency_hz: Optional[float] = None) -> HardwareLimits:
    if compute is None:
        compute_macs_per_cycle = 0.0
        compute_frequency = frequency_hz or 1.0
    else:
        num_pes = getattr(compute.config, "num_pes", 0)
        macs_per_pe = getattr(compute.config, "macs_per_pe_per_cycle", 1)
        compute_macs_per_cycle = num_pes * macs_per_pe
        compute_frequency = getattr(compute.config, "frequency_hz", frequency_hz or 1.0)
    if memory is None:
        read_bandwidth = 0.0
        write_bandwidth = 0.0
    else:
        read_bandwidth = getattr(memory, "read_bandwidth_bytes_per_cycle", 0)
        write_bandwidth = getattr(memory, "write_bandwidth_bytes_per_cycle", 0)
    if frequency_hz is not None:
        compute_frequency = frequency_hz
    return HardwareLimits(compute_macs_per_cycle=float(compute_macs_per_cycle), frequency_hz=float(compute_frequency), memory_read_bytes_per_cycle=float(read_bandwidth), memory_write_bytes_per_cycle=float(write_bandwidth))


class Benchmark:
    def __init__(self, compute: Optional[ComputeArray] = None, memory: Optional[Memory] = None, frequency_hz: Optional[float] = None):
        self.compute = compute
        self.memory = memory
        self.limits = hardware_limits(compute=compute, memory=memory, frequency_hz=frequency_hz)

    def workload(self, macs: int, memory_bytes: int, tokens: int = 1, name: str = "workload", target_tokens_per_second: Optional[float] = None) -> BenchmarkResult:
        if macs < 0:
            raise ValueError("macs must be >= 0")
        if memory_bytes < 0:
            raise ValueError("memory_bytes must be >= 0")
        if tokens <= 0:
            raise ValueError("tokens must be > 0")
        compute_throughput = self.limits.compute_macs_per_second
        memory_bandwidth = self.limits.total_memory_bandwidth
        compute_time = macs / compute_throughput if compute_throughput > 0 else float("inf")
        memory_time = memory_bytes / memory_bandwidth if memory_bandwidth > 0 else float("inf")
        latency = max(compute_time, memory_time)
        throughput = tokens / latency if latency else float("inf")
        compute_cycles = int((macs / self.limits.compute_macs_per_cycle) + 0.999999) if self.limits.compute_macs_per_cycle > 0 else 0
        memory_bytes_per_cycle = self.limits.total_memory_bandwidth / self.limits.frequency_hz if self.limits.frequency_hz > 0 else 0
        memory_cycles = int((memory_bytes / memory_bytes_per_cycle) + 0.999999) if memory_bytes_per_cycle > 0 else 0
        compute_bound = compute_time >= memory_time
        memory_bound = memory_time >= compute_time
        required_bandwidth = memory_bytes / latency if latency > 0 else float("inf")
        target_reached = throughput >= target_tokens_per_second if target_tokens_per_second is not None else None
        return BenchmarkResult(name=name, tokens=tokens, sequence_length=0, compute_cycles=compute_cycles, memory_cycles=memory_cycles, compute_time_seconds=compute_time, memory_time_seconds=memory_time, latency_seconds=latency, throughput_tokens_per_second=throughput, total_macs=macs, total_memory_bytes=memory_bytes, compute_bound=compute_bound, memory_bound=memory_bound, required_memory_bandwidth_bytes_per_second=required_bandwidth, target_tokens_per_second=target_tokens_per_second, target_reached=target_reached)

    def transformer_decode(self, model: TransformerModel, sequence_length: int, target_tokens_per_second: Optional[float] = None) -> BenchmarkResult:
        workload = model.decode_cost(sequence_length)
        result = self.workload(macs=workload.macs, memory_bytes=workload.memory_bytes, tokens=1, name="transformer_decode", target_tokens_per_second=target_tokens_per_second)
        result.sequence_length = sequence_length
        return result

    def transformer_prefill(self, model: TransformerModel, sequence_length: int) -> BenchmarkResult:
        workload = model.prefill_cost(sequence_length)
        return self.workload(macs=workload.macs, memory_bytes=workload.memory_bytes, tokens=sequence_length, name="transformer_prefill")

    def moe(self, moe_model: MoE, tokens: int, target_tokens_per_second: Optional[float] = None) -> BenchmarkResult:
        workload = moe_model.cost(tokens=tokens)
        return self.workload(macs=workload.macs, memory_bytes=workload.total_memory_bytes, tokens=tokens, name="moe", target_tokens_per_second=target_tokens_per_second)

    def roofline(self, macs: int, memory_bytes: int) -> dict:
        intensity = float("inf") if memory_bytes <= 0 else macs / memory_bytes
        compute_roof = self.limits.compute_macs_per_second
        memory_roof = float("inf") if intensity == float("inf") else self.limits.total_memory_bandwidth * intensity
        attainable = min(compute_roof, memory_roof)
        return {"arithmetic_intensity": intensity, "compute_roof_macs_per_second": compute_roof, "memory_roof_macs_per_second": memory_roof, "attainable_macs_per_second": attainable, "compute_bound": compute_roof <= memory_roof, "memory_bound": memory_roof <= compute_roof}
