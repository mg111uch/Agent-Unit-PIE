"""VSE Transformer layer + KVCache — split from transformer.py."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Optional

from vse.core.compute import ComputeArray
from vse.core.memory import Memory
from vse.models.config import TransformerConfig
from vse.models.ops import OpCost, attention_cost, combine_costs, linear_cost, mlp_cost, tensor_bytes


@dataclass
class TransformerLayerCost:
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
        return self.attention.macs + self.mlp.macs

    @property
    def input_bytes(self) -> int:
        return self.attention.input_bytes + self.mlp.input_bytes + self.kv_read_bytes

    @property
    def output_bytes(self) -> int:
        return self.attention.output_bytes + self.mlp.output_bytes + self.kv_write_bytes

    @property
    def total_memory_bytes(self) -> int:
        return self.input_bytes + self.output_bytes + self.normalization_bytes

    @property
    def compute_cycles(self) -> int:
        return self.attention.compute_cycles + self.mlp.compute_cycles

    @property
    def memory_cycles(self) -> int:
        return self.attention.total_memory_cycles + self.mlp.total_memory_cycles

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


class KVCache:
    def __init__(self, config: TransformerConfig, num_layers: int, max_sequence_length: int):
        if num_layers <= 0:
            raise ValueError("num_layers must be > 0")
        if max_sequence_length <= 0:
            raise ValueError("max_sequence_length must be > 0")
        self.config = config
        self.num_layers = num_layers
        self.max_sequence_length = max_sequence_length

    def bytes_per_token_per_layer(self) -> int:
        elements = 2 * self.config.num_heads * self.config.head_dim
        return (elements * self.config.kv_bits + 7) // 8

    def total_bytes(self, sequence_length: Optional[int] = None) -> int:
        if sequence_length is None:
            sequence_length = self.max_sequence_length
        if sequence_length < 0:
            raise ValueError("sequence_length must be >= 0")
        if sequence_length > self.max_sequence_length:
            raise ValueError("sequence_length exceeds cache capacity")
        return self.num_layers * sequence_length * self.bytes_per_token_per_layer()

    def read_bytes_for_decode(self, sequence_length: int) -> int:
        if sequence_length < 0:
            raise ValueError("sequence_length must be >= 0")
        return sequence_length * self.bytes_per_token_per_layer()

    def write_bytes_for_token(self) -> int:
        return self.bytes_per_token_per_layer()


class TransformerLayer:
    def __init__(self, config: TransformerConfig, compute: Optional[ComputeArray] = None, memory: Optional[Memory] = None, name: str = "transformer_layer"):
        self.config = config
        self.compute = compute
        self.memory = memory
        self.name = name

    def prefill_cost(self, sequence_length: int) -> TransformerLayerCost:
        if sequence_length <= 0:
            raise ValueError("sequence_length must be > 0")
        attention = attention_cost(tokens=sequence_length, hidden_dim=self.config.hidden_dim, num_heads=self.config.num_heads, head_dim=self.config.head_dim, compute=self.compute, memory=self.memory, input_bits=self.config.activation_bits, output_bits=self.config.activation_bits)
        mlp = mlp_cost(tokens=sequence_length, hidden_dim=self.config.hidden_dim, intermediate_dim=self.config.intermediate_dim, compute=self.compute, memory=self.memory, input_bits=self.config.activation_bits, weight_bits=self.config.weight_bits, output_bits=self.config.activation_bits, gated=self.config.gated_mlp)
        normalization_bytes = 2 * tensor_bytes((sequence_length, self.config.hidden_dim), self.config.activation_bits)
        return TransformerLayerCost(name=f"{self.name}:prefill", tokens=sequence_length, sequence_length=sequence_length, attention=attention, mlp=mlp, kv_read_bytes=0, kv_write_bytes=sequence_length * (tensor_bytes((self.config.num_heads, self.config.head_dim), self.config.kv_bits) * 2), normalization_bytes=normalization_bytes)

    def decode_cost(self, sequence_length: int) -> TransformerLayerCost:
        if sequence_length < 0:
            raise ValueError("sequence_length must be >= 0")
        projection_costs = []
        for projection in ("q", "k", "v"):
            projection_costs.append(linear_cost(tokens=1, input_dim=self.config.hidden_dim, output_dim=self.config.hidden_dim, input_bits=self.config.activation_bits, weight_bits=self.config.weight_bits, output_bits=self.config.activation_bits, compute=self.compute, memory=self.memory, name=f"decode_{projection}"))
        attention_score_macs = self.config.num_heads * sequence_length * self.config.head_dim
        attention_value_macs = attention_score_macs
        attention_score_input_bytes = tensor_bytes((self.config.num_heads, 1, self.config.head_dim), self.config.activation_bits) + tensor_bytes((self.config.num_heads, sequence_length, self.config.head_dim), self.config.kv_bits)
        attention_score_output_bytes = tensor_bytes((self.config.num_heads, 1, sequence_length), self.config.activation_bits)
        score_cost = OpCost(name="decode_attention_score", op_type=__import__("vse.models.ops", fromlist=["OpType"]).OpType.ATTENTION, macs=attention_score_macs, input_bytes=attention_score_input_bytes, output_bytes=attention_score_output_bytes, compute_cycles=self.compute.cycles_for_macs(attention_score_macs) if self.compute is not None else 0, memory_read_cycles=(attention_score_input_bytes + self.memory.read_bandwidth_bytes_per_cycle - 1) // self.memory.read_bandwidth_bytes_per_cycle if self.memory is not None else 0, memory_write_cycles=(attention_score_output_bytes + self.memory.write_bandwidth_bytes_per_cycle - 1) // self.memory.write_bandwidth_bytes_per_cycle if self.memory is not None else 0)
        value_input_bytes = tensor_bytes((self.config.num_heads, 1, sequence_length), self.config.activation_bits) + tensor_bytes((self.config.num_heads, sequence_length, self.config.head_dim), self.config.kv_bits)
        value_output_bytes = tensor_bytes((self.config.num_heads, 1, self.config.head_dim), self.config.activation_bits)
        value_cost = OpCost(name="decode_attention_value", op_type=__import__("vse.models.ops", fromlist=["OpType"]).OpType.ATTENTION, macs=attention_value_macs, input_bytes=value_input_bytes, output_bytes=value_output_bytes, compute_cycles=self.compute.cycles_for_macs(attention_value_macs) if self.compute is not None else 0, memory_read_cycles=(value_input_bytes + self.memory.read_bandwidth_bytes_per_cycle - 1) // self.memory.read_bandwidth_bytes_per_cycle if self.memory is not None else 0, memory_write_cycles=(value_output_bytes + self.memory.write_bandwidth_bytes_per_cycle - 1) // self.memory.write_bandwidth_bytes_per_cycle if self.memory is not None else 0)
        attention = combine_costs(projection_costs + [score_cost, value_cost] + [linear_cost(tokens=1, input_dim=self.config.hidden_dim, output_dim=self.config.hidden_dim, input_bits=self.config.activation_bits, weight_bits=self.config.weight_bits, output_bits=self.config.activation_bits, compute=self.compute, memory=self.memory, name="decode_attention_output")], name="decode_attention")
        mlp = mlp_cost(tokens=1, hidden_dim=self.config.hidden_dim, intermediate_dim=self.config.intermediate_dim, compute=self.compute, memory=self.memory, input_bits=self.config.activation_bits, weight_bits=self.config.weight_bits, output_bits=self.config.activation_bits, gated=self.config.gated_mlp)
        kv_cache_read = sequence_length * (tensor_bytes((self.config.num_heads, self.config.head_dim), self.config.kv_bits) * 2)
        kv_cache_write = tensor_bytes((self.config.num_heads, self.config.head_dim), self.config.kv_bits) * 2
        normalization_bytes = 2 * tensor_bytes((1, self.config.hidden_dim), self.config.activation_bits)
        return TransformerLayerCost(name=f"{self.name}:decode", tokens=1, sequence_length=sequence_length, attention=attention, mlp=mlp, kv_read_bytes=kv_cache_read, kv_write_bytes=kv_cache_write, normalization_bytes=normalization_bytes)
