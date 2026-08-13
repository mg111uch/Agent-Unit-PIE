"""
VSE - Virtual Silicon Engine
vse/graph_moe.py

MoE task-graph construction. `build_moe_tasks` converts routing and
expert costs into an executable scheduler graph with weight streaming,
double buffering, NoC placement, and expert replication. Kept separate
from graph.py to stay under the file line budget.
"""

from __future__ import annotations

from typing import Optional

from vse.core.noc import NoC
from vse.models.ops import OpCost
from vse.scheduler import ResourceType, Task


def build_moe_tasks(
    routing_cost: OpCost,
    expert_costs: list[OpCost],
    expert_units: Optional[int] = None,
    weight_bytes_per_expert: int = 0,
    resident: bool = False,
    chunks: int = 1,
    noc: Optional[NoC] = None,
    replicas: int = 1,
    placement: str = "round_robin",
) -> list[Task]:
    """
    Build the execution graph for one MoE layer.

    Graph:
        router → expert 0 ─┐
                  expert 1 │
                  ...      └ (experts run in parallel)

    expert_units:
        PEs assigned per expert so experts execute concurrently.

    weight_bytes_per_expert:
        If > 0, weight-load tasks are added per active expert.
        Non-resident weights stream from HBM; resident weights are read
        from SRAM (concurrent, banked) after an HBM cold load via DMA.

    chunks:
        > 1 enables double buffering: weight streaming and expert
        compute are split so compute of chunk c overlaps the stream of
        chunk c+1.

    noc:
        If given and enabled, tokens move router → expert node and
        expert results move expert node → combine over the NoC. Experts
        are placed across nodes; with `broadcast` the router sends the
        full token tensor to every node in one task.

    replicas:
        > 1 replicates each expert across `replicas` copies. Every
        replica handles tokens/replicas and holds weights/replicas, so
        the weight stream is parallelized (the dominant MoE cost) while
        total weight traffic and total MACs stay unchanged. Needs
        noc_nodes >= active × replicas to give each copy its own node.

    placement:
        "round_robin" interleaves replicas across nodes
        (expert i replica r → node (i + r × active) % nodes);
        "contiguous" packs one expert's replicas together
        (expert i replica r → node (i × replicas + r) % nodes).
    """

    if chunks <= 0:
        raise ValueError("chunks must be > 0")

    if replicas < 1:
        raise ValueError("replicas must be >= 1")

    if placement not in ("round_robin", "contiguous"):
        raise ValueError(
            "placement must be 'round_robin' or 'contiguous'"
        )

    active = len(expert_costs)

    tasks: list[Task] = []
    router_ids: list[str] = []

    if routing_cost is not None:
        router = Task(
            task_id="moe_router",
            name="MoE Router",
            resource_type=ResourceType.ROUTER,
            work=routing_cost.macs,
        )

        tasks.append(router)
        router_ids.append(router.task_id)

    noc_active = noc is not None and noc.config.enabled

    if noc_active:
        combine_inputs: list[str] = []

    broadcast_id: Optional[str] = None

    if noc_active and noc.config.broadcast:
        total_tokens_bytes = sum(
            e.input_bytes for e in expert_costs
        )

        broadcast = noc.broadcast_task(
            task_id="moe_tokens_broadcast",
            name="Router broadcast tokens",
            data_bytes=total_tokens_bytes,
            src=0,
            dependencies=list(router_ids),
            metadata={"phase": "broadcast"},
        )

        tasks.append(broadcast)
        broadcast_id = broadcast.task_id

    weight_chunk_ids: list[list[list[str]]] = []

    if weight_bytes_per_expert > 0:
        total_weight = (
            weight_bytes_per_expert
            * active
        )

        if resident:
            tasks.append(
                Task(
                    task_id="moe_weights_fetch",
                    name="Weight HBM fetch",
                    resource_type=ResourceType.MEMORY_READ,
                    work=total_weight,
                    mem_level="hbm",
                    metadata={
                        "kind": "weight_load",
                    },
                )
            )

            tasks.append(
                Task(
                    task_id="moe_weights_dma",
                    name="Weight DMA transfer",
                    resource_type=ResourceType.DMA,
                    work=total_weight,
                    metadata={"kind": "dma"},
                )
            )

        level = "sram" if resident else "hbm"

        weight_per_replica = (
            weight_bytes_per_expert // replicas
        )
        replica_remainder = (
            weight_bytes_per_expert % replicas
        )

        per_chunk = weight_per_replica // chunks
        remainder = weight_per_replica % chunks

        for index in range(active):
            expert_chunks: list[list[str]] = []

            for replica in range(replicas):
                chunk_ids: list[str] = []

                for chunk in range(chunks):
                    chunk_id = (
                        f"expert_{index}_r{replica}"
                        f"_wchunk_{chunk}"
                    )

                    tasks.append(
                        Task(
                            task_id=chunk_id,
                            name=(
                                f"Expert {index} "
                                f"replica {replica} "
                                f"weights {chunk}"
                            ),
                            resource_type=ResourceType.MEMORY_READ,
                            work=(
                                per_chunk
                                + (
                                    remainder
                                    if chunk
                                    == chunks - 1
                                    else 0
                                )
                                + (
                                    1
                                    if replica
                                    < replica_remainder
                                    and chunk == 0
                                    else 0
                                )
                            ),
                            mem_level=level,
                            units=1 if resident else 0,
                            banks=1 if resident else 0,
                            metadata={
                                "kind": "weight",
                                "expert": index,
                                "replica": replica,
                                "chunk": chunk,
                            },
                        )
                    )

                    chunk_ids.append(chunk_id)

                expert_chunks.append(chunk_ids)

            weight_chunk_ids.append(expert_chunks)

    for index, expert_cost in enumerate(expert_costs):
        in_base = expert_cost.input_bytes // replicas
        in_remainder = expert_cost.input_bytes % replicas
        macs_base = expert_cost.macs // replicas
        macs_remainder = expert_cost.macs % replicas
        out_base = expert_cost.output_bytes // replicas
        out_remainder = expert_cost.output_bytes % replicas

        for replica in range(replicas):
            in_bytes = (
                in_base
                + (1 if replica < in_remainder else 0)
            )
            macs_r = (
                macs_base
                + (1 if replica < macs_remainder else 0)
            )
            out_bytes = (
                out_base
                + (1 if replica < out_remainder else 0)
            )

            if noc_active:
                node = _moe_node(
                    index,
                    replica,
                    replicas,
                    active,
                    noc.config.nodes,
                    placement,
                )

            activation_deps: list[str] = list(router_ids)

            if broadcast_id is not None:
                activation_deps = [broadcast_id]
            elif noc_active:
                noc_send = noc.transfer_task(
                    task_id=(
                        f"expert_{index}_r{replica}_noc_send"
                    ),
                    name=(
                        f"Expert {index} r{replica} "
                        f"tokens to node {node}"
                    ),
                    data_bytes=in_bytes,
                    src=0,
                    dst=node,
                    dependencies=list(router_ids),
                    metadata={
                        "expert": index,
                        "replica": replica,
                        "phase": "send",
                    },
                )

                tasks.append(noc_send)
                activation_deps = [noc_send.task_id]

            activation_read = Task(
                task_id=(
                    f"expert_{index}_r{replica}_act_read"
                ),
                name=(
                    f"Expert {index} r{replica} "
                    f"activations in"
                ),
                resource_type=ResourceType.MEMORY_READ,
                work=in_bytes,
                mem_level="sram",
                units=1,
                banks=1,
                dependencies=activation_deps,
                metadata={
                    "kind": "activation",
                    "expert": index,
                    "replica": replica,
                },
            )

            tasks.append(activation_read)

            per_chunk_macs = macs_r // chunks
            remainder_macs = macs_r % chunks

            previous_compute: Optional[str] = None

            for chunk in range(chunks):
                dependencies = (
                    list(router_ids)
                    + [activation_read.task_id]
                )

                if weight_chunk_ids:
                    dependencies.append(
                        weight_chunk_ids[index][replica][chunk]
                    )

                if previous_compute is not None:
                    dependencies.append(
                        previous_compute
                    )

                compute_id = (
                    f"expert_{index}_r{replica}_compute_{chunk}"
                )

                tasks.append(
                    Task(
                        task_id=compute_id,
                        name=(
                            f"Expert {index} r{replica} "
                            f"compute {chunk}"
                        ),
                        resource_type=ResourceType.COMPUTE,
                        work=(
                            per_chunk_macs
                            + (
                                remainder_macs
                                if chunk == chunks - 1
                                else 0
                            )
                        ),
                        dependencies=dependencies,
                        units=expert_units or 0,
                    )
                )

                previous_compute = compute_id

            tasks.append(
                Task(
                    task_id=(
                        f"expert_{index}_r{replica}_act_write"
                    ),
                    name=(
                        f"Expert {index} r{replica} "
                        f"activations out"
                    ),
                    resource_type=ResourceType.MEMORY_WRITE,
                    work=out_bytes,
                    mem_level="sram",
                    units=1,
                    banks=1,
                    dependencies=[
                        previous_compute
                    ],
                    metadata={
                        "kind": "activation",
                        "expert": index,
                        "replica": replica,
                    },
                )
            )

            if noc_active:
                noc_return = noc.transfer_task(
                    task_id=(
                        f"expert_{index}_r{replica}_noc_return"
                    ),
                    name=(
                        f"Expert {index} r{replica} "
                        f"results from node {node}"
                    ),
                    data_bytes=out_bytes,
                    src=node,
                    dst=0,
                    dependencies=[
                        f"expert_{index}_r{replica}_act_write"
                    ],
                    metadata={
                        "expert": index,
                        "replica": replica,
                        "phase": "return",
                    },
                )

                tasks.append(noc_return)
                combine_inputs.append(noc_return.task_id)

    if noc_active and combine_inputs:
        tasks.append(
            Task(
                task_id="moe_combine",
                name="MoE Combine",
                resource_type=ResourceType.ROUTER,
                work=sum(
                    e.output_bytes for e in expert_costs
                ),
                dependencies=combine_inputs,
                metadata={
                    "kind": "combine",
                },
            )
        )

    return tasks


def _moe_node(
    index: int,
    replica: int,
    replicas: int,
    active: int,
    nodes: int,
    placement: str,
) -> int:
    """
    Map (expert, replica) → NoC node.
    """

    if placement == "contiguous":
        return (index * replicas + replica) % nodes

    return (index + replica * active) % nodes
