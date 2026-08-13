from vse.scheduler import (
    Scheduler,
    Resource,
    ResourceType,
    Task,
)

scheduler = Scheduler(
    frequency_hz=1e9
)

scheduler.add_resource(
    Resource(
        name="compute",
        resource_type=ResourceType.COMPUTE,
        capacity=4096,
        throughput=1,
    )
)

scheduler.add_task(
    Task(
        task_id="matmul",
        name="Transformer MatMul",
        resource_type=ResourceType.COMPUTE,
        work=1_000_000_000,
    )
)

result = scheduler.schedule()

print(result.report())