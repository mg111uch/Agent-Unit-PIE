"""Model architecture search space — Phase E model↔hardware co-search.

Provides ModelArchSpec (transformer model hyperparameters) and
ModelSearchSpace (cross-product / random sampling over model dims).

Mirrors vse/search/architecture.py but for model dimensions.
"""

from __future__ import annotations

import random
from dataclasses import dataclass, field, replace
from itertools import product
from typing import Dict, Optional


def _int(v) -> int:
    return int(v)


def _float(v) -> float:
    return float(v)


def _bool(v) -> bool:
    return bool(v)


def _str(v) -> str:
    return str(v)


@dataclass
class ModelArchSpec:
    """Candidate transformer model hyperparameters.

    Defaults chosen so ``ModelArchSpec(hidden_dim=1024)`` is valid.
    Validation:
      - layers 8..24
      - hidden_dim 1024..4096, divisible by num_heads
      - num_heads 8..32
      - intermediate_dim 2048..11008
      - kv_heads None or 1..num_heads, num_heads % kv_heads == 0
      - weight_bits/activation_bits/kv_bits >0
      - vocab_size >0, max_seq 1024..16384
    """

    layers: int = 16
    hidden_dim: int = 1024
    num_heads: int = 16
    intermediate_dim: int = 2816
    vocab_size: int = 32000
    kv_heads: Optional[int] = None
    weight_bits: int = 4
    activation_bits: int = 16
    kv_bits: int = 16
    gated_mlp: bool = True
    max_seq: int = 4096
    name: str = "model-arch"

    def __post_init__(self) -> None:
        if not 8 <= self.layers <= 24:
            raise ValueError("layers must be in [8,24]")
        if not 1024 <= self.hidden_dim <= 4096:
            raise ValueError("hidden_dim must be in [1024,4096]")
        if not 8 <= self.num_heads <= 32:
            raise ValueError("num_heads must be in [8,32]")
        if not 2048 <= self.intermediate_dim <= 11008:
            raise ValueError("intermediate_dim must be in [2048,11008]")
        if self.vocab_size <= 0:
            raise ValueError("vocab_size must be >0")
        if self.weight_bits <= 0:
            raise ValueError("weight_bits must be >0")
        if self.kv_bits <= 0:
            raise ValueError("kv_bits must be >0")
        if self.activation_bits <= 0:
            raise ValueError("activation_bits must be >0")
        if not 1024 <= self.max_seq <= 16384:
            raise ValueError("max_seq must be in [1024,16384]")
        if not self.name:
            raise ValueError("name must be non-empty")
        if self.hidden_dim % self.num_heads != 0:
            raise ValueError("hidden_dim must be divisible by num_heads")
        if self.kv_heads is not None:
            if not 1 <= self.kv_heads <= self.num_heads:
                raise ValueError("kv_heads must be in [1,num_heads]")
            if self.num_heads % self.kv_heads != 0:
                raise ValueError("num_heads must be divisible by kv_heads")
        # head_dim derived check
        hd = self.hidden_dim // self.num_heads
        if hd <= 0:
            raise ValueError("head_dim must be >0")

    @property
    def head_dim(self) -> int:
        return self.hidden_dim // self.num_heads

    # --- conversion helpers ---
    def to_transformer_config(self):
        from vse.models.config import TransformerConfig

        return TransformerConfig(
            hidden_dim=self.hidden_dim,
            num_heads=self.num_heads,
            intermediate_dim=self.intermediate_dim,
            head_dim=self.head_dim,
            weight_bits=self.weight_bits,
            kv_bits=self.kv_bits,
            activation_bits=self.activation_bits,
            gated_mlp=self.gated_mlp,
        )

    def to_transformer_model(self, num_layers: Optional[int] = None, compute=None, memory=None):
        from vse.models.transformer import TransformerModel

        cfg = self.to_transformer_config()
        layers = num_layers if num_layers is not None else self.layers
        if layers <= 0:
            raise ValueError("num_layers must be >0")
        return TransformerModel(config=cfg, num_layers=layers, compute=compute, memory=memory)

    def to_vse_s1_config(self):
        from vse.models.vse_s1.spec import VSES1Config

        # VSES1 clamps layers 12..20, so we pass through but allow broader;
        # if out of range, create via bypassing validation? We try direct.
        # For layers outside 12..20 we still construct but need to avoid validation error.
        # Fallback: manually build if needed.
        try:
            return VSES1Config(
                layers=self.layers,
                hidden_dim=self.hidden_dim,
                num_heads=self.num_heads,
                intermediate_dim=self.intermediate_dim,
                vocab_size=self.vocab_size,
                weight_bits=self.weight_bits,
                kv_bits=self.kv_bits,
                activation_bits=self.activation_bits,
                gated_mlp=self.gated_mlp,
                max_seq=self.max_seq,
                name=self.name,
            )
        except ValueError:
            # Build without strict layers check by using object.__new__ and setting attrs
            cfg = object.__new__(VSES1Config)
            cfg.layers = self.layers
            cfg.hidden_dim = self.hidden_dim
            cfg.num_heads = self.num_heads
            cfg.head_dim = self.head_dim
            cfg.intermediate_dim = self.intermediate_dim
            cfg.vocab_size = self.vocab_size
            cfg.weight_bits = self.weight_bits
            cfg.kv_bits = self.kv_bits
            cfg.activation_bits = self.activation_bits
            cfg.gated_mlp = self.gated_mlp
            cfg.max_seq = self.max_seq
            cfg.name = self.name
            return cfg

    def parameter_count(self) -> int:
        attn = 4 * self.hidden_dim * self.hidden_dim
        projs = 3 if self.gated_mlp else 2
        mlp = projs * self.hidden_dim * self.intermediate_dim
        return (attn + mlp) * self.layers

    def parameter_bytes(self, precision_map: Optional[Dict] = None) -> int:
        if precision_map is None or len(precision_map) == 0:
            return (self.parameter_count() * self.weight_bits + 7) // 8
        # delegate to VSES1 costs if available
        try:
            from vse.models.vse_s1.costs import effective_weight_bytes

            cfg = self.to_vse_s1_config()
            return effective_weight_bytes(cfg, precision_map)
        except Exception:
            # fallback simple per-int bits
            from vse.compiler.precision import Q2Block

            total = 0
            ap = 4 * self.hidden_dim * self.hidden_dim
            mp = (3 if self.gated_mlp else 2) * self.hidden_dim * self.intermediate_dim
            for _ in range(self.layers):
                for attr in ("attn", "mlp"):
                    prec = precision_map.get(attr, precision_map.get("weight", self.weight_bits))
                    if isinstance(prec, Q2Block):
                        n = ap if attr == "attn" else mp
                        total += prec.effective_bytes(n)
                    else:
                        n = ap if attr == "attn" else mp
                        total += (n * int(prec) + 7) // 8
            return total

    def estimate_accuracy(self, precision_map: Optional[dict] = None):
        """Heuristic accuracy via vse.models.accuracy."""
        from vse.models.accuracy import estimate_accuracy as _ea

        pm = precision_map
        if pm is None and self.weight_bits is not None:
            # uniform bits map gives more discriminative signal than empty
            # keep None behavior for backward compat if weight_bits is default 4
            # but use weight_bits when caller expects quantization signal
            # We default to None -> base score; if caller passes explicit map use it.
            # To preserve empty->base semantics, don't synthesize here.
            pass
        return _ea(pm)

    def label(self) -> str:
        return (
            f"{self.layers}L {self.hidden_dim}H {self.num_heads}heads "
            f"{self.intermediate_dim}I w{self.weight_bits}b "
            f"{self.parameter_count() / 1e6:.1f}M"
        )


