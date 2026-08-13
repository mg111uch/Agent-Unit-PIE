"""
Phase 4a tests: Network-on-Chip topology, transfer tasks, MoE flow.
"""

from vse.core.engine import CycleEngine
from vse.graphs.graph import build_moe_tasks
from vse.core.noc import NoC, NoCConfig
from vse.core.types import (
    Resource,
    ResourceType,
    Task,
)
from vse.workload import (
    HardwareConfig,
    simulate_moe,
)
from vse.models.moe import MoE, MoEConfig


def make_moe():
    return MoE(
        MoEConfig(
            hidden_dim=1024,
            intermediate_dim=2048,
            num_experts=8,
            top_k=2,
        )
    )


def make_noc(nodes=16, topology="ring"):
    return NoC(
        NoCConfig(
            topology=topology,
            nodes=nodes,
            link_bw=256,
            per_hop_cycles=4,
        )
    )


def test_noc_disabled_by_default():
    noc = make_noc(nodes=1)
    assert not noc.config.enabled
    assert noc.distance(3, 7) == 0


def test_ring_distance_wraps():
    noc = make_noc(nodes=16, topology="ring")
    assert noc.distance(0, 1) == 1
    assert noc.distance(0, 15) == 1
    assert noc.distance(0, 8) == 8


def test_mesh_distance_manhattan():
    noc = make_noc(nodes=16, topology="mesh")
    assert noc.distance(0, 3) == 3
    assert noc.distance(0, 15) == 6
    assert noc.distance(5, 10) == 2


def test_add_resources_only_when_enabled():
    engine = CycleEngine(frequency_hz=1e9)

    make_noc(nodes=1).add_resources(engine)
    assert "noc" not in engine.resources

    make_noc(nodes=8).add_resources(engine)
    assert engine.resources["noc"].resource_type == (
        ResourceType.NOC
    )


def test_transfer_task_hop_latency():
    noc = make_noc(nodes=16)

    task = noc.transfer_task(
        task_id="t",
        name="transfer",
        data_bytes=1024,
        src=0,
        dst=8,
        dependencies=[],
        metadata={},
    )

    assert task.work == 1024
    assert task.pipeline_latency == 32
    assert task.metadata["hops"] == 8
    assert task.resource_type == ResourceType.NOC


def test_moe_graph_without_noc_has_no_noc_tasks():
    tasks = build_moe_tasks(
        routing_cost=None,
        expert_costs=[],
    )
    assert tasks == []


def test_moe_graph_with_noc_adds_transfers():
    moe = make_moe()
    cost = moe.cost(tokens=8)
    noc = make_noc(nodes=16)

    tasks = build_moe_tasks(
        cost.routing_cost,
        cost.expert_costs,
        expert_units=64,
        weight_bytes_per_expert=1024,
        resident=True,
        chunks=2,
        noc=noc,
    )

    sends = [
        t for t in tasks if t.metadata.get("phase") == "send"
    ]
    returns = [
        t for t in tasks if t.metadata.get("phase") == "return"
    ]
    combines = [
        t for t in tasks if t.metadata.get("kind") == "combine"
    ]

    assert len(sends) == len(cost.expert_costs)
    assert len(returns) == len(cost.expert_costs)
    assert len(combines) == 1

    first_send = sends[0]
    expert_node = 0 % noc.config.nodes
    assert first_send.metadata["dst"] == expert_node


def test_engine_respects_task_latency_override():
    engine = CycleEngine(frequency_hz=1e9)

    engine.add_resource(
        Resource(
            name="noc",
            resource_type=ResourceType.NOC,
            capacity=1,
            throughput=256,
            pipeline_latency=0,
        )
    )

    engine.add_task(
        Task(
            task_id="t",
            name="transfer",
            resource_type=ResourceType.NOC,
            work=256,
            pipeline_latency=12,
        )
    )

    schedule = engine.schedule()

    task = schedule.tasks["t"]
    assert task.duration == 13


