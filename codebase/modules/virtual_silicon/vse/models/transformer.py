"""
VSE - Virtual Silicon Engine
vse/transformer.py

Transformer workload model for the Virtual Silicon Engine.

MVP scope:
    - Decoder-only Transformer layer
    - Prefill workload
    - Single-token decode workload
    - Q/K/V/O projections
    - Attention
    - MLP
    - KV-cache traffic
    - INT4/FP4 weight-size estimation
    - Hardware cost estimation

This module does NOT perform neural-network inference.

It converts a Transformer architecture into a workload that VSE can
execute on its virtual compute and memory hardware.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Optional

from vse.core.compute import ComputeArray
from vse.core.memory import Memory
from vse.models.ops import (
    OpCost,
    attention_cost,
    combine_costs,
    linear_cost,
    mlp_cost,
    tensor_bytes,
)


# ---------------------------------------------------------------------------
# Transformer configuration
# ---------------------------------------------------------------------------

@dataclass
class TransformerConfig:
    """
    Architecture of one decoder Transformer layer.

    hidden_dim:
        Model embedding/hidden dimension.

    num_heads:
        Number of attention heads.

    head_dim:
        Dimension of each attention head.

    intermediate_dim:
        MLP intermediate dimension.

    weight_bits:
        Weight precision.

    activation_bits:
        Activation precision.

    kv_bits:
        KV-cache precision.

    gated_mlp:
        Whether the MLP uses a gate projection.

    use_bias:
        Currently informational only.
    """

    hidden_dim: int
    num_heads: int
    intermediate_dim: int

    head_dim: Optional[int] = None

    weight_bits: int = 4
    activation_bits: int = 16
    kv_bits: int = 16

    gated_mlp: bool = True
    use_bias: bool = False

    def __post_init__(self) -> None:
        if self.hidden_dim <= 0:
            raise ValueError("hidden_dim must be > 0")

        if self.num_heads <= 0:
            raise ValueError("num_heads must be > 0")

        if self.intermediate_dim <= 0:
            raise ValueError(
                "intermediate_dim must be > 0"
            )

        if self.head_dim is None:
            if self.hidden_dim % self.num_heads != 0:
                raise ValueError(
                    "hidden_dim must be divisible by num_heads "
                    "when head_dim is not specified"
                )

            self.head_dim = (
                self.hidden_dim // self.num_heads
            )

        if self.head_dim <= 0:
            raise ValueError("head_dim must be > 0")

        if self.weight_bits <= 0:
            raise ValueError("weight_bits must be > 0")

        if self.activation_bits <= 0:
            raise ValueError(
                "activation_bits must be > 0"
            )

        if self.kv_bits <= 0:
            raise ValueError("kv_bits must be > 0")


# ---------------------------------------------------------------------------
# Layer cost
# ---------------------------------------------------------------------------

@dataclass
class TransformerLayerCost:
    """
    Aggregate cost of one Transformer layer.
    """

    name: str

    tokens: int
    sequence_length: int

    attention: OpCost
    mlp: OpCost

    kv_read_bytes: int = 0
    kv_write_bytes: int = 0

    normalization_bytes: int = 0

    @property
    def macs(self) -> int:
        return (
            self.attention.macs
            + self.mlp.macs
        )

    @property
    def input_bytes(self) -> int:
        return (
            self.attention.input_bytes
            + self.mlp.input_bytes
            + self.kv_read_bytes
        )

    @property
    def output_bytes(self) -> int:
        return (
            self.attention.output_bytes
            + self.mlp.output_bytes
            + self.kv_write_bytes
        )

    @property
    def total_memory_bytes(self) -> int:
        return (
            self.input_bytes
            + self.output_bytes
            + self.normalization_bytes
        )

    @property
    def compute_cycles(self) -> int:
        return (
            self.attention.compute_cycles
            + self.mlp.compute_cycles
        )

    @property
    def memory_cycles(self) -> int:
        return (
            self.attention.total_memory_cycles
            + self.mlp.total_memory_cycles
        )

    @property
    def arithmetic_intensity(self) -> float:
        if self.total_memory_bytes == 0:
            return 0.0

        return self.macs / self.total_memory_bytes

    def report(self) -> dict:
        return {
            "name": self.name,
            "tokens": self.tokens,
            "sequence_length": self.sequence_length,
            "macs": self.macs,
            "attention_macs": self.attention.macs,
            "mlp_macs": self.mlp.macs,
            "kv_read_bytes": self.kv_read_bytes,
            "kv_write_bytes": self.kv_write_bytes,
            "normalization_bytes": self.normalization_bytes,
            "total_memory_bytes": self.total_memory_bytes,
            "compute_cycles": self.compute_cycles,
            "memory_cycles": self.memory_cycles,
            "arithmetic_intensity": self.arithmetic_intensity,
        }


# ---------------------------------------------------------------------------
# KV cache
# ---------------------------------------------------------------------------

class KVCache:
    """
    Architectural KV-cache model.

    This stores only metadata/capacity information.

    No actual key/value tensors are allocated.

    For a decoder model:

        K = [layers, sequence, heads, head_dim]
        V = [layers, sequence, heads, head_dim]
    """

    def __init__(
        self,
        config: TransformerConfig,
        num_layers: int,
        max_sequence_length: int,
    ):
        if num_layers <= 0:
            raise ValueError("num_layers must be > 0")

        if max_sequence_length <= 0:
            raise ValueError(
                "max_sequence_length must be > 0"
            )

        self.config = config
        self.num_layers = num_layers
        self.max_sequence_length = max_sequence_length

    # ------------------------------------------------------------------
    # Size
    # ------------------------------------------------------------------

    def bytes_per_token_per_layer(self) -> int:
        """
        Bytes added to the KV cache by one token.

        K + V:

            2 × heads × head_dim × kv_bits
        """

        elements = (
            2
            * self.config.num_heads
            * self.config.head_dim
        )

        return (
            elements * self.config.kv_bits + 7
        ) // 8

    def total_bytes(
        self,
        sequence_length: Optional[int] = None,
    ) -> int:
        """
        Total KV-cache storage.
        """

        if sequence_length is None:
            sequence_length = self.max_sequence_length

        if sequence_length < 0:
            raise ValueError(
                "sequence_length must be >= 0"
            )

        if sequence_length > self.max_sequence_length:
            raise ValueError(
                "sequence_length exceeds cache capacity"
            )

        return (
            self.num_layers
            * sequence_length
            * self.bytes_per_token_per_layer()
        )

    def read_bytes_for_decode(
        self,
        sequence_length: int,
    ) -> int:
        """
        KV bytes read by one decoding layer for one new token.

        Both K and V for all previous positions are read.
        """

        if sequence_length < 0:
            raise ValueError(
                "sequence_length must be >= 0"
            )

        return (
            sequence_length
            * self.bytes_per_token_per_layer()
        )

    def write_bytes_for_token(self) -> int:
        """
        KV bytes written when adding one new token.
        """

        return self.bytes_per_token_per_layer()


# ---------------------------------------------------------------------------
# Transformer Layer
# ---------------------------------------------------------------------------

class TransformerLayer:
    """
    One decoder-only Transformer layer.

    Example:

        config = TransformerConfig(
            hidden_dim=4096,
            num_heads=32,
            intermediate_dim=11008,
        )

        layer = TransformerLayer(
            config,
            compute=compute,
            memory=memory,
        )

        cost = layer.decode_cost(
            sequence_length=4096
        )
    """

    def __init__(
        self,
        config: TransformerConfig,
        compute: Optional[ComputeArray] = None,
        memory: Optional[Memory] = None,
        name: str = "transformer_layer",
    ):
        self.config = config
        self.compute = compute
        self.memory = memory
        self.name = name

    # ------------------------------------------------------------------
    # Prefill
    # ------------------------------------------------------------------

    def prefill_cost(
        self,
        sequence_length: int,
    ) -> TransformerLayerCost:
        """
        Estimate cost of processing a prompt.

        This treats the entire prompt as a token batch.
        """

        if sequence_length <= 0:
            raise ValueError(
                "sequence_length must be > 0"
            )

        attention = attention_cost(
            tokens=sequence_length,
            hidden_dim=self.config.hidden_dim,
            num_heads=self.config.num_heads,
            head_dim=self.config.head_dim,
            compute=self.compute,
            memory=self.memory,
            input_bits=self.config.activation_bits,
            output_bits=self.config.activation_bits,
        )

        mlp = mlp_cost(
            tokens=sequence_length,
            hidden_dim=self.config.hidden_dim,
            intermediate_dim=self.config.intermediate_dim,
            compute=self.compute,
            memory=self.memory,
            input_bits=self.config.activation_bits,
            weight_bits=self.config.weight_bits,
            output_bits=self.config.activation_bits,
            gated=self.config.gated_mlp,
        )

        # Approximate normalization/residual traffic.
        normalization_bytes = (
            2
            * tensor_bytes(
                (
                    sequence_length,
                    self.config.hidden_dim,
                ),
                self.config.activation_bits,
            )
        )

        return TransformerLayerCost(
            name=f"{self.name}:prefill",
            tokens=sequence_length,
            sequence_length=sequence_length,
            attention=attention,
            mlp=mlp,
            kv_read_bytes=0,
            kv_write_bytes=(
                sequence_length
                * (
                    tensor_bytes(
                        (
                            self.config.num_heads,
                            self.config.head_dim,
                        ),
                        self.config.kv_bits,
                    )
                    * 2
                )
            ),
            normalization_bytes=normalization_bytes,
        )

    # ------------------------------------------------------------------
    # Decode
    # ------------------------------------------------------------------

    def decode_cost(
        self,
        sequence_length: int,
    ) -> TransformerLayerCost:
        """
        Estimate cost of generating ONE new token.

        sequence_length represents the number of existing tokens
        already present in the KV cache.

        This is the important workload for our eventual high-throughput
        fixed-model accelerator.
        """

        if sequence_length < 0:
            raise ValueError(
                "sequence_length must be >= 0"
            )

        # For decode, Q has one token while K/V cover the entire context.

        # Q/K/V projections for one token.
        projection_costs = []

        for projection in ("q", "k", "v"):
            projection_costs.append(
                linear_cost(
                    tokens=1,
                    input_dim=self.config.hidden_dim,
                    output_dim=self.config.hidden_dim,
                    input_bits=self.config.activation_bits,
                    weight_bits=self.config.weight_bits,
                    output_bits=self.config.activation_bits,
                    compute=self.compute,
                    memory=self.memory,
                    name=f"decode_{projection}",
                )
            )

        # Attention score:
        #
        # Q [heads, 1, head_dim]
        # K [heads, sequence, head_dim]
        #
        # MACs = heads × sequence × head_dim
        attention_score_macs = (
            self.config.num_heads
            * sequence_length
            * self.config.head_dim
        )

        # Attention weighted V:
        #
        # scores [heads, 1, sequence]
        # V     [heads, sequence, head_dim]
        #
        # MACs = heads × sequence × head_dim
        attention_value_macs = attention_score_macs

        attention_score_input_bytes = (
            tensor_bytes(
                (
                    self.config.num_heads,
                    1,
                    self.config.head_dim,
                ),
                self.config.activation_bits,
            )
            +
            tensor_bytes(
                (
                    self.config.num_heads,
                    sequence_length,
                    self.config.head_dim,
                ),
                self.config.kv_bits,
            )
        )

        attention_score_output_bytes = tensor_bytes(
            (
                self.config.num_heads,
                1,
                sequence_length,
            ),
            self.config.activation_bits,
        )

        score_cost = OpCost(
            name="decode_attention_score",
            op_type=attention_cost.__annotations__.get(
                "return",
                object,
            ) and __import__(
                "vse.models.ops",
                fromlist=["OpType"],
            ).OpType.ATTENTION,
            macs=attention_score_macs,
            input_bytes=attention_score_input_bytes,
            output_bytes=attention_score_output_bytes,
            compute_cycles=(
                self.compute.cycles_for_macs(
                    attention_score_macs
                )
                if self.compute is not None
                else 0
            ),
            memory_read_cycles=(
                (
                    attention_score_input_bytes
                    + self.memory.read_bandwidth_bytes_per_cycle
                    - 1
                )
                // self.memory.read_bandwidth_bytes_per_cycle
                if self.memory is not None
                else 0
            ),
            memory_write_cycles=(
                (
                    attention_score_output_bytes
                    + self.memory.write_bandwidth_bytes_per_cycle
                    - 1
                )
                // self.memory.write_bandwidth_bytes_per_cycle
                if self.memory is not None
                else 0
            ),
        )

        value_input_bytes = (
            tensor_bytes(
                (
                    self.config.num_heads,
                    1,
                    sequence_length,
                ),
                self.config.activation_bits,
            )
            +
            tensor_bytes(
                (
                    self.config.num_heads,
                    sequence_length,
                    self.config.head_dim,
                ),
                self.config.kv_bits,
            )
        )

        value_output_bytes = tensor_bytes(
            (
                self.config.num_heads,
                1,
                self.config.head_dim,
            ),
            self.config.activation_bits,
        )

        value_cost = OpCost(
            name="decode_attention_value",
            op_type=__import__(
                "vse.models.ops",
                fromlist=["OpType"],
            ).OpType.ATTENTION,
            macs=attention_value_macs,
            input_bytes=value_input_bytes,
            output_bytes=value_output_bytes,
            compute_cycles=(
                self.compute.cycles_for_macs(
                    attention_value_macs
                )
                if self.compute is not None
                else 0
            ),
            memory_read_cycles=(
                (
                    value_input_bytes
                    + self.memory.read_bandwidth_bytes_per_cycle
                    - 1
                )
                // self.memory.read_bandwidth_bytes_per_cycle
                if self.memory is not None
                else 0
            ),
            memory_write_cycles=(
                (
                    value_output_bytes
                    + self.memory.write_bandwidth_bytes_per_cycle
                    - 1
                )
                // self.memory.write_bandwidth_bytes_per_cycle
                if self.memory is not None
                else 0
            ),
        )

        attention = combine_costs(
            projection_costs
            + [score_cost, value_cost]
            + [
                linear_cost(
                    tokens=1,
                    input_dim=self.config.hidden_dim,
                    output_dim=self.config.hidden_dim,
                    input_bits=self.config.activation_bits,
                    weight_bits=self.config.weight_bits,
                    output_bits=self.config.activation_bits,
                    compute=self.compute,
                    memory=self.memory,
                    name="decode_attention_output",
                )
            ],
            name="decode_attention",
        )

        # MLP.
        mlp = mlp_cost(
            tokens=1,
            hidden_dim=self.config.hidden_dim,
            intermediate_dim=self.config.intermediate_dim,
            compute=self.compute,
            memory=self.memory,
            input_bits=self.config.activation_bits,
            weight_bits=self.config.weight_bits,
            output_bits=self.config.activation_bits,
            gated=self.config.gated_mlp,
        )

        kv_cache_read = (
            sequence_length
            * (
                tensor_bytes(
                    (
                        self.config.num_heads,
                        self.config.head_dim,
                    ),
                    self.config.kv_bits,
                )
                * 2
            )
        )

        kv_cache_write = (
            tensor_bytes(
                (
                    self.config.num_heads,
                    self.config.head_dim,
                ),
                self.config.kv_bits,
            )
            * 2
        )

        normalization_bytes = (
            2
            * tensor_bytes(
                (1, self.config.hidden_dim),
                self.config.activation_bits,
            )
        )

        return TransformerLayerCost(
            name=f"{self.name}:decode",
            tokens=1,
            sequence_length=sequence_length,
            attention=attention,
            mlp=mlp,
            kv_read_bytes=kv_cache_read,
            kv_write_bytes=kv_cache_write,
            normalization_bytes=normalization_bytes,
        )


# ---------------------------------------------------------------------------
# Full Transformer workload
# ---------------------------------------------------------------------------

@dataclass
class TransformerWorkloadCost:
    """
    Aggregate cost across all Transformer layers.
    """

    layers: int
    tokens: int
    sequence_length: int

    layer_cost: TransformerLayerCost

    @property
    def macs(self) -> int:
        return self.layer_cost.macs * self.layers

    @property
    def memory_bytes(self) -> int:
        return (
            self.layer_cost.total_memory_bytes
            * self.layers
        )

    @property
    def compute_cycles(self) -> int:
        return (
            self.layer_cost.compute_cycles
            * self.layers
        )

    @property
    def memory_cycles(self) -> int:
        return (
            self.layer_cost.memory_cycles
            * self.layers
        )

    def report(self) -> dict:
        return {
            "layers": self.layers,
            "tokens": self.tokens,
            "sequence_length": self.sequence_length,
            "total_macs": self.macs,
            "total_memory_bytes": self.memory_bytes,
            "compute_cycles": self.compute_cycles,
            "memory_cycles": self.memory_cycles,
            "arithmetic_intensity": (
                self.macs / self.memory_bytes
                if self.memory_bytes
                else 0.0
            ),
        }


class TransformerModel:
    """
    Complete decoder-only Transformer workload model.

    The MVP treats all layers as identical.

    This is sufficient for architectural exploration before introducing
    heterogeneous layers or model-specific hardware mappings.
    """

    def __init__(
        self,
        config: TransformerConfig,
        num_layers: int,
        compute: Optional[ComputeArray] = None,
        memory: Optional[Memory] = None,
    ):
        if num_layers <= 0:
            raise ValueError(
                "num_layers must be > 0"
            )

        self.config = config
        self.num_layers = num_layers

        self.layer = TransformerLayer(
            config=config,
            compute=compute,
            memory=memory,
        )

    def prefill_cost(
        self,
        sequence_length: int,
    ) -> TransformerWorkloadCost:
        layer_cost = self.layer.prefill_cost(
            sequence_length
        )

        return TransformerWorkloadCost(
            layers=self.num_layers,
            tokens=sequence_length,
            sequence_length=sequence_length,
            layer_cost=layer_cost,
        )

    def decode_cost(
        self,
        sequence_length: int,
    ) -> TransformerWorkloadCost:
        layer_cost = self.layer.decode_cost(
            sequence_length
        )

        return TransformerWorkloadCost(
            layers=self.num_layers,
            tokens=1,
            sequence_length=sequence_length,
            layer_cost=layer_cost,
        )

    def parameter_bytes(self) -> int:
        """
        Approximate parameter storage for the model.

        Includes:
            Q/K/V/O projections
            MLP projections

        Embedding and LM head are intentionally excluded from this
        layer-level MVP.
        """

        hidden = self.config.hidden_dim
        intermediate = self.config.intermediate_dim

        # Attention:
        #
        # Q + K + V + O
        attention_params = (
            4 * hidden * hidden
        )

        # MLP:
        #
        # up + down
        # gated MLP adds another up/gate projection.
        mlp_projections = 3 if self.config.gated_mlp else 2

        mlp_params = (
            mlp_projections
            * hidden
            * intermediate
        )

        total_params = (
            attention_params
            + mlp_params
        ) * self.num_layers

        return (
            total_params
            * self.config.weight_bits
            + 7
        ) // 8

    def parameter_count(self) -> int:
        """
        Approximate parameter count represented by the modeled layers.
        """

        hidden = self.config.hidden_dim
        intermediate = self.config.intermediate_dim

        attention_params = 4 * hidden * hidden

        mlp_projections = (
            3 if self.config.gated_mlp else 2
        )

        mlp_params = (
            mlp_projections
            * hidden
            * intermediate
        )

        return (
            attention_params
            + mlp_params
        ) * self.num_layers
