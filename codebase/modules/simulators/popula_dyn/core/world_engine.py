"""
simulation_engine/world_engine.py

Unified world simulation engine.

Purpose
-------
Acts as the master orchestration layer for all
simulation systems inside agent_unit_pie.

This engine coordinates:

- units
- environments
- economies
- populations
- events
- behaviors
- resources
- timelines
- digital twins
- civilizations
- financial systems

Supported Simulation Domains
----------------------------
- humans
- organizations
- companies
- cities
- states
- countries
- ecosystems
- markets
- global economies
- geopolitical systems
- AI societies

Core Responsibilities
---------------------
- advance simulation ticks
- orchestrate subsystems
- manage world state
- process events
- process behaviors
- process resources
- evolve environments
- trigger simulations
- generate projections
- generate world statistics

Core Philosophy
----------------
The world is an interconnected evolving system.

Everything affects everything else through:

- resources
- behaviors
- incentives
- relations
- information
- feedback loops
"""

from __future__ import annotations

import logging
from datetime import datetime, timezone
from typing import Dict, Any, Optional, List

logger = logging.getLogger(__name__)

class WorldEngine:
    """
    Master simulation orchestrator.
    """
    # INIT
    def __init__(
        self,
        unit_registry=None,
        resource_engine=None,
        behavior_registry=None,
        event_engine=None,
        timeline_engine=None,
        pattern_engine=None,
        relation_engine=None,
        simulation_model=None,
        config: Optional[
            Dict[str, Any]
        ] = None,
    ):
        self.unit_registry = (
            unit_registry
        )
        self.resource_engine = (
            resource_engine
        )
        self.behavior_registry = (
            behavior_registry
        )
        self.event_engine = (
            event_engine
        )
        self.timeline_engine = (
            timeline_engine
        )
        self.pattern_engine = (
            pattern_engine
        )
        self.relation_engine = (
            relation_engine
        )
        self.simulation_model = (
            simulation_model
        )
        self.config = config or {}
        # WORLD STATE
        self.world_state = {
            "world_time": 0,
            "tick_count": 0,
            "simulation_running": False,
            "last_tick_time": None,
        }
        # ENVIRONMENT STATE
        self.environment = {
            "stability": 1.0,
            "economic_health": 1.0,
            "resource_pressure": 0.0,
            "conflict_level": 0.0,
        }
        # TICK HISTORY
        self.tick_history = []
    # START SIMULATION
    def start(
        self,
    ) -> None:
        """
        Start simulation.
        """
        self.world_state[
            "simulation_running"
        ] = True
        logger.info(
            "World simulation started."
        )
    # STOP SIMULATION
    def stop(
        self,
    ) -> None:
        """
        Stop simulation.
        """
        self.world_state[
            "simulation_running"
        ] = False
        logger.info(
            "World simulation stopped."
        )
    # SIMULATION TICK
    def tick(
        self,
        delta_time: int = 1,
    ) -> Dict[str, Any]:
        """
        Advance world simulation.
        """
        if not self.world_state.get(
            "simulation_running"
        ):
            return {
                "status": "stopped"
            }
        # ADVANCE TIME
        self.world_state[
            "world_time"
        ] += delta_time
        self.world_state[
            "tick_count"
        ] += 1
        self.world_state[
            "last_tick_time"
        ] = self.utc_now()
        # PROCESS SIMULATION MODEL
        simulation_results = self.process_simulation()
        # PROCESS SYSTEMS
        behavior_results = (
            self.process_behaviors()
        )
        resource_results = (
            self.process_resources()
        )
        event_results = (
            self.process_events()
        )
        environment_results = (
            self.evolve_environment()
        )
        pattern_results = (
            self.process_patterns()
        )
        # WORLD SNAPSHOT
        snapshot = {
            "tick": (
                self.world_state[
                    "tick_count"
                ]
            ),
            "world_time": (
                self.world_state[
                    "world_time"
                ]
            ),
            "timestamp": (
                self.utc_now()
            ),
            "simulation_results": (
                simulation_results
            ),
            "behavior_results": (
                behavior_results
            ),
            "resource_results": (
                resource_results
            ),
            "event_results": (
                event_results
            ),
            "environment_results": (
                environment_results
            ),
            "pattern_results": (
                pattern_results
            ),
        }
        self.tick_history.append(
            snapshot
        )
        return snapshot
    # PROCESS SIMULATION
    def process_simulation(
        self,
    ) -> Dict[str, Any]:
        """
        Advance the agricultural simulation model.
        """
        if self.simulation_model is None:
            return {
                "status": "no_simulation_model"
            }
        try:
            self.simulation_model.step()
            return {
                "population": (
                    self.simulation_model.get_population_count()
                ),
                "total_wealth": (
                    self.simulation_model.get_total_wealth()
                ),
                "births": (
                    self.simulation_model.births
                ),
                "deaths": (
                    self.simulation_model.deaths
                ),
                "total_units": (
                    len(self.simulation_model.units)
                ),
            }
        except Exception:
            logger.exception(
                "Simulation step failed."
            )
            return {
                "status": "error"
            }
    # PROCESS BEHAVIORS
    def process_behaviors(
        self,
    ) -> Dict[str, Any]:
        """
        Process all active unit behaviors.
        """
        processed = 0
        if (
            self.unit_registry is None
            or self.behavior_registry
            is None
        ):
            return {
                "processed": 0
            }
        for unit in (
            self.unit_registry.units.values()
        ):
            behaviors = unit.get(
                "behaviors",
                [],
            )
            for behavior_name in (
                behaviors
            ):
                try:
                    self.behavior_registry.execute_behavior(
                        behavior_name=(
                            behavior_name
                        ),
                        unit=unit,
                        world_state=(
                            self.world_state
                        ),
                    )
                    processed += 1
                except Exception:
                    logger.exception(
                        "Behavior execution "
                        "failed."
                    )
        return {
            "processed": processed
        }
    # PROCESS RESOURCES
    def process_resources(
        self,
    ) -> Dict[str, Any]:
        """
        Process resource dynamics.
        """
        if self.resource_engine is None:
            return {}
        scarcity = (
            self.resource_engine
            .detect_scarcity()
        )
        bottlenecks = (
            self.resource_engine
            .detect_bottlenecks()
        )
        corruption = (
            self.resource_engine
            .detect_corruption_patterns()
        )
        return {
            "scarcity_count": len(
                scarcity
            ),
            "bottlenecks": len(
                bottlenecks
            ),
            "corruption_flags": len(
                corruption
            ),
        }
    # PROCESS EVENTS
    def process_events(
        self,
    ) -> Dict[str, Any]:
        """
        Process world events.
        """
        if self.event_engine is None:
            return {}
        try:
            events = (
                self.event_engine
                .process_pending_events()
            )
            return {
                "processed_events": len(
                    events
                )
            }
        except Exception:
            logger.exception(
                "Event processing failed."
            )
            return {}
    # EVOLVE ENVIRONMENT
    def evolve_environment(
        self,
    ) -> Dict[str, Any]:
        """
        Evolve world environment state.
        """
        # RESOURCE PRESSURE
        if self.resource_engine:
            scarcity = (
                self.resource_engine
                .detect_scarcity()
            )
            self.environment[
                "resource_pressure"
            ] = min(
                1.0,
                len(scarcity) / 10.0,
            )
        # CONFLICT
        corruption_flags = 0
        if self.resource_engine:
            corruption_flags = len(
                self.resource_engine
                .detect_corruption_patterns()
            )
        self.environment[
            "conflict_level"
        ] = min(
            1.0,
            corruption_flags / 20.0,
        )
        # ECONOMIC HEALTH
        pressure = self.environment[
            "resource_pressure"
        ]
        conflict = self.environment[
            "conflict_level"
        ]
        economic_health = (
            1.0
            - (pressure * 0.5)
            - (conflict * 0.5)
        )
        self.environment[
            "economic_health"
        ] = max(
            0.0,
            economic_health,
        )
        # STABILITY
        self.environment[
            "stability"
        ] = (
            self.environment[
                "economic_health"
            ]
        )
        return self.environment
    # PROCESS PATTERNS
    def process_patterns(
        self,
    ) -> Dict[str, Any]:
        """
        Process pattern generation.
        """
        if self.pattern_engine is None:
            return {}
        try:
            generated = (
                self.pattern_engine
                .detect_patterns()
            )
            return {
                "patterns_detected": len(
                    generated
                )
            }
        except Exception:
            logger.exception(
                "Pattern processing failed."
            )
            return {}
    # GENERATE PROJECTION
    def generate_projection(
        self,
        unit_id: Optional[
            str
        ] = None,
        future_ticks: int = 30,
    ) -> Dict[str, Any]:
        """
        Generate future simulation projection.
        """
        current_state = {
            "environment": dict(
                self.environment
            ),
            "world_time": (
                self.world_state[
                    "world_time"
                ]
            ),
        }
        projections = []
        simulated_environment = dict(
            self.environment
        )
        for tick in range(
            future_ticks
        ):
            # SIMPLE FUTURE EVOLUTION
            simulated_environment[
                "stability"
            ] *= 0.999
            simulated_environment[
                "resource_pressure"
            ] *= 1.001
            projections.append(
                {
                    "future_tick": tick,
                    "environment": dict(
                        simulated_environment
                    ),
                }
            )
        return {
            "current_state": (
                current_state
            ),
            "future_projections": (
                projections
            ),
        }
    # DIGITAL TWIN SNAPSHOT
    def generate_world_snapshot(
        self,
    ) -> Dict[str, Any]:
        """
        Generate full world snapshot.
        """
        active_units = 0
        if self.unit_registry:
            active_units = len(
                self.unit_registry.units
            )
        return {
            "timestamp": (
                self.utc_now()
            ),
            "world_state": (
                self.world_state
            ),
            "environment": (
                self.environment
            ),
            "active_units": (
                active_units
            ),
            "resource_summary": (
                self.resource_engine
                .summarize_resources()
                if self.resource_engine
                else {}
            ),
        }
    # WORLD STATISTICS
    def world_statistics(
        self,
    ) -> Dict[str, Any]:
        """
        Generate world statistics.
        """
        return {
            "ticks": (
                self.world_state[
                    "tick_count"
                ]
            ),
            "world_time": (
                self.world_state[
                    "world_time"
                ]
            ),
            "simulation_running": (
                self.world_state[
                    "simulation_running"
                ]
            ),
            "environment": (
                self.environment
            ),
            "tick_history": len(
                self.tick_history
            ),
        }
    # RESET WORLD
    def reset(
        self,
    ) -> None:
        """
        Reset simulation world.
        """
        self.world_state = {
            "world_time": 0,
            "tick_count": 0,
            "simulation_running": False,
            "last_tick_time": None,
        }
        self.environment = {
            "stability": 1.0,
            "economic_health": 1.0,
            "resource_pressure": 0.0,
            "conflict_level": 0.0,
        }
        self.tick_history.clear()
        logger.info(
            "World simulation reset."
        )
    # HEALTH CHECK
    def health_check(
        self,
    ) -> Dict[str, Any]:
        return {
            "unit_registry": (
                self.unit_registry
                is not None
            ),
            "resource_engine": (
                self.resource_engine
                is not None
            ),
            "behavior_registry": (
                self.behavior_registry
                is not None
            ),
            "event_engine": (
                self.event_engine
                is not None
            ),
            "timeline_engine": (
                self.timeline_engine
                is not None
            ),
            "pattern_engine": (
                self.pattern_engine
                is not None
            ),
            "relation_engine": (
                self.relation_engine
                is not None
            ),
            "simulation_model": (
                self.simulation_model
                is not None
            ),
        }
    # CONVENIENCE FACTORY
    @classmethod
    def with_agricultural_simulation(
        cls,
        params: Optional[Dict[str, Any]] = None,
    ) -> "WorldEngine":
        """
        Create WorldEngine with agricultural simulation.

        Usage:
            world = WorldEngine.with_agricultural_simulation(params)
            world.start()
            for _ in range(100):
                world.tick()
        """
        from modules.simulators.popula_dyn.constants import PARAMS
        from modules.simulators.popula_dyn.core.simulation_model import (
            SimulationModel,
        )
        from modules.simulators.popula_dyn.behavior_registry import (
            BehaviorRegistry,
        )
        params = params or PARAMS
        sim_model = SimulationModel(params)
        return cls(
            simulation_model=sim_model,
            behavior_registry=BehaviorRegistry(),
        )
    # HELPERS
    @staticmethod
    def utc_now() -> str:
        return datetime.now(
            timezone.utc
        ).isoformat()