def test_simulate_moe_with_noc_reports_transfers():
    result = simulate_moe(
        make_moe(),
        tokens=8,
        config=HardwareConfig(
            num_pes=512,
            noc_nodes=16,
        ),
    )

    assert result.noc["transfers"] == 16
    assert result.noc["hops"] > 0


def test_mesh_vs_ring_hop_counts():
    mesh = make_noc(nodes=16, topology="mesh")
    ring = make_noc(nodes=16, topology="ring")

    mesh_hops = sum(
        mesh.distance(0, i) for i in range(16)
    )
    ring_hops = sum(
        ring.distance(0, i) for i in range(16)
    )

    assert mesh_hops < ring_hops


def test_transformer_ignores_noc_config():
    result = simulate_moe(
        make_moe(),
        tokens=8,
        config=HardwareConfig(
            num_pes=512,
            noc_nodes=1,
        ),
    )

    assert result.noc.get("transfers", 0) == 0


def test_multicast_scales_work_with_copies():
    noc = make_noc(nodes=16)

    task = noc.transfer_task(
        task_id="mc",
        name="multicast",
        data_bytes=1024,
        src=0,
        dst=0,
        dependencies=[],
        metadata={},
        dests=[4, 8, 12],
    )

    assert task.metadata["kind"] == "noc_multicast"
    assert task.metadata["copies"] == 3
    assert task.work == 3072
    assert task.pipeline_latency == 32


def test_broadcast_reaches_all_nodes():
    noc = make_noc(nodes=16)

    task = noc.broadcast_task(
        task_id="bc",
        name="broadcast",
        data_bytes=512,
        src=0,
        dependencies=[],
        metadata={},
    )

    assert task.metadata["kind"] == "noc_broadcast"
    assert task.metadata["copies"] == 16
    assert task.work == 8192


def test_moe_broadcast_replaces_per_expert_sends():
    moe = make_moe()
    cost = moe.cost(tokens=8)
    noc = make_noc(nodes=16)
    noc.config.broadcast = True

    tasks = build_moe_tasks(
        cost.routing_cost,
        cost.expert_costs,
        expert_units=64,
        weight_bytes_per_expert=1024,
        resident=True,
        chunks=2,
        noc=noc,
    )

    broadcasts = [
        t for t in tasks
        if t.metadata.get("kind") == "noc_broadcast"
    ]
    sends = [
        t for t in tasks if t.metadata.get("phase") == "send"
    ]

    assert len(broadcasts) == 1
    assert sends == []


def test_simulate_moe_broadcast_reports_congestion_and_deadlock():
    result = simulate_moe(
        make_moe(),
        tokens=8,
        config=HardwareConfig(
            num_pes=512,
            noc_nodes=16,
            noc_broadcast=True,
        ),
    )

    assert result.noc["broadcasts"] == 1
    assert result.noc["congestion"]["peak_concurrency"] >= 1
    assert result.noc["deadlock"]["acyclic"] is True


def test_deadlock_check_detects_cycles():
    from vse.core.noc import check_deadlock

    a = Task(
        task_id="a",
        name="a",
        resource_type=ResourceType.NOC,
        dependencies=["b"],
    )
    b = Task(
        task_id="b",
        name="b",
        resource_type=ResourceType.NOC,
        dependencies=["a"],
    )

    result = check_deadlock([a, b])

    assert result["acyclic"] is False
    assert set(result["cycle_tasks"]) == {"a", "b"}


def test_deadlock_check_accepts_acyclic():
    from vse.core.noc import check_deadlock

    a = Task(task_id="a", name="a", resource_type=ResourceType.NOC)
    b = Task(
        task_id="b",
        name="b",
        resource_type=ResourceType.NOC,
        dependencies=["a"],
    )

    assert check_deadlock([a, b])["acyclic"] is True
