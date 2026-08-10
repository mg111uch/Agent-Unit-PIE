from vse.core import Simulator
from vse.compute import ComputeArray, ComputeConfig
from vse.memory import Memory, MemoryConfig
from vse.ops import (
    OpType,
    attention_cost,
    combine_costs,
    linear_cost,
    matmul_cost,
    mlp_cost,
    tensor_bytes,
)


def make_hardware():
    sim = Simulator(frequency_hz=1e9)

    compute = ComputeArray(
        sim,
        "INT4",
        ComputeConfig(
            num_pes=1024,
            macs_per_pe_per_cycle=1,
            frequency_hz=1e9,
            pipeline_latency=2,
            data_bits=4,
        ),
    )

    memory = Memory(
        sim,
        "SRAM",
        MemoryConfig(
            capacity_bytes=1024 * 1024,
            read_bandwidth_bytes_per_cycle=64,
            write_bandwidth_bytes_per_cycle=64,
            read_latency_cycles=10,
            write_latency_cycles=10,
            max_outstanding=16,
        ),
    )

    return sim, compute, memory


def test_tensor_bytes():
    assert tensor_bytes((10,), 4) == 5
    assert tensor_bytes((10, 10), 4) == 50
    assert tensor_bytes((10, 10), 8) == 100


def test_matmul_mac_count():
    cost = matmul_cost(
        m=10,
        k=20,
        n=30,
    )

    assert cost.macs == 6000


def test_matmul_memory():
    cost = matmul_cost(
        m=10,
        k=20,
        n=30,
        input_bits=4,
        output_bits=16,
    )

    # A = 10 × 20 × 4 bits = 100 bytes
    # B = 20 × 30 × 4 bits = 300 bytes
    # C = 10 × 30 × 16 bits = 600 bytes
    assert cost.input_bytes == 400
    assert cost.output_bytes == 600


def test_linear():
    cost = linear_cost(
        tokens=4,
        input_dim=128,
        output_dim=256,
    )

    assert cost.macs == 4 * 128 * 256


def test_mlp():
    cost = mlp_cost(
        tokens=1,
        hidden_dim=4096,
        intermediate_dim=11008,
        gated=True,
    )

    expected = (
        4096 * 11008
        + 4096 * 11008
        + 11008 * 4096
    )

    assert cost.macs == expected


def test_attention():
    cost = attention_cost(
        tokens=8,
        hidden_dim=512,
        num_heads=8,
    )

    assert cost.op_type == OpType.ATTENTION
    assert cost.macs > 0


def test_hardware_estimates():
    sim, compute, memory = make_hardware()

    cost = matmul_cost(
        m=1,
        k=1024,
        n=1024,
        compute=compute,
        memory=memory,
    )

    assert cost.macs == 1024 * 1024
    assert cost.compute_cycles > 0
    assert cost.memory_read_cycles > 0
    assert cost.memory_write_cycles > 0


def test_combine():
    a = matmul_cost(1, 10, 20)
    b = matmul_cost(1, 20, 30)

    combined = combine_costs(
        [a, b],
        name="test",
    )

    assert combined.macs == (
        a.macs + b.macs
    )
