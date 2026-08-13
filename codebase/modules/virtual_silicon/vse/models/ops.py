"""
VSE - Virtual Silicon Engine
vse/ops.py

Neural-network operation cost model.

Converts logical operations such as:
    - MatMul
    - Linear
    - Attention projections
    - MLP
    - Elementwise operations

into hardware work:
    - MAC count
    - input/output bytes
    - estimated compute cycles
    - arithmetic intensity

This module does NOT perform numerical tensor operations.

The purpose is to answer:

    "How much hardware work does this neural-network operation require?"
"""

from __future__ import annotations

from dataclasses import dataclass
from enum import Enum

from vse.core.compute import ComputeArray
from vse.core.memory import Memory


# ---------------------------------------------------------------------------
# Operation types
# ---------------------------------------------------------------------------

class OpType(str, Enum):
    MATMUL = "matmul"
    BATCH_MATMUL = "batch_matmul"
    ELEMENTWISE = "elementwise"
    ATTENTION = "attention"
    SOFTMAX = "softmax"
    EMBEDDING = "embedding"
    CUSTOM = "custom"


# ---------------------------------------------------------------------------
# Operation description
# ---------------------------------------------------------------------------

@dataclass
class OpCost:
    """
    Hardware cost of a neural-network operation.

    macs:
        Number of multiply-accumulate operations.

    input_bytes:
        Data that must be read.

    output_bytes:
        Data that must be written.

    compute_cycles:
        Estimated compute cycles.

    memory_read_cycles:
        Estimated memory read transfer cycles.

    memory_write_cycles:
        Estimated memory write transfer cycles.
    """

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
        return (
            self.memory_read_cycles
            + self.memory_write_cycles
        )

    @property
    def arithmetic_intensity(self) -> float:
        """
        MACs per byte transferred.

        Higher intensity generally means the operation is more
        compute-bound.
        """

        if self.total_memory_bytes == 0:
            return 0.0

        return self.macs / self.total_memory_bytes

    @property
    def total_cycles_serial(self) -> int:
        """
        Simple non-overlapped estimate.

        Later pipeline simulation will allow compute and memory
        to overlap.
        """

        return max(
            self.compute_cycles,
            self.total_memory_cycles,
        )


# ---------------------------------------------------------------------------
# Tensor shape helpers
# ---------------------------------------------------------------------------

def _validate_shape(
    shape: tuple[int, ...],
    name: str,
) -> None:
    if not shape:
        raise ValueError(f"{name} cannot be empty")

    if any(dim <= 0 for dim in shape):
        raise ValueError(
            f"{name} dimensions must be > 0"
        )


def _num_elements(shape: tuple[int, ...]) -> int:
    _validate_shape(shape, "shape")

    result = 1

    for dim in shape:
        result *= dim

    return result


def tensor_bytes(
    shape: tuple[int, ...],
    bits: int = 4,
) -> int:
    """
    Calculate storage size of a tensor.

    Uses ceiling division because tensors cannot occupy fractional bytes.
    """

    if bits <= 0:
        raise ValueError("bits must be > 0")

    elements = _num_elements(shape)

    return (
        elements * bits + 7
    ) // 8


# ---------------------------------------------------------------------------
# Matrix multiplication
# ---------------------------------------------------------------------------

def matmul_cost(
    m: int,
    k: int,
    n: int,
    input_bits: int = 4,
    output_bits: int = 16,
    compute: ComputeArray | None = None,
    memory: Memory | None = None,
    name: str = "matmul",
) -> OpCost:
    """
    Calculate cost of:

        [M × K] @ [K × N]

    MAC count:

        M × K × N

    Args:
        m, k, n:
            Matrix dimensions.

        input_bits:
            Input/weight precision.

        output_bits:
            Output/accumulator precision.

        compute:
            Optional VSE compute array.

        memory:
            Optional VSE memory.

    Returns:
        OpCost
    """

    if m <= 0 or k <= 0 or n <= 0:
        raise ValueError(
            "m, k and n must all be > 0"
        )

    if input_bits <= 0:
        raise ValueError("input_bits must be > 0")

    if output_bits <= 0:
        raise ValueError("output_bits must be > 0")

    macs = m * k * n

    input_bytes = (
        tensor_bytes((m, k), input_bits)
        + tensor_bytes((k, n), input_bits)
    )

    output_bytes = tensor_bytes(
        (m, n),
        output_bits,
    )

    compute_cycles = 0

    if compute is not None:
        compute_cycles = compute.cycles_for_macs(macs)

    memory_read_cycles = 0
    memory_write_cycles = 0

    if memory is not None:
        memory_read_cycles = (
            input_bytes
            + memory.read_bandwidth_bytes_per_cycle
            - 1
        ) // memory.read_bandwidth_bytes_per_cycle

        memory_write_cycles = (
            output_bytes
            + memory.write_bandwidth_bytes_per_cycle
            - 1
        ) // memory.write_bandwidth_bytes_per_cycle

    return OpCost(
        name=name,
        op_type=OpType.MATMUL,
        macs=macs,
        input_bytes=input_bytes,
        output_bytes=output_bytes,
        compute_cycles=compute_cycles,
        memory_read_cycles=memory_read_cycles,
        memory_write_cycles=memory_write_cycles,
    )


