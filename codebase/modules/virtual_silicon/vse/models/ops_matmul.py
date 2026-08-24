"""VSE matmul/linear/mlp ops — split from ops.py."""

from __future__ import annotations

from vse.core.compute import ComputeArray
from vse.core.memory import Memory
from vse.models.ops_base import OpCost, OpType, combine_costs, tensor_bytes


def matmul_cost(m: int, k: int, n: int, input_bits: int = 4, output_bits: int = 16, compute: ComputeArray | None = None, memory: Memory | None = None, name: str = "matmul") -> OpCost:
    if m <= 0 or k <= 0 or n <= 0:
        raise ValueError("m, k and n must all be > 0")
    if input_bits <= 0:
        raise ValueError("input_bits must be > 0")
    if output_bits <= 0:
        raise ValueError("output_bits must be > 0")
    macs = m * k * n
    input_bytes = tensor_bytes((m, k), input_bits) + tensor_bytes((k, n), input_bits)
    output_bytes = tensor_bytes((m, n), output_bits)
    compute_cycles = compute.cycles_for_macs(macs) if compute is not None else 0
    memory_read_cycles = (input_bytes + memory.read_bandwidth_bytes_per_cycle - 1) // memory.read_bandwidth_bytes_per_cycle if memory is not None else 0
    memory_write_cycles = (output_bytes + memory.write_bandwidth_bytes_per_cycle - 1) // memory.write_bandwidth_bytes_per_cycle if memory is not None else 0
    return OpCost(name=name, op_type=OpType.MATMUL, macs=macs, input_bytes=input_bytes, output_bytes=output_bytes, compute_cycles=compute_cycles, memory_read_cycles=memory_read_cycles, memory_write_cycles=memory_write_cycles)


def linear_cost(tokens: int, input_dim: int, output_dim: int, input_bits: int = 4, weight_bits: int = 4, output_bits: int = 16, compute: ComputeArray | None = None, memory: Memory | None = None, name: str = "linear") -> OpCost:
    return matmul_cost(m=tokens, k=input_dim, n=output_dim, input_bits=input_bits, output_bits=output_bits, compute=compute, memory=memory, name=name)


def mlp_cost(tokens: int, hidden_dim: int, intermediate_dim: int, compute: ComputeArray | None = None, memory: Memory | None = None, input_bits: int = 4, weight_bits: int = 4, output_bits: int = 16, gated: bool = True) -> OpCost:
    up = linear_cost(tokens=tokens, input_dim=hidden_dim, output_dim=intermediate_dim, input_bits=input_bits, weight_bits=weight_bits, output_bits=output_bits, compute=compute, memory=memory, name="mlp_up")
    down = linear_cost(tokens=tokens, input_dim=intermediate_dim, output_dim=hidden_dim, input_bits=input_bits, weight_bits=weight_bits, output_bits=output_bits, compute=compute, memory=memory, name="mlp_down")
    costs = [up, down]
    if gated:
        gate = linear_cost(tokens=tokens, input_dim=hidden_dim, output_dim=intermediate_dim, input_bits=input_bits, weight_bits=weight_bits, output_bits=output_bits, compute=compute, memory=memory, name="mlp_gate")
        costs.append(gate)
    return combine_costs(costs, name="mlp", op_type=OpType.CUSTOM)
