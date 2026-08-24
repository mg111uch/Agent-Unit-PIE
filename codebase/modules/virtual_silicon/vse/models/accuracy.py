"""Accuracy proxy — Phase B3 heuristic for mixed precision."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Optional

SENSITIVITY: dict[str, float] = {
    "attn": 1.0,
    "mlp": 0.5,
    "head": 2.0,
    "kv": 0.8,
}

# aliases for robustness
_ALIASES: dict[str, str] = {
    "attention": "attn",
    "attention_qkv": "attn",
    "qkv": "attn",
    "ffn": "mlp",
    "feedforward": "mlp",
    "lm_head": "head",
    "head_out": "head",
    "kvcache": "kv",
    "kv_cache": "kv",
}


def _normalize_map(precision_map: Optional[dict]) -> Optional[dict[str, int]]:
    if precision_map is None:
        return None
    if not precision_map:
        return None
    out: dict[str, int] = {}
    for k, v in precision_map.items():
        nk = _ALIASES.get(str(k).lower(), str(k).lower())
        try:
            iv = int(v)
        except Exception:
            continue
        out[nk] = iv
    return out if out else None


def _clamp(v: float, lo: float = 0.0, hi: float = 1.0) -> float:
    return max(lo, min(hi, v))


@dataclass
class AccuracyEstimate:
    ppl_delta: float
    pass_at_k: float
    coding_score: float
    bits_avg: float

    def report(self) -> dict:
        return {
            "ppl_delta": self.ppl_delta,
            "pass_at_k": self.pass_at_k,
            "coding_score": self.coding_score,
            "bits_avg": self.bits_avg,
        }


def estimate_accuracy(
    precision_map: Optional[dict] = None,
    base_score: float = 0.85,
) -> AccuracyEstimate:
    """Heuristic accuracy estimate from per-tensor bits.

    - If map is None/empty -> base score, ppl_delta 0, bits_avg 4.
    - ppl_delta = sum((4 - bits) * sensitivity * 0.05)
      (negative delta = better than 4-bit baseline when bits>4)
    - pass_at_k = clamp(base - ppl_delta*0.5)
    - coding_score = clamp(base - ppl_delta*0.45)

    Deterministic, no ML.
    """
    norm = _normalize_map(precision_map)
    if norm is None:
        return AccuracyEstimate(
            ppl_delta=0.0,
            pass_at_k=_clamp(base_score),
            coding_score=_clamp(base_score),
            bits_avg=4.0,
        )
    bits_avg = sum(norm.values()) / len(norm) if norm else 4.0
    ppl_delta = 0.0
    for key, bits in norm.items():
        sens = SENSITIVITY.get(key, 0.5)
        ppl_delta += (4 - bits) * sens * 0.05
    # round for determinism/stability
    ppl_delta = round(ppl_delta, 6)
    pass_at_k = _clamp(base_score - ppl_delta * 0.5)
    coding_score = _clamp(base_score - ppl_delta * 0.45)
    return AccuracyEstimate(
        ppl_delta=ppl_delta,
        pass_at_k=round(pass_at_k, 6),
        coding_score=round(coding_score, 6),
        bits_avg=round(float(bits_avg), 4),
    )


def score_model(config, precision_map: Optional[dict] = None) -> AccuracyEstimate:
    """Score a model config under a precision map.

    `config` is unused in heuristic (kept for API compatibility with
    future teacher-distilled scorer). Accepts any object.
    """
    # allow config to carry base_score attribute
    base = 0.85
    if config is not None and hasattr(config, "base_accuracy"):
        try:
            base = float(getattr(config, "base_accuracy"))
        except Exception:
            base = 0.85
    return estimate_accuracy(precision_map, base_score=base)


def accuracy_for_spec(spec, precision_map: Optional[dict] = None) -> AccuracyEstimate:
    """Helper for search: score a spec under precision_map.

    If precision_map is None, tries spec.precision_map or spec.weight_bits.
    """
    pm = precision_map
    if pm is None and hasattr(spec, "precision_map") and getattr(spec, "precision_map") is not None:
        pm = getattr(spec, "precision_map")
    if pm is None and hasattr(spec, "weight_bits") and getattr(spec, "weight_bits") is not None:
        # single global bits -> treat as uniform mlp map
        pm = {"mlp": int(spec.weight_bits), "attn": int(spec.weight_bits)}
    return estimate_accuracy(pm)


__all__ = [
    "SENSITIVITY",
    "AccuracyEstimate",
    "estimate_accuracy",
    "score_model",
    "accuracy_for_spec",
]
