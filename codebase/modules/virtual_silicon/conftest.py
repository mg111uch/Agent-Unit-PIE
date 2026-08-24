"""Shared fixtures for Phase 0 regression."""

import pytest
from vse.core.compute import ComputeArray, ComputeConfig
from vse.core.memory import Memory, MemoryConfig
from vse.models.config import TransformerConfig
from vse.models.moe_config import MoEConfig
from vse.models.transformer import TransformerModel
from vse.models.moe import MoE
from vse.workload import HardwareConfig


@pytest.fixture
def hw_small():
    return HardwareConfig(num_pes=512, memory_bytes_per_cycle=256, frequency_hz=1e9)


@pytest.fixture
def transformer_small():
    cfg = TransformerConfig(hidden_dim=1024, num_heads=8, intermediate_dim=2816)
    return TransformerModel(cfg, num_layers=8)


@pytest.fixture
def moe_small():
    cfg = MoEConfig(hidden_dim=1024, intermediate_dim=2048, num_experts=8, top_k=2)
    return MoE(cfg)


@pytest.fixture
def compute_small():
    from vse.core.core import Simulator
    sim = Simulator(frequency_hz=1e9)
    cfg = ComputeConfig(num_pes=512, frequency_hz=1e9)
    return ComputeArray(sim, "compute", cfg)


@pytest.fixture
def memory_small():
    from vse.core.core import Simulator
    sim = Simulator(frequency_hz=1e9)
    cfg = MemoryConfig(capacity_bytes=64*1024, read_bandwidth_bytes_per_cycle=256, write_bandwidth_bytes_per_cycle=256, read_latency_cycles=1, write_latency_cycles=1, max_outstanding=1)
    return Memory(sim, "mem", cfg)
