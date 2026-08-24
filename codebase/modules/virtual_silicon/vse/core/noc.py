"""Network-on-Chip model (Phase 4a + Phase C tiling).

Models a configurable interconnect as a set of scheduler resources.
Topology only affects hop distance between nodes; hop count feeds the
per-transfer pipeline latency while the shared "noc" resource carries
link-bandwidth contention.

Phase C (tiling):
- ``NoCConfig.num_tiles`` distributes bandwidth across tiles.
- ``per_tile_bandwidth`` / ``effective_bandwidth`` helpers expose
  per-tile vs aggregate bandwidth. When ``num_tiles>1``, effective
  per-tile share is ``total_bw / num_tiles`` and aggregate is
  ``link_bw * num_tiles``. Congestion reports both global and
  per-tile utilization.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Dict, List, Optional, Tuple

from vse.core.types import Resource, ResourceType, Task


@dataclass
class NoCConfig:
    """Interconnect configuration.

    nodes:
        Number of router nodes. 1 disables cross-node traffic.
    topology:
        "ring" or "mesh".
    link_bw:
        Bytes per cycle per concurrent transfer.
    per_hop_cycles:
        Pipeline latency per hop.
    links:
        Number of concurrent transfers.
    broadcast:
        If true, MoE router broadcasts token tensor to every node.
    num_tiles:
        Distributed tile count for bandwidth scaling (Phase C). When
        >1, per-tile bandwidth is total_bw / num_tiles.
    per_tile_bw:
        If true, link_bw is per-tile and aggregate = link_bw*num_tiles.
    """

    topology: str = "ring"
    nodes: int = 1
    link_bw: int = 256
    per_hop_cycles: int = 4
    links: int = 1
    broadcast: bool = False
    num_tiles: int = 1
    per_tile_bw: bool = False

    def __post_init__(self) -> None:
        if self.topology not in ("ring", "mesh"):
            raise ValueError(f"unknown NoC topology '{self.topology}'")
        if self.nodes < 1:
            raise ValueError("NoC nodes must be >= 1")
        if self.link_bw <= 0:
            raise ValueError("NoC link_bw must be > 0")
        if self.per_hop_cycles < 0:
            raise ValueError("NoC per_hop_cycles must be >= 0")
        if self.links <= 0:
            raise ValueError("NoC links must be > 0")
        if self.num_tiles < 1:
            raise ValueError("NoC num_tiles must be >= 1")
        if self.num_tiles > 64:
            raise ValueError("NoC num_tiles must be <= 64")

    @property
    def enabled(self) -> bool:
        return self.nodes > 1

    def per_tile_bandwidth(self, total_bw: Optional[int] = None, num_tiles: Optional[int] = None) -> float:
        """Per-tile share of bandwidth. ``total_bw/num_tiles`` when tiled."""
        bw = total_bw if total_bw is not None else self.link_bw
        tiles = num_tiles if num_tiles is not None else self.num_tiles
        if tiles is None or tiles <= 1:
            return float(bw)
        return float(bw) / float(tiles)

    def effective_bandwidth(self) -> int:
        """Aggregate bandwidth: link_bw * num_tiles when distributed."""
        if self.num_tiles > 1:
            return self.link_bw * self.num_tiles
        return self.link_bw

    @staticmethod
    def per_tile_bandwidth_static(total_bw: int, num_tiles: int) -> float:
        """Static helper: per-tile bw = total_bw/num_tiles."""
        if num_tiles <= 1:
            return float(total_bw)
        return float(total_bw) / float(num_tiles)


def per_tile_bandwidth(total_bw: int, num_tiles: int) -> float:
    """Module helper: per-tile bandwidth = total_bw / num_tiles."""
    if num_tiles <= 1:
        return float(total_bw)
    return float(total_bw) / float(num_tiles)


@dataclass
class NoC:
    """A NoC instance: nodes, topology, and scheduler resources."""

    config: NoCConfig
    _positions: List[Tuple[int, int]] = field(init=False, repr=False)

    def __post_init__(self) -> None:
        self._positions = self._build_positions()

    def _build_positions(self) -> List[Tuple[int, int]]:
        if self.config.topology == "ring":
            return [(i, 0) for i in range(self.config.nodes)]
        cols = self._grid_cols(self.config.nodes)
        return [(i // cols, i % cols) for i in range(self.config.nodes)]

    @staticmethod
    def _grid_cols(nodes: int) -> int:
        if nodes <= 1:
            return 1
        cols = 1
        while cols * cols < nodes:
            cols += 1
        return cols

    def distance(self, src: int, dst: int) -> int:
        """Hop count between two nodes. Works with tiles mapping to nodes."""
        n = self.config.nodes
        if n <= 1:
            return 0
        if src == dst:
            return 0
        if self.config.topology == "ring":
            diff = abs(src - dst)
            return min(diff, n - diff)
        (r1, c1) = self._positions[src]
        (r2, c2) = self._positions[dst]
        return abs(r1 - r2) + abs(c1 - c2)

    def per_tile_bandwidth(self, total_bw: Optional[int] = None) -> float:
        """Instance helper forwarding to config."""
        return self.config.per_tile_bandwidth(total_bw)

    def effective_bandwidth(self) -> int:
        return self.config.effective_bandwidth()

    def add_resources(self, scheduler) -> None:
        """Register shared noc resource with scheduler."""
        if not self.config.enabled:
            return
        scheduler.add_resource(Resource(name="noc", resource_type=ResourceType.NOC, capacity=self.config.links, throughput=self.config.link_bw))

    def transfer_task(self, task_id: str, name: str, data_bytes: int, src: int, dst: int, dependencies: List[str], metadata: Dict[str, object], dests: Optional[List[int]] = None) -> Task:
        """Transfer over interconnect; dests -> multicast."""
        if dests:
            hops = max(self.distance(src, d) for d in dests)
            return Task(task_id=task_id, name=name, resource_type=ResourceType.NOC, work=float(data_bytes * len(dests)), dependencies=list(dependencies), metadata={**metadata, "kind": "noc_multicast", "src": src, "dests": list(dests), "copies": len(dests), "hops": hops}, units=1, pipeline_latency=hops * self.config.per_hop_cycles)
        hops = self.distance(src, dst)
        return Task(task_id=task_id, name=name, resource_type=ResourceType.NOC, work=float(data_bytes), dependencies=list(dependencies), metadata={**metadata, "kind": "noc", "src": src, "dst": dst, "hops": hops}, units=1, pipeline_latency=hops * self.config.per_hop_cycles)

    def broadcast_task(self, task_id: str, name: str, data_bytes: int, src: int, dependencies: List[str], metadata: Dict[str, object]) -> Task:
        """Broadcast one copy to every node."""
        task = self.transfer_task(task_id=task_id, name=name, data_bytes=data_bytes, src=src, dst=0, dependencies=dependencies, metadata=metadata, dests=list(range(self.config.nodes)))
        task.metadata["kind"] = "noc_broadcast"
        return task

    def aggregate(self, tasks: List[Task]) -> Dict[str, object]:
        """Summary stats over transfer tasks."""
        transfers = [t for t in tasks if t.metadata.get("kind") in ("noc", "noc_multicast", "noc_broadcast")]
        return {"transfers": len(transfers), "bytes": sum(int(t.work) for t in transfers), "hops": sum(int(t.metadata.get("hops", 0)) for t in transfers), "latency_cycles": sum((t.duration for t in transfers), 0), "broadcasts": sum(1 for t in transfers if t.metadata.get("kind") == "noc_broadcast"), "multicasts": sum(1 for t in transfers if t.metadata.get("kind") == "noc_multicast")}

    def congestion(self, schedule) -> Dict[str, object]:
        """Link-bandwidth saturation and per-tile view."""
        util = schedule.resource_utilization("noc") if "noc" in schedule.resources else 0.0
        per_tile = util / self.config.num_tiles if self.config.num_tiles > 1 else util
        return {"utilization": util, "per_tile_utilization": per_tile, "per_tile_bandwidth": self.config.per_tile_bandwidth(), "effective_bandwidth": self.config.effective_bandwidth(), "num_tiles": self.config.num_tiles, "peak_concurrency": schedule.peak_concurrency.get("noc", 0)}

    def report(self, schedule) -> Dict[str, object]:
        """Full NoC report: traffic + congestion + deadlock."""
        report = self.aggregate(schedule.tasks.values())
        report["congestion"] = self.congestion(schedule)
        report["deadlock"] = check_deadlock(schedule.tasks.values())
        return report


def check_deadlock(tasks: List[Task]) -> Dict[str, object]:
    """Detect cyclic dependencies via Kahn's algorithm."""
    indegree: Dict[str, int] = {t.task_id: 0 for t in tasks}
    dependents: Dict[str, List[str]] = {t.task_id: [] for t in tasks}
    known = set(indegree)
    for task in tasks:
        for dep in task.dependencies:
            if dep in known:
                dependents[dep].append(task.task_id)
                indegree[task.task_id] += 1
    queue = [tid for tid, degree in indegree.items() if degree == 0]
    ordered = 0
    while queue:
        tid = queue.pop()
        ordered += 1
        for dependent in dependents[tid]:
            indegree[dependent] -= 1
            if indegree[dependent] == 0:
                queue.append(dependent)
    acyclic = ordered == len(tasks)
    return {"acyclic": acyclic, "cycle_tasks": ([tid for tid, degree in indegree.items() if degree > 0] if not acyclic else [])}
