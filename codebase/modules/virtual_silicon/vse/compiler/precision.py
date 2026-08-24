"""Precision interfaces — Phase B mixed precision."""

from __future__ import annotations

import json
from dataclasses import dataclass
from typing import Optional, Union

PrecisionMap = dict[str, Union[int, "Q2Block"]]


@dataclass
class Q2Block:
    bits: int = 2
    group_size: int = 32
    scale_bits: int = 8

    def effective_bytes(self, num_weights: int) -> int:
        groups = (num_weights + self.group_size - 1) // self.group_size
        packed = (num_weights * self.bits + 7) // 8
        scale_bytes = (groups * self.scale_bits + 7) // 8
        return packed + scale_bytes


@dataclass
class SensitivityTable:
    attention_qkv: float = 1.0
    mlp: float = 0.5
    head: float = 2.0
    kv: float = 1.0
    activation: float = 0.5


def resolve_precision(
    key: str,
    precision_map: Optional[PrecisionMap],
    default: Union[int, Q2Block, None],
) -> Union[int, Q2Block, None]:
    if not precision_map:
        return default
    if key in precision_map:
        return precision_map[key]
    if "." in key:
        base = key.split(".")[-1]
        if base in precision_map:
            return precision_map[base]
        # also try without layer prefix alias
        if base == "attention" and "attn" in precision_map:
            return precision_map["attn"]
        if base == "attn" and "attention" in precision_map:
            return precision_map["attention"]
    # generic fallbacks
    if key in ("attn", "attention") and "attention_qkv" in precision_map:
        return precision_map["attention_qkv"]
    if "weight" in precision_map:
        return precision_map["weight"]
    return default


def effective_bits(precision: Union[int, Q2Block]) -> float:
    if isinstance(precision, Q2Block):
        return float(precision.bits) + float(precision.scale_bits) / float(precision.group_size)
    return float(int(precision))


def precision_to_bytes(num_weights: int, precision: Union[int, Q2Block]) -> int:
    if isinstance(precision, Q2Block):
        return precision.effective_bytes(num_weights)
    return (int(num_weights) * int(precision) + 7) // 8


def _coerce_q2block(v: dict) -> Q2Block:
    bits = v.get("bits", v.get("bit", 2))
    group = v.get("group", v.get("group_size", v.get("groupSize", 32)))
    scale = v.get("scale_bits", v.get("scale", v.get("scaleBits", 8)))
    return Q2Block(bits=int(bits), group_size=int(group), scale_bits=int(scale))


def parse_precision_map(s: Union[str, dict]) -> PrecisionMap:
    if isinstance(s, str):
        try:
            data = json.loads(s)
        except json.JSONDecodeError:
            # fallback: try to parse as simple k:v like "attn:3,mlp:2"
            data = {}
            for part in s.split(","):
                part = part.strip()
                if not part or ":" not in part:
                    continue
                k, v = part.split(":", 1)
                k = k.strip().strip('"').strip("'")
                v = v.strip()
                try:
                    data[k] = int(v)
                except ValueError:
                    try:
                        data[k] = json.loads(v)
                    except Exception:
                        data[k] = int(v)
        else:
            if not isinstance(data, dict):
                raise ValueError("precision map must be a dict")
    elif isinstance(s, dict):
        data = dict(s)
    else:
        raise TypeError("precision map must be str or dict")

    out: PrecisionMap = {}
    for k, v in data.items():
        if isinstance(v, Q2Block):
            out[k] = v
        elif isinstance(v, int):
            out[k] = int(v)
        elif isinstance(v, float):
            out[k] = int(v)
        elif isinstance(v, dict):
            # check if dict represents Q2Block
            if any(x in v for x in ("bits", "bit", "group", "group_size", "groupSize", "scale_bits", "scale")):
                out[k] = _coerce_q2block(v)
            else:
                # unknown dict, try coerce
                out[k] = _coerce_q2block(v)
        elif isinstance(v, str):
            v = v.strip()
            try:
                out[k] = int(v)
            except ValueError:
                try:
                    j = json.loads(v)
                    if isinstance(j, dict):
                        out[k] = _coerce_q2block(j)
                    else:
                        out[k] = int(j)
                except Exception:
                    out[k] = int(v)
        else:
            try:
                out[k] = int(v)  # type: ignore
            except Exception:
                continue
    return out


__all__ = [
    "PrecisionMap",
    "Q2Block",
    "SensitivityTable",
    "resolve_precision",
    "effective_bits",
    "precision_to_bytes",
    "parse_precision_map",
]
