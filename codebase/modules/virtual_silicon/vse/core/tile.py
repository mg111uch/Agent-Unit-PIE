"""Distributed tile abstraction — Phase C1.

Tiles partition SRAM / PEs across N chiplets. Each TileSpec owns its
SRAM shard; TiledHierarchy aggregates tiles and exposes helpers to map
into ``MemoryHierarchy``.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import TYPE_CHECKING, Dict, List, Optional

if TYPE_CHECKING:
    from vse.core.memory_hierarchy import MemoryHierarchy, MemoryLevel
    from vse.silicon.process import ProcessTechnology
    from vse.silicon.sram.sram_array import SRAMArray


# ---------------------------------------------------------------------------
# TileSpec
# ---------------------------------------------------------------------------

@dataclass
class TileSpec:
    """One compute+SRAM tile."""

    tile_id: int
    sram_weight_bytes: int = 0
    sram_act_bytes: int = 0
    sram_kv_bytes: int = 0
    pes: int = 0
    sram_array: Optional["SRAMArray"] = None
    sram_banks: int = 1
    sram_ports: int = 1
    sram_bits: int = 32
    frequency_hz: float = 1e9

    def __post_init__(self) -> None:
        if self.tile_id < 0:
            raise ValueError("tile_id must be >= 0")
        if self.pes <= 0:
            raise ValueError("pes must be > 0")
        for name in ("sram_weight_bytes", "sram_act_bytes", "sram_kv_bytes"):
            v = getattr(self, name)
            if v < 0:
                raise ValueError(f"{name} must be >= 0")
        if not 1 <= self.sram_banks <= 512:
            raise ValueError(f"sram_banks must be 1..512, got {self.sram_banks}")
        if not 1 <= self.sram_ports <= 4:
            raise ValueError(f"sram_ports must be 1..4, got {self.sram_ports}")
        if not 8 <= self.sram_bits <= 512:
            raise ValueError(f"sram_bits must be 8..512, got {self.sram_bits}")
        if self.frequency_hz <= 0:
            raise ValueError("frequency_hz must be > 0")

    # -- capacity ---------------------------------------------------------
    @property
    def total_sram_bytes(self) -> int:
        return self.sram_weight_bytes + self.sram_act_bytes + self.sram_kv_bytes

    # keep callable alias for spec that expects method
    def total_bytes(self) -> int:
        return self.total_sram_bytes  # type: ignore

    # -- SRAMArray helpers ------------------------------------------------
    def _make_array(self, capacity: int, tech=None) -> "SRAMArray":
        from vse.silicon.sram.sram_array import SRAMArray

        return SRAMArray(
            banks=self.sram_banks,
            ports_per_bank=self.sram_ports,
            bits_per_access=self.sram_bits,
            capacity_bytes_total=max(0, capacity),
            frequency_hz=self.frequency_hz,
            tech=tech,
        )

    def weight_array(self, tech=None) -> "SRAMArray":
        return self._make_array(self.sram_weight_bytes, tech=tech)

    def act_array(self, tech=None) -> "SRAMArray":
        return self._make_array(self.sram_act_bytes, tech=tech)

    def kv_array(self, tech=None) -> "SRAMArray":
        return self._make_array(self.sram_kv_bytes, tech=tech)

    # -- physical ---------------------------------------------------------
    def area_mm2(self, tech: Optional["ProcessTechnology"] = None) -> float:
        """Tile area = PE array + SRAM (if any)."""
        if tech is None:
            from vse.silicon.process import DEFAULT as _DEFAULT

            tech = _DEFAULT
        compute_mm2 = self.pes * tech.mac_area_um2 / 1e6 * tech.routing_overhead
        if self.sram_array is not None:
            try:
                sram_mm2 = float(self.sram_array.area_mm2(tech))  # type: ignore
            except Exception:
                sram_mm2 = 0.0
        else:
            # sum of per-purpose arrays
            sram_mm2 = 0.0
            for cap in (self.sram_weight_bytes, self.sram_act_bytes, self.sram_kv_bytes):
                if cap > 0:
                    try:
                        sram_mm2 += self._make_array(cap, tech=tech).area_mm2(tech)
                    except Exception:
                        sram_mm2 += cap * 8 * tech.sram_area_um2_per_bit / 1e6
        # compute already includes routing; sram array already includes its own routing
        # combine without double-counting sram routing
        return compute_mm2 + sram_mm2

    def report(self) -> Dict:
        bw = None
        if self.sram_array is not None:
            try:
                bw = self.sram_array.bandwidth_bytes_per_cycle()  # type: ignore
            except Exception:
                bw = None
        return {
            "tile_id": self.tile_id,
            "pes": self.pes,
            "sram_weight_bytes": self.sram_weight_bytes,
            "sram_act_bytes": self.sram_act_bytes,
            "sram_kv_bytes": self.sram_kv_bytes,
            "total_sram_bytes": self.total_sram_bytes,
            "sram_banks": self.sram_banks,
            "sram_ports": self.sram_ports,
            "sram_bits": self.sram_bits,
            "frequency_hz": self.frequency_hz,
            "bandwidth_bytes_per_cycle": bw,
            "area_mm2": self.area_mm2(),
        }


# ---------------------------------------------------------------------------
# TiledHierarchy
# ---------------------------------------------------------------------------

@dataclass
class TiledHierarchy:
    """Collection of tiles plus global HBM view."""

    tiles: List[TileSpec] = field(default_factory=list)
    num_tiles: int = 0
    global_sram_bytes: int = 0
    global_bw: int = 0
    topology: str = "mesh"

    def __post_init__(self) -> None:
        if not self.num_tiles:
            self.num_tiles = len(self.tiles)
        if self.num_tiles < 0:
            raise ValueError("num_tiles must be >=0")
        if self.global_sram_bytes < 0:
            raise ValueError("global_sram_bytes must be >=0")
        if self.global_bw < 0:
            raise ValueError("global_bw must be >=0")

    # -- aggregates -------------------------------------------------------
    @property
    def total_pes(self) -> int:
        return sum(t.pes for t in self.tiles)

    @property
    def total_sram_bytes(self) -> int:
        return sum(t.total_sram_bytes for t in self.tiles)

    @property
    def total_weight_bytes(self) -> int:
        return sum(t.sram_weight_bytes for t in self.tiles)

    @property
    def total_act_bytes(self) -> int:
        return sum(t.sram_act_bytes for t in self.tiles)

    @property
    def total_kv_bytes(self) -> int:
        return sum(t.sram_kv_bytes for t in self.tiles)

    # -- builders ---------------------------------------------------------
    @classmethod
    def build_tiled_hierarchy(cls, config) -> "TiledHierarchy":
        """Split ``config.sram_bytes`` / ``num_pes`` evenly across tiles.

        Handles missing ``num_tiles`` gracefully via getattr(...,1).
        Banks/ports/bits/frequency/tech are resolved from tile-specific
        overrides falling back to global ``HardwareConfig`` fields.
        """
        num_tiles = int(getattr(config, "num_tiles", 1) or 1)
        if num_tiles <= 0:
            num_tiles = 1
        num_pes = int(getattr(config, "num_pes", 0) or 0)
        sram_bytes = int(getattr(config, "sram_bytes", 0) or 0)

        # resolve tile-local overrides -> global fallback -> defaults
        banks = getattr(config, "tile_sram_banks", None)
        if banks is None:
            banks = getattr(config, "banks", 1)
        sram_ports = getattr(config, "tile_sram_ports", None)
        if sram_ports is None:
            sram_ports = getattr(config, "sram_ports", 1)
        # bits: try multiple names
        sram_bits = getattr(config, "tile_sram_bits", None)
        if sram_bits is None:
            sram_bits = getattr(config, "tile_sram_bits_per_access", None)
        if sram_bits is None:
            sram_bits = getattr(config, "sram_bits_per_access", None)
        if sram_bits is None:
            sram_bits = getattr(config, "sram_bits", 32)
        frequency_hz = float(getattr(config, "frequency_hz", 1e9) or 1e9)
        sram_model = getattr(config, "sram_model", "analytical")
        tech = getattr(config, "tech", None)
        topology = getattr(config, "noc_topology", "mesh")

        # sram per-tile override hint
        sram_per_tile = getattr(config, "sram_per_tile_bytes", None)
        pes_per_tile_hint = getattr(config, "pes_per_tile", None)

        # distribute
        if pes_per_tile_hint is not None and pes_per_tile_hint > 0:
            # explicit per-tile hint overrides even split
            pes_list = [int(pes_per_tile_hint)] * num_tiles
            # remainder handled by adjusting last tile to match num_pes if needed?
            # keep as hint; total may differ — honour hint
        else:
            base = num_pes // num_tiles if num_tiles else 0
            rem = num_pes % num_tiles if num_tiles else 0
            pes_list = [base + (1 if i < rem else 0) for i in range(num_tiles)]

        if sram_per_tile is not None and sram_per_tile >= 0:
            sram_list = [int(sram_per_tile)] * num_tiles
        else:
            base_b = sram_bytes // num_tiles if num_tiles else 0
            rem_b = sram_bytes % num_tiles if num_tiles else 0
            sram_list = [base_b + (1 if i < rem_b else 0) for i in range(num_tiles)]

        tiles: List[TileSpec] = []
        for i in range(num_tiles):
            cap = int(sram_list[i])
            pes_i = int(pes_list[i])
            # avoid pes=0 validation failure when num_pes=0 (e.g. in tests) -> set 1 if 0?
            # but spec says pes>0; we ensure at least 1 pes per tile when num_pes==0 -> use 1
            if pes_i <= 0:
                # if original num_pes==0 keep 1 to satisfy validation unless explicitly 0?
                # allow 0 only if caller explicitly wants 0 pes — skip validation by using 1
                # but we raise if 0, so we map 0->1 for hierarchy construction when num_pes==0
                # this keeps build_tiled_hierarchy usable with dummy configs that have 0 pes
                pes_i = 1 if num_pes == 0 else 0
                if pes_i <= 0:
                    pes_i = 1
            sram_array = None
            if cap > 0:
                try:
                    from vse.silicon.sram.sram_array import SRAMArray

                    if sram_model == "physical":
                        sram_array = SRAMArray(
                            banks=int(banks),
                            ports_per_bank=int(sram_ports),
                            bits_per_access=int(sram_bits),
                            capacity_bytes_total=cap,
                            frequency_hz=frequency_hz,
                            tech=tech,
                        )
                    else:
                        # analytical: still build array for area reporting? keep None to preserve analytical semantics
                        # but create lightweight array for area if needed -> leave None
                        sram_array = None
                        # optionally build for uniform handling but keep None
                except Exception:
                    sram_array = None
            tiles.append(
                TileSpec(
                    tile_id=i,
                    sram_weight_bytes=cap,
                    sram_act_bytes=0,
                    sram_kv_bytes=0,
                    pes=pes_i,
                    sram_array=sram_array,
                    sram_banks=int(banks),
                    sram_ports=int(sram_ports),
                    sram_bits=int(sram_bits),
                    frequency_hz=frequency_hz,
                )
            )

        global_bw = 0
        # try derive global_bw from config bandwidth hints
        for attr in ("sram_bytes_per_cycle", "memory_bytes_per_cycle", "hbm_bytes_per_cycle"):
            v = getattr(config, attr, None)
            if v is not None:
                try:
                    global_bw = int(v)
                    break
                except Exception:
                    pass

        return cls(
            tiles=tiles,
            num_tiles=num_tiles,
            global_sram_bytes=sram_bytes,
            global_bw=global_bw,
            topology=str(topology),
        )

    # -- hierarchy conversion ---------------------------------------------
    def to_memory_levels(self) -> List["MemoryLevel"]:
        from vse.core.memory_hierarchy import MemoryLevel

        levels: List["MemoryLevel"] = []
        for t in self.tiles:
            cap = t.total_sram_bytes
            bw = 0
            if t.sram_array is not None:
                try:
                    bw = int(t.sram_array.bandwidth_bytes_per_cycle())  # type: ignore
                except Exception:
                    bw = 0
            else:
                # analytical fallback: derive from banks*ports*bits/8
                try:
                    bw = int(t.sram_banks * t.sram_ports * t.sram_bits / 8)
                except Exception:
                    bw = 0
            levels.append(
                MemoryLevel(
                    name=f"tile{t.tile_id}_sram",
                    capacity_bytes=cap,
                    read_bw_bytes_per_cycle=bw,
                    write_bw_bytes_per_cycle=bw,
                    banks=t.sram_banks,
                    sram_array=t.sram_array,
                    ports=t.sram_ports,
                    bits_per_access=t.sram_bits,
                )
            )
        # global HBM
        hbm_bw = self.global_bw or 0
        # fallback to first tile bw if not set
        if hbm_bw == 0 and self.tiles:
            try:
                hbm_bw = int(self.tiles[0].sram_banks * self.tiles[0].sram_ports * self.tiles[0].sram_bits / 8)
            except Exception:
                hbm_bw = 256
            if hbm_bw == 0:
                hbm_bw = 256
        levels.append(
            MemoryLevel(
                name="hbm",
                capacity_bytes=0,
                read_bw_bytes_per_cycle=hbm_bw,
                write_bw_bytes_per_cycle=hbm_bw,
                banks=1,
            )
        )
        return levels

    def to_hierarchy(self) -> "MemoryHierarchy":
        from vse.core.memory_hierarchy import MemoryHierarchy

        return MemoryHierarchy(self.to_memory_levels())

    # legacy alias
    def to_memory_hierarchy(self) -> "MemoryHierarchy":
        return self.to_hierarchy()

    def report(self) -> Dict:
        return {
            "num_tiles": self.num_tiles,
            "topology": self.topology,
            "global_sram_bytes": self.global_sram_bytes,
            "global_bw": self.global_bw,
            "total_pes": self.total_pes,
            "total_sram_bytes": self.total_sram_bytes,
            "total_weight_bytes": self.total_weight_bytes,
            "total_act_bytes": self.total_act_bytes,
            "total_kv_bytes": self.total_kv_bytes,
            "tiles": [t.report() for t in self.tiles],
        }


__all__ = ["TileSpec", "TiledHierarchy"]
