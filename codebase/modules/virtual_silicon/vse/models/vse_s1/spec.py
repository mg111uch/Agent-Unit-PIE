"""VSE-S1 sub-1B model spec — production-ready.

VSES1Config covers 500M–1B coding model (Python+JS+English).
Parameter formula per layer (gated): 4*H^2 + 3*H*I  (attention QKVO + SwiGLU MLP).
Total  = (4*H^2 + 3*H*I) * L   (embedding / head excluded, matches TransformerModel).

Presets hit targets within ~2% using hidden 1024-2048:
  preset_500m: L=16 H=1536 I=4608  -> 490.7M
  preset_700m: L=18 H=1792 I=4864  -> 701.9M
  preset_1b:   L=20 H=2048 I=5504  -> 1011.9M

Example:
  >>> from vse.models.vse_s1 import VSES1Config
  >>> cfg = VSES1Config.preset_500m()
  >>> cfg.parameter_count() / 1e9  # ~0.49
  >>> cfg.parameter_bytes()  # weight_bits=2
  >>> cfg.to_transformer_config()
  >>> cfg.to_transformer_model().prefill_cost(2048)
  >>> from vse.compiler.precision import Q2Block
  >>> cfg.parameter_bytes({"attn": Q2Block(2,32,8), "mlp": 3})
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Dict, Optional, Union

from vse.compiler.precision import Q2Block
from vse.models.config import TransformerConfig

try:
    from vse.models.transformer import TransformerModel  # type: ignore
except Exception:  # pragma: no cover
    TransformerModel = None  # type: ignore


@dataclass
class VSES1Config:
    """500M-1B coding model config.

    Fields:
      layers 12-20, hidden_dim, num_heads, head_dim (derived), intermediate_dim,
      vocab_size, weight_bits, kv_bits, activation_bits, gated_mlp, max_seq 4096-8192, name.
    """

    layers: int = 16
    hidden_dim: int = 1024
    num_heads: int = 16
    head_dim: Optional[int] = None
    intermediate_dim: int = 2816
    vocab_size: int = 32000
    weight_bits: int = 2
    kv_bits: int = 4
    activation_bits: int = 16
    gated_mlp: bool = True
    max_seq: int = 4096
    name: str = "vse-s1"

    def __post_init__(self) -> None:
        if not 12 <= self.layers <= 20:
            raise ValueError("layers must be in [12,20]")
        if self.hidden_dim <= 0:
            raise ValueError("hidden_dim must be >0")
        if self.num_heads <= 0:
            raise ValueError("num_heads must be >0")
        if self.intermediate_dim <= 0:
            raise ValueError("intermediate_dim must be >0")
        if self.vocab_size <= 0:
            raise ValueError("vocab_size must be >0")
        if self.weight_bits <= 0:
            raise ValueError("weight_bits must be >0")
        if self.kv_bits <= 0:
            raise ValueError("kv_bits must be >0")
        if self.activation_bits <= 0:
            raise ValueError("activation_bits must be >0")
        if not 4096 <= self.max_seq <= 8192:
            raise ValueError("max_seq must be in [4096,8192]")
        if not self.name:
            raise ValueError("name must be non-empty")
        # head_dim derivation / validation
        if self.head_dim is None:
            if self.hidden_dim % self.num_heads != 0:
                raise ValueError("hidden_dim must be divisible by num_heads when head_dim is None")
            self.head_dim = self.hidden_dim // self.num_heads
        else:
            if self.head_dim <= 0:
                raise ValueError("head_dim must be >0")
            if self.hidden_dim != self.num_heads * self.head_dim:
                raise ValueError("hidden_dim must equal num_heads * head_dim")
        if self.head_dim is not None and self.head_dim <= 0:
            raise ValueError("head_dim must be >0")

    # --- presets ---
    @classmethod
    def preset_500m(cls) -> "VSES1Config":
        """~491M params: L=16 H=1536 I=4608 heads=24."""
        return cls(layers=16, hidden_dim=1536, num_heads=24, intermediate_dim=4608, vocab_size=32000, weight_bits=2, kv_bits=4, activation_bits=16, gated_mlp=True, max_seq=4096, name="vse-s1-500m")

    @classmethod
    def preset_700m(cls) -> "VSES1Config":
        """~702M params: L=18 H=1792 I=4864 heads=28."""
        return cls(layers=18, hidden_dim=1792, num_heads=28, intermediate_dim=4864, vocab_size=32000, weight_bits=2, kv_bits=4, activation_bits=16, gated_mlp=True, max_seq=4096, name="vse-s1-700m")

    @classmethod
    def preset_1b(cls) -> "VSES1Config":
        """~1.01B params: L=20 H=2048 I=5504 heads=32."""
        return cls(layers=20, hidden_dim=2048, num_heads=32, intermediate_dim=5504, vocab_size=32000, weight_bits=2, kv_bits=4, activation_bits=16, gated_mlp=True, max_seq=4096, name="vse-s1-1b")

    # --- methods ---
    def _attn_params_per_layer(self) -> int:
        return 4 * self.hidden_dim * self.hidden_dim

    def _mlp_params_per_layer(self) -> int:
        projs = 3 if self.gated_mlp else 2
        return projs * self.hidden_dim * self.intermediate_dim

    def parameter_count(self) -> int:
        """Transformer layer params only (excludes embedding/head)."""
        return (self._attn_params_per_layer() + self._mlp_params_per_layer()) * self.layers

    def parameter_bytes(self, precision_map: Optional[Dict[str, Union[int, Q2Block]]] = None) -> int:
        """Effective weight bytes.

        If precision_map is None -> (count*weight_bits+7)//8.
        If provided, keys like 'attn','mlp','head' map to int bits or Q2Block.
        """
        if precision_map is None or len(precision_map) == 0:
            return (self.parameter_count() * self.weight_bits + 7) // 8

        def _b(n: int, prec: Union[int, Q2Block]) -> int:
            if isinstance(prec, Q2Block):
                return prec.effective_bytes(n)
            if isinstance(prec, int):
                if prec <= 0:
                    raise ValueError("bits must be >0")
                return (n * prec + 7) // 8
            raise TypeError("precision must be int or Q2Block")

        attn_params = self._attn_params_per_layer() * self.layers
        mlp_params = self._mlp_params_per_layer() * self.layers
        # fallback bits
        attn_prec = precision_map.get("attn", precision_map.get("weight", self.weight_bits))
        mlp_prec = precision_map.get("mlp", precision_map.get("weight", self.weight_bits))
        total = 0
        # per-layer grouping to preserve Q2Block group rounding
        ap = self._attn_params_per_layer()
        mp = self._mlp_params_per_layer()
        for _ in range(self.layers):
            total += _b(ap, attn_prec)
            total += _b(mp, mlp_prec)
        if "head" in precision_map:
            head_params = self.vocab_size * self.hidden_dim
            total += _b(head_params, precision_map["head"])
        # kv is cache, not weight — ignored for weight bytes
        return total

    def kv_bytes_per_token(self) -> int:
        assert self.head_dim is not None
        elements = 2 * self.num_heads * self.head_dim
        return (elements * self.kv_bits + 7) // 8

    def kv_total_bytes(self, seq_len: int) -> int:
        if seq_len < 0:
            raise ValueError("seq_len must be >=0")
        if seq_len > self.max_seq:
            raise ValueError("seq_len exceeds max_seq")
        return self.layers * seq_len * self.kv_bytes_per_token()

    def to_transformer_config(self) -> TransformerConfig:
        return TransformerConfig(hidden_dim=self.hidden_dim, num_heads=self.num_heads, intermediate_dim=self.intermediate_dim, head_dim=self.head_dim, weight_bits=self.weight_bits, kv_bits=self.kv_bits, activation_bits=self.activation_bits, gated_mlp=self.gated_mlp)

    def to_transformer_model(self, num_layers: Optional[int] = None, compute=None, memory=None):  # type: ignore
        if TransformerModel is None:
            raise ImportError("TransformerModel not available")
        cfg = self.to_transformer_config()
        layers = num_layers if num_layers is not None else self.layers
        if layers <= 0:
            raise ValueError("num_layers must be >0")
        return TransformerModel(config=cfg, num_layers=layers, compute=compute, memory=memory)
