"""VSE target feasibility — split from benchmark.py."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Optional

from vse.benchmark.roofline import Benchmark, BenchmarkResult, hardware_limits
from vse.core.compute import ComputeArray
from vse.core.memory import Memory


@dataclass
class TargetAnalysis:
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
        return self.required_memory_bandwidth / 1e9

    @property
    def available_memory_bandwidth_gbps(self) -> float:
        return self.available_memory_bandwidth / 1e9

    def report(self) -> dict:
        return {"target_tok_s": self.target_tokens_per_second, "required_macs_s": self.required_macs_per_second, "available_macs_s": self.available_macs_per_second, "required_memory_GB_s": self.required_memory_bandwidth_gbps, "available_memory_GB_s": self.available_memory_bandwidth_gbps, "compute_utilization": self.compute_utilization, "memory_utilization": self.memory_utilization, "compute_feasible": self.compute_feasible, "memory_feasible": self.memory_feasible, "feasible": self.feasible}


def analyze_target(macs_per_token: int, memory_bytes_per_token: int, target_tokens_per_second: float, compute: Optional[ComputeArray], memory: Optional[Memory], frequency_hz: Optional[float] = None) -> TargetAnalysis:
    if target_tokens_per_second <= 0:
        raise ValueError("target_tokens_per_second must be > 0")
    limits = hardware_limits(compute=compute, memory=memory, frequency_hz=frequency_hz)
    required_macs = macs_per_token * target_tokens_per_second
    required_memory = memory_bytes_per_token * target_tokens_per_second
    available_macs = limits.compute_macs_per_second
    available_memory = limits.total_memory_bandwidth
    compute_utilization = required_macs / available_macs if available_macs > 0 else float("inf")
    memory_utilization = required_memory / available_memory if available_memory > 0 else float("inf")
    compute_feasible = required_macs <= available_macs
    memory_feasible = required_memory <= available_memory
    return TargetAnalysis(target_tokens_per_second=target_tokens_per_second, required_macs_per_second=required_macs, available_macs_per_second=available_macs, required_memory_bandwidth=required_memory, available_memory_bandwidth=available_memory, compute_utilization=compute_utilization, memory_utilization=memory_utilization, compute_feasible=compute_feasible, memory_feasible=memory_feasible, feasible=compute_feasible and memory_feasible)


def batch_decode_analysis(macs_per_token: int, memory_bytes_per_token: int, batch_sizes: list[int], compute: Optional[ComputeArray], memory: Optional[Memory], frequency_hz: Optional[float] = None) -> list[BenchmarkResult]:
    if not batch_sizes:
        raise ValueError("batch_sizes cannot be empty")
    results = []
    benchmark = Benchmark(compute=compute, memory=memory, frequency_hz=frequency_hz)
    for batch in batch_sizes:
        if batch <= 0:
            raise ValueError("batch sizes must be > 0")
        result = benchmark.workload(macs=macs_per_token * batch, memory_bytes=memory_bytes_per_token * batch, tokens=batch, name=f"batch_decode_{batch}")
        results.append(result)
    return results


def format_benchmark(result: BenchmarkResult) -> str:
    return (f"{result.name}\n  tokens:              {result.tokens:,}\n  sequence length:     {result.sequence_length:,}\n  MACs:                {result.total_macs:,}\n  memory:              {result.total_memory_bytes:,} bytes\n  compute cycles:      {result.compute_cycles:,}\n  memory cycles:       {result.memory_cycles:,}\n  latency:             {result.latency_ms:.6f} ms\n  throughput:          {result.throughput_tokens_per_second:,.2f} tok/s\n  bandwidth required:  {result.required_bandwidth_gb_per_second:,.2f} GB/s\n  compute bound:       {result.compute_bound}\n  memory bound:        {result.memory_bound}\n  target:              {result.target_tokens_per_second}\n  target reached:      {result.target_reached}")


def format_target(result: TargetAnalysis) -> str:
    return (f"Target: {result.target_tokens_per_second:,.0f} tok/s\n  Required compute:    {result.required_macs_per_second / 1e15:.3f} P-MAC/s\n  Available compute:   {result.available_macs_per_second / 1e15:.3f} P-MAC/s\n  Compute utilization: {result.compute_utilization * 100:.2f}%\n  Required bandwidth:  {result.required_memory_bandwidth_gbps:.2f} GB/s\n  Available bandwidth: {result.available_memory_bandwidth_gbps:.2f} GB/s\n  Memory utilization:  {result.memory_utilization * 100:.2f}%\n  Compute feasible:    {result.compute_feasible}\n  Memory feasible:     {result.memory_feasible}\n  OVERALL FEASIBLE:    {result.feasible}")