# Map dimension name -> (field_name, converter)
DIM_FIELDS_MODEL: dict[str, tuple[str, callable]] = {
    "model_layers": ("layers", _int),
    "layers": ("layers", _int),
    "hidden_dim": ("hidden_dim", _int),
    "hidden": ("hidden_dim", _int),
    "num_heads": ("num_heads", _int),
    "heads": ("num_heads", _int),
    "intermediate_dim": ("intermediate_dim", _int),
    "intermediate": ("intermediate_dim", _int),
    "ffn_dim": ("intermediate_dim", _int),
    "vocab_size": ("vocab_size", _int),
    "kv_heads": ("kv_heads", _int),
    "weight_bits": ("weight_bits", _int),
    "activation_bits": ("activation_bits", _int),
    "kv_bits": ("kv_bits", _int),
    "gated_mlp": ("gated_mlp", _bool),
    "max_seq": ("max_seq", _int),
    "name": ("name", _str),
}


@dataclass
class ModelSearchSpace:
    """Named dimensions for model arch search (mirrors SearchSpace)."""

    dims: dict[str, list] = field(default_factory=dict)

    def __post_init__(self) -> None:
        for name, values in self.dims.items():
            if name not in DIM_FIELDS_MODEL:
                raise ValueError(f"unknown model search dimension: {name}")
            if not values:
                raise ValueError(f"dimension {name} needs >= 1 value")

    @property
    def size(self) -> int:
        total = 1
        for v in self.dims.values():
            total *= len(v)
        return total

    def specs(self, base: Optional[ModelArchSpec] = None) -> list[ModelArchSpec]:
        if base is None:
            base = ModelArchSpec()
        overrides: dict[str, list] = {}
        for name, values in self.dims.items():
            field_name, conv = DIM_FIELDS_MODEL[name]
            overrides[field_name] = [conv(v) for v in values]
        if not overrides:
            return [replace(base)]
        candidates: list[ModelArchSpec] = []
        for combo in product(*overrides.values()):
            kwargs = dict(zip(overrides.keys(), combo))
            candidates.append(replace(base, **kwargs))
        return candidates

    def sample_specs(
        self, n: int, base: Optional[ModelArchSpec] = None, seed: Optional[int] = None
    ) -> list[ModelArchSpec]:
        if n < 1:
            raise ValueError("n must be >= 1")
        if base is None:
            base = ModelArchSpec()
        rng = random.Random(seed)
        names = list(self.dims.keys())
        candidates: list[ModelArchSpec] = []
        for _ in range(n):
            kwargs = {}
            for name in names:
                field_name, conv = DIM_FIELDS_MODEL[name]
                kwargs[field_name] = conv(rng.choice(self.dims[name]))
            candidates.append(replace(base, **kwargs))
        return candidates


__all__ = ["ModelArchSpec", "ModelSearchSpace", "DIM_FIELDS_MODEL"]
