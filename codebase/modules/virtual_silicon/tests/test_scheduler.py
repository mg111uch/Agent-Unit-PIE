import pytest

from vse.scheduler import (
    Resource,
    ResourceType,
    Scheduler,
    Task,
    moe_tasks,
    transformer_tasks,
    schedule_moe,
)


def make_scheduler():
    scheduler = Scheduler(
        frequency_hz=1e9
    )

    scheduler.add_resource(
        Resource(
            name="compute",
            resource_type=ResourceType.COMPUTE,
            capacity=1024,
            throughput=1,
        )
    )

    scheduler.add_resource(
        Resource(
            name="router",
            resource_type=ResourceType.ROUTER,
            capacity=1,
            throughput=1024,
        )
    )

    return scheduler


def test_resource_cycles():
    resource = Resource(
        name="compute",
        resource_type=ResourceType.COMPUTE,
        capacity=10,
        throughput=2,
    )

    # Effective throughput = 10 × 2 = 20/cycle.
    assert resource.cycles_for_work(20) == 1
    assert resource.cycles_for_work(21) == 2


def test_simple_task():
    scheduler = make_scheduler()

    scheduler.add_task(
        Task(
            task_id="a",
            name="A",
            resource_type=ResourceType.COMPUTE,
            work=100,
        )
    )

    result = scheduler.schedule()

    assert result.total_cycles == 1
    assert len(result.events) == 1


def test_dependencies():
    scheduler = make_scheduler()

    scheduler.add_task(
        Task(
            task_id="a",
            name="A",
            resource_type=ResourceType.COMPUTE,
            work=1024,
        )
    )

    scheduler.add_task(
        Task(
            task_id="b",
            name="B",
            resource_type=ResourceType.COMPUTE,
            work=1024,
            dependencies=["a"],
        )
    )

    result = scheduler.schedule()

    a = result.tasks["a"]
    b = result.tasks["b"]

    assert a.end_cycle == b.start_cycle


def test_parallel_dependency_graph():
    scheduler = make_scheduler()

    scheduler.add_task(
        Task(
            task_id="root",
            name="Root",
            resource_type=ResourceType.COMPUTE,
            work=1024,
        )
    )

    scheduler.add_task(
        Task(
            task_id="a",
            name="A",
            resource_type=ResourceType.COMPUTE,
            work=1024,
            dependencies=["root"],
        )
    )

    scheduler.add_task(
        Task(
            task_id="b",
            name="B",
            resource_type=ResourceType.COMPUTE,
            work=1024,
            dependencies=["root"],
        )
    )

    scheduler.add_task(
        Task(
            task_id="join",
            name="Join",
            resource_type=ResourceType.COMPUTE,
            work=1024,
            dependencies=[
                "a",
                "b",
            ],
        )
    )

    result = scheduler.schedule()

    assert result.total_cycles > 0
    assert len(result.events) == 4


def test_cycle_detection():
    scheduler = make_scheduler()

    scheduler.add_task(
        Task(
            task_id="a",
            name="A",
            resource_type=ResourceType.COMPUTE,
            work=10,
            dependencies=["b"],
        )
    )

    scheduler.add_task(
        Task(
            task_id="b",
            name="B",
            resource_type=ResourceType.COMPUTE,
            work=10,
            dependencies=["a"],
        )
    )

    with pytest.raises(RuntimeError):
        scheduler.schedule()


def test_transformer_tasks():
    tasks = transformer_tasks(
        layers=4,
        hidden_dim=512,
        intermediate_dim=2048,
        sequence_length=1024,
    )

    assert len(tasks) > 0

    task_ids = {
        task.task_id
        for task in tasks
    }

    assert "layer_0_attention" in task_ids
    assert "layer_3_down" in task_ids


def test_moe_tasks():
    tasks = moe_tasks(
        num_experts=8,
        active_experts=2,
        tokens_per_expert=[
            2, 2, 0, 0,
            0, 0, 0, 0,
        ],
        hidden_dim=512,
        intermediate_dim=2048,
    )

    task_ids = {
        task.task_id
        for task in tasks
    }

    assert "moe_router" in task_ids
    assert "expert_0" in task_ids
    assert "expert_1" in task_ids
    assert "moe_combine" in task_ids


def test_moe_schedule():
    result = schedule_moe(
        num_experts=8,
        active_experts=2,
        tokens_per_expert=[
            2, 2, 0, 0,
            0, 0, 0, 0,
        ],
        hidden_dim=512,
        intermediate_dim=2048,
        num_pes=1024,
    )

    assert result.total_cycles > 0
    assert len(result.events) > 0
