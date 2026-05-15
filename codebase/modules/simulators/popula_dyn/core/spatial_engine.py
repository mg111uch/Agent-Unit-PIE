"""
core/spatial_engine.py

Spatial engine for behavior-based simulation.

Purpose
-------
Manages unit positions in toroidal space.
Adapted from old_str/base_classes.py MultiGrid for UnitAgent.

Usage
-----
    from core.spatial_engine import SpatialEngine
    
    engine = SpatialEngine(width=20, height=20)
    engine.place_agent(unit, (x, y))
    neighbors = engine.get_neighbors(unit, radius=2)
"""

from typing import Dict, List, Tuple, Optional, Any


class SpatialEngine:
    """
    Grid-based spatial management for units.
    """

    def __init__(
        self,
        width: int = 20,
        height: int = 20,
        torus: bool = True,
    ):
        self.width = width
        self.height = height
        self.torus = torus
        self.grid: Dict[Tuple[int, int], List[Any]] = {}

        for x in range(width):
            for y in range(height):
                self.grid[(x, y)] = []

    def place_agent(
        self,
        unit: Any,
        pos: Tuple[int, int],
    ) -> None:
        """Place a unit at the specified position."""

        if pos in self.grid:
            unit.pos = pos
            self.grid[pos].append(unit)

    def remove_agent(self, unit: Any) -> None:
        """Remove a unit from its current position."""

        if hasattr(unit, "pos") and unit.pos in self.grid:
            if unit in self.grid[unit.pos]:
                self.grid[unit.pos].remove(unit)
            unit.pos = None

    def move_agent(
        self,
        unit: Any,
        pos: Tuple[int, int],
    ) -> None:
        """Move a unit to a new position."""

        self.remove_agent(unit)
        if pos in self.grid:
            unit.pos = pos
            self.grid[pos].append(unit)

    def get_cell_list_contents(
        self,
        positions: List[Tuple[int, int]],
    ) -> List[Any]:
        """Get all units at the specified positions."""

        contents = []
        for pos in positions:
            if pos in self.grid:
                contents.extend(self.grid[pos])
        return contents

    def get_neighborhood(
        self,
        pos: Tuple[int, int],
        moore: bool = True,
        include_center: bool = False,
        radius: int = 1,
    ) -> List[Tuple[int, int]]:
        """Get neighboring positions within the given radius."""

        x, y = pos
        neighbors = []

        for dx in range(-radius, radius + 1):
            for dy in range(-radius, radius + 1):
                if not moore and abs(dx) + abs(dy) > radius:
                    continue
                if not include_center and dx == 0 and dy == 0:
                    continue

                nx, ny = x + dx, y + dy

                if self.torus:
                    nx %= self.width
                    ny %= self.height

                if 0 <= nx < self.width and 0 <= ny < self.height:
                    neighbors.append((nx, ny))

        return neighbors

    def is_cell_empty(self, pos: Tuple[int, int]) -> bool:
        """Check if a cell is empty."""

        return len(self.grid.get(pos, [])) == 0

    def get_neighbors(
        self,
        pos: Tuple[int, int],
        moore: bool = True,
        radius: int = 1,
        include_center: bool = False,
    ) -> List[Any]:
        """Get all units in neighboring positions."""

        neighborhood = self.get_neighborhood(pos, moore, include_center, radius)
        neighbors = []

        for p in neighborhood:
            neighbors.extend(self.grid.get(p, []))

        return neighbors

    def get_units_at(self, pos: Tuple[int, int]) -> List[Any]:
        """Get all units at a specific position."""

        return self.grid.get(pos, [])

    def is_valid_position(self, pos: Tuple[int, int]) -> bool:
        """Check if position is within grid bounds."""

        x, y = pos
        return 0 <= x < self.width and 0 <= y < self.height

    def get_random_position(self) -> Tuple[int, int]:
        """Get a random position on the grid."""

        import numpy as np

        return (
            np.random.randint(self.width),
            np.random.randint(self.height),
        )

    def get_all_positions(self) -> List[Tuple[int, int]]:
        """Get all valid grid positions."""

        return list(self.grid.keys())

    def summary(self) -> Dict[str, Any]:
        """Get spatial summary."""

        total_units = sum(len(cells) for cells in self.grid.values())
        occupied_cells = sum(
            1 for cells in self.grid.values() if cells
        )

        return {
            "width": self.width,
            "height": self.height,
            "total_units": total_units,
            "occupied_cells": occupied_cells,
            "torus": self.torus,
        }