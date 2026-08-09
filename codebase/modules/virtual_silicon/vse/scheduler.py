"""
VSE - Virtual Silicon Engine
vse/scheduler.py

Cycle-level MVP scheduler.

Purpose:
    Convert VSE operations into a virtual hardware execution schedule.

MVP model:
    - Compute resource
    - Memory resource
    - Sequential task scheduling
    - Optional task dependencies
    - Resource contention
    - Start/end cycles
    - Critical-path latency
    - Resource utilization

This is intentionally NOT a full RTL simulator.

Later versions can add:
    - Multiple compute clusters
    - SRAM banks
    - NoC routing
    - DMA engines
    - Expert-specific accelerators
    - Double buffering
    - Pipeline overlap
    - Out-of-order execution
    - Cycle-accurate arbitration
"""

from __future__ import annotations

from dataclasses import dataclass, field
from enum import Enum
from typing import Dict, Iterable, List, Optional


# ---------------------------------------------------------------------------
# Resource types
# ---------------------------------------------------------------------------

class ResourceType(str, Enum):
    COMPUTE = "compute"
    MEMORY_READ = "memory_read"
    MEMORY_WRITE = "memory_write"
    ROUTER = "router"
    DMA = "dma"
    CUSTOM = "custom"


# ---------------------------------------------------------------------------
# Resource
# ---------------------------------------------------------------------------

@dataclass
class Resource:
    """
    A virtual hardware resource.

    capacity:
        Number of identical units available.

    throughput:
        Work units processed per cycle.

    Examples:

        4096 PEs:
            capacity = 4096

        HBM:
            throughput = bytes/cycle
    """

    name: str
    resource_type: ResourceType

    capacity: int = 1
    throughput: float = 1.0

    available_cycle: int = 0

    busy_cycles: int = 0
    total_work: float = 0.0

    def __post_init__(self) -> None:
        if self.capacity <= 0:
            raise ValueError(
                "resource capacity must be > 0"
            )

        if self.throughput <= 0:
            raise ValueError(
                "resource throughput must be > 0"
            )

    def cycles_for_work(
        self,
        work: float,
    ) -> int:
        if work <= 0:
            return 0

        effective_rate = (
            self.throughput
            * self.capacity
        )

        cycles = (
            work / effective_rate
        )

        return max(
            1,
            int(cycles + 0.999999),
        )

    def reserve(
        self,
        start_cycle: int,
        work: float,
    ) -> tuple[int, int]:
        """
        Reserve this resource for a unit of work.

        Returns:
            (start_cycle, end_cycle)
        """

        start = max(
            start_cycle,
            self.available_cycle,
        )

        duration = self.cycles_for_work(
            work
        )

        end = start + duration

        self.available_cycle = end
        self.busy_cycles += duration
        self.total_work += work

        return start, end

    def reset(self) -> None:
        self.available_cycle = 0
        self.busy_cycles = 0
        self.total_work = 0.0


# ---------------------------------------------------------------------------
# Task
# ---------------------------------------------------------------------------

@dataclass
class Task:
    """
    One executable unit in the virtual silicon graph.
    """

    task_id: str
    name: str

    resource_type: ResourceType

    work: float = 0.0

    dependencies: List[str] = field(
        default_factory=list
    )

    metadata: Dict[str, object] = field(
        default_factory=dict
    )

    start_cycle: Optional[int] = None
    end_cycle: Optional[int] = None

    resource_name: Optional[str] = None

    @property
    def duration(self) -> int:
        if (
            self.start_cycle is None
            or self.end_cycle is None
        ):
            return 0

        return (
            self.end_cycle
            - self.start_cycle
        )

    @property
    def scheduled(self) -> bool:
        return (
            self.start_cycle is not None
            and self.end_cycle is not None
        )


# ---------------------------------------------------------------------------
# Schedule event
# ---------------------------------------------------------------------------

@dataclass
class ScheduleEvent:
    task_id: str
    task_name: str

    resource_name: str

    start_cycle: int
    end_cycle: int

    work: float

    @property
    def duration(self) -> int:
        return (
            self.end_cycle
            - self.start_cycle
        )


# ---------------------------------------------------------------------------
# Schedule result
# ---------------------------------------------------------------------------

@dataclass
class ScheduleResult:
    """
    Complete execution schedule.
    """

    events: List[ScheduleEvent]

    total_cycles: int

    resources: Dict[str, Resource]

    tasks: Dict[str, Task]

    frequency_hz: float = 1.0

    @property
    def latency_seconds(self) -> float:
        if self.frequency_hz <= 0:
            return 0.0

        return (
            self.total_cycles
            / self.frequency_hz
        )

    @property
    def latency_us(self) -> float:
        return (
            self.latency_seconds
            * 1e6
        )

    def resource_utilization(
        self,
        resource_name: str,
    ) -> float:
        resource = self.resources[
            resource_name
        ]

        if self.total_cycles <= 0:
            return 0.0

        return (
            resource.busy_cycles
            / (
                self.total_cycles
                * resource.capacity
            )
        )

    def all_utilization(self) -> dict[str, float]:
        return {
            name: self.resource_utilization(name)
            for name in self.resources
        }

    def report(self) -> dict:
        return {
            "total_cycles": self.total_cycles,
            "latency_us": self.latency_us,
            "latency_seconds": (
                self.latency_seconds
            ),
            "frequency_hz": self.frequency_hz,
            "events": len(self.events),
            "resource_utilization": (
                self.all_utilization()
            ),
        }


