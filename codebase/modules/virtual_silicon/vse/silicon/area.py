"""
VSE - Virtual Silicon Engine
vse/area.py

Phase 7: silicon area estimation.

Estimates the die area of a candidate chip from its PE array, SRAM
capacity, and NoC router count using a `ProcessTechnology`. Replaces the
crude `ArchitectureSpec.area_proxy` with an area model grounded in
process constants.
"""

from __future__ import annotations

from dataclasses import dataclass

from vse.silicon.process import DEFAULT, ProcessTechnology


@dataclass
class AreaEstimate:
    """Area breakdown of one chip, in mm²."""

    compute_area_mm2: float
    sram_area_mm2: float
    noc_area_mm2: float
    total_area_mm2: float

    def report(self) -> dict:
        return {
            "compute_area_mm2": (
                self.compute_area_mm2
            ),
            "sram_area_mm2": self.sram_area_mm2,
            "noc_area_mm2": self.noc_area_mm2,
            "total_area_mm2": self.total_area_mm2,
        }


def _tiled_area(
    chip, tech: ProcessTechnology
):
    """Try tiled area via TiledHierarchy/TileSpec. Returns AreaEstimate or None."""
    try:
        n_tiles = int(getattr(chip, "num_tiles", 1) or 1)
    except Exception:
        n_tiles = 1
    has_tiles = False
    try:
        v = getattr(chip, "tiles", None)
        has_tiles = isinstance(v, (list, tuple)) and len(v) > 0
    except Exception:
        has_tiles = False
    has_th = False
    try:
        v = getattr(chip, "tiled_hierarchy", None)
        has_th = v is not None
    except Exception:
        has_th = False
    if not (n_tiles > 1 or has_tiles or has_th):
        return None
    tiles = None
    try:
        if has_th:
            th = getattr(chip, "tiled_hierarchy")
            if hasattr(th, "tiles"):
                tiles = list(getattr(th, "tiles"))  # type: ignore
        elif has_tiles:
            tiles = list(getattr(chip, "tiles"))  # type: ignore
    except Exception:
        tiles = None
    if not tiles:
        try:
            from vse.core.tile import TiledHierarchy  # lazy

            th = TiledHierarchy.build_tiled_hierarchy(chip)  # type: ignore
            tiles = th.tiles  # type: ignore
        except Exception:
            return None
    if not tiles:
        return None
    # sum per-tile area
    macs = getattr(chip, "macs_per_pe", getattr(chip, "macs_per_pe_per_cycle", 1))
    try:
        macs = int(macs)  # type: ignore
    except Exception:
        macs = 1
    compute_unrouted = 0.0
    total_tiles_mm2 = 0.0
    for t in tiles:
        try:
            area = float(t.area_mm2(tech))  # type: ignore
        except Exception:
            pes = int(getattr(t, "pes", getattr(t, "num_pes", 0)) or 0)
            comp = pes * macs * tech.mac_area_um2 / 1e6 * tech.routing_overhead
            sram = 0.0
            if hasattr(t, "sram_array") and getattr(t, "sram_array") is not None:
                try:
                    sram = float(getattr(t, "sram_array").area_mm2(tech))  # type: ignore
                except Exception:
                    sram = 0.0
            else:
                cap = 0
                for attr in ("total_sram_bytes", "sram_weight_bytes"):
                    v = getattr(t, attr, None)
                    if isinstance(v, int) and v > 0:
                        cap = v
                        break
                    if callable(v):
                        try:
                            vv = v()
                            if isinstance(vv, int) and vv > 0:
                                cap = vv
                                break
                        except Exception:
                            pass
                if cap:
                    sram = cap * 8 * tech.sram_area_um2_per_bit / 1e6
            area = comp + sram
        total_tiles_mm2 += area
        try:
            pes = int(getattr(t, "pes", 0) or 0)
            compute_unrouted += pes * macs * tech.mac_area_um2 / 1e6
        except Exception:
            pass
    # noc global
    try:
        noc_nodes = int(getattr(chip, "noc_nodes", 1) or 1)
    except Exception:
        noc_nodes = 1
    noc_um2 = noc_nodes * tech.noc_area_um2_per_node
    noc_mm2 = noc_um2 / 1e6
    # tiles already include per-tile routing for compute and sram routing;
    # noc needs routing overhead (consistent with non-tiled)
    total_mm2 = total_tiles_mm2 + noc_mm2 * tech.routing_overhead
    # derive sram_mm2 as residual to avoid double counting
    sram_mm2 = max(0.0, total_tiles_mm2 - compute_unrouted * tech.routing_overhead)
    return AreaEstimate(
        compute_area_mm2=compute_unrouted,
        sram_area_mm2=sram_mm2,
        noc_area_mm2=noc_mm2,
        total_area_mm2=total_mm2,
    )


