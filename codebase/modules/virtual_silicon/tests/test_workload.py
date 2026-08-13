from vse.models.moe import MoE, MoEConfig
from vse.models.transformer import (
    TransformerConfig,
    TransformerModel,
)
from vse.workload import (
    HardwareConfig,
    simulate_moe,
    simulate_transformer,
)


def make_transformer():
    return TransformerModel(
        TransformerConfig(
            hidden_dim=4096,
            num_heads=32,
            intermediate_dim=11008,
        ),
        num_layers=8,
    )


def make_moe():
    return MoE(
        MoEConfig(
            hidden_dim=4096,
            intermediate_dim=14336,
            num_experts=64,
            top_k=2,
        )
    )


def test_transformer_decode_end_to_end():
    result = simulate_transformer(
        make_transformer(),
        sequence_length=4096,
        config=HardwareConfig(),
    )

    assert result.name == "transformer"
    assert result.tokens == 1
    assert result.total_cycles > 0
    assert result.total_macs > 0
    assert result.total_memory_bytes > 0


def test_transformer_prefill_end_to_end():
    result = simulate_transformer(
        make_transformer(),
        sequence_length=1024,
        mode="prefill",
        config=HardwareConfig(),
    )

    assert result.tokens == 1024
    assert result.total_cycles > 0


def test_transformer_invalid_mode():
    try:
        simulate_transformer(
            make_transformer(),
            sequence_length=128,
            mode="bogus",
        )
        assert False
    except ValueError:
        pass


def test_moe_end_to_end():
    result = simulate_moe(
        make_moe(),
        tokens=32,
        config=HardwareConfig(),
    )

    assert result.name == "moe"
    assert result.tokens == 32
    assert result.total_cycles > 0
    assert result.total_macs > 0


def test_result_report_keys():
    result = simulate_transformer(
        make_transformer(),
        sequence_length=512,
        config=HardwareConfig(),
    )

    report = result.report()

    for key in (
        "name",
        "tokens",
        "sequence_length",
        "total_cycles",
        "latency_us",
        "tokens_per_second",
        "compute_utilization",
        "memory_utilization",
    ):
        assert key in report

    assert report["compute_utilization"] >= 0.0
    assert report["compute_utilization"] <= 1.0
    assert report["memory_utilization"] >= 0.0
    assert report["memory_utilization"] <= 1.0


def test_moe_expert_parallelism():
    result = simulate_moe(
        make_moe(),
        tokens=8,
        config=HardwareConfig(),
    )

    # Router task followed by parallel expert tasks.
    events = result.schedule.events

    assert any(
        event.resource_name == "router"
        for event in events
    )

    compute_events = [
        event
        for event in events
        if event.resource_name == "compute"
    ]

    assert len(compute_events) > 1
