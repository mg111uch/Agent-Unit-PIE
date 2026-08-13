"""
VSE - Virtual Silicon Engine
vse/compiler.py

Phase 5: model-specific hardware compilation.

Compiles an exact model + hardware into a fixed execution graph with an
explicit compile-time plan: PE allocation, expert placement, memory
placement, routing, operation fusion, pipeline depth, and precision.

The compiler reuses the graph builders and records every decision in
`CompiledProgram.plan` so the schedule is reproducible and auditable.
"""

from __future__ import annotations

import re
from dataclasses import dataclass, replace
from typing import Optional

from vse.graphs.graph import (
    build_moe_tasks,
    build_transformer_tasks,
)
from vse.models.moe import MoE
from vse.core.noc import NoC, NoCConfig
from vse.scheduler import ResourceType, Task
from vse.models.transformer import TransformerModel
from vse.workload import (
    HardwareConfig,
    VirtualMachine,
    build_memory_hierarchy,
)


@dataclass
class CompileOptions:
    """Compile-time decisions. None inherits the model's precision."""

    weight_bits: Optional[int] = None
    activation_bits: Optional[int] = None
    kv_bits: Optional[int] = None
    fusion: bool = True
    expert_placement: str = "round_robin"
    replicas: int = 1

    def __post_init__(self) -> None:
        if self.expert_placement not in (
            "round_robin",
            "contiguous",
        ):
            raise ValueError(
                "expert_placement must be "
                "'round_robin' or 'contiguous'"
            )

        if self.replicas < 1:
            raise ValueError("replicas must be >= 1")


@dataclass
class CompiledProgram:
    """A model compiled into a fixed execution graph plus its plan."""

    name: str
    model: object
    tokens: int
    sequence_length: int
    mode: str
    config: HardwareConfig
    tasks: list[Task]
    plan: dict
    total_macs: int = 0
    total_memory_bytes: int = 0
    weight_bytes: int = 0


def _bit_overrides(
    options: CompileOptions,
) -> dict:
    return {
        key: value
        for key, value in {
            "weight_bits": options.weight_bits,
            "activation_bits": options.activation_bits,
            "kv_bits": options.kv_bits,
        }.items()
        if value is not None
    }


def compile_moe(
    moe: MoE,
    tokens: int,
    config: HardwareConfig,
    options: Optional[CompileOptions] = None,
) -> CompiledProgram:
    """Compile an exact MoE layer into a fixed execution graph."""

    if options is None:
        options = CompileOptions()

    overrides = _bit_overrides(options)
    compiled = MoE(
        replace(moe.config, **overrides)
        if overrides
        else moe.config
    )

    cost = compiled.cost(tokens=tokens)

    hierarchy = build_memory_hierarchy(config)

    active = len(cost.expert_costs)

    weight_bytes_per_expert = (
        cost.total_weight_bytes // cost.num_experts
        if cost.num_experts
        else 0
    )

    weight_traffic = (
        weight_bytes_per_expert * active
    )

    resident = hierarchy.weights_resident(
        weight_traffic
    )

    noc = NoC(
        NoCConfig(
            topology=config.noc_topology,
            nodes=config.noc_nodes,
            link_bw=config.noc_link_bw,
            per_hop_cycles=config.noc_per_hop_cycles,
            links=config.noc_links,
            broadcast=config.noc_broadcast,
        )
    )

    tasks = build_moe_tasks(
        cost.routing_cost,
        cost.expert_costs,
        expert_units=(
            max(
                1,
                config.num_pes
                // (active * options.replicas),
            )
            if active
            else None
        ),
        weight_bytes_per_expert=weight_bytes_per_expert,
        resident=resident,
        chunks=config.weight_chunks,
        noc=noc if noc.config.enabled else None,
        replicas=options.replicas,
        placement=options.expert_placement,
    )

    if options.fusion:
        tasks = _fuse_moe_activation_writes(tasks)

    transfers = [
        t for t in tasks if t.metadata.get("kind") == "noc"
    ]

    plan = {
        "precision": {
            "weight_bits": compiled.config.weight_bits,
            "activation_bits": (
                compiled.config.activation_bits
            ),
        },
        "pe_allocation": {
            "total_pes": config.num_pes,
            "expert_pes": (
                max(
                    1,
                    config.num_pes
                    // (active * options.replicas),
                )
                if active
                else 0
            ),
        },
        "expert_placement": {
            "strategy": options.expert_placement,
            "nodes": noc.config.nodes,
            "topology": noc.config.topology,
            "replicas": options.replicas,
        },
        "memory_placement": {
            "weights": (
                "resident (sram)"
                if resident
                else "streamed (hbm)"
            ),
            "activations": "sram",
        },
        "routing": {
            "transfers": len(transfers),
            "hops": sum(
                int(t.metadata.get("hops", 0))
                for t in transfers
            ),
        },
        "pipeline": {
            "double_buffer_depth": config.weight_chunks,
            "stages": 1,
        },
        "fusion": {
            "enabled": options.fusion,
            "saved_sram_round_trips": (
                active if options.fusion else 0
            ),
        },
    }

    return CompiledProgram(
        name="moe",
        model=compiled,
        tokens=tokens,
        sequence_length=0,
        mode="decode",
        config=config,
        tasks=tasks,
        plan=plan,
        total_macs=cost.macs,
        total_memory_bytes=cost.total_memory_bytes,
        weight_bytes=weight_traffic,
    )