def estimate_area(
    chip,
    tech: ProcessTechnology = DEFAULT,
) -> AreaEstimate:
    """
    Estimate die area for any chip description exposing `num_pes`,
    `macs_per_pe`, `sram_bytes`, and `noc_nodes` (e.g. an
    `ArchitectureSpec` or `HardwareConfig`).

    Physical SRAM area can be derived via SRAMArray.area_mm2(tech)
    when chip exposes a `sram_array` attribute — prefer that over
    bytes*area_per_bit for accuracy (banks*ports*bits*freq model).
    Handles tiled chips (num_tiles>1 or tiles/tiled_hierarchy).
    """

    tiled = _tiled_area(chip, tech)
    if tiled is not None:
        return tiled

    compute_um2 = (
        chip.num_pes
        * getattr(
            chip,
            "macs_per_pe",
            getattr(
                chip,
                "macs_per_pe_per_cycle",
                1,
            ),
        )
        * tech.mac_area_um2
    )

    # Prefer physical SRAMArray area if available (lazy duck-type).
    # Physical SRAM area can be derived via SRAMArray.area_mm2(tech)
    # which already includes per-bank routing_overhead and port overhead,
    # so total must avoid double multiplication for that case.
    noc_um2 = (
        chip.noc_nodes
        * tech.noc_area_um2_per_node
    )
    use_array = False
    sram_mm2_phys: float = 0.0
    sram_um2: float = 0.0
    if hasattr(chip, "sram_array") and getattr(
        chip, "sram_array"
    ) is not None:
        try:
            arr = getattr(chip, "sram_array")
            # arr is expected to be SRAMArray with area_mm2(tech)
            sram_mm2_phys = float(arr.area_mm2(tech))  # type: ignore
            sram_um2 = sram_mm2_phys * 1e6
            use_array = True
        except Exception:
            use_array = False
    if not use_array:
        sram_um2 = (
            chip.sram_bytes
            * 8
            * tech.sram_area_um2_per_bit
        )

    if use_array:
        # sram already includes its routing; apply routing only to
        # compute and noc to avoid double counting
        total_mm2 = (
            (compute_um2 + noc_um2)
            * tech.routing_overhead
            / 1e6
            + sram_mm2_phys
        )
        return AreaEstimate(
            compute_area_mm2=compute_um2 / 1e6,
            sram_area_mm2=sram_mm2_phys,
            noc_area_mm2=noc_um2 / 1e6,
            total_area_mm2=total_mm2,
        )

    total_um2 = (
        compute_um2 + sram_um2 + noc_um2
    ) * tech.routing_overhead

    return AreaEstimate(
        compute_area_mm2=compute_um2 / 1e6,
        sram_area_mm2=sram_um2 / 1e6,
        noc_area_mm2=noc_um2 / 1e6,
        total_area_mm2=total_um2 / 1e6,
    )


__all__ = [
    "AreaEstimate",
    "estimate_area",
]
