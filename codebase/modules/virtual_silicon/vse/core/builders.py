"""
VSE - Virtual Silicon Engine
vse/builders.py

Task builders and convenience schedulers for Transformer and MoE
workloads.

These construct Task graphs for the cycle engine and provide the
`Scheduler` facade used as the public entry point.
"""

from __future__ import annotations

from typing import Optional

from vse.core.engine import CycleEngine
from vse.core.types import Resource, ResourceType, ScheduleResult, Task


class Scheduler(CycleEngine):
    """
    Parallel cycle-level scheduler.

    A thin subclass of the cycle engine. Tasks with explicit `units`
    run concurrently on different capacity units of the same resource.
    """


# ---------------------------------------------------------------------------
# Transformer task generation
# ---------------------------------------------------------------------------

def transformer_tasks(
    layers: int,
    hidden_dim: int,
    intermediate_dim: int,
    sequence_length: int,
    gated_mlp: bool = True,
) -> list[Task]:
    """
    Generate a simple Transformer decode graph.

    This is intentionally generic and does not depend on TransformerModel.

    One layer:

        attention
            ↓
        MLP projections
            ↓
        next layer

    The goal is to expose the execution graph to the scheduler.
    """

    if layers <= 0:
        raise ValueError(
            "layers must be > 0"
        )

    if hidden_dim <= 0:
        raise ValueError(
            "hidden_dim must be > 0"
        )

    if intermediate_dim <= 0:
        raise ValueError(
            "intermediate_dim must be > 0"
        )

    if sequence_length <= 0:
        raise ValueError(
            "sequence_length must be > 0"
        )

    tasks: list[Task] = []

    previous: Optional[str] = None

    for layer in range(layers):

        attention_id = (
            f"layer_{layer}_attention"
        )

        attention_work = (
            4
            * hidden_dim
            * hidden_dim
            + 2
            * sequence_length
            * hidden_dim
        )

        attention = Task(
            task_id=attention_id,
            name=f"Layer {layer} Attention",
            resource_type=ResourceType.COMPUTE,
            work=attention_work,
            dependencies=(
                [previous]
                if previous is not None
                else []
            ),
            metadata={
                "layer": layer,
                "type": "attention",
            },
        )

        tasks.append(attention)

        if gated_mlp:

            gate_id = (
                f"layer_{layer}_gate"
            )

            gate = Task(
                task_id=gate_id,
                name=f"Layer {layer} Gate",
                resource_type=ResourceType.COMPUTE,
                work=(
                    hidden_dim
                    * intermediate_dim
                ),
                dependencies=[
                    attention_id
                ],
                metadata={
                    "layer": layer,
                    "type": "mlp_gate",
                },
            )

            tasks.append(gate)

            up_id = (
                f"layer_{layer}_up"
            )

            up = Task(
                task_id=up_id,
                name=f"Layer {layer} Up",
                resource_type=ResourceType.COMPUTE,
                work=(
                    hidden_dim
                    * intermediate_dim
                ),
                dependencies=[
                    attention_id
                ],
                metadata={
                    "layer": layer,
                    "type": "mlp_up",
                },
            )

            tasks.append(up)

            down_id = (
                f"layer_{layer}_down"
            )

            down = Task(
                task_id=down_id,
                name=f"Layer {layer} Down",
                resource_type=ResourceType.COMPUTE,
                work=(
                    intermediate_dim
                    * hidden_dim
                ),
                dependencies=[
                    gate_id,
                    up_id,
                ],
                metadata={
                    "layer": layer,
                    "type": "mlp_down",
                },
            )

            tasks.append(down)

            previous = down_id

        else:

            mlp_id = (
                f"layer_{layer}_mlp"
            )

            mlp = Task(
                task_id=mlp_id,
                name=f"Layer {layer} MLP",
                resource_type=ResourceType.COMPUTE,
                work=(
                    2
                    * hidden_dim
                    * intermediate_dim
                ),
                dependencies=[
                    attention_id
                ],
                metadata={
                    "layer": layer,
                    "type": "mlp",
                },
            )

            tasks.append(mlp)

            previous = mlp_id

    return tasks


# ---------------------------------------------------------------------------
# MoE task generation
# ---------------------------------------------------------------------------

