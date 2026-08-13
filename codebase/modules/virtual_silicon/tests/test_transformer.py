from vse.core.core import Simulator
from vse.core.compute import ComputeArray, ComputeConfig
from vse.core.memory import Memory, MemoryConfig
from vse.models.transformer import (
    KVCache,
    TransformerConfig,
    TransformerLayer,
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

    return sim, compute, memory


def test_transformer_config():
    config = TransformerConfig(
        hidden_dim=4096,
        num_heads=32,
        intermediate_dim=11008,
    )

    assert config.head_dim == 128


def test_kv_cache():
    config = TransformerConfig(
        hidden_dim=4096,
        num_heads=32,
        intermediate_dim=11008,
        kv_bits=16,
    )

    cache = KVCache(
        config,
        num_layers=32,
        max_sequence_length=4096,
    )

    # 2 × 32 × 128 × 16 bits
    expected_per_token = 16_384

    assert cache.bytes_per_token_per_layer() == expected_per_token

    assert (
        cache.total_bytes(4096)
        == 32 * 4096 * expected_per_token
    )


def test_decode_cost():
    sim, compute, memory = make_hardware()

    config = TransformerConfig(
        hidden_dim=4096,
        num_heads=32,
        intermediate_dim=11008,
    )

    layer = TransformerLayer(
        config,
        compute=compute,
        memory=memory,
    )

    cost = layer.decode_cost(
        sequence_length=4096,
    )

    assert cost.tokens == 1
    assert cost.sequence_length == 4096
    assert cost.macs > 0
    assert cost.kv_read_bytes > 0
    assert cost.kv_write_bytes > 0


def test_prefill_cost():
    sim, compute, memory = make_hardware()

    config = TransformerConfig(
        hidden_dim=1024,
        num_heads=16,
        intermediate_dim=4096,
    )

    layer = TransformerLayer(
        config,
        compute=compute,
        memory=memory,
    )

    cost = layer.prefill_cost(
        sequence_length=128,
    )

    assert cost.tokens == 128
    assert cost.sequence_length == 128
    assert cost.macs > 0


def test_model():
    sim, compute, memory = make_hardware()

    config = TransformerConfig(
        hidden_dim=1024,
        num_heads=16,
        intermediate_dim=4096,
    )

    model = TransformerModel(
        config,
        num_layers=24,
        compute=compute,
        memory=memory,
    )

    cost = model.decode_cost(
        sequence_length=4096,
    )

    assert cost.macs > 0
    assert cost.memory_bytes > 0
    assert cost.layers == 24


def test_parameter_count():
    config = TransformerConfig(
        hidden_dim=4096,
        num_heads=32,
        intermediate_dim=11008,
    )

    model = TransformerModel(
        config,
        num_layers=32,
    )

    assert model.parameter_count() > 0
    assert model.parameter_bytes() > 0
