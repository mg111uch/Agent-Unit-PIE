"""VSE benchmark — facade (split for <500 LOC)."""

from vse.benchmark.roofline import Benchmark, BenchmarkResult, HardwareLimits, hardware_limits
from vse.benchmark.target import TargetAnalysis, analyze_target, batch_decode_analysis, format_benchmark, format_target

__all__ = ["BenchmarkResult", "HardwareLimits", "hardware_limits", "Benchmark", "TargetAnalysis", "analyze_target", "batch_decode_analysis", "format_benchmark", "format_target"]
