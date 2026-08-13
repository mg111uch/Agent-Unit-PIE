"""
VSE - Virtual Silicon Engine
vse/graph.py

Task-graph construction from workload costs for Transformer and MoE
models. The graph builders convert operation costs into executable
scheduler task graphs for the cycle engine.
"""

from __future__ import annotations

from typing import Optional

from vse.models.ops import OpCost
from vse.scheduler import ResourceType, Task
from vse.models.transformer import TransformerLayerCost
from vse.core.noc import NoC


def op_stage(
    op: OpCost,
    prefix: str,
) -> list[Task]:
    """
    Build compute/read/write tasks for one OpCost.

    Compute, read, and write run in parallel within a stage.
    """

    stage: list[Task] = []

    if op.macs > 0:
        stage.append(
            Task(
                task_id=f"{prefix}_compute",
                name=op.name,
                resource_type=ResourceType.COMPUTE,
                work=op.macs,
                metadata={"kind": "compute"},
            )
        )

    if op.input_bytes > 0:
        stage.append(
            Task(
                task_id=f"{prefix}_read",
                name=f"{op.name} read",
                resource_type=ResourceType.MEMORY_READ,
                work=op.input_bytes,
                metadata={"kind": "read"},
            )
        )

    if op.output_bytes > 0:
        stage.append(
            Task(
                task_id=f"{prefix}_write",
                name=f"{op.name} write",
                resource_type=ResourceType.MEMORY_WRITE,
                work=op.output_bytes,
                metadata={"kind": "write"},
            )
        )

    return stage


def _chain_stages(
    stages: list[list[Task]],
) -> list[Task]:
    """
    Chain stages serially: each stage's tasks depend on every task of
    the previous stage.
    """

    previous_ids: list[str] = []
    all_tasks: list[Task] = []

    for stage in stages:
        for task in stage:
            task.dependencies = list(previous_ids)
            all_tasks.append(task)

        previous_ids = [
            task.task_id
            for task in stage
        ]

    return all_tasks


def build_transformer_tasks(
    layer_cost: TransformerLayerCost,
    layers: int,
    kv_level: str = "sram",
    fusion: bool = False,
) -> list[Task]:
    """
    Build the execution graph for a complete Transformer model.

    Layers are replicated; each layer is attention → MLP → KV update.
    kv_level routes KV reads/writes to a memory level. With `fusion`,
    only the model input is read and the model output is written;
    intermediate activations never touch memory (KV traffic unchanged).
    """

    stages: list[list[Task]] = []

    for layer in range(layers):
        prefix = f"layer_{layer}"

        stages.append(
            op_stage(
                layer_cost.attention,
                f"{prefix}_attention",
            )
        )

        stages.append(
            op_stage(
                layer_cost.mlp,
                f"{prefix}_mlp",
            )
        )

        if layer_cost.kv_read_bytes > 0:
            stages.append(
                [
                    Task(
                        task_id=f"{prefix}_kv_read",
                        name="KV read",
                        resource_type=ResourceType.MEMORY_READ,
                        work=layer_cost.kv_read_bytes,
                        mem_level=kv_level,
                        metadata={
                            "kind": "kv_cache",
                        },
                    )
                ]
            )

        if layer_cost.kv_write_bytes > 0:
            stages.append(
                [
                    Task(
                        task_id=f"{prefix}_kv_write",
                        name="KV write",
                        resource_type=ResourceType.MEMORY_WRITE,
                        work=layer_cost.kv_write_bytes,
                        mem_level=kv_level,
                        metadata={
                            "kind": "kv_cache",
                        },
                    )
                ]
            )

    if fusion:
        stages = _fuse_transformer_stages(stages)

    return _chain_stages(stages)


def _fuse_transformer_stages(
    stages: list[list[Task]],
) -> list[list[Task]]:
    """
    Drop intermediate activation read/write tasks, keeping only the
    first model input read and the final model output write.
    """

    first_read_kept = False
    last_write: Optional[Task] = None

    for stage in stages:
        kept: list[Task] = []

        for task in stage:
            kind = task.metadata.get("kind")

            if kind == "read":
                if first_read_kept:
                    continue
                first_read_kept = True
            elif kind == "write":
                last_write = task
                continue

            kept.append(task)

        stage[:] = kept

    if last_write is not None:
        stages[-1].append(last_write)

    return stages


# MoE graph construction lives in vse/graph_moe.py to stay under the
# file line budget; re-exported here so imports keep working.
from vse.graphs.graph_moe import _moe_node, build_moe_tasks  # noqa: E402,F401