def moe_tasks(
    num_experts: int,
    active_experts: int,
    tokens_per_expert: list[int],
    hidden_dim: int,
    intermediate_dim: int,
    gated: bool = True,
    num_pes: Optional[int] = None,
) -> list[Task]:
    """
    Generate an executable MoE task graph.

    Graph:

        router
          ↓
        expert 0 ─┐
        expert 1  │
        ...       ├→ combine
        expert N ─┘

    Only active experts receive compute tasks.

    If num_pes is provided, expert tasks receive explicit units so
    they execute in parallel on the compute array.
    """

    if num_experts <= 0:
        raise ValueError(
            "num_experts must be > 0"
        )

    if active_experts <= 0:
        raise ValueError(
            "active_experts must be > 0"
        )

    if active_experts > num_experts:
        raise ValueError(
            "active_experts cannot exceed "
            "num_experts"
        )

    if len(tokens_per_expert) != num_experts:
        raise ValueError(
            "tokens_per_expert length must "
            "equal num_experts"
        )

    expert_units = 0

    if num_pes:
        expert_units = max(
            1,
            num_pes // active_experts,
        )

    tasks: list[Task] = []

    router_id = "moe_router"

    router_work = (
        sum(tokens_per_expert)
        * hidden_dim
        * num_experts
    )

    router = Task(
        task_id=router_id,
        name="MoE Router",
        resource_type=ResourceType.ROUTER,
        work=router_work,
        metadata={
            "type": "router",
        },
    )

    tasks.append(router)

    expert_ids = []

    for expert_id in range(num_experts):

        token_count = (
            tokens_per_expert[
                expert_id
            ]
        )

        if token_count <= 0:
            continue

        if len(expert_ids) >= active_experts:
            break

        expert_task_id = (
            f"expert_{expert_id}"
        )

        projections = (
            3 if gated else 2
        )

        work = (
            token_count
            * projections
            * hidden_dim
            * intermediate_dim
        )

        task = Task(
            task_id=expert_task_id,
            name=f"Expert {expert_id}",
            resource_type=ResourceType.COMPUTE,
            work=work,
            dependencies=[
                router_id
            ],
            units=expert_units,
            metadata={
                "type": "expert",
                "expert_id": expert_id,
                "tokens": token_count,
            },
        )

        tasks.append(task)
        expert_ids.append(
            expert_task_id
        )

    combine_id = "moe_combine"

    combine = Task(
        task_id=combine_id,
        name="MoE Combine",
        resource_type=ResourceType.COMPUTE,
        work=(
            sum(tokens_per_expert)
            * hidden_dim
            * max(1, active_experts)
        ),
        dependencies=expert_ids,
        metadata={
            "type": "combine",
        },
    )

    tasks.append(combine)

    return tasks


# ---------------------------------------------------------------------------
# Convenience builders
# ---------------------------------------------------------------------------

def make_basic_scheduler(
    num_pes: int = 4096,
    frequency_hz: float = 1e9,
    macs_per_pe_per_cycle: int = 1,
    memory_bytes_per_cycle: int = 256,
) -> Scheduler:
    """
    Construct a basic VSE scheduler.

    Useful for experiments and tests.
    """

    scheduler = Scheduler(
        frequency_hz=frequency_hz
    )

    scheduler.add_resource(
        Resource(
            name="compute",
            resource_type=ResourceType.COMPUTE,
            capacity=num_pes,
            throughput=(
                macs_per_pe_per_cycle
            ),
        )
    )

    scheduler.add_resource(
        Resource(
            name="memory_read",
            resource_type=ResourceType.MEMORY_READ,
            capacity=1,
            throughput=memory_bytes_per_cycle,
        )
    )

    scheduler.add_resource(
        Resource(
            name="router",
            resource_type=ResourceType.ROUTER,
            capacity=1,
            throughput=memory_bytes_per_cycle,
        )
    )

    return scheduler


def schedule_transformer(
    layers: int,
    hidden_dim: int,
    intermediate_dim: int,
    sequence_length: int,
    num_pes: int = 4096,
    frequency_hz: float = 1e9,
) -> ScheduleResult:
    """
    Convenience function for scheduling a Transformer.
    """

    scheduler = make_basic_scheduler(
        num_pes=num_pes,
        frequency_hz=frequency_hz,
    )

    tasks = transformer_tasks(
        layers=layers,
        hidden_dim=hidden_dim,
        intermediate_dim=intermediate_dim,
        sequence_length=sequence_length,
    )

    scheduler.add_tasks(tasks)

    return scheduler.schedule()


def schedule_moe(
    num_experts: int,
    active_experts: int,
    tokens_per_expert: list[int],
    hidden_dim: int,
    intermediate_dim: int,
    num_pes: int = 4096,
    frequency_hz: float = 1e9,
) -> ScheduleResult:
    """
    Convenience function for scheduling an MoE layer.
    """

    scheduler = make_basic_scheduler(
        num_pes=num_pes,
        frequency_hz=frequency_hz,
    )

    tasks = moe_tasks(
        num_experts=num_experts,
        active_experts=active_experts,
        tokens_per_expert=tokens_per_expert,
        hidden_dim=hidden_dim,
        intermediate_dim=intermediate_dim,
        num_pes=num_pes,
    )

    scheduler.add_tasks(tasks)

    return scheduler.schedule()


# ---------------------------------------------------------------------------
# Timeline formatter
# ---------------------------------------------------------------------------

def format_schedule(
    result: ScheduleResult,
) -> str:
    """
    Produce a compact textual timeline.
    """

    lines = [
        "VSE SCHEDULE",
        "=" * 60,
        f"Total cycles : {result.total_cycles:,}",
        f"Latency      : {result.latency_us:.6f} us",
        "",
        "EVENTS",
        "-" * 60,
    ]

    for event in result.events:

        lines.append(
            f"{event.start_cycle:>10,}"
            f" -> "
            f"{event.end_cycle:<10,}"
            f" | "
            f"{event.resource_name:<15}"
            f" | "
            f"{event.task_name}"
        )

    lines.extend(
        [
            "",
            "UTILIZATION",
            "-" * 60,
        ]
    )

    for name, utilization in (
        result.all_utilization().items()
    ):
        lines.append(
            f"{name:<20}"
            f"{utilization * 100:>8.2f}%"
        )

    return "\n".join(lines)
