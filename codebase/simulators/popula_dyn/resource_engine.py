"""
simulation_engine/resource_engine.py

Unified resource simulation engine.

Purpose
-------
Simulates resource creation, movement, allocation,
consumption, scarcity, abundance, and optimization
across all unit systems.

Supported Domains
-----------------
- humans
- organizations
- companies
- cities
- states
- countries
- ecosystems
- economies
- digital twins
- civilization simulations

Supported Resource Types
------------------------
- money
- energy
- food
- water
- land
- labor
- compute
- knowledge
- infrastructure
- materials
- influence
- attention
- time

Core Responsibilities
---------------------
- track resources
- allocate resources
- transfer resources
- simulate scarcity
- simulate abundance
- detect bottlenecks
- simulate economic flows
- detect corruption leakage
- optimize distributions
- forecast resource collapse

Core Philosophy
----------------
Resources are fundamental system constraints.

Most behaviors, conflicts, opportunities,
and collapses emerge from:

resource distribution dynamics.
"""

from __future__ import annotations

import logging
from datetime import datetime, timezone
from typing import Dict, Any, Optional, List


logger = logging.getLogger(__name__)


class ResourceEngine:
    """
    Unified resource simulation engine.
    """

    # ============================================================
    # INIT
    # ============================================================

    def __init__(
        self,
        ontology_registry=None,
        unit_registry=None,
        event_engine=None,
        pattern_engine=None,
        config: Optional[
            Dict[str, Any]
        ] = None,
    ):

        self.ontology_registry = (
            ontology_registry
        )

        self.unit_registry = (
            unit_registry
        )

        self.event_engine = (
            event_engine
        )

        self.pattern_engine = (
            pattern_engine
        )

        self.config = config or {}

        # --------------------------------------------------------
        # GLOBAL RESOURCE STATE
        # --------------------------------------------------------

        self.resource_pools = {}

        # --------------------------------------------------------
        # RESOURCE TRANSFERS
        # --------------------------------------------------------

        self.transfer_history = []

        # --------------------------------------------------------
        # RESOURCE ALERTS
        # --------------------------------------------------------

        self.resource_alerts = []

    # ============================================================
    # CREATE RESOURCE POOL
    # ============================================================

    def create_resource_pool(
        self,
        resource_type: str,
        initial_amount: float = 0.0,
        metadata: Optional[
            Dict[str, Any]
        ] = None,
    ) -> Dict[str, Any]:
        """
        Create global resource pool.
        """

        pool = {
            "resource_type": (
                resource_type
            ),
            "total_amount": (
                float(initial_amount)
            ),
            "created_at": (
                self.utc_now()
            ),
            "updated_at": (
                self.utc_now()
            ),
            "metadata": (
                metadata or {}
            ),
        }

        self.resource_pools[
            resource_type
        ] = pool

        logger.info(
            f"Created resource pool: "
            f"{resource_type}"
        )

        return pool

    # ============================================================
    # GET RESOURCE POOL
    # ============================================================

    def get_resource_pool(
        self,
        resource_type: str,
    ) -> Optional[Dict[str, Any]]:

        return self.resource_pools.get(
            resource_type
        )

    # ============================================================
    # ADD RESOURCE
    # ============================================================

    def add_resource(
        self,
        resource_type: str,
        amount: float,
    ) -> bool:
        """
        Add resources into pool.
        """

        pool = self.get_resource_pool(
            resource_type
        )

        if pool is None:

            pool = (
                self.create_resource_pool(
                    resource_type
                )
            )

        pool["total_amount"] += float(
            amount
        )

        pool["updated_at"] = (
            self.utc_now()
        )

        return True

    # ============================================================
    # REMOVE RESOURCE
    # ============================================================

    def remove_resource(
        self,
        resource_type: str,
        amount: float,
    ) -> bool:
        """
        Remove resources from pool.
        """

        pool = self.get_resource_pool(
            resource_type
        )

        if pool is None:
            return False

        if (
            pool["total_amount"]
            < amount
        ):
            return False

        pool["total_amount"] -= float(
            amount
        )

        pool["updated_at"] = (
            self.utc_now()
        )

        return True

    # ============================================================
    # ALLOCATE RESOURCE
    # ============================================================

    def allocate_resource(
        self,
        unit_id: str,
        resource_type: str,
        amount: float,
    ) -> bool:
        """
        Allocate resource to unit.
        """

        unit = self.resolve_unit(
            unit_id
        )

        if unit is None:
            return False

        success = self.remove_resource(
            resource_type,
            amount,
        )

        if not success:
            return False

        resources = unit.setdefault(
            "resources",
            {}
        )

        resources.setdefault(
            resource_type,
            0.0,
        )

        resources[
            resource_type
        ] += float(amount)

        self.emit_resource_event(
            event_type=(
                "resource_allocated"
            ),
            unit_id=unit_id,
            resource_type=resource_type,
            amount=amount,
        )

        return True

    # ============================================================
    # TRANSFER RESOURCE
    # ============================================================

    def transfer_resource(
        self,
        source_unit_id: str,
        target_unit_id: str,
        resource_type: str,
        amount: float,
        metadata: Optional[
            Dict[str, Any]
        ] = None,
    ) -> bool:
        """
        Transfer resources between units.
        """

        source = self.resolve_unit(
            source_unit_id
        )

        target = self.resolve_unit(
            target_unit_id
        )

        if (
            source is None
            or target is None
        ):
            return False

        source_resources = (
            source.setdefault(
                "resources",
                {}
            )
        )

        current = source_resources.get(
            resource_type,
            0.0,
        )

        if current < amount:
            return False

        # --------------------------------------------------------
        # REMOVE FROM SOURCE
        # --------------------------------------------------------

        source_resources[
            resource_type
        ] -= float(amount)

        # --------------------------------------------------------
        # ADD TO TARGET
        # --------------------------------------------------------

        target_resources = (
            target.setdefault(
                "resources",
                {}
            )
        )

        target_resources.setdefault(
            resource_type,
            0.0,
        )

        target_resources[
            resource_type
        ] += float(amount)

        # --------------------------------------------------------
        # LOG TRANSFER
        # --------------------------------------------------------

        transfer = {
            "source_unit_id": (
                source_unit_id
            ),
            "target_unit_id": (
                target_unit_id
            ),
            "resource_type": (
                resource_type
            ),
            "amount": float(amount),
            "timestamp": (
                self.utc_now()
            ),
            "metadata": (
                metadata or {}
            ),
        }

        self.transfer_history.append(
            transfer
        )

        # --------------------------------------------------------
        # EVENT
        # --------------------------------------------------------

        self.emit_resource_event(
            event_type=(
                "resource_transferred"
            ),
            unit_id=source_unit_id,
            resource_type=resource_type,
            amount=amount,
        )

        return True

    # ============================================================
    # CONSUME RESOURCE
    # ============================================================

    def consume_resource(
        self,
        unit_id: str,
        resource_type: str,
        amount: float,
    ) -> bool:
        """
        Consume resources from unit.
        """

        unit = self.resolve_unit(
            unit_id
        )

        if unit is None:
            return False

        resources = unit.setdefault(
            "resources",
            {}
        )

        current = resources.get(
            resource_type,
            0.0,
        )

        if current < amount:
            return False

        resources[
            resource_type
        ] -= float(amount)

        self.emit_resource_event(
            event_type=(
                "resource_consumed"
            ),
            unit_id=unit_id,
            resource_type=resource_type,
            amount=amount,
        )

        return True

    # ============================================================
    # SCARCITY DETECTION
    # ============================================================

    def detect_scarcity(
        self,
        threshold: float = 10.0,
    ) -> List[Dict[str, Any]]:
        """
        Detect scarce resources.
        """

        scarce = []

        for resource_type, pool in (
            self.resource_pools.items()
        ):

            amount = pool.get(
                "total_amount",
                0.0,
            )

            if amount <= threshold:

                scarce.append(
                    {
                        "resource_type": (
                            resource_type
                        ),
                        "amount": amount,
                        "status": (
                            "scarcity"
                        ),
                    }
                )

        return scarce

    # ============================================================
    # ABUNDANCE DETECTION
    # ============================================================

    def detect_abundance(
        self,
        threshold: float = 1000000.0,
    ) -> List[Dict[str, Any]]:
        """
        Detect highly abundant resources.
        """

        abundant = []

        for resource_type, pool in (
            self.resource_pools.items()
        ):

            amount = pool.get(
                "total_amount",
                0.0,
            )

            if amount >= threshold:

                abundant.append(
                    {
                        "resource_type": (
                            resource_type
                        ),
                        "amount": amount,
                        "status": (
                            "abundance"
                        ),
                    }
                )

        return abundant

    # ============================================================
    # BOTTLENECK DETECTION
    # ============================================================

    def detect_bottlenecks(
        self,
    ) -> List[Dict[str, Any]]:
        """
        Detect resource bottlenecks.
        """

        bottlenecks = []

        scarce = self.detect_scarcity()

        for item in scarce:

            bottlenecks.append(
                {
                    "resource_type": (
                        item[
                            "resource_type"
                        ]
                    ),
                    "severity": "high",
                    "reason": (
                        "resource_scarcity"
                    ),
                }
            )

        return bottlenecks

    # ============================================================
    # CORRUPTION DETECTION
    # ============================================================

    def detect_corruption_patterns(
        self,
    ) -> List[Dict[str, Any]]:
        """
        Detect suspicious resource flows.
        """

        suspicious = []

        for transfer in (
            self.transfer_history
        ):

            amount = transfer.get(
                "amount",
                0.0,
            )

            # ----------------------------------------------------
            # SIMPLE HEURISTIC
            # ----------------------------------------------------

            if amount > 10000000:

                suspicious.append(
                    {
                        "type": (
                            "large_transfer"
                        ),
                        "transfer": transfer,
                    }
                )

        return suspicious

    # ============================================================
    # ECONOMIC FLOW SIMULATION
    # ============================================================

    def simulate_economic_cycle(
        self,
    ) -> Dict[str, Any]:
        """
        Simulate economic movement.
        """

        total_resources = sum(
            pool.get(
                "total_amount",
                0.0,
            )
            for pool in (
                self.resource_pools.values()
            )
        )

        return {
            "timestamp": (
                self.utc_now()
            ),
            "total_resources": (
                total_resources
            ),
            "resource_pools": len(
                self.resource_pools
            ),
            "transfers": len(
                self.transfer_history
            ),
        }

    # ============================================================
    # FORECAST COLLAPSE
    # ============================================================

    def forecast_resource_collapse(
        self,
    ) -> Dict[str, Any]:
        """
        Forecast collapse risks.
        """

        bottlenecks = (
            self.detect_bottlenecks()
        )

        risks = []

        for bottleneck in bottlenecks:

            risks.append(
                {
                    "resource_type": (
                        bottleneck[
                            "resource_type"
                        ]
                    ),
                    "risk_level": "high",
                    "forecast": (
                        "potential_system_"
                        "instability"
                    ),
                }
            )

        return {
            "risks": risks,
            "risk_count": len(
                risks
            ),
        }

    # ============================================================
    # RESOURCE SUMMARY
    # ============================================================

    def summarize_resources(
        self,
    ) -> Dict[str, Any]:
        """
        Generate resource statistics.
        """

        total = sum(
            pool.get(
                "total_amount",
                0.0,
            )
            for pool in (
                self.resource_pools.values()
            )
        )

        return {
            "resource_types": len(
                self.resource_pools
            ),
            "total_resources": total,
            "transfers": len(
                self.transfer_history
            ),
            "alerts": len(
                self.resource_alerts
            ),
        }

    # ============================================================
    # EVENT EMISSION
    # ============================================================

    def emit_resource_event(
        self,
        event_type: str,
        unit_id: str,
        resource_type: str,
        amount: float,
    ) -> None:
        """
        Emit simulation resource event.
        """

        if self.event_engine is None:
            return

        try:

            self.event_engine.create_event(
                event_type=event_type,
                unit_id=unit_id,
                metadata={
                    "resource_type": (
                        resource_type
                    ),
                    "amount": amount,
                },
            )

        except Exception:

            logger.exception(
                "Failed emitting "
                "resource event."
            )

    # ============================================================
    # UNIT RESOLUTION
    # ============================================================

    def resolve_unit(
        self,
        unit_id: str,
    ) -> Optional[Dict[str, Any]]:
        """
        Resolve unit from registry.
        """

        if self.unit_registry is None:

            return None

        return self.unit_registry.get_unit(
            unit_id
        )

    # ============================================================
    # HEALTH CHECK
    # ============================================================

    def health_check(
        self,
    ) -> Dict[str, Any]:

        return {
            "resource_pools": len(
                self.resource_pools
            ),
            "transfers": len(
                self.transfer_history
            ),
            "ontology_registry": (
                self.ontology_registry
                is not None
            ),
            "unit_registry": (
                self.unit_registry
                is not None
            ),
            "event_engine": (
                self.event_engine
                is not None
            ),
            "pattern_engine": (
                self.pattern_engine
                is not None
            ),
        }

    # ============================================================
    # HELPERS
    # ============================================================

    @staticmethod
    def utc_now() -> str:

        return datetime.now(
            timezone.utc
        ).isoformat()