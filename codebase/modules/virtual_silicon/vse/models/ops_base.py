"""VSE ops base — OpCost, OpType, tensor helpers."""

from __future__ import annotations

from dataclasses import dataclass
from enum import Enum

from vse.core.compute import ComputeArray
from vse.core.memory import Memory


class OpType(str, Enum):
    MATMUL = "matmul"
    BATCH_MATMUL = "batch_matmul"
    ELEMENTWISE = "elementwise"
    ATTENTION = "attention"
    SOFTMAX = "softmax"
    EMBEDDING = "embedding"
    CUSTOM = "custom"


@dataclass
class OpCost:
    name: str
    op_type: OpType
    macs: int = 0
    input_bytes: int = 0
    output_bytes: int = 0
    compute_cycles: int = 0
    memory_read_cycles: int = 0
    memory_write_cycles: int = 0

    @property
    def total_memory_bytes(self) -> int:
        return self.input_bytes + self.output_bytes

    @property
    def total_memory_cycles(self) -> int:
        return self.memory_read_cycles + self.memory_write_cycles

    @property
    def arithmetic_intensity(self) -> float:
        if self.total_memory_bytes == 0:
            return 0.0
        return self.macs / self.total_memory_bytes

    @property
    def total_cycles_serial(self) -> int:
        return max(self.compute_cycles, self.total_memory_cycles)


def _validate_shape(shape: tuple[int, ...], name: str) -> None:
    if not shape:
        raise ValueError(f"{name} cannot be empty")
    if any(dim <= 0 for dim in shape):
        raise ValueError(f"{name} dimensions must be > 0")


def _num_elements(shape: tuple[int, ...]) -> int:
    _validate_shape(shape, "shape")
    result = 1
    for dim in shape:
        result *= dim
    return result


def tensor_bytes(shape: tuple[int, ...], bits: int = 4) -> int:
    if bits <= 0:
        raise ValueError("bits must be > 0")
    elements = _num_elements(shape)
    return (elements * bits + 7) // 8


def combine_costs(costs: list[OpCost], name: str = "combined", op_type: OpType = OpType.CUSTOM) -> OpCost:
    if not costs:
        raise ValueError("costs cannot be empty")
    return OpCost(name=name, op_type=op_type, macs=sum(c.macs for c in costs), input_bytes=sum(c.input_bytes for c in costs), output_bytes=sum(c.output_bytes for c in costs), compute_cycles=sum(c.compute_cycles for c in costs), memory_read_cycles=sum(c.memory_read_cycles for c in costs), memory_write_cycles=sum(c.memory_write_cycles for c in costs))


def format_cost(cost: OpCost) -> str:
    return (f"{cost.name}\n  type:                {cost.op_type.value}\n  MACs:                {cost.macs:,}\n  input:               {cost.input_bytes:,} bytes\n  output:              {cost.output_bytes:,} bytes\n  total memory:        {cost.total_memory_bytes:,} bytes\n  compute cycles:      {cost.compute_cycles:,}\n  memory read cycles:  {cost.memory_read_cycles:,}\n  memory write cycles: {cost.memory_write_cycles:,}\n  arithmetic intensity: {cost.arithmetic_intensity:.4f} MAC/byte\n  serial cycles:       {cost.total_cycles_serial:,}")
