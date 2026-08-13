"""Network-on-Chip model (Phase 4a).

Models a configurable interconnect as a set of scheduler resources.
Topology only affects hop distance between nodes; hop count feeds the
per-transfer pipeline latency while the shared "noc" resource carries
link-bandwidth contention.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Dict, List, Optional, Tuple

from vse.core.types import Resource, ResourceType, Task


@dataclass
class NoCConfig:
    """Interconnect configuration.

    nodes:
        Number of router nodes. 1 (default) disables cross-node traffic.

    topology:
        "ring" or "mesh".

    link_bw:
        Bytes per cycle per concurrent transfer (throughput).

    per_hop_cycles:
        Pipeline latency per hop (routing + transit).

    links:
        Number of concurrent transfers the interconnect can carry.

    broadcast:
        If true, the MoE router broadcasts the full token tensor to
        every node instead of sending per-expert token slices.
    """

    topology: str = "ring"
    nodes: int = 1
    link_bw: int = 256
    per_hop_cycles: int = 4
    links: int = 1
    broadcast: bool = False

    def __post_init__(self) -> None:
        if self.topology not in ("ring", "mesh"):
            raise ValueError(
                f"unknown NoC topology '{self.topology}'"
            )

        if self.nodes < 1:
            raise ValueError("NoC nodes must be >= 1")

        if self.link_bw <= 0:
            raise ValueError("NoC link_bw must be > 0")

        if self.per_hop_cycles < 0:
            raise ValueError("NoC per_hop_cycles must be >= 0")

        if self.links <= 0:
            raise ValueError("NoC links must be > 0")

    @property
    def enabled(self) -> bool:
        return self.nodes > 1


@dataclass
class NoC:
    """A NoC instance: nodes, topology, and scheduler resources."""

    config: NoCConfig
    _positions: List[Tuple[int, int]] = field(
        init=False, repr=False
    )

    def __post_init__(self) -> None:
        self._positions = self._build_positions()

    def _build_positions(self) -> List[Tuple[int, int]]:
        if self.config.topology == "ring":
            return [(i, 0) for i in range(self.config.nodes)]

        cols = self._grid_cols(self.config.nodes)
        return [
            (i // cols, i % cols)
            for i in range(self.config.nodes)
        ]

    @staticmethod
    def _grid_cols(nodes: int) -> int:
        if nodes <= 1:
            return 1

        cols = 1
        while cols * cols < nodes:
            cols += 1

        return cols

    def distance(self, src: int, dst: int) -> int:
        """Hop count between two nodes."""
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

    def add_resources(self, scheduler) -> None:
        """Register the shared noc resource with the scheduler."""
        if not self.config.enabled:
            return

        scheduler.add_resource(
            Resource(
                name="noc",
                resource_type=ResourceType.NOC,
                capacity=self.config.links,
                throughput=self.config.link_bw,
            )
        )

    def transfer_task(
        self,
        task_id: str,
        name: str,
        data_bytes: int,
        src: int,
        dst: int,
        dependencies: List[str],
        metadata: Dict[str, object],
        dests: Optional[List[int]] = None,
    ) -> Task:
        """
        A transfer over the interconnect.

        With a single `dst` this is a point-to-point transfer. With
        `dests` given it becomes a multicast: the source sends a copy to
        every destination, so link work scales with the number of copies
        and latency is the farthest destination.
        """
        if dests:
            hops = max(
                self.distance(src, d) for d in dests
            )
            return Task(
                task_id=task_id,
                name=name,
                resource_type=ResourceType.NOC,
                work=float(data_bytes * len(dests)),
                dependencies=list(dependencies),
                metadata={
                    **metadata,
                    "kind": "noc_multicast",
                    "src": src,
                    "dests": list(dests),
                    "copies": len(dests),
                    "hops": hops,
                },
                units=1,
                pipeline_latency=(
                    hops * self.config.per_hop_cycles
                ),
            )

        hops = self.distance(src, dst)

        return Task(
            task_id=task_id,
            name=name,
            resource_type=ResourceType.NOC,
            work=float(data_bytes),
            dependencies=list(dependencies),
            metadata={
                **metadata,
                "kind": "noc",
                "src": src,
                "dst": dst,
                "hops": hops,
            },
            units=1,
            pipeline_latency=hops * self.config.per_hop_cycles,
        )

    def broadcast_task(
        self,
        task_id: str,
        name: str,
        data_bytes: int,
        src: int,
        dependencies: List[str],
        metadata: Dict[str, object],
    ) -> Task:
        """Broadcast one copy of `data_bytes` to every node."""
        task = self.transfer_task(
            task_id=task_id,
            name=name,
            data_bytes=data_bytes,
            src=src,
            dst=0,
            dependencies=dependencies,
            metadata=metadata,
            dests=list(range(self.config.nodes)),
        )
        task.metadata["kind"] = "noc_broadcast"
        return task

    def aggregate(
        self, tasks: List[Task]
    ) -> Dict[str, object]:
        """Summary stats over the given transfer tasks."""
        transfers = [
            t for t in tasks
            if t.metadata.get("kind") in (
                "noc", "noc_multicast", "noc_broadcast",
            )
        ]

        return {
            "transfers": len(transfers),
            "bytes": sum(
                int(t.work) for t in transfers
            ),
            "hops": sum(
                int(t.metadata.get("hops", 0))
                for t in transfers
            ),
            "latency_cycles": sum(
                (t.duration for t in transfers),
                0,
            ),
            "broadcasts": sum(
                1 for t in transfers
                if t.metadata.get("kind") == "noc_broadcast"
            ),
            "multicasts": sum(
                1 for t in transfers
                if t.metadata.get("kind") == "noc_multicast"
            ),
        }

    def congestion(
        self, schedule,
    ) -> Dict[str, object]:
        """Link-bandwidth saturation and peak in-flight transfers."""
        return {
            "utilization": (
                schedule.resource_utilization("noc")
                if "noc" in schedule.resources
                else 0.0
            ),
            "peak_concurrency": (
                schedule.peak_concurrency.get("noc", 0)
            ),
        }

    def report(
        self, schedule,
    ) -> Dict[str, object]:
        """Full NoC report: traffic + congestion + deadlock status."""
        report = self.aggregate(
            schedule.tasks.values()
        )
        report["congestion"] = self.congestion(schedule)
        report["deadlock"] = check_deadlock(
            schedule.tasks.values()
        )
        return report


def check_deadlock(
    tasks: List[Task],
) -> Dict[str, object]:
    """
    Detect cyclic resource dependencies (NoC deadlock) via Kahn's
    algorithm. The cycle engine schedules acyclic graphs, so this is a
    validation pass over any candidate task graph.
    """
    indegree: Dict[str, int] = {
        t.task_id: 0 for t in tasks
    }
    dependents: Dict[str, List[str]] = {
        t.task_id: [] for t in tasks
    }
    known = set(indegree)

    for task in tasks:
        for dep in task.dependencies:
            if dep in known:
                dependents[dep].append(task.task_id)
                indegree[task.task_id] += 1

    queue = [
        tid for tid, degree in indegree.items()
        if degree == 0
    ]
    ordered = 0

    while queue:
        tid = queue.pop()
        ordered += 1
        for dependent in dependents[tid]:
            indegree[dependent] -= 1
            if indegree[dependent] == 0:
                queue.append(dependent)

    acyclic = ordered == len(tasks)

    return {
        "acyclic": acyclic,
        "cycle_tasks": (
            [tid for tid, degree in indegree.items()
             if degree > 0]
            if not acyclic
            else []
        ),
    }
