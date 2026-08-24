"""VSE TransformerConfig — split from transformer.py for <500 LOC."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Optional


@dataclass
class TransformerConfig:
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
            raise ValueError("intermediate_dim must be > 0")
        if self.head_dim is None:
            if self.hidden_dim % self.num_heads != 0:
                raise ValueError("hidden_dim must be divisible by num_heads when head_dim is not specified")
            self.head_dim = self.hidden_dim // self.num_heads
        if self.head_dim <= 0:
            raise ValueError("head_dim must be > 0")
        if self.weight_bits <= 0:
            raise ValueError("weight_bits must be > 0")
        if self.activation_bits <= 0:
            raise ValueError("activation_bits must be > 0")
        if self.kv_bits <= 0:
            raise ValueError("kv_bits must be > 0")
