from vse.core.core import Simulator
from vse.core.compute import ComputeArray, ComputeConfig
from vse.core.memory import Memory, MemoryConfig
from vse.models.moe import MoE, MoEConfig


def make_moe():
    sim = Simulator()

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

    config = MoEConfig(
        hidden_dim=4096,
        intermediate_dim=11008,
        num_experts=8,
        top_k=2,
    )

    return MoE(
        config,
        compute=compute,
        memory=memory,
    )


def test_routing():
    moe = make_moe()

    routing = moe.balanced_routing(
        tokens=16,
    )

    assert routing.num_tokens == 16
    assert routing.top_k == 2

    assert sum(
        routing.tokens_per_expert
    ) == 32


def test_expert_balance():
    moe = make_moe()

    routing = moe.balanced_routing(
        tokens=16,
    )

    assert routing.load_imbalance == 1.0


def test_parameter_count():
    moe = make_moe()

    # 3 projections × hidden × intermediate
    expected_expert = (
        3
        * 4096
        * 11008
    )

    assert (
        moe.expert_parameter_count
        == expected_expert
    )

    assert (
        moe.total_parameter_count
        == expected_expert * 8
    )

    assert (
        moe.active_parameter_count
        == expected_expert * 2
    )


def test_cost():
    moe = make_moe()

    cost = moe.cost(
        tokens=16,
    )

    assert cost.tokens == 16
    assert cost.num_experts == 8
    assert cost.top_k == 2

    assert cost.macs > 0
    assert cost.total_parameter_count > 0
    assert cost.active_parameter_count > 0


def test_architecture_report():
    moe = make_moe()

    report = moe.architecture_report()

    assert report["num_experts"] == 8
    assert report["top_k"] == 2
    assert report["total_parameters"] > 0
    assert report["active_parameters"] > 0
    assert 0 < report["activation_ratio"] <= 1


def test_large_moe_ratio():
    """
    Verify the basic 300B/30B architectural relationship
    can be represented.
    """

    # Choose dimensions that produce approximately the desired
    # active/total ratio through top-K routing.
    moe = MoE(
        MoEConfig(
            hidden_dim=4096,
            intermediate_dim=11008,
            num_experts=100,
            top_k=10,
        )
    )

    report = moe.architecture_report()

    assert report["activation_ratio"] == 0.1
