"""
Phase 3 tests: memory hierarchy, weight residency, bank conflicts.
"""

import pytest

from vse.core.engine import CycleEngine
from vse.core.memory_hierarchy import (
    MemoryHierarchy,
    MemoryLevel,
    format_memory_report,
)
from vse.models.moe import MoE, MoEConfig
from vse.models.transformer import (
    TransformerConfig,
    TransformerModel,
)
from vse.core.types import Resource, ResourceType, Task
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


def test_level_validation():
    with pytest.raises(ValueError):
        MemoryLevel(name="sram", capacity_bytes=-1)

    with pytest.raises(ValueError):
        MemoryLevel(name="sram", banks=0)


def test_default_hierarchy_has_sram_and_hbm():
    hierarchy = MemoryHierarchy.default(
        sram_bytes=1024,
        memory_bytes_per_cycle=256,
    )

    assert set(hierarchy.levels) == {"sram", "hbm"}
    assert hierarchy.levels["sram"].capacity_bytes == 1024
    assert hierarchy.levels["hbm"].capacity_bytes == 0


def test_weights_resident_by_capacity():
    hierarchy = MemoryHierarchy.default(
        sram_bytes=1000,
        memory_bytes_per_cycle=256,
    )

    assert hierarchy.weights_resident(500) is True
    assert hierarchy.weights_resident(1000) is True
    assert hierarchy.weights_resident(1001) is False
    assert hierarchy.weights_resident(0) is False


def test_residency_report():
    hierarchy = MemoryHierarchy.default(
        sram_bytes=1000,
        memory_bytes_per_cycle=256,
    )

    resident = hierarchy.residency_report(500)
    assert resident["resident"] is True
    assert resident["resident_bytes"] == 500
    assert resident["level"] == "sram"

    streamed = hierarchy.residency_report(5000)
    assert streamed["resident"] is False
    assert streamed["hbm_bytes"] == 5000
    assert streamed["level"] == "hbm"


def test_engine_routes_by_mem_level():
    engine = CycleEngine(frequency_hz=1e9)

    engine.add_resource(
        Resource(
            name="sram_read",
            resource_type=ResourceType.MEMORY_READ,
            capacity=4,
            throughput=8,
            banks=4,
        )
    )

    engine.add_resource(
        Resource(
            name="hbm_read",
            resource_type=ResourceType.MEMORY_READ,
            capacity=1,
            throughput=8,
            primary=True,
        )
    )

    engine.add_task(
        Task(
            task_id="sram_access",
            name="SRAM",
            resource_type=ResourceType.MEMORY_READ,
            work=16,
            mem_level="sram",
        )
    )

    engine.add_task(
        Task(
            task_id="hbm_access",
            name="HBM",
            resource_type=ResourceType.MEMORY_READ,
            work=16,
            mem_level="hbm",
        )
    )

    result = engine.schedule()

    names = {
        event.task_id: event.resource_name
        for event in result.events
    }

    assert names["sram_access"] == "sram_read"
    assert names["hbm_access"] == "hbm_read"


def test_bank_conflict_stalls():
    """
    Two tasks needing 2 banks each cannot both run on a 2-bank
    resource, so they serialize (bank conflict).
    """

    engine = CycleEngine(frequency_hz=1e9)

    engine.add_resource(
        Resource(
            name="sram_read",
            resource_type=ResourceType.MEMORY_READ,
            capacity=2,
            throughput=1,
            banks=2,
        )
    )

    for index in range(2):
        engine.add_task(
            Task(
                task_id=f"a{index}",
                name=f"A{index}",
                resource_type=ResourceType.MEMORY_READ,
                work=10,
                mem_level="sram",
                units=1,
                banks=2,
            )
        )

    result = engine.schedule()

    # Serialized: 10 cycles + 10 cycles (each at 1 unit x throughput 1).
    assert result.total_cycles == 20
    assert result.peak_banks["sram_read"] == 2

    # Without bank conflict (banks enough) both fit at cycle 0.
    engine2 = CycleEngine(frequency_hz=1e9)

    engine2.add_resource(
        Resource(
            name="sram_read",
            resource_type=ResourceType.MEMORY_READ,
            capacity=4,
            throughput=1,
            banks=4,
        )
    )

    for index in range(2):
        engine2.add_task(
            Task(
                task_id=f"b{index}",
                name=f"B{index}",
                resource_type=ResourceType.MEMORY_READ,
                work=10,
                mem_level="sram",
                units=1,
                banks=2,
            )
        )

    result2 = engine2.schedule()

    assert result2.total_cycles == 10