# ---------------------------------------------------------------------------
# Linear layer
# ---------------------------------------------------------------------------

def linear_cost(
    tokens: int,
    input_dim: int,
    output_dim: int,
    input_bits: int = 4,
    weight_bits: int = 4,
    output_bits: int = 16,
    compute: ComputeArray | None = None,
    memory: Memory | None = None,
    name: str = "linear",
) -> OpCost:
    """
    Cost of a Transformer linear projection.

        [tokens × input_dim]
             @
        [input_dim × output_dim]

    Bias is ignored in the MAC count.
    """

    return matmul_cost(
        m=tokens,
        k=input_dim,
        n=output_dim,
        input_bits=input_bits,
        output_bits=output_bits,
        compute=compute,
        memory=memory,
        name=name,
    )


# ---------------------------------------------------------------------------
# MLP
# ---------------------------------------------------------------------------

def mlp_cost(
    tokens: int,
    hidden_dim: int,
    intermediate_dim: int,
    compute: ComputeArray | None = None,
    memory: Memory | None = None,
    input_bits: int = 4,
    weight_bits: int = 4,
    output_bits: int = 16,
    gated: bool = True,
) -> OpCost:
    """
    Cost of a Transformer MLP.

    Standard MLP:

        hidden -> intermediate -> hidden

    Gated MLP:

        hidden -> intermediate
        hidden -> intermediate
        intermediate -> hidden

    For gated architectures, two input projections are counted.
    """

    up = linear_cost(
        tokens=tokens,
        input_dim=hidden_dim,
        output_dim=intermediate_dim,
        input_bits=input_bits,
        weight_bits=weight_bits,
        output_bits=output_bits,
        compute=compute,
        memory=memory,
        name="mlp_up",
    )

    down = linear_cost(
        tokens=tokens,
        input_dim=intermediate_dim,
        output_dim=hidden_dim,
        input_bits=input_bits,
        weight_bits=weight_bits,
        output_bits=output_bits,
        compute=compute,
        memory=memory,
        name="mlp_down",
    )

    costs = [up, down]

    if gated:
        gate = linear_cost(
            tokens=tokens,
            input_dim=hidden_dim,
            output_dim=intermediate_dim,
            input_bits=input_bits,
            weight_bits=weight_bits,
            output_bits=output_bits,
            compute=compute,
            memory=memory,
            name="mlp_gate",
        )

        costs.append(gate)

    return combine_costs(
        costs,
        name="mlp",
        op_type=OpType.CUSTOM,
    )


# ---------------------------------------------------------------------------
# Attention
# ---------------------------------------------------------------------------

def attention_cost(
    tokens: int,
    hidden_dim: int,
    num_heads: int,
    head_dim: int | None = None,
    compute: ComputeArray | None = None,
    memory: Memory | None = None,
    input_bits: int = 4,
    output_bits: int = 16,
) -> OpCost:
    """
    Approximate self-attention cost.

    Includes:

        Q projection
        K projection
        V projection
        QK^T
        softmax (modeled as elementwise)
        Attention × V
        output projection

    This is an architectural approximation, not numerical attention.
    """

    if tokens <= 0:
        raise ValueError("tokens must be > 0")

    if hidden_dim <= 0:
        raise ValueError("hidden_dim must be > 0")

    if num_heads <= 0:
        raise ValueError("num_heads must be > 0")

    if head_dim is None:
        if hidden_dim % num_heads != 0:
            raise ValueError(
                "hidden_dim must be divisible by num_heads"
            )

        head_dim = hidden_dim // num_heads

    if head_dim <= 0:
        raise ValueError("head_dim must be > 0")

    costs: list[OpCost] = []

    # Q/K/V projections.
    for projection in ("q", "k", "v"):
        costs.append(
            linear_cost(
                tokens=tokens,
                input_dim=hidden_dim,
                output_dim=hidden_dim,
                input_bits=input_bits,
                output_bits=output_bits,
                compute=compute,
                memory=memory,
                name=f"attention_{projection}",
            )
        )

    # Q @ K^T
    qk_macs = (
        num_heads
        * tokens
        * tokens
        * head_dim
    )

    qk_input_bytes = (
        tensor_bytes(
            (num_heads, tokens, head_dim),
            input_bits,
        )
        * 2
    )

    qk_output_bytes = tensor_bytes(
        (num_heads, tokens, tokens),
        output_bits,
    )

    costs.append(
        _custom_cost(
            name="attention_qk",
            op_type=OpType.ATTENTION,
            macs=qk_macs,
            input_bytes=qk_input_bytes,
            output_bytes=qk_output_bytes,
            compute=compute,
            memory=memory,
        )
    )

    # Softmax is approximated as one elementwise operation per score.
    softmax_elements = (
        num_heads
        * tokens
        * tokens
    )

    costs.append(
        _custom_cost(
            name="attention_softmax",
            op_type=OpType.SOFTMAX,
            macs=0,
            input_bytes=tensor_bytes(
                (num_heads, tokens, tokens),
                output_bits,
            ),
            output_bytes=tensor_bytes(
                (num_heads, tokens, tokens),
                output_bits,
            ),
            compute=compute,
            memory=memory,
            elementwise_operations=softmax_elements,
        )
    )

    # Attention probabilities @ V.
    av_macs = (
        num_heads
        * tokens
        * tokens
        * head_dim
    )

    av_input_bytes = (
        tensor_bytes(
            (num_heads, tokens, tokens),
            output_bits,
        )
        + tensor_bytes(
            (num_heads, tokens, head_dim),
            input_bits,
        )
    )

    av_output_bytes = tensor_bytes(
        (num_heads, tokens, head_dim),
        output_bits,
    )

    costs.append(
        _custom_cost(
            name="attention_av",
            op_type=OpType.ATTENTION,
            macs=av_macs,
            input_bytes=av_input_bytes,
            output_bytes=av_output_bytes,
            compute=compute,
            memory=memory,
        )
    )

    # Output projection.
    costs.append(
        linear_cost(
            tokens=tokens,
            input_dim=hidden_dim,
            output_dim=hidden_dim,
            input_bits=input_bits,
            output_bits=output_bits,
            compute=compute,
            memory=memory,
            name="attention_output",
        )
    )

    return combine_costs(
        costs,
        name="attention",
        op_type=OpType.ATTENTION,
    )


