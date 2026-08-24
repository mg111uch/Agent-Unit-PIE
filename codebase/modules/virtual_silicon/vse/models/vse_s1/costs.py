"""VSE-S1 costs — reuses TransformerModel, adds Q2Block-aware effective bytes."""

from __future__ import annotations

from typing import Dict, Optional, Union

from vse.compiler.precision import Q2Block
from vse.models.transformer import TransformerModel, TransformerWorkloadCost
from vse.models.vse_s1.spec import VSES1Config


def _bytes_for(num_weights: int, prec: Union[int, Q2Block]) -> int:
    if isinstance(prec, Q2Block):
        return prec.effective_bytes(num_weights)
    if isinstance(prec, int):
        if prec <= 0:
            raise ValueError("bits must be >0")
        return (num_weights * prec + 7) // 8
    raise TypeError("precision must be int or Q2Block")


def effective_weight_bytes(config: VSES1Config, precision_map: Optional[Dict[str, Union[int, Q2Block]]] = None) -> int:
    """Per-layer effective weight bytes.

    precision_map keys: 'attn','mlp','head','kv','weight'.
    int -> (n*bits+7)//8, Q2Block -> effective_bytes(n).
    Computed per-layer to preserve group rounding (e.g. Q2 group32 scale8).
    Example: 16 layers, attn Q3 vs mlp Q2(2b group32 scale8).
    """
    if precision_map is None or len(precision_map) == 0:
        return (config.parameter_count() * config.weight_bits + 7) // 8
    attn_prec = precision_map.get("attn", precision_map.get("weight", config.weight_bits))
    mlp_prec = precision_map.get("mlp", precision_map.get("weight", config.weight_bits))
    ap = 4 * config.hidden_dim * config.hidden_dim
    mp = (3 if config.gated_mlp else 2) * config.hidden_dim * config.intermediate_dim
    total = 0
    for _ in range(config.layers):
        total += _bytes_for(ap, attn_prec)
        total += _bytes_for(mp, mlp_prec)
    if "head" in precision_map:
        head_params = config.vocab_size * config.hidden_dim
        total += _bytes_for(head_params, precision_map["head"])
    # kv is cache, not weight bytes — intentionally excluded
    return total


def parameter_bytes(config: VSES1Config, precision_map: Optional[Dict[str, Union[int, Q2Block]]] = None) -> int:
    """Alias for effective_weight_bytes."""
    return effective_weight_bytes(config, precision_map)


def vse_s1_cost(config: VSES1Config, seq_len: int, compute=None, memory=None, decode: bool = False) -> TransformerWorkloadCost:
    """TransformerWorkloadCost via TransformerModel (prefill by default)."""
    if seq_len < 0:
        raise ValueError("seq_len must be >=0")
    if not decode and seq_len <= 0:
        raise ValueError("seq_len must be >0 for prefill")
    model = config.to_transformer_model(compute=compute, memory=memory)
    return model.decode_cost(seq_len) if decode else model.prefill_cost(seq_len)


def vse_s1_prefill_cost(config: VSES1Config, seq_len: int, compute=None, memory=None) -> TransformerWorkloadCost:
    return vse_s1_cost(config, seq_len, compute=compute, memory=memory, decode=False)


def vse_s1_decode_cost(config: VSES1Config, seq_len: int, compute=None, memory=None) -> TransformerWorkloadCost:
    return vse_s1_cost(config, seq_len, compute=compute, memory=memory, decode=True)


def vse_s1_decode_cycles(config: VSES1Config, seq_len: int, compute=None, memory=None) -> int:
    """Total decode cycles (compute+memory) for one token with seq_len context."""
    cost = vse_s1_decode_cost(config, seq_len, compute=compute, memory=memory)
    return cost.compute_cycles + cost.memory_cycles


def vse_s1_kv_bytes(config: VSES1Config, seq_len: int) -> int:
    return config.kv_total_bytes(seq_len)