def test_traffic_aggregation_from_schedule():
    hierarchy = MemoryHierarchy.default(
        sram_bytes=1024,
        memory_bytes_per_cycle=256,
    )

    engine = CycleEngine(frequency_hz=1e9)

    for level in hierarchy.levels.values():
        engine.add_resource(
            Resource(
                name=f"{level.name}_read",
                resource_type=ResourceType.MEMORY_READ,
                capacity=1,
                throughput=8,
            )
        )

    engine.add_task(
        Task(
            task_id="r1",
            name="R1",
            resource_type=ResourceType.MEMORY_READ,
            work=100,
            mem_level="sram",
        )
    )

    engine.add_task(
        Task(
            task_id="r2",
            name="R2",
            resource_type=ResourceType.MEMORY_READ,
            work=200,
            mem_level="hbm",
        )
    )

    traffic = hierarchy.traffic(engine.schedule())

    assert traffic["sram"]["read_bytes"] == 100
    assert traffic["hbm"]["read_bytes"] == 200


def test_moe_weight_traffic_reported():
    result = simulate_moe(
        make_moe(),
        tokens=32,
        config=HardwareConfig(),
    )

    memory = result.memory_traffic

    # 64 experts, 1 token each -> all expert weights stream from HBM.
    assert memory["hbm_read_bytes"] > 0
    assert memory["hbm_write_bytes"] == 0
    assert memory["weight_residency"]["resident"] is False


def test_moe_weights_resident_with_large_sram():
    config = HardwareConfig(
        sram_bytes=6 * 1024**3,
        sram_bytes_per_cycle=2048,
        banks=16,
    )

    result = simulate_moe(
        make_moe(),
        tokens=32,
        config=config,
    )

    memory = result.memory_traffic

    assert memory["weight_residency"]["resident"] is True
    assert memory["sram_read_bytes"] > 0
    assert memory["hbm_read_bytes"] > 0


def test_format_memory_report_smoke():
    hierarchy = MemoryHierarchy.default(
        sram_bytes=1024,
        memory_bytes_per_cycle=256,
    )

    engine = CycleEngine(frequency_hz=1e9)

    for level in hierarchy.levels.values():
        engine.add_resource(
            Resource(
                name=f"{level.name}_read",
                resource_type=ResourceType.MEMORY_READ,
                capacity=1,
                throughput=8,
            )
        )

    engine.add_task(
        Task(
            task_id="r1",
            name="R1",
            resource_type=ResourceType.MEMORY_READ,
            work=64,
            mem_level="sram",
        )
    )

    report = hierarchy.report(
        engine.schedule(),
        weight_bytes=64,
    )

    text = format_memory_report(report)

    assert "MEMORY HIERARCHY" in text
    assert "SRAM" in text
    assert "HBM" in text


# ---------------------------------------------------------------------------
# Phase 3.2: KV-cache routing, activation movement, DMA, double buffering
# ---------------------------------------------------------------------------

def test_transformer_kv_on_sram_when_resident():
    resident = simulate_transformer(
        make_transformer(),
        sequence_length=4096,
        config=HardwareConfig(
            sram_bytes=8 * 1024**3,
            sram_bytes_per_cycle=8192,
        ),
    )

    streamed = simulate_transformer(
        make_transformer(),
        sequence_length=4096,
        config=HardwareConfig(),
    )

    assert resident.memory_traffic["sram_read_bytes"] > 0
    assert resident.memory_traffic["hbm_read_bytes"] < streamed.memory_traffic["hbm_read_bytes"]
    assert resident.total_cycles < streamed.total_cycles


def test_transformer_kv_streams_from_hbm_by_default():
    result = simulate_transformer(
        make_transformer(),
        sequence_length=4096,
        config=HardwareConfig(),
    )

    assert result.memory_traffic["sram_read_bytes"] == 0
    assert result.memory_traffic["hbm_read_bytes"] > 0


def test_moe_activation_movement_on_sram():
    result = simulate_moe(
        make_moe(),
        tokens=32,
        config=HardwareConfig(),
    )

    events = result.schedule.events

    assert any(
        event.resource_name == "sram_read"
        for event in events
    )
    assert any(
        event.resource_name == "sram_write"
        for event in events
    )


def test_resident_weights_use_dma():
    result = simulate_moe(
        make_moe(),
        tokens=32,
        config=HardwareConfig(
            sram_bytes=6 * 1024**3,
            sram_bytes_per_cycle=2048,
            banks=16,
        ),
    )

    assert any(
        event.resource_name == "dma"
        for event in result.schedule.events
    )


def test_double_buffering_speeds_up_streaming():
    base = simulate_moe(
        make_moe(),
        tokens=32,
        config=HardwareConfig(weight_chunks=1),
    )

    buffered = simulate_moe(
        make_moe(),
        tokens=32,
        config=HardwareConfig(weight_chunks=8),
    )

    assert buffered.total_cycles < base.total_cycles
