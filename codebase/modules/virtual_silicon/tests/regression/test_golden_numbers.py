"""Golden numbers from usage.md §5 — Phase 0 regression harness.

Pins flagship analytical numbers so Phase A-F refactors don't silently
drift them. Tolerances are tight for cycle counts, looser for timing.
"""

from vse.models.config import TransformerConfig
from vse.models.moe_config import MoEConfig
from vse.models.transformer import TransformerModel
from vse.workload import HardwareConfig, simulate_moe, simulate_transformer


def _hw(num_pes=4096, mem_bw=256, freq=1e9, **kw):
    return HardwareConfig(num_pes=num_pes, memory_bytes_per_cycle=mem_bw, frequency_hz=freq, **kw)


def test_transformer_decode_golden():
    model = TransformerModel(TransformerConfig(hidden_dim=4096, num_heads=32, intermediate_dim=11008), num_layers=8)
    r = simulate_transformer(model, sequence_length=4096, config=_hw(mem_bw=1024))
    assert r.total_cycles == 4213488, f"decode cycles {r.total_cycles} != 4213488"
    assert 230 < r.tokens_per_second < 245


def test_transformer_fused_golden():
    from vse.compiler.compiler import compile_transformer
    from vse.compiler.compiler import execute
    model = TransformerModel(TransformerConfig(hidden_dim=4096, num_heads=32, intermediate_dim=11008), num_layers=8)
    prog = compile_transformer(model, sequence_length=4096, config=_hw(mem_bw=1024))
    r = execute(prog)
    assert r.total_cycles == 1157595, f"fused cycles {r.total_cycles} != 1157595"
    assert 850 < r.tokens_per_second < 880


def test_moe_golden():
    from vse.models.moe import MoE
    moe = MoE(MoEConfig(hidden_dim=4096, intermediate_dim=14336, num_experts=64, top_k=2))
    r = simulate_moe(moe, tokens=32, config=_hw())
    assert r.total_cycles == 24514592, f"moe cycles {r.total_cycles} != 24514592"
    assert 1.2e3 < r.tokens_per_second < 1.4e3


def test_physics_gate_stub():
    from vse.physics.gate import PhysicsGate
    res = PhysicsGate.check()
    assert res.plausible is True
    assert len(res.checks) == 14


def test_precision_map_stub():
    from vse.compiler.precision import Q2Block
    b = Q2Block(bits=2, group_size=32, scale_bits=8)
    assert b.effective_bytes(64) < 64
