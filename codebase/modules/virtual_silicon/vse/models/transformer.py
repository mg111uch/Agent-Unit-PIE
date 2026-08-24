"""Transformer workload — facade (split for <500 LOC)."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Optional

from vse.core.compute import ComputeArray
from vse.core.memory import Memory
from vse.models.config import TransformerConfig
from vse.models.layer import KVCache, TransformerLayer, TransformerLayerCost

__all__ = ["TransformerConfig", "TransformerLayerCost", "KVCache", "TransformerLayer", "TransformerWorkloadCost", "TransformerModel"]


@dataclass
class TransformerWorkloadCost:
    layers: int
    tokens: int
    sequence_length: int
    layer_cost: TransformerLayerCost

    @property
    def macs(self) -> int:
        return self.layer_cost.macs * self.layers

    @property
    def memory_bytes(self) -> int:
        return self.layer_cost.total_memory_bytes * self.layers

    @property
    def compute_cycles(self) -> int:
        return self.layer_cost.compute_cycles * self.layers

    @property
    def memory_cycles(self) -> int:
        return self.layer_cost.memory_cycles * self.layers

    def report(self) -> dict:
        return {"layers": self.layers, "tokens": self.tokens, "sequence_length": self.sequence_length, "total_macs": self.macs, "total_memory_bytes": self.memory_bytes, "compute_cycles": self.compute_cycles, "memory_cycles": self.memory_cycles, "arithmetic_intensity": self.macs / self.memory_bytes if self.memory_bytes else 0.0}


class TransformerModel:
    def __init__(self, config: TransformerConfig, num_layers: int, compute: Optional[ComputeArray] = None, memory: Optional[Memory] = None):
        if num_layers <= 0:
            raise ValueError("num_layers must be > 0")
        self.config = config
        self.num_layers = num_layers
        self.layer = TransformerLayer(config=config, compute=compute, memory=memory)

    def prefill_cost(self, sequence_length: int) -> TransformerWorkloadCost:
        layer_cost = self.layer.prefill_cost(sequence_length)
        return TransformerWorkloadCost(layers=self.num_layers, tokens=sequence_length, sequence_length=sequence_length, layer_cost=layer_cost)

    def decode_cost(self, sequence_length: int) -> TransformerWorkloadCost:
        layer_cost = self.layer.decode_cost(sequence_length)
        return TransformerWorkloadCost(layers=self.num_layers, tokens=1, sequence_length=sequence_length, layer_cost=layer_cost)

    def parameter_bytes(self) -> int:
        hidden = self.config.hidden_dim
        intermediate = self.config.intermediate_dim
        attention_params = 4 * hidden * hidden
        mlp_projections = 3 if self.config.gated_mlp else 2
        mlp_params = mlp_projections * hidden * intermediate
        total_params = (attention_params + mlp_params) * self.num_layers
        return (total_params * self.config.weight_bits + 7) // 8

    def parameter_count(self) -> int:
        hidden = self.config.hidden_dim
        intermediate = self.config.intermediate_dim
        attention_params = 4 * hidden * hidden
        mlp_projections = 3 if self.config.gated_mlp else 2
        mlp_params = mlp_projections * hidden * intermediate
        return (attention_params + mlp_params) * self.num_layers
