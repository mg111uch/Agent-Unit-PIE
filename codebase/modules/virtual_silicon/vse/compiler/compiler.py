"""
VSE - Virtual Silicon Engine
vse/compiler.py
Phase 5: model-specific hardware compilation.
Compiles an exact model + hardware into a fixed execution graph with an
explicit compile-time plan: PE allocation, expert placement, memory
placement, routing, operation fusion, pipeline depth, and precision.
"""

from __future__ import annotations

import re
from dataclasses import dataclass, replace
from typing import Optional

from vse.compiler.precision import (
    Q2Block,
    effective_bits,
    parse_precision_map,
    precision_to_bytes,
    resolve_precision,
)
from vse.core.noc import NoC, NoCConfig
from vse.graphs.graph import build_moe_tasks, build_transformer_tasks
from vse.models.moe import MoE
from vse.models.transformer import TransformerModel
from vse.scheduler import Task
from vse.workload import HardwareConfig, VirtualMachine, build_memory_hierarchy


@dataclass
class CompileOptions:
    """Compile-time decisions. None inherits the model's precision."""

    weight_bits: Optional[int] = None
    activation_bits: Optional[int] = None
    kv_bits: Optional[int] = None
    fusion: bool = True
    expert_placement: str = "round_robin"
    replicas: int = 1
    precision_map: Optional[dict] = None
    q2_group_size: int = 32
    q2_scale_bits: int = 8

    def __post_init__(self) -> None:
        if self.expert_placement not in ("round_robin", "contiguous"):
            raise ValueError("expert_placement must be 'round_robin' or 'contiguous'")
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


def _bit_overrides(options: CompileOptions) -> dict:
    return {k: v for k, v in {"weight_bits": options.weight_bits, "activation_bits": options.activation_bits, "kv_bits": options.kv_bits}.items() if v is not None}


def _normalize_map(m) -> Optional[dict]:
    if m is None:
        return None
    if isinstance(m, str):
        return parse_precision_map(m)
    if isinstance(m, dict):
        return parse_precision_map(m)
    return None


def _precision_label(p) -> str:
    if isinstance(p, Q2Block):
        return f"Q2({p.bits}b,g{p.group_size})"
    return f"{int(p)}b"


def _bits_str(pmap: Optional[dict]) -> str:
    if not pmap:
        return ""
    uniq = set()
    for v in pmap.values():
        if isinstance(v, Q2Block):
            uniq.add(v.bits)
        else:
            try:
                uniq.add(int(v))
            except Exception:
                uniq.add(str(v))
    try:
        ordered = sorted(uniq)
    except TypeError:
        ordered = sorted(str(x) for x in uniq)
    return "w" + "/".join(str(b) for b in ordered)


def _map_for_plan(pmap: Optional[dict]) -> dict:
    if not pmap:
        return {}
    out = {}
    for k, v in pmap.items():
        if isinstance(v, Q2Block):
            out[k] = {"bits": v.bits, "group": v.group_size, "scale_bits": v.scale_bits}
        else:
            out[k] = v
    return out


