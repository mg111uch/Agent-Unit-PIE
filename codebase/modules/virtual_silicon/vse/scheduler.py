"""
VSE - Virtual Silicon Engine
vse/scheduler.py

Public scheduling API.

Phase 2: this module is now a thin facade over the parallel cycle
engine in vse/engine.py and the workload builders in vse/builders.py.
All types are re-exported so existing imports keep working:

    from vse.scheduler import (
        Scheduler,
        Resource,
        ResourceType,
        Task,
        ScheduleResult,
        schedule_moe,
    )

The engine performs cycle-level scheduling with true parallel
execution across capacity units.
"""

from __future__ import annotations

from vse.core.builders import (
    Scheduler,
    format_schedule,
    make_basic_scheduler,
    moe_tasks,
    schedule_moe,
    schedule_transformer,
    transformer_tasks,
)
from vse.core.types import (
    CycleTraceEntry,
    Resource,
    ResourceType,
    ScheduleEvent,
    ScheduleResult,
    Task,
)

__all__ = [
    "CycleTraceEntry",
    "Resource",
    "ResourceType",
    "ScheduleEvent",
    "ScheduleResult",
    "Scheduler",
    "Task",
    "format_schedule",
    "make_basic_scheduler",
    "moe_tasks",
    "schedule_moe",
    "schedule_transformer",
    "transformer_tasks",
]