# ---------------------------------------------------------------------------
# Scheduler
# ---------------------------------------------------------------------------

class Scheduler:
    """
    Deterministic dependency-aware scheduler.

    The MVP uses a list scheduler:

        1. Find tasks whose dependencies are complete.
        2. Select the next task.
        3. Find its resource.
        4. Reserve the resource.
        5. Repeat.

    It does not yet model multiple tasks executing on different
    resource units at the same exact cycle with detailed arbitration.

    That comes in the next scheduler iteration.
    """

    def __init__(
        self,
        frequency_hz: float = 1e9,
    ):
        if frequency_hz <= 0:
            raise ValueError(
                "frequency_hz must be > 0"
            )

        self.frequency_hz = frequency_hz

        self.resources: Dict[
            str,
            Resource,
        ] = {}

        self.tasks: Dict[
            str,
            Task,
        ] = {}

    # ------------------------------------------------------------------
    # Resources
    # ------------------------------------------------------------------

    def add_resource(
        self,
        resource: Resource,
    ) -> None:
        if resource.name in self.resources:
            raise ValueError(
                f"resource already exists: "
                f"{resource.name}"
            )

        self.resources[
            resource.name
        ] = resource

    def get_resource(
        self,
        resource_type: ResourceType,
    ) -> Resource:
        """
        Return the first resource matching the type.

        MVP behavior.

        Later:
            select least-loaded resource,
            nearest resource,
            expert-local resource, etc.
        """

        for resource in self.resources.values():
            if resource.resource_type == resource_type:
                return resource

        raise KeyError(
            f"no resource for type "
            f"{resource_type}"
        )

    # ------------------------------------------------------------------
    # Tasks
    # ------------------------------------------------------------------

    def add_task(
        self,
        task: Task,
    ) -> None:
        if task.task_id in self.tasks:
            raise ValueError(
                f"task already exists: "
                f"{task.task_id}"
            )

        self.tasks[
            task.task_id
        ] = task

    def add_tasks(
        self,
        tasks: Iterable[Task],
    ) -> None:
        for task in tasks:
            self.add_task(task)

    # ------------------------------------------------------------------
    # Dependency handling
    # ------------------------------------------------------------------

    def _dependency_end(
        self,
        task: Task,
    ) -> int:
        """
        Return the latest completion cycle among
        all dependencies.
        """

        if not task.dependencies:
            return 0

        latest = 0

        for dependency_id in task.dependencies:

            if dependency_id not in self.tasks:
                raise KeyError(
                    f"unknown dependency: "
                    f"{dependency_id}"
                )

            dependency = self.tasks[
                dependency_id
            ]

            if not dependency.scheduled:
                raise RuntimeError(
                    f"dependency not scheduled: "
                    f"{dependency_id}"
                )

            assert (
                dependency.end_cycle
                is not None
            )

            latest = max(
                latest,
                dependency.end_cycle,
            )

        return latest

    def _ready_tasks(
        self,
    ) -> list[Task]:
        ready = []

        for task in self.tasks.values():

            if task.scheduled:
                continue

            dependencies_ready = True

            for dependency_id in (
                task.dependencies
            ):
                dependency = self.tasks[
                    dependency_id
                ]

                if not dependency.scheduled:
                    dependencies_ready = False
                    break

            if dependencies_ready:
                ready.append(task)

        return ready

    # ------------------------------------------------------------------
    # Scheduling
    # ------------------------------------------------------------------

    def schedule(
        self,
    ) -> ScheduleResult:
        """
        Schedule all tasks.

        Raises RuntimeError if a dependency cycle exists.
        """

        # Reset resources so a Scheduler instance can be reused.
        for resource in self.resources.values():
            resource.reset()

        # Reset tasks.
        for task in self.tasks.values():
            task.start_cycle = None
            task.end_cycle = None
            task.resource_name = None

        events: list[ScheduleEvent] = []

        scheduled_count = 0

        while scheduled_count < len(
            self.tasks
        ):

            ready = self._ready_tasks()

            if not ready:
                raise RuntimeError(
                    "unable to schedule tasks; "
                    "dependency cycle or missing "
                    "dependency detected"
                )

            # Deterministic ordering.
            ready.sort(
                key=lambda task: task.task_id
            )

            task = ready[0]

            resource = self.get_resource(
                task.resource_type
            )

            dependency_end = (
                self._dependency_end(task)
            )

            start, end = resource.reserve(
                dependency_end,
                task.work,
            )

            task.start_cycle = start
            task.end_cycle = end
            task.resource_name = (
                resource.name
            )

            events.append(
                ScheduleEvent(
                    task_id=task.task_id,
                    task_name=task.name,
                    resource_name=resource.name,
                    start_cycle=start,
                    end_cycle=end,
                    work=task.work,
                )
            )

            scheduled_count += 1

        total_cycles = 0

        for task in self.tasks.values():

            if task.end_cycle is not None:
                total_cycles = max(
                    total_cycles,
                    task.end_cycle,
                )

        return ScheduleResult(
            events=events,
            total_cycles=total_cycles,
            resources=self.resources.copy(),
            tasks=self.tasks.copy(),
            frequency_hz=self.frequency_hz,
        )

    # ------------------------------------------------------------------
    # Reset
    # ------------------------------------------------------------------

    def clear(self) -> None:
        self.resources.clear()
        self.tasks.clear()


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

    This is the first step toward modeling actual MoE hardware.
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
