"""
VSE - Virtual Silicon Engine
vse/engine.py

Parallel cycle-level scheduling engine (Phase 2).

This replaces the Phase-1 list scheduler with an actual cycle engine:

    - Multiple tasks can run concurrently on different units of the
      same resource (true parallel execution).
    - Tasks occupy `units` of a resource's capacity and release them
      when their compute completes.
    - Dependencies gate on result-ready cycles.
    - Optional per-resource pipeline latency.
    - Deterministic dispatch (task_id ordering).
    - Per-cycle activity trace and peak concurrency.

The engine is event-driven (heap-based) so long simulations skip idle
cycles instead of stepping through every cycle.

Example:
    engine = CycleEngine(frequency_hz=1e9)

    engine.add_resource(
        Resource(
            name="compute",
            resource_type=ResourceType.COMPUTE,
            capacity=1024,
            throughput=1,
        )
    )

    engine.add_task(
        Task(
            task_id="a",
            name="A",
            resource_type=ResourceType.COMPUTE,
            work=512,
            units=512,
        )
    )

    result = engine.schedule()
"""

from __future__ import annotations

from typing import Dict, Iterable, Optional
import heapq

from vse.core.types import (
    CycleTraceEntry,
    Resource,
    ResourceType,
    ScheduleEvent,
    ScheduleResult,
    Task,
)


