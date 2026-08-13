from vse.core.core import Simulator
from vse.core.compute import ComputeArray, ComputeConfig
from vse.core.memory import Memory, MemoryConfig
from vse.benchmark.benchmark import (
    Benchmark,
    analyze_target,
    batch_decode_analysis,
)
from vse.models.transformer import (
    TransformerConfig,
    TransformerModel,
)


def make_hardware():
    sim = Simulator(frequency_hz=1e9)

    compute = ComputeArray(
        sim,
        "INT4_ARRAY",
        ComputeConfig(
            num_pes=4096,
            macs_per_pe_per_cycle=1,
            frequency_hz=1e9,
            pipeline_latency=2,
            data_bits=4,
        ),
    )

    memory = Memory(
        sim,
        "HBM",
        MemoryConfig(
            capacity_bytes=16 * 1024**3,
            read_bandwidth_bytes_per_cycle=256,
            write_bandwidth_bytes_per_cycle=256,
            read_latency_cycles=20,
            write_latency_cycles=20,
            max_outstanding=64,
        ),
    )

    return compute, memory


def test_generic_workload():
    compute, memory = make_hardware()

    benchmark = Benchmark(
        compute=compute,
        memory=memory,
    )

    result = benchmark.workload(
        macs=1_000_000,
        memory_bytes=10_000,
        tokens=1,
    )

    assert result.total_macs == 1_000_000
    assert result.latency_seconds > 0
    assert result.throughput_tokens_per_second > 0


def test_transformer_decode():
    compute, memory = make_hardware()

    model = TransformerModel(
        TransformerConfig(
            hidden_dim=1024,
            num_heads=16,
            intermediate_dim=4096,
        ),
        num_layers=24,
        compute=compute,
        memory=memory,
    )

    benchmark = Benchmark(
        compute=compute,
        memory=memory,
    )

    result = benchmark.transformer_decode(
        model,
        sequence_length=4096,
    )

    assert result.total_macs > 0
    assert result.total_memory_bytes > 0
    assert result.throughput_tokens_per_second > 0


def test_target_analysis():
    compute, memory = make_hardware()

    result = analyze_target(
        macs_per_token=1_000_000,
        memory_bytes_per_token=1_000,
        target_tokens_per_second=1_000,
        compute=compute,
        memory=memory,
    )

    assert result.target_tokens_per_second == 1_000
    assert result.required_macs_per_second == 1_000_000_000
    assert result.required_memory_bandwidth == 1_000_000


def test_batch_scaling():
    compute, memory = make_hardware()

    results = batch_decode_analysis(
        macs_per_token=1_000_000,
        memory_bytes_per_token=10_000,
        batch_sizes=[1, 2, 4, 8],
        compute=compute,
        memory=memory,
    )

    assert len(results) == 4

    for result in results:
        assert (
            result.throughput_tokens_per_second
            > 0
        )


def test_roofline():
    compute, memory = make_hardware()

    benchmark = Benchmark(
        compute=compute,
        memory=memory,
    )

    result = benchmark.roofline(
        macs=1_000_000,
        memory_bytes=10_000,
    )

    assert (
        result["arithmetic_intensity"]
        == 100.0
    )

    assert (
        result["attainable_macs_per_second"]
        > 0
    )
