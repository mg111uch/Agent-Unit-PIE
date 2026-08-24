"""
VSE - Virtual Silicon Engine
vse/memory_hierarchy.py

Memory hierarchy model (Phase 3).

Models a multi-level on-/off-chip memory system:

    PE SRAM
        ↓
    Global SRAM
        ↓
    HBM

Each level has capacity, read/write bandwidth, and a bank count.
Tasks that carry a `mem_level` are routed to the matching level's
read/write resources by the cycle engine; bank conflicts surface as
capacity contention on those resources.

The hierarchy is also used to decide weight residency (whether a
working set fits on-chip) and to report per-level traffic from a
finished schedule.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import TYPE_CHECKING, Dict, List, Optional

from vse.core.types import Resource, ResourceType, ScheduleResult

if TYPE_CHECKING:
    from vse.silicon.process import ProcessTechnology
    from vse.silicon.sram.sram_array import SRAMArray


# ---------------------------------------------------------------------------
# Level
# ---------------------------------------------------------------------------

@dataclass
class MemoryLevel:
    """
    One level of the memory hierarchy.

    capacity_bytes:
        0 means unbounded (HBM).

    read/write_bw_bytes_per_cycle:
        Bandwidth of this level. 0 means no bandwidth-limited resource
        is created for that direction.

    banks:
        Independent banks; concurrent tasks touching more banks than
        this must wait.
    sram_array:
        Physical SRAMArray when sram_model=="physical", else None.
    ports, bits_per_access:
        Physical port/count per access for SRAMArray bandwidth calc.
    """

    name: str

    capacity_bytes: int = 0
    read_bw_bytes_per_cycle: int = 0
    write_bw_bytes_per_cycle: int = 0

    banks: int = 1
    sram_array: Optional["SRAMArray"] = None
    ports: int = 1
    bits_per_access: int = 32

    def __post_init__(self) -> None:
        if self.capacity_bytes < 0:
            raise ValueError("capacity_bytes must be >= 0")
        if self.read_bw_bytes_per_cycle < 0:
            raise ValueError("read_bw_bytes_per_cycle must be >= 0")
        if self.write_bw_bytes_per_cycle < 0:
            raise ValueError("write_bw_bytes_per_cycle must be >= 0")
        if self.banks <= 0:
            raise ValueError("banks must be > 0")
        if self.ports <= 0 or self.ports > 4:
            raise ValueError("ports must be 1..4")
        if self.bits_per_access < 8 or self.bits_per_access > 512:
            raise ValueError("bits_per_access must be 8..512")


# ---------------------------------------------------------------------------
# Hierarchy
# ---------------------------------------------------------------------------

class MemoryHierarchy:
    """
    Ordered set of memory levels plus residency/traffic helpers.
    """

    def __init__(
        self,
        levels: List[MemoryLevel],
    ) -> None:
        if not levels:
            raise ValueError(
                "at least one memory level is required"
            )

        self.levels: Dict[str, MemoryLevel] = {
            level.name: level
            for level in levels
        }

        if "hbm" not in self.levels:
            raise ValueError(
                "hierarchy must include an 'hbm' level"
            )

    @classmethod
    def default(
        cls,
        sram_bytes: int = 0,
        memory_bytes_per_cycle: int = 256,
        sram_bw_bytes_per_cycle: int = 0,
        hbm_bw_bytes_per_cycle: int = 0,
        banks: int = 1,
        sram_model: str = "analytical",
        sram_ports: int = 1,
        sram_bits_per_access: int = 32,
        frequency_hz: float = 1e9,
        tech: Optional["ProcessTechnology"] = None,
    ) -> MemoryHierarchy:
        """
        Two-level hierarchy: on-chip SRAM over unbounded HBM.

        A zero bandwidth value inherits memory_bytes_per_cycle.
        When sram_model=="physical" and sram_bytes>0, bandwidth is
        derived from SRAMArray(banks, ports, bits, capacity, freq, tech).
        """
        if sram_model not in ("analytical", "physical"):
            raise ValueError("sram_model must be 'analytical' or 'physical'")
        if not 1 <= sram_ports <= 4:
            raise ValueError("sram_ports must be 1..4")
        if not 8 <= sram_bits_per_access <= 512:
            raise ValueError("sram_bits_per_access must be 8..512")

        requested_sram_bw = sram_bw_bytes_per_cycle or memory_bytes_per_cycle
        sram_bw = requested_sram_bw
        hbm_bw = hbm_bw_bytes_per_cycle or memory_bytes_per_cycle

        sram_array = None
        if sram_model == "physical" and sram_bytes > 0:
            from vse.silicon.sram.sram_array import SRAMArray

            sram_array = SRAMArray(
                banks=banks,
                ports_per_bank=sram_ports,
                bits_per_access=sram_bits_per_access,
                capacity_bytes_total=sram_bytes,
                frequency_hz=frequency_hz,
                tech=tech,
            )
            sram_bw = int(sram_array.bandwidth_bytes_per_cycle())

        hierarchy = cls(
            [
                MemoryLevel(
                    name="sram",
                    capacity_bytes=sram_bytes,
                    read_bw_bytes_per_cycle=sram_bw,
                    write_bw_bytes_per_cycle=sram_bw,
                    banks=banks,
                    sram_array=sram_array,
                    ports=sram_ports,
                    bits_per_access=sram_bits_per_access,
                ),
                MemoryLevel(
                    name="hbm",
                    capacity_bytes=0,
                    read_bw_bytes_per_cycle=hbm_bw,
                    write_bw_bytes_per_cycle=hbm_bw,
                    banks=banks,
                ),
            ]
        )
        # stash for physical reports
        hierarchy._sram_model = sram_model  # type: ignore
        hierarchy._requested_sram_bw = requested_sram_bw  # type: ignore
        hierarchy._frequency_hz = frequency_hz  # type: ignore
        hierarchy._tech = tech  # type: ignore
        hierarchy._sram_ports = sram_ports  # type: ignore
        hierarchy._sram_bits = sram_bits_per_access  # type: ignore
        return hierarchy

    def physical_bandwidth_report(self) -> dict:
        sram = self.levels.get("sram")
        requested = getattr(self, "_requested_sram_bw", None)
        if requested is None and sram is not None:
            requested = sram.read_bw_bytes_per_cycle
        if sram is not None and sram.sram_array is not None:
            derived = int(sram.sram_array.bandwidth_bytes_per_cycle())
            return {
                "sram_model": getattr(self, "_sram_model", "physical"),
                "requested_bw_bytes_per_cycle": requested,
                "derived_bw_bytes_per_cycle": derived,
                "physical_bw_bytes_per_cycle": derived,
                "achievable": derived >= (requested or 0),
                "ports": sram.ports,
                "bits_per_access": sram.bits_per_access,
                "banks": sram.banks,
                "frequency_hz": getattr(self, "_frequency_hz", 1e9),
            }
        return {
            "sram_model": getattr(self, "_sram_model", "analytical"),
            "requested_bw_bytes_per_cycle": requested,
            "derived_bw_bytes_per_cycle": requested,
            "physical_bw_bytes_per_cycle": None,
            "achievable": True,
            "ports": getattr(sram, "ports", 1) if sram else 1,
            "bits_per_access": getattr(sram, "bits_per_access", 32) if sram else 32,
            "banks": sram.banks if sram else 1,
            "frequency_hz": getattr(self, "_frequency_hz", 1e9),
        }

    def validate_physical(self) -> bool:
        sram = self.levels.get("sram")
        if sram is None or sram.sram_array is None:
            return True
        report = self.physical_bandwidth_report()
        return bool(report.get("achievable", True))

    # ------------------------------------------------------------------
    # Resource wiring
    # ------------------------------------------------------------------

    def add_resources(
        self,
        scheduler,
    ) -> None:
        """
        Register a read/write scheduler resource per level.

        Each resource has `banks` capacity (concurrent bank accesses),
        per-unit throughput = level bandwidth / banks, and HBM is
        marked primary (the default target for level-less tasks).
        """

        for level in self.levels.values():
            for direction in ("read", "write"):
                bandwidth = getattr(
                    level,
                    f"{direction}_bw_bytes_per_cycle",
                )

                if bandwidth <= 0:
                    continue

                scheduler.add_resource(
                    Resource(
                        name=f"{level.name}_{direction}",
                        resource_type=(
                            ResourceType.MEMORY_READ
                            if direction == "read"
                            else ResourceType.MEMORY_WRITE
                        ),
                        capacity=level.banks,
                        throughput=(
                            bandwidth / level.banks
                        ),
                        banks=level.banks,
                        primary=(
                            level.name == "hbm"
                        ),
                    )
                )

    # ------------------------------------------------------------------
    # Residency
    # ------------------------------------------------------------------

    def _total_sram_capacity(self) -> int:
        if "sram" in self.levels:
            return self.levels["sram"].capacity_bytes
        return sum(l.capacity_bytes for n, l in self.levels.items() if n.endswith("_sram"))

    def on_chip_level(
        self,
        bytes: int,
    ) -> str:
        """Level for bytes: sram if fits on-chip else hbm (supports tiling)."""
        cap = self._total_sram_capacity()
        if 0 < bytes <= cap:
            return "sram"
        return "hbm"

    def weights_resident(
        self,
        weight_bytes: int,
    ) -> bool:
        """
        True if a weight working set fits entirely in on-chip SRAM.
        """

        return (
            self.on_chip_level(weight_bytes)
            == "sram"
        )

    def residency_report(
        self,
        weight_bytes: int,
    ) -> dict:
        resident = self.weights_resident(
            weight_bytes
        )

        return {
            "resident": resident,
            "resident_bytes": (
                weight_bytes if resident else 0
            ),
            "hbm_bytes": (
                0 if resident else weight_bytes
            ),
            "level": (
                "sram" if resident else "hbm"
            ),
        }

    # ------------------------------------------------------------------
    # Traffic accounting
    # ------------------------------------------------------------------

    @staticmethod
    def _level_direction(
        resource_name: str,
    ) -> Optional[tuple[str, str]]:
        if resource_name.endswith("_read"):
            return (
                resource_name[:-5],
                "read",
            )

        if resource_name.endswith("_write"):
            return (
                resource_name[:-6],
                "write",
            )

        return None

    def traffic(
        self,
        result: ScheduleResult,
    ) -> dict:
        """
        Per-level read/write bytes aggregated from a finished schedule.
        """

        per_level: dict[str, dict] = {}

        for level_name in self.levels:
            per_level[level_name] = {
                "read_bytes": 0,
                "write_bytes": 0,
                "peak_banks": 0,
            }

        for event in result.events:
            parsed = self._level_direction(
                event.resource_name
            )

            if parsed is None:
                continue

            level_name, direction = parsed

            if level_name not in per_level:
                continue

            per_level[level_name][
                f"{direction}_bytes"
            ] += int(event.work)

        for level_name in per_level:
            per_level[level_name][
                "peak_banks"
            ] = result.peak_banks.get(
                f"{level_name}_read",
                0,
            )

        return per_level

    def report(
        self,
        result: ScheduleResult,
        weight_bytes: int = 0,
    ) -> dict:
        """
        Combined per-level traffic + weight residency summary.
        """

        traffic = self.traffic(result)
        # tiled: aggregate tile*_sram into sram for backward compat
        if "sram" not in traffic:
            sram_r = sum(v["read_bytes"] for k, v in traffic.items() if k.endswith("_sram"))
            sram_w = sum(v["write_bytes"] for k, v in traffic.items() if k.endswith("_sram"))
        else:
            sram_r = traffic["sram"]["read_bytes"]
            sram_w = traffic["sram"]["write_bytes"]
        return {
            "traffic": traffic,
            "weight_residency": self.residency_report(weight_bytes),
            "hbm_read_bytes": traffic.get("hbm", {}).get("read_bytes", 0),
            "hbm_write_bytes": traffic.get("hbm", {}).get("write_bytes", 0),
            "sram_read_bytes": sram_r,
            "sram_write_bytes": sram_w,
        }


def format_memory_report(
    memory_report: dict,
) -> str:
    """
    Compact text rendering of a hierarchy report.
    """

    traffic = memory_report["traffic"]
    residency = memory_report["weight_residency"]

    lines = [
        "MEMORY HIERARCHY",
        "-" * 60,
    ]

    for level_name, level_traffic in traffic.items():
        lines.append(
            f"{level_name.upper():<5}"
            f" read {level_traffic['read_bytes']:>13,} B"
            f"  write {level_traffic['write_bytes']:>13,} B"
            f"  peak banks {level_traffic['peak_banks']}"
        )

    lines.append(
        f"Weights       : "
        f"{'resident (SRAM)' if residency['resident'] else 'streamed (HBM)'}"
    )

    lines.append(
        f"HBM total     : "
        f"{memory_report['hbm_read_bytes'] + memory_report['hbm_write_bytes']:,} B"
    )

    return "\n".join(lines)
