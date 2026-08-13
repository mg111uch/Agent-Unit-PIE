import pytest

from vse.core.engine import (
    CycleEngine,
    Resource,
    ResourceType,
    Task,
)


def make_compute(capacity=100, pipeline_latency=0):
    engine = CycleEngine(frequency_hz=1e9)

    engine.add_resource(
        Resource(
            name="compute",
            resource_type=ResourceType.COMPUTE,
            capacity=capacity,
            throughput=1,
            pipeline_latency=pipeline_latency,
        )
    )

    return engine


def test_parallel_tasks():
    engine = make_compute()

    engine.add_task(
        Task(
            task_id="a",
            name="A",
            resource_type=ResourceType.COMPUTE,
            work=100,
            units=50,
        )
    )

    engine.add_task(
        Task(
            task_id="b",
            name="B",
            resource_type=ResourceType.COMPUTE,
            work=100,
            units=50,
        )
    )

    result = engine.schedule()

    # Both fit at cycle 0 (50 + 50 units), each takes 2 cycles.
    assert result.total_cycles == 2
    assert result.peak_concurrency["compute"] == 100


def test_parallel_utilization():
    engine = make_compute()

    for index in range(4):
        engine.add_task(
            Task(
                task_id=f"t{index}",
                name=f"T{index}",
                resource_type=ResourceType.COMPUTE,
                work=25,
                units=25,
            )
        )

    result = engine.schedule()

    # 4 tasks × 25 work on 100 units in parallel → one cycle.
    assert result.total_cycles == 1
    assert result.resource_utilization("compute") == pytest.approx(1.0)


def test_serial_when_units_exceed_capacity():
    engine = make_compute(capacity=100)

    engine.add_task(
        Task(
            task_id="a",
            name="A",
            resource_type=ResourceType.COMPUTE,
            work=100,
            units=100,
        )
    )

    engine.add_task(
        Task(
            task_id="b",
            name="B",
            resource_type=ResourceType.COMPUTE,
            work=100,
            units=100,
        )
    )

    result = engine.schedule()

    # Only one fits at a time → serialized.
    assert result.total_cycles == 2


def test_units_exceeding_capacity_rejected():
    engine = make_compute(capacity=100)

    engine.add_task(
        Task(
            task_id="a",
            name="A",
            resource_type=ResourceType.COMPUTE,
            work=1,
            units=200,
        )
    )

    with pytest.raises(ValueError):
        engine.schedule()


def test_pipeline_latency_delays_result_but_frees_units():
    engine = make_compute(capacity=10, pipeline_latency=3)

    engine.add_task(
        Task(
            task_id="a",
            name="A",
            resource_type=ResourceType.COMPUTE,
            work=10,
            units=10,
        )
    )

    engine.add_task(
        Task(
            task_id="b",
            name="B",
            resource_type=ResourceType.COMPUTE,
            work=10,
            units=10,
        )
    )

    engine.add_task(
        Task(
            task_id="c",
            name="C",
            resource_type=ResourceType.COMPUTE,
            work=10,
            units=10,
            dependencies=["a"],
        )
    )

    result = engine.schedule()

    # A: occupancy 1 cycle, result at cycle 4 (1 + 3 pipeline).
    a = result.tasks["a"]
    assert a.end_cycle == 4

    # B waits only for A's units (released at cycle 1), not its result.
    b = result.tasks["b"]
    assert b.start_cycle == 1

    # C depends on A's result → starts at cycle 4.
    c = result.tasks["c"]
    assert c.start_cycle == 4
    assert c.end_cycle == 8

    assert result.total_cycles == 8


def test_cycle_detection():
    engine = make_compute()

    engine.add_task(
        Task(
            task_id="a",
            name="A",
            resource_type=ResourceType.COMPUTE,
            work=10,
            dependencies=["b"],
        )
    )

    engine.add_task(
        Task(
            task_id="b",
            name="B",
            resource_type=ResourceType.COMPUTE,
            work=10,
            dependencies=["a"],
        )
    )

    with pytest.raises(RuntimeError):
        engine.schedule()


def test_trace_and_peak():
    engine = make_compute()

    engine.add_task(
        Task(
            task_id="a",
            name="A",
            resource_type=ResourceType.COMPUTE,
            work=50,
            units=50,
        )
    )

    engine.add_task(
        Task(
            task_id="b",
            name="B",
            resource_type=ResourceType.COMPUTE,
            work=50,
            units=50,
        )
    )

    result = engine.schedule()

    assert len(result.trace) > 0

    for entry in result.trace:
        assert entry.resource == "compute"
        assert entry.busy_units <= entry.capacity

    assert result.peak_concurrency["compute"] == 100


def test_default_units_use_whole_resource():
    engine = make_compute(capacity=10)

    engine.add_task(
        Task(
            task_id="a",
            name="A",
            resource_type=ResourceType.COMPUTE,
            work=20,
        )
    )

    result = engine.schedule()

    # units=0 → full capacity: ceil(20 / 10) = 2 cycles.
    assert result.total_cycles == 2
