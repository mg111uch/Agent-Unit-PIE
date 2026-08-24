"""
VSE - PE architecture families.
"""
from __future__ import annotations

from dataclasses import dataclass
from enum import Enum

# ---------------------------------------------------------------------------
# ArchFamily
# ---------------------------------------------------------------------------

class ArchFamily(str, Enum):
    scalar = "scalar"
    simd = "simd"
    vector = "vector"
    systolic = "systolic"
    weight_stationary = "weight_stationary"
    output_stationary = "output_stationary"
    cim = "cim"
    near_memory = "near_memory"


_VALID_FAMILIES = {e.value for e in ArchFamily}
_VALID_DATAFLOWS = {"weight_stationary", "output_stationary"}

def _coerce_family(v) -> ArchFamily:
    if isinstance(v, ArchFamily):
        return v
    if isinstance(v, str):
        try:
            return ArchFamily(v)
        except ValueError:
            raise ValueError(f"family must be one of {sorted(_VALID_FAMILIES)}, got {v!r}")
    raise ValueError(f"family must be ArchFamily or str, got {type(v).__name__}")


@dataclass
class PEFamilyConfig:
    family: ArchFamily = ArchFamily.scalar
    vector_width: int = 1
    systolic_dim: int = 0
    simd_lanes: int = 1
    dataflow: str = "weight_stationary"

    def __post_init__(self) -> None:
        # coerce family from str
        self.family = _coerce_family(self.family)
        if not 1 <= self.vector_width <= 16:
            raise ValueError("vector_width must be 1..16")
        if not 0 <= self.systolic_dim <= 64:
            raise ValueError("systolic_dim must be 0..64")
        if not 1 <= self.simd_lanes <= 8:
            raise ValueError("simd_lanes must be 1..8")
        if self.dataflow not in _VALID_DATAFLOWS:
            raise ValueError(f"dataflow must be one of {sorted(_VALID_DATAFLOWS)}, got {self.dataflow!r}")
        # dataflow only meaningful for systolic families but allow any
        # vector_width/systolic_dim/simd_lanes are validated regardless


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def effective_macs_per_cycle(base_macs_per_pe: int, config: PEFamilyConfig) -> int:
    """Effective MACs per PE per cycle for the family."""
    if base_macs_per_pe <= 0:
        raise ValueError("base_macs_per_pe must be > 0")
    fam = config.family
    if fam == ArchFamily.scalar:
        return int(base_macs_per_pe)
    if fam == ArchFamily.simd:
        return int(base_macs_per_pe * config.simd_lanes)
    if fam == ArchFamily.vector:
        return int(base_macs_per_pe * config.vector_width)
    if fam in (ArchFamily.systolic, ArchFamily.weight_stationary, ArchFamily.output_stationary):
        if config.systolic_dim > 0:
            # systolic array of dim x dim MACs per PE (or per tile)
            return int(base_macs_per_pe * config.systolic_dim * config.systolic_dim)
        return int(base_macs_per_pe)
    if fam == ArchFamily.cim:
        return int(base_macs_per_pe)
    if fam == ArchFamily.near_memory:
        return int(base_macs_per_pe)
    return int(base_macs_per_pe)


def gate_overhead(config: PEFamilyConfig) -> int:
    """Extra NAND2 gates for family-specific control/datapath."""
    fam = config.family
    if fam == ArchFamily.scalar:
        return 0
    if fam == ArchFamily.simd:
        return int(config.simd_lanes * 20)
    if fam == ArchFamily.vector:
        return int(config.vector_width * 50)
    if fam in (ArchFamily.systolic, ArchFamily.weight_stationary, ArchFamily.output_stationary):
        # dim*30 captures sequencers / stationarity buffers
        return int(config.systolic_dim * 30)
    if fam == ArchFamily.cim:
        return 100
    if fam == ArchFamily.near_memory:
        return 50
    return 0


def latency_extra(config: PEFamilyConfig) -> int:
    """Extra cycles for fill/drain or pipeline depth."""
    fam = config.family
    if fam in (ArchFamily.systolic, ArchFamily.weight_stationary, ArchFamily.output_stationary):
        return int(config.systolic_dim)
    if fam == ArchFamily.vector:
        return 1
    if fam == ArchFamily.cim:
        return 0
    if fam == ArchFamily.simd:
        return 0
    if fam == ArchFamily.near_memory:
        return 0
    # scalar
    return 0


def area_factor(config: PEFamilyConfig) -> float:
    """Area multiplier relative to scalar baseline."""
    fam = config.family
    if fam == ArchFamily.scalar:
        return 1.0
    if fam == ArchFamily.simd:
        return 1.0 + config.simd_lanes * 0.05
    if fam == ArchFamily.vector:
        return 1.0 + config.vector_width * 0.08
    if fam in (ArchFamily.systolic, ArchFamily.weight_stationary, ArchFamily.output_stationary):
        return 1.0 + config.systolic_dim * 0.04
    if fam == ArchFamily.cim:
        return 1.25
    if fam == ArchFamily.near_memory:
        return 1.15
    return 1.0


__all__ = [
    "ArchFamily",
    "PEFamilyConfig",
    "effective_macs_per_cycle",
    "gate_overhead",
    "latency_extra",
    "area_factor",
]
