"""MoE config + Expert — split from moe.py."""

from __future__ import annotations

from dataclasses import dataclass


@dataclass
class MoEConfig:
    hidden_dim: int
    intermediate_dim: int
    num_experts: int
    top_k: int = 1
    weight_bits: int = 4
    activation_bits: int = 16
    gated: bool = True

    def __post_init__(self) -> None:
        if self.hidden_dim <= 0:
            raise ValueError("hidden_dim must be > 0")
        if self.intermediate_dim <= 0:
            raise ValueError("intermediate_dim must be > 0")
        if self.num_experts <= 0:
            raise ValueError("num_experts must be > 0")
        if self.top_k <= 0:
            raise ValueError("top_k must be > 0")
        if self.top_k > self.num_experts:
            raise ValueError("top_k cannot exceed num_experts")
        if self.weight_bits <= 0:
            raise ValueError("weight_bits must be > 0")
        if self.activation_bits <= 0:
            raise ValueError("activation_bits must be > 0")


@dataclass
class Expert:
    expert_id: int
    hidden_dim: int
    intermediate_dim: int
    weight_bits: int
    gated: bool = True

    @property
    def projection_count(self) -> int:
        return 3 if self.gated else 2

    @property
    def parameter_count(self) -> int:
        return self.projection_count * self.hidden_dim * self.intermediate_dim

    @property
    def weight_bytes(self) -> int:
        return (self.parameter_count * self.weight_bits + 7) // 8
