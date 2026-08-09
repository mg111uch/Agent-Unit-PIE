"""
VSE - Virtual Silicon Engine
vse/core.py

Minimal cycle-accurate simulation kernel.

Purpose:
    Provides the timing/event foundation for the Virtual Silicon Engine.
    Hardware components such as SRAM, MAC arrays, routers, and pipelines
    can schedule work against this simulator.

Design goals:
    - Deterministic
    - Simple
    - No ML/framework dependencies
    - Easy to extend
    - Suitable for architectural experiments

This is NOT a transistor simulator or FPGA simulator.
It models architectural timing at the cycle level.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Callable, Optional
import heapq


# ---------------------------------------------------------------------------
# Events
# ---------------------------------------------------------------------------

@dataclass(order=True)
class Event:
    """
    An event scheduled to occur at a specific simulation cycle.

    Events are ordered by cycle and then by event ID so that simulation
    remains deterministic when multiple events occur on the same cycle.
    """

    cycle: int
    event_id: int
    callback: Callable[[], None]
    name: str = ""


# ---------------------------------------------------------------------------
# Statistics
# ---------------------------------------------------------------------------

@dataclass
class SimulationStats:
    """Basic simulation statistics."""

    events_executed: int = 0
    cycles_executed: int = 0


# ---------------------------------------------------------------------------
# Simulation
# ---------------------------------------------------------------------------

class Simulator:
    """
    Cycle-accurate discrete-event simulator.

    Example:

        sim = Simulator()

        def done():
            print("Operation completed")

        sim.schedule(10, done, name="operation")
        sim.run()

    The callback executes at simulation cycle 10.
    """

    def __init__(self, frequency_hz: float = 1e9):
        if frequency_hz <= 0:
            raise ValueError("frequency_hz must be > 0")

        self.frequency_hz = frequency_hz

        # Current simulated cycle.
        self.cycle: int = 0

        # Monotonically increasing event identifier.
        self._next_event_id: int = 0

        # Priority queue of pending events.
        self._events: list[Event] = []

        # Statistics.
        self.stats = SimulationStats()

        # Simulation state.
        self.running: bool = False

    # ------------------------------------------------------------------
    # Time
    # ------------------------------------------------------------------

    @property
    def time_seconds(self) -> float:
        """Current simulated time in seconds."""
        return self.cycle / self.frequency_hz

    @property
    def time_ns(self) -> float:
        """Current simulated time in nanoseconds."""
        return self.time_seconds * 1e9

    # ------------------------------------------------------------------
    # Event scheduling
    # ------------------------------------------------------------------

    def schedule(
        self,
        delay_cycles: int,
        callback: Callable[[], None],
        name: str = "",
    ) -> int:
        """
        Schedule a callback after delay_cycles.

        Returns:
            Event ID.

        Example:

            sim.schedule(20, callback)

        If current cycle is 100 and delay is 20, the callback executes
        at cycle 120.
        """

        if delay_cycles < 0:
            raise ValueError("delay_cycles must be >= 0")

        if not callable(callback):
            raise TypeError("callback must be callable")

        event_id = self._next_event_id
        self._next_event_id += 1

        event = Event(
            cycle=self.cycle + delay_cycles,
            event_id=event_id,
            callback=callback,
            name=name,
        )

        heapq.heappush(self._events, event)

        return event_id

    def schedule_at(
        self,
        cycle: int,
        callback: Callable[[], None],
        name: str = "",
    ) -> int:
        """
        Schedule a callback at an absolute simulation cycle.
        """

        if cycle < self.cycle:
            raise ValueError(
                f"Cannot schedule event in the past: "
                f"{cycle} < current cycle {self.cycle}"
            )

        if not callable(callback):
            raise TypeError("callback must be callable")

        event_id = self._next_event_id
        self._next_event_id += 1

        event = Event(
            cycle=cycle,
            event_id=event_id,
            callback=callback,
            name=name,
        )

        heapq.heappush(self._events, event)

        return event_id

    # ------------------------------------------------------------------
    # Execution
    # ------------------------------------------------------------------

    def step(self) -> bool:
        """
        Execute the next scheduled event.

        Returns:
            True if an event was executed.
            False if no events remain.
        """

        if not self._events:
            return False

        event = heapq.heappop(self._events)

        # Advance simulation time.
        self.cycle = event.cycle

        # Execute hardware action.
        event.callback()

        self.stats.events_executed += 1
        self.stats.cycles_executed = max(
            self.stats.cycles_executed,
            self.cycle,
        )

        return True

    def run(
        self,
        max_cycles: Optional[int] = None,
        max_events: Optional[int] = None,
    ) -> SimulationStats:
        """
        Run until:

            - no events remain
            - max_cycles is reached
            - max_events is reached

        Returns:
            Simulation statistics.
        """

        self.running = True

        try:
            while self._events:

                if max_events is not None:
                    if self.stats.events_executed >= max_events:
                        break

                next_cycle = self._events[0].cycle

                if max_cycles is not None:
                    if next_cycle > max_cycles:
                        self.cycle = max_cycles
                        break

                if not self.step():
                    break

        finally:
            self.running = False

        return self.stats

    def reset(self) -> None:
        """Reset simulator to cycle zero."""

        self.cycle = 0
        self._next_event_id = 0
        self._events.clear()
        self.stats = SimulationStats()
        self.running = False

    # ------------------------------------------------------------------
    # Inspection
    # ------------------------------------------------------------------

    @property
    def pending_events(self) -> int:
        """Number of events waiting to execute."""
        return len(self._events)

    def __repr__(self) -> str:
        return (
            f"Simulator("
            f"cycle={self.cycle}, "
            f"time_ns={self.time_ns:.3f}, "
            f"pending_events={self.pending_events})"
        )


# ---------------------------------------------------------------------------
# Hardware component base class
# ---------------------------------------------------------------------------

class HardwareComponent:
    """
    Base class for simulated hardware components.

    Memory, compute arrays, routers, and other hardware blocks can inherit
    from this class.

    Components receive a reference to the shared simulator.
    """

    def __init__(
        self,
        simulator: Simulator,
        name: str,
    ):
        if not name:
            raise ValueError("Hardware component requires a name")

        self.sim = simulator
        self.name = name

        # Component-level counters.
        self.operations = 0
        self.busy_cycles = 0

    def schedule(
        self,
        latency_cycles: int,
        callback: Callable[[], None],
        operation_name: str = "",
    ) -> int:
        """
        Schedule an operation performed by this component.
        """

        self.operations += 1

        event_name = (
            f"{self.name}:{operation_name}"
            if operation_name
            else self.name
        )

        return self.sim.schedule(
            latency_cycles,
            callback,
            name=event_name,
        )

    @property
    def utilization(self) -> float:
        """
        Placeholder utilization metric.

        Later hardware components will override this with more precise
        accounting.
        """

        if self.sim.cycle == 0:
            return 0.0

        return min(
            1.0,
            self.busy_cycles / self.sim.cycle,
        )

    def __repr__(self) -> str:
        return (
            f"{self.__class__.__name__}("
            f"name={self.name!r}, "
            f"operations={self.operations})"
        )


# ---------------------------------------------------------------------------
# Simple pipeline stage
# ---------------------------------------------------------------------------

class PipelineStage(HardwareComponent):
    """
    Simple fixed-latency pipeline stage.

    Useful for constructing the first version of the transformer datapath.

    Example:

        stage = PipelineStage(sim, "attention", latency_cycles=20)

        stage.process(lambda: print("attention complete"))
    """

    def __init__(
        self,
        simulator: Simulator,
        name: str,
        latency_cycles: int,
    ):
        super().__init__(simulator, name)

        if latency_cycles <= 0:
            raise ValueError("latency_cycles must be > 0")

        self.latency_cycles = latency_cycles

    def process(
        self,
        callback: Callable[[], None],
    ) -> int:
        """Send an operation through the pipeline stage."""

        self.busy_cycles += self.latency_cycles

        return self.schedule(
            self.latency_cycles,
            callback,
            operation_name="process",
        )


# ---------------------------------------------------------------------------
# Convenience function
# ---------------------------------------------------------------------------

def cycles_to_seconds(
    cycles: int,
    frequency_hz: float,
) -> float:
    """Convert simulation cycles to seconds."""

    if cycles < 0:
        raise ValueError("cycles must be >= 0")

    if frequency_hz <= 0:
        raise ValueError("frequency_hz must be > 0")

    return cycles / frequency_hz


def cycles_to_nanoseconds(
    cycles: int,
    frequency_hz: float,
) -> float:
    """Convert simulation cycles to nanoseconds."""

    return cycles_to_seconds(cycles, frequency_hz) * 1e9
