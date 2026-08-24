"""VSE attention + combine helpers — split from ops.py."""

from __future__ import annotations

from vse.core.compute import ComputeArray
from vse.core.memory import Memory
from vse.models.ops_base import OpCost, OpType, combine_costs, tensor_bytes
from vse.models.ops_matmul import linear_cost


def _custom_cost(name: str, op_type: OpType, macs: int, input_bytes: int, output_bytes: int, compute: ComputeArray | None, memory: Memory | None, elementwise_operations: int = 0) -> OpCost:
    total_compute_ops = macs + elementwise_operations
    compute_cycles = compute.cycles_for_macs(total_compute_ops) if compute is not None and total_compute_ops > 0 else 0
    memory_read_cycles = (input_bytes + memory.read_bandwidth_bytes_per_cycle - 1) // memory.read_bandwidth_bytes_per_cycle if memory is not None else 0
    memory_write_cycles = (output_bytes + memory.write_bandwidth_bytes_per_cycle - 1) // memory.write_bandwidth_bytes_per_cycle if memory is not None else 0
    return OpCost(name=name, op_type=op_type, macs=total_compute_ops, input_bytes=input_bytes, output_bytes=output_bytes, compute_cycles=compute_cycles, memory_read_cycles=memory_read_cycles, memory_write_cycles=memory_write_cycles)


def attention_cost(tokens: int, hidden_dim: int, num_heads: int, head_dim: int | None = None, compute: ComputeArray | None = None, memory: Memory | None = None, input_bits: int = 4, output_bits: int = 16) -> OpCost:
    if tokens <= 0:
        raise ValueError("tokens must be > 0")
    if hidden_dim <= 0:
        raise ValueError("hidden_dim must be > 0")
    if num_heads <= 0:
        raise ValueError("num_heads must be > 0")
    if head_dim is None:
        if hidden_dim % num_heads != 0:
            raise ValueError("hidden_dim must be divisible by num_heads")
        head_dim = hidden_dim // num_heads
    if head_dim <= 0:
        raise ValueError("head_dim must be > 0")
    costs: list[OpCost] = []
    for projection in ("q", "k", "v"):
        costs.append(linear_cost(tokens=tokens, input_dim=hidden_dim, output_dim=hidden_dim, input_bits=input_bits, output_bits=output_bits, compute=compute, memory=memory, name=f"attention_{projection}"))
    qk_macs = num_heads * tokens * tokens * head_dim
    qk_input_bytes = tensor_bytes((num_heads, tokens, head_dim), input_bits) * 2
    qk_output_bytes = tensor_bytes((num_heads, tokens, tokens), output_bits)
    costs.append(_custom_cost(name="attention_qk", op_type=OpType.ATTENTION, macs=qk_macs, input_bytes=qk_input_bytes, output_bytes=qk_output_bytes, compute=compute, memory=memory))
    softmax_elements = num_heads * tokens * tokens
    costs.append(_custom_cost(name="attention_softmax", op_type=OpType.SOFTMAX, macs=0, input_bytes=tensor_bytes((num_heads, tokens, tokens), output_bits), output_bytes=tensor_bytes((num_heads, tokens, tokens), output_bits), compute=compute, memory=memory, elementwise_operations=softmax_elements))
    av_macs = num_heads * tokens * tokens * head_dim
    av_input_bytes = tensor_bytes((num_heads, tokens, tokens), output_bits) + tensor_bytes((num_heads, tokens, head_dim), input_bits)
    av_output_bytes = tensor_bytes((num_heads, tokens, head_dim), output_bits)
    costs.append(_custom_cost(name="attention_av", op_type=OpType.ATTENTION, macs=av_macs, input_bytes=av_input_bytes, output_bytes=av_output_bytes, compute=compute, memory=memory))
    costs.append(linear_cost(tokens=tokens, input_dim=hidden_dim, output_dim=hidden_dim, input_bits=input_bits, output_bits=output_bits, compute=compute, memory=memory, name="attention_output"))
    return combine_costs(costs, name="attention", op_type=OpType.ATTENTION)


def format_cost(cost: OpCost) -> str:
    from vse.models.ops_base import format_cost as _format_cost
    return _format_cost(cost)