class CycleEngine:
    """
    Deterministic parallel cycle engine.

    Scheduling:

        1. At each cycle, dispatch every ready task that fits into the
           free units of its resource (greedy, task_id ordered).
        2. A task holds `units` until its compute duration elapses.
        3. Releasing units triggers another dispatch attempt.
        4. Dependencies become ready when the dependency's result cycle
           has passed.

    Raises RuntimeError if not every task can be scheduled (dependency
    cycle or a resource that can never admit a task).
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
        mem_level: Optional[str] = None,
    ) -> Resource:
        """
        Return the resource for a type, preferring the matching memory
        level when one is requested.
        """

        if mem_level:
            for name, resource in self.resources.items():
                if (
                    resource.resource_type == resource_type
                    and name
                    in (
                        f"{mem_level}_read",
                        f"{mem_level}_write",
                    )
                ):
                    return resource

        # Default: the primary resource of this type, then the first.
        for resource in self.resources.values():
            if (
                resource.resource_type == resource_type
                and resource.primary
            ):
                return resource

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
    # Dependencies
    # ------------------------------------------------------------------

    def _dependencies_ready(
        self,
        task: Task,
        cycle: int,
    ) -> bool:
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
                return False

            assert dependency.end_cycle is not None

            if dependency.end_cycle > cycle:
                return False

        return True

    # ------------------------------------------------------------------
    # Scheduling
    # ------------------------------------------------------------------

    def schedule(
        self,
    ) -> ScheduleResult:
        # Reset resources so the engine can be reused.
        for resource in self.resources.values():
            resource.reset()

        # Reset tasks.
        for task in self.tasks.values():
            task.start_cycle = None
            task.end_cycle = None
            task.resource_name = None

        for task in self.tasks.values():
            resource = self.get_resource(
                task.resource_type,
                task.mem_level,
            )

            if (
                task.units > 0
                and task.units > resource.capacity
            ):
                raise ValueError(
                    f"task '{task.task_id}' requests "
                    f"{task.units} units but resource "
                    f"'{resource.name}' has capacity "
                    f"{resource.capacity}"
                )

            if (
                task.banks > 0
                and task.banks > resource.banks
            ):
                raise ValueError(
                    f"task '{task.task_id}' requests "
                    f"{task.banks} banks but resource "
                    f"'{resource.name}' has {resource.banks}"
                )

        in_use: Dict[str, int] = {
            name: 0
            for name in self.resources
        }

        banks_in_use: Dict[str, int] = {
            name: 0
            for name in self.resources
        }

        active_tasks: Dict[str, int] = {
            name: 0
            for name in self.resources
        }

        peak: Dict[str, int] = {
            name: 0
            for name in self.resources
        }

        peak_banks: Dict[str, int] = {
            name: 0
            for name in self.resources
        }

        events: list[ScheduleEvent] = []
        trace: list[CycleTraceEntry] = []

        # Event heap: (cycle, sequence, kind, resource_name, units).
        queue: list[tuple] = []
        sequence = 0

        def record(
            cycle: int,
            resource_name: str,
        ) -> None:
            resource = self.resources[
                resource_name
            ]

            peak[resource_name] = max(
                peak[resource_name],
                in_use[resource_name],
            )

            trace.append(
                CycleTraceEntry(
                    cycle=cycle,
                    resource=resource_name,
                    busy_units=in_use[resource_name],
                    capacity=resource.capacity,
                    active_tasks=active_tasks[
                        resource_name
                    ],
                )
            )

        def dispatch(
            cycle: int,
        ) -> None:
            """
            Greedily dispatch ready tasks that fit in free units.
            """

            nonlocal sequence

            changed = True

            while changed:
                changed = False

                ready = sorted(
                    (
                        task
                        for task in self.tasks.values()
                        if task.start_cycle is None
                        and self._dependencies_ready(
                            task,
                            cycle,
                        )
                    ),
                    key=lambda task: task.task_id,
                )

                for task in ready:
                    resource = self.get_resource(
                        task.resource_type,
                        task.mem_level,
                    )

                    units = (
                        task.units
                        if task.units > 0
                        else resource.capacity
                    )

                    if (
                        in_use[resource.name] + units
                        > resource.capacity
                    ):
                        continue

                    banks = task.banks

                    if (
                        banks > 0
                        and banks_in_use[resource.name] + banks
                        > resource.banks
                    ):
                        continue

                    task.start_cycle = cycle
                    task.resource_name = resource.name

                    duration = (
                        resource.cycles_for_units(
                            task.work,
                            units,
                        )
                    )

                    occupancy_end = (
                        cycle + duration
                    )

                    latency = (
                        task.pipeline_latency
                        if task.pipeline_latency is not None
                        else resource.pipeline_latency
                    )

                    task.end_cycle = (
                        occupancy_end
                        + latency
                    )

                    resource.busy_cycles += duration
                    resource.total_work += task.work

                    resource.available_cycle = max(
                        resource.available_cycle,
                        occupancy_end,
                    )

                    in_use[resource.name] += units
                    active_tasks[resource.name] += 1

                    if banks > 0:
                        banks_in_use[resource.name] += banks
                        peak_banks[resource.name] = max(
                            peak_banks[resource.name],
                            banks_in_use[resource.name],
                        )

                    heapq.heappush(
                        queue,
                        (
                            occupancy_end,
                            sequence,
                            "release",
                            resource.name,
                            units,
                            banks,
                        ),
                    )

                    sequence += 1

                    if task.end_cycle > occupancy_end:
                        # Pipeline latency: the result becomes ready
                        # later, which may unlock dependent tasks.
                        heapq.heappush(
                            queue,
                            (
                                task.end_cycle,
                                sequence,
                                "result",
                                resource.name,
                                0,
                                0,
                            ),
                        )

                        sequence += 1

                    events.append(
                        ScheduleEvent(
                            task_id=task.task_id,
                            task_name=task.name,
                            resource_name=resource.name,
                            start_cycle=cycle,
                            end_cycle=task.end_cycle,
                            work=task.work,
                            units=units,
                        )
                    )

                    record(cycle, resource.name)

                    changed = True

        dispatch(0)

        while queue:
            event_cycle, _, kind, name, units, banks = (
                heapq.heappop(queue)
            )

            if kind == "release":
                in_use[name] -= units
                active_tasks[name] -= 1

                if banks > 0:
                    banks_in_use[name] -= banks

                record(event_cycle, name)

            dispatch(event_cycle)

        total_cycles = 0

        for task in self.tasks.values():
            if task.start_cycle is None:
                raise RuntimeError(
                    "unable to schedule all tasks; "
                    "dependency cycle or resource "
                    "deadlock detected"
                )

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
            trace=trace,
            peak_concurrency=peak,
            peak_banks=peak_banks,
        )

    # ------------------------------------------------------------------
    # Reset
    # ------------------------------------------------------------------

    def clear(self) -> None:
        self.resources.clear()
        self.tasks.clear()