def _fuse_moe_activation_writes(
    tasks: list[Task],
) -> list[Task]:
    """
    Remove per-expert activation writes; expert results go straight to
    the NoC return / combine instead of round-tripping SRAM.
    """

    pattern = re.compile(
        r"expert_(\d+)(_r\d+)?_compute_(\d+)"
    )
    last_compute: dict[tuple, str] = {}

    for task in tasks:
        match = pattern.fullmatch(task.task_id)
        if match:
            last_compute[
                (
                    int(match.group(1)),
                    match.group(2),
                )
            ] = task.task_id

    result: list[Task] = []

    for task in tasks:
        if task.task_id.endswith("_act_write"):
            continue

        if task.task_id.endswith("_noc_return"):
            match = re.fullmatch(
                r"expert_(\d+)(_r\d+)?_noc_return",
                task.task_id,
            )
            task.dependencies = [
                last_compute[
                    (
                        int(match.group(1)),
                        match.group(2),
                    )
                ]
            ]

        result.append(task)

    return result


def compile_transformer(
    model: TransformerModel,
    sequence_length: int,
    config: HardwareConfig,
    options: Optional[CompileOptions] = None,
    mode: str = "decode",
) -> CompiledProgram:
    """Compile an exact Transformer into a fixed execution graph."""

    if options is None:
        options = CompileOptions()

    overrides = _bit_overrides(options)
    compiled = TransformerModel(
        replace(model.config, **overrides)
        if overrides
        else model.config,
        num_layers=model.num_layers,
    )

    if mode == "decode":
        workload = compiled.decode_cost(sequence_length)
        tokens = 1
    elif mode == "prefill":
        workload = compiled.prefill_cost(sequence_length)
        tokens = sequence_length
    else:
        raise ValueError(
            "mode must be 'decode' or 'prefill'"
        )

    hierarchy = build_memory_hierarchy(config)

    kv_bytes = (
        workload.layer_cost.kv_read_bytes
        + workload.layer_cost.kv_write_bytes
    ) * model.num_layers

    kv_level = hierarchy.on_chip_level(kv_bytes)

    tasks = build_transformer_tasks(
        workload.layer_cost,
        model.num_layers,
        kv_level=kv_level,
        fusion=options.fusion,
    )

    plan = {
        "precision": {
            "weight_bits": compiled.config.weight_bits,
            "activation_bits": (
                compiled.config.activation_bits
            ),
            "kv_bits": compiled.config.kv_bits,
        },
        "pe_allocation": {
            "total_pes": config.num_pes,
            "layers_in_parallel": 1,
        },
        "memory_placement": {
            "kv": kv_level,
            "weights": "streamed (hbm, not modeled)",
        },
        "pipeline": {
            "stages": 1,
            "layers": model.num_layers,
        },
        "fusion": {
            "enabled": options.fusion,
            "saved_sram_round_trips": (
                model.num_layers * 2 - 1
                if options.fusion
                else 0
            ),
        },
    }

    return CompiledProgram(
        name="transformer",
        model=compiled,
        tokens=tokens,
        sequence_length=sequence_length,
        mode=mode,
        config=config,
        tasks=tasks,
        plan=plan,
        total_macs=workload.macs,
        total_memory_bytes=workload.memory_bytes,
    )


def execute(
    program: CompiledProgram,
    target_tokens_per_second: Optional[float] = None,
):
    """
    Run a compiled program on the virtual machine and produce an
    end-to-end result carrying the compile plan.
    """

    from vse.benchmark.benchmark import Benchmark
    from vse.silicon.area import estimate_area
    from vse.silicon.power import estimate_power
    from vse.report.result import EndToEndResult

    machine = VirtualMachine(program.config)

    machine.scheduler.add_tasks(program.tasks)

    schedule = machine.run()

    benchmark = Benchmark(
        compute=machine.compute,
        memory=machine.memory,
        frequency_hz=program.config.frequency_hz,
    )

    if program.name == "moe":
        benchmark_result = benchmark.moe(
            program.model,
            tokens=program.tokens,
            target_tokens_per_second=(
                target_tokens_per_second
            ),
        )
    elif program.mode == "decode":
        benchmark_result = benchmark.transformer_decode(
            program.model,
            sequence_length=program.sequence_length,
            target_tokens_per_second=(
                target_tokens_per_second
            ),
        )
    else:
        benchmark_result = benchmark.transformer_prefill(
            program.model,
            sequence_length=program.sequence_length,
        )

    result = EndToEndResult(
        name=program.name,
        tokens=program.tokens,
        sequence_length=program.sequence_length,
        schedule=schedule,
        benchmark=benchmark_result,
        total_macs=program.total_macs,
        total_memory_bytes=program.total_memory_bytes,
        memory_traffic=machine.memory_hierarchy.report(
            schedule,
            weight_bytes=program.weight_bytes,
        ),
        noc=machine.noc.report(schedule),
        plan=program.plan,
    )

    result.power = estimate_power(
        result,
        chip=program.config,
    ).report()
    result.area = estimate_area(program.config).report()

    return result


__all__ = [
    "CompileOptions",
    "CompiledProgram",
    "compile_moe",
    "compile_transformer",
    "execute",
]
