"""MoE task-graph with tile-aware placement (Phase C) + CIM support."""
from __future__ import annotations
from typing import List, Optional
from vse.core.noc import NoC
from vse.models.ops import OpCost
from vse.scheduler import ResourceType, Task


def _is_cim(cim: bool = False, arch_family: str = "scalar") -> bool:
    if cim:
        return True
    if arch_family is None:
        return False
    try:
        fam = str(arch_family).lower()
    except Exception:
        return False
    try:
        from vse.core.pe_families import ArchFamily  # noqa: WPS433

        if isinstance(arch_family, ArchFamily):
            return arch_family in (ArchFamily.cim, ArchFamily.near_memory)
    except Exception:
        pass
    return fam in ("cim", "near_memory", "near-memory")


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
    tile_hierarchy: Optional[object] = None,
    tile_ids: Optional[List[int]] = None,
    cim: bool = False,
    arch_family: str = "scalar",
) -> list[Task]:
    """Build MoE graph; tile_hierarchy/ tile_ids enable per-tile SRAM."""
    if chunks <= 0:
        raise ValueError("chunks must be > 0")
    if replicas < 1:
        raise ValueError("replicas must be >= 1")
    if placement not in ("round_robin", "contiguous"):
        raise ValueError("placement must be 'round_robin' or 'contiguous'")
    active = len(expert_costs)
    tasks: list[Task] = []
    router_ids: list[str] = []
    if routing_cost is not None:
        router = Task(task_id="moe_router", name="MoE Router", resource_type=ResourceType.ROUTER, work=routing_cost.macs)
        tasks.append(router)
        router_ids.append(router.task_id)
    noc_active = noc is not None and noc.config.enabled
    combine_inputs: list[str] = []
    broadcast_id: Optional[str] = None
    if noc_active and noc.config.broadcast:
        total_tokens_bytes = sum(e.input_bytes for e in expert_costs)
        broadcast = noc.broadcast_task(task_id="moe_tokens_broadcast", name="Router broadcast tokens", data_bytes=total_tokens_bytes, src=0, dependencies=list(router_ids), metadata={"phase": "broadcast"})
        tasks.append(broadcast)
        broadcast_id = broadcast.task_id
    weight_chunk_ids: list[list[list[str]]] = []
    tiled = tile_hierarchy is not None or tile_ids is not None

    def _resolve_tile(node: int) -> int:
        if tile_hierarchy is not None and getattr(tile_hierarchy, "tiles", None):
            tiles = tile_hierarchy.tiles  # type: ignore
            return tiles[node % len(tiles)].tile_id
        if tile_ids is not None and len(tile_ids) > 0:
            return tile_ids[node % len(tile_ids)]
        return node

    def _placement_nodes() -> int:
        if tile_hierarchy is not None and getattr(tile_hierarchy, "tiles", None):
            return len(tile_hierarchy.tiles)  # type: ignore
        if tile_ids is not None and len(tile_ids) > 0:
            return len(tile_ids)
        if noc_active:
            return noc.config.nodes
        return 1

    cim_mode = _is_cim(cim, arch_family)
    if weight_bytes_per_expert > 0 and not cim_mode:
        total_weight = weight_bytes_per_expert * active
        if resident:
            tasks.append(Task(task_id="moe_weights_fetch", name="Weight HBM fetch", resource_type=ResourceType.MEMORY_READ, work=total_weight, mem_level="hbm", metadata={"kind": "weight_load"}))
            tasks.append(Task(task_id="moe_weights_dma", name="Weight DMA transfer", resource_type=ResourceType.DMA, work=total_weight, metadata={"kind": "dma"}))
        level = "sram" if resident else "hbm"
        weight_per_replica = weight_bytes_per_expert // replicas
        replica_remainder = weight_bytes_per_expert % replicas
        per_chunk = weight_per_replica // chunks
        remainder = weight_per_replica % chunks
        for index in range(active):
            expert_chunks: list[list[str]] = []
            for replica in range(replicas):
                chunk_ids: list[str] = []
                if tiled:
                    nodes_for_place = _placement_nodes()
                    base_node = _moe_node(index, replica, replicas, active, nodes_for_place, placement)
                    tile_id = _resolve_tile(base_node)
                    w_level = f"tile{tile_id}_sram" if resident else level
                else:
                    w_level = level
                    tile_id = None
                for chunk in range(chunks):
                    chunk_id = f"expert_{index}_r{replica}_tile{tile_id}_wchunk_{chunk}" if tiled and tile_id is not None else f"expert_{index}_r{replica}_wchunk_{chunk}"
                    tasks.append(Task(task_id=chunk_id, name=f"Expert {index} replica {replica} weights {chunk}", resource_type=ResourceType.MEMORY_READ, work=per_chunk + (remainder if chunk == chunks - 1 else 0) + (1 if replica < replica_remainder and chunk == 0 else 0), mem_level=w_level, units=1 if resident else 0, banks=1 if resident else 0, metadata={"kind": "weight", "expert": index, "replica": replica, "chunk": chunk, **({"tile_id": tile_id} if tile_id is not None else {})}))
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
            in_bytes = in_base + (1 if replica < in_remainder else 0)
            macs_r = macs_base + (1 if replica < macs_remainder else 0)
            out_bytes = out_base + (1 if replica < out_remainder else 0)
            node: Optional[int] = None
            tile_id_act: Optional[int] = None
            if noc_active or tiled:
                nodes_for_place = _placement_nodes() if tiled else noc.config.nodes
                base = _moe_node(index, replica, replicas, active, nodes_for_place, placement)
                if tiled:
                    tile_id_act = _resolve_tile(base)
                    node = base if noc_active else tile_id_act
                    if noc_active and tile_hierarchy is not None:
                        node = base
                else:
                    node = base
            activation_deps: list[str] = list(router_ids)
            if broadcast_id is not None:
                activation_deps = [broadcast_id]
            elif noc_active and node is not None:
                noc_send = noc.transfer_task(task_id=f"expert_{index}_r{replica}_noc_send", name=f"Expert {index} r{replica} tokens to node {node}", data_bytes=in_bytes, src=0, dst=node, dependencies=list(router_ids), metadata={"expert": index, "replica": replica, "phase": "send"})
                tasks.append(noc_send)
                activation_deps = [noc_send.task_id]
            act_level = f"tile{tile_id_act}_sram" if tiled and tile_id_act is not None else "sram"
            activation_read = Task(task_id=f"expert_{index}_r{replica}_act_read", name=f"Expert {index} r{replica} activations in", resource_type=ResourceType.MEMORY_READ, work=in_bytes, mem_level=act_level, units=1, banks=1, dependencies=activation_deps, metadata={"kind": "activation", "expert": index, "replica": replica, **({"tile_id": tile_id_act} if tile_id_act is not None else {})})
            tasks.append(activation_read)
            per_chunk_macs = macs_r // chunks
            remainder_macs = macs_r % chunks
            previous_compute: Optional[str] = None
            for chunk in range(chunks):
                dependencies = list(router_ids) + [activation_read.task_id]
                if weight_chunk_ids and not cim_mode:
                    dependencies.append(weight_chunk_ids[index][replica][chunk])
                if previous_compute is not None:
                    dependencies.append(previous_compute)
                compute_id = f"expert_{index}_r{replica}_compute_{chunk}"
                if cim_mode:
                    tasks.append(Task(task_id=compute_id, name=f"Expert {index} r{replica} CIM {chunk}", resource_type=ResourceType.COMPUTE, work=per_chunk_macs + (remainder_macs if chunk == chunks - 1 else 0), dependencies=dependencies, units=expert_units or 0, metadata={"kind": "cim", "arch_family": "cim", "expert": index, "replica": replica, "chunk": chunk, **({"tile_id": tile_id_act} if tile_id_act is not None else {})}))
                else:
                    tasks.append(Task(task_id=compute_id, name=f"Expert {index} r{replica} compute {chunk}", resource_type=ResourceType.COMPUTE, work=per_chunk_macs + (remainder_macs if chunk == chunks - 1 else 0), dependencies=dependencies, units=expert_units or 0))
                previous_compute = compute_id
            tasks.append(Task(task_id=f"expert_{index}_r{replica}_act_write", name=f"Expert {index} r{replica} activations out", resource_type=ResourceType.MEMORY_WRITE, work=out_bytes, mem_level=act_level, units=1, banks=1, dependencies=[previous_compute], metadata={"kind": "activation", "expert": index, "replica": replica, **({"tile_id": tile_id_act} if tile_id_act is not None else {})}))
            if noc_active and node is not None:
                noc_return = noc.transfer_task(task_id=f"expert_{index}_r{replica}_noc_return", name=f"Expert {index} r{replica} results from node {node}", data_bytes=out_bytes, src=node, dst=0, dependencies=[f"expert_{index}_r{replica}_act_write"], metadata={"expert": index, "replica": replica, "phase": "return"})
                tasks.append(noc_return)
                combine_inputs.append(noc_return.task_id)
    if noc_active and combine_inputs:
        tasks.append(Task(task_id="moe_combine", name="MoE Combine", resource_type=ResourceType.ROUTER, work=sum(e.output_bytes for e in expert_costs), dependencies=combine_inputs, metadata={"kind": "combine"}))
    return tasks


def _moe_node(index: int, replica: int, replicas: int, active: int, nodes: int, placement: str) -> int:
    if placement == "contiguous":
        return (index * replicas + replica) % nodes
    return (index + replica * active) % nodes