def compile_moe(moe: MoE, tokens: int, config: HardwareConfig, options: Optional[CompileOptions] = None) -> CompiledProgram:
    """Compile an exact MoE layer into a fixed execution graph."""
    if options is None:
        options = CompileOptions()
    overrides = _bit_overrides(options)
    compiled = MoE(replace(moe.config, **overrides) if overrides else moe.config)
    cost = compiled.cost(tokens=tokens)
    hierarchy = build_memory_hierarchy(config)
    active = len(cost.expert_costs)
    # per-tensor precision for MoE weights
    pmap = _normalize_map(options.precision_map)
    weight_bytes_per_expert = cost.total_weight_bytes // cost.num_experts if cost.num_experts else 0
    eff_bits: Optional[float] = None
    if pmap is not None:
        param = compiled.expert_parameter_count
        prec = resolve_precision("mlp", pmap, None)
        if prec is None:
            prec = resolve_precision("weight", pmap, compiled.config.weight_bits)
        if prec is None:
            prec = compiled.config.weight_bits
        weight_bytes_per_expert = precision_to_bytes(param, prec)
        eff_bits = effective_bits(prec)
    weight_traffic = weight_bytes_per_expert * active
    resident = hierarchy.weights_resident(weight_traffic)
    noc = NoC(NoCConfig(topology=config.noc_topology, nodes=config.noc_nodes, link_bw=config.noc_link_bw, per_hop_cycles=config.noc_per_hop_cycles, links=config.noc_links, broadcast=config.noc_broadcast))
    tasks = build_moe_tasks(cost.routing_cost, cost.expert_costs, expert_units=max(1, config.num_pes // (active * options.replicas)) if active else None, weight_bytes_per_expert=weight_bytes_per_expert, resident=resident, chunks=config.weight_chunks, noc=noc if noc.config.enabled else None, replicas=options.replicas, placement=options.expert_placement, arch_family=getattr(config, "arch_family", "scalar"))
    if options.fusion:
        tasks = _fuse_moe_activation_writes(tasks)
    transfers = [t for t in tasks if t.metadata.get("kind") == "noc"]
    prec_plan = {"weight_bits": compiled.config.weight_bits, "activation_bits": compiled.config.activation_bits}
    if pmap is not None:
        prec_plan["map"] = _map_for_plan(pmap)
        prec_plan["effective_weight_bits"] = eff_bits
        prec_plan["bits_str"] = _bits_str(pmap)
        prec_plan["weight_bits_str"] = _bits_str(pmap)
    plan = {"precision": prec_plan, "pe_allocation": {"total_pes": config.num_pes, "expert_pes": max(1, config.num_pes // (active * options.replicas)) if active else 0}, "expert_placement": {"strategy": options.expert_placement, "nodes": noc.config.nodes, "topology": noc.config.topology, "replicas": options.replicas}, "memory_placement": {"weights": "resident (sram)" if resident else "streamed (hbm)", "activations": "sram"}, "routing": {"transfers": len(transfers), "hops": sum(int(t.metadata.get("hops", 0)) for t in transfers)}, "pipeline": {"double_buffer_depth": config.weight_chunks, "stages": 1}, "fusion": {"enabled": options.fusion, "saved_sram_round_trips": active if options.fusion else 0}}
    return CompiledProgram(name="moe", model=compiled, tokens=tokens, sequence_length=0, mode="decode", config=config, tasks=tasks, plan=plan, total_macs=cost.macs, total_memory_bytes=cost.total_memory_bytes, weight_bytes=weight_traffic)


def _fuse_moe_activation_writes(tasks: list[Task]) -> list[Task]:
    """Remove per-expert activation writes; expert results go straight to NoC."""
    pattern = re.compile(r"expert_(\d+)(_r\d+)?_compute_(\d+)")
    last_compute: dict[tuple, str] = {}
    for task in tasks:
        match = pattern.fullmatch(task.task_id)
        if match:
            last_compute[(int(match.group(1)), match.group(2))] = task.task_id
    result: list[Task] = []
    for task in tasks:
        if task.task_id.endswith("_act_write"):
            continue
        if task.task_id.endswith("_noc_return"):
            match = re.fullmatch(r"expert_(\d+)(_r\d+)?_noc_return", task.task_id)
            task.dependencies = [last_compute[(int(match.group(1)), match.group(2))]]
        result.append(task)
    return result


def compile_transformer(model: TransformerModel, sequence_length: int, config: HardwareConfig, options: Optional[CompileOptions] = None, mode: str = "decode") -> CompiledProgram:
    """Compile an exact Transformer into a fixed execution graph."""
    if options is None:
        options = CompileOptions()
    overrides = _bit_overrides(options)
    compiled = TransformerModel(replace(model.config, **overrides) if overrides else model.config, num_layers=model.num_layers)
    if mode == "decode":
        workload = compiled.decode_cost(sequence_length)
        tokens = 1
    elif mode == "prefill":
        workload = compiled.prefill_cost(sequence_length)
        tokens = sequence_length
    else:
        raise ValueError("mode must be 'decode' or 'prefill'")
    hierarchy = build_memory_hierarchy(config)
    kv_bytes = (workload.layer_cost.kv_read_bytes + workload.layer_cost.kv_write_bytes) * model.num_layers
    kv_level = hierarchy.on_chip_level(kv_bytes)
    tasks = build_transformer_tasks(workload.layer_cost, model.num_layers, kv_level=kv_level, fusion=options.fusion, arch_family=getattr(config, "arch_family", "scalar"))
    # per-tensor precision handling
    pmap = _normalize_map(options.precision_map)
    weight_bytes = 0
    eff_wbits: Optional[float] = None
    bits_label = ""
    if pmap is not None:
        hidden = compiled.config.hidden_dim
        inter = compiled.config.intermediate_dim
        gated = compiled.config.gated_mlp
        attn_params = 4 * hidden * hidden
        mlp_params = (3 if gated else 2) * hidden * inter
        total = 0
        wsum = 0.0
        total_params = 0
        bits_set: set = set()
        for i in range(compiled.num_layers):
            a_prec = resolve_precision(f"layer{i}.attn", pmap, None)
            if a_prec is None:
                a_prec = resolve_precision("attn", pmap, None)
                if a_prec is None:
                    a_prec = resolve_precision("attention", pmap, compiled.config.weight_bits)
                if a_prec is None:
                    a_prec = compiled.config.weight_bits
            if isinstance(a_prec, Q2Block) and a_prec.group_size == 32 and a_prec.scale_bits == 8:
                pass
            m_prec = resolve_precision(f"layer{i}.mlp", pmap, None)
            if m_prec is None:
                m_prec = resolve_precision("mlp", pmap, compiled.config.weight_bits)
            a_b = precision_to_bytes(attn_params, a_prec)
            m_b = precision_to_bytes(mlp_params, m_prec)
            total += a_b + m_b
            wsum += attn_params * effective_bits(a_prec) + mlp_params * effective_bits(m_prec)
            total_params += attn_params + mlp_params
            for prec in (a_prec, m_prec):
                if isinstance(prec, Q2Block):
                    bits_set.add(prec.bits)
                else:
                    bits_set.add(int(prec))
        # include head/kv/activation bits if present for display
        for k in ("head", "kv", "activation"):
            if k in pmap:
                v = pmap[k]
                if isinstance(v, Q2Block):
                    bits_set.add(v.bits)
                else:
                    try:
                        bits_set.add(int(v))
                    except Exception:
                        pass
        weight_bytes = total
        eff_wbits = wsum / total_params if total_params else 0.0
        try:
            ordered = sorted(bits_set)
        except TypeError:
            ordered = sorted(str(x) for x in bits_set)
        bits_label = "w" + "/".join(str(b) for b in ordered)
    prec_plan = {"weight_bits": compiled.config.weight_bits, "activation_bits": compiled.config.activation_bits, "kv_bits": compiled.config.kv_bits}
    if pmap is not None:
        prec_plan["map"] = _map_for_plan(pmap)
        prec_plan["effective_weight_bits"] = eff_wbits
        prec_plan["bits_str"] = bits_label
        prec_plan["weight_bits_str"] = bits_label
        prec_plan["weight_bytes"] = weight_bytes
        # optional: resolve kv/activation overrides for completeness
        kv_p = resolve_precision("kv", pmap, None)
        if kv_p is not None and not isinstance(kv_p, Q2Block):
            try:
                prec_plan["kv_bits"] = int(kv_p)
            except Exception:
                pass
        act_p = resolve_precision("activation", pmap, None)
        if act_p is not None and not isinstance(act_p, Q2Block):
            try:
                prec_plan["activation_bits"] = int(act_p)
            except Exception:
                pass
    plan = {"precision": prec_plan, "pe_allocation": {"total_pes": config.num_pes, "layers_in_parallel": 1}, "memory_placement": {"kv": kv_level, "weights": "streamed (hbm, not modeled)"}, "pipeline": {"stages": 1, "layers": model.num_layers}, "fusion": {"enabled": options.fusion, "saved_sram_round_trips": model.num_layers * 2 - 1 if options.fusion else 0}}
    return CompiledProgram(name="transformer", model=compiled, tokens=tokens, sequence_length=sequence_length, mode=mode, config=config, tasks=tasks, plan=plan, total_macs=workload.macs, total_memory_bytes=workload.memory_bytes, weight_bytes=weight_bytes)


def execute(program: CompiledProgram, target_tokens_per_second: Optional[float] = None):
    """Run a compiled program on the virtual machine and produce an end-to-end result."""
    from vse.benchmark.benchmark import Benchmark
    from vse.report.result import EndToEndResult
    from vse.silicon.area import estimate_area
    from vse.silicon.power import estimate_power

    machine = VirtualMachine(program.config)
    machine.scheduler.add_tasks(program.tasks)
    schedule = machine.run()
    benchmark = Benchmark(compute=machine.compute, memory=machine.memory, frequency_hz=program.config.frequency_hz)
    if program.name == "moe":
        benchmark_result = benchmark.moe(program.model, tokens=program.tokens, target_tokens_per_second=target_tokens_per_second)
    elif program.mode == "decode":
        benchmark_result = benchmark.transformer_decode(program.model, sequence_length=program.sequence_length, target_tokens_per_second=target_tokens_per_second)
    else:
        benchmark_result = benchmark.transformer_prefill(program.model, sequence_length=program.sequence_length)
    result = EndToEndResult(name=program.name, tokens=program.tokens, sequence_length=program.sequence_length, schedule=schedule, benchmark=benchmark_result, total_macs=program.total_macs, total_memory_bytes=program.total_memory_bytes, memory_traffic=machine.memory_hierarchy.report(schedule, weight_bytes=program.weight_bytes), noc=machine.noc.report(schedule), plan=program.plan)
    result.power = estimate_power(result, chip=program.config).report()
    result.area = estimate_area(program.config).report()
    return result


__all__ = ["CompileOptions", "CompiledProgram", "compile_moe", "compile_transformer", "execute"]