# ---------------------------------------------------------------------------
# Custom operation
# ---------------------------------------------------------------------------

def _custom_cost(
    name: str,
    op_type: OpType,
    macs: int,
    input_bytes: int,
    output_bytes: int,
    compute: ComputeArray | None,
    memory: Memory | None,
    elementwise_operations: int = 0,
) -> OpCost:
    """
    Internal helper for operations that don't fit a normal matrix multiply.
    """

    total_compute_ops = macs + elementwise_operations

    compute_cycles = 0

    if compute is not None and total_compute_ops > 0:
        compute_cycles = compute.cycles_for_macs(
            total_compute_ops
        )

    memory_read_cycles = 0
    memory_write_cycles = 0

    if memory is not None:
        memory_read_cycles = (
            input_bytes
            + memory.read_bandwidth_bytes_per_cycle
            - 1
        ) // memory.read_bandwidth_bytes_per_cycle

        memory_write_cycles = (
            output_bytes
            + memory.write_bandwidth_bytes_per_cycle
            - 1
        ) // memory.write_bandwidth_bytes_per_cycle

    return OpCost(
        name=name,
        op_type=op_type,
        macs=total_compute_ops,
        input_bytes=input_bytes,
        output_bytes=output_bytes,
        compute_cycles=compute_cycles,
        memory_read_cycles=memory_read_cycles,
        memory_write_cycles=memory_write_cycles,
    )


# ---------------------------------------------------------------------------
# Cost aggregation
# ---------------------------------------------------------------------------

def combine_costs(
    costs: list[OpCost],
    name: str = "combined",
    op_type: OpType = OpType.CUSTOM,
) -> OpCost:
    """
    Combine multiple operation costs into one aggregate cost.
    """

    if not costs:
        raise ValueError("costs cannot be empty")

    return OpCost(
        name=name,
        op_type=op_type,
        macs=sum(cost.macs for cost in costs),
        input_bytes=sum(
            cost.input_bytes
            for cost in costs
        ),
        output_bytes=sum(
            cost.output_bytes
            for cost in costs
        ),
        compute_cycles=sum(
            cost.compute_cycles
            for cost in costs
        ),
        memory_read_cycles=sum(
            cost.memory_read_cycles
            for cost in costs
        ),
        memory_write_cycles=sum(
            cost.memory_write_cycles
            for cost in costs
        ),
    )


# ---------------------------------------------------------------------------
# Formatting
# ---------------------------------------------------------------------------

def format_cost(cost: OpCost) -> str:
    """Human-readable operation report."""

    return (
        f"{cost.name}\n"
        f"  type:                {cost.op_type.value}\n"
        f"  MACs:                {cost.macs:,}\n"
        f"  input:               {cost.input_bytes:,} bytes\n"
        f"  output:              {cost.output_bytes:,} bytes\n"
        f"  total memory:        "
        f"{cost.total_memory_bytes:,} bytes\n"
        f"  compute cycles:      "
        f"{cost.compute_cycles:,}\n"
        f"  memory read cycles:  "
        f"{cost.memory_read_cycles:,}\n"
        f"  memory write cycles: "
        f"{cost.memory_write_cycles:,}\n"
        f"  arithmetic intensity:"
        f" {cost.arithmetic_intensity:.4f} MAC/byte\n"
        f"  serial cycles:       "
        f"{cost.total_cycles_serial:,}"
    )
