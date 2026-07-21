"""
storage/unit_storage.py

Universal unit-centric storage system.

Purpose
-------
Provides persistent storage and retrieval for all unit types:

- humans
- companies
- cities
- countries
- organizations
- stocks
- simulations

This replaces fragmented topic-centric storage with:

unit-centric cognition storage.

Storage Philosophy
------------------
Each unit maintains:

identity/
timeline/
signals/
patterns/
relations/
hypotheses/
summaries/
working_memory/

This file acts as the foundational persistence layer
for the entire agent_unit_pie architecture.
"""

from __future__ import annotations

import json
import logging
from pathlib import Path
from datetime import datetime, timezone
from typing import Dict, Any, Optional, List

logger = logging.getLogger(__name__)

class UnitStorage:
    """
    Universal persistent unit storage manager.
    """
    # INIT
    def __init__(
        self,
        base_path: str = "units",
    ):
        self.base_path = Path(base_path)
        self.base_path.mkdir(
            parents=True,
            exist_ok=True,
        )
    # UNIT CREATION
    def create_unit(
        self,
        unit_id: str,
        unit_type: str,
        metadata: Optional[Dict[str, Any]] = None,
    ) -> Dict[str, Any]:
        """
        Create new unit directory structure.
        """
        unit_path = self.get_unit_path(
            unit_type,
            unit_id,
        )
        unit_path.mkdir(
            parents=True,
            exist_ok=True,
        )
        # STANDARD SUBDIRECTORIES
        subdirs = [
            "identity",
            "timeline",
            "signals",
            "patterns",
            "relations",
            "hypotheses",
            "summaries",
            "working_memory",
            "events",
            "observations",
            "simulations",
            "digital_twin",
        ]
        for subdir in subdirs:
            (
                unit_path / subdir
            ).mkdir(
                parents=True,
                exist_ok=True,
            )
        # IDENTITY FILE
        identity = {
            "unit_id": unit_id,
            "unit_type": unit_type,
            "created_at": self.utc_now(),
            "updated_at": self.utc_now(),
            "metadata": metadata or {},
        }
        self.write_json(
            unit_path
            / "identity"
            / "identity.json",
            identity,
        )
        logger.info(
            f"Created unit: {unit_type}/{unit_id}"
        )
        return identity
    # UNIT LOADING
    def load_unit(
        self,
        unit_type: str,
        unit_id: str,
    ) -> Optional[Dict[str, Any]]:
        """
        Load unit identity.
        """
        identity_path = (
            self.get_unit_path(
                unit_type,
                unit_id,
            )
            / "identity"
            / "identity.json"
        )
        if not identity_path.exists():
            return None
        return self.read_json(identity_path)
    # SAVE OBSERVATION
    def save_observation(
        self,
        unit_type: str,
        unit_id: str,
        observation: Dict[str, Any],
    ) -> str:
        """
        Store observation.
        """
        observation_id = observation.get(
            "observation_id",
            self.generate_timestamp_id(),
        )
        path = (
            self.get_unit_path(
                unit_type,
                unit_id,
            )
            / "observations"
            / f"{observation_id}.json"
        )
        self.write_json(path, observation)
        return observation_id
    # SAVE EVENT
    def save_event(
        self,
        unit_type: str,
        unit_id: str,
        event: Dict[str, Any],
    ) -> str:
        """
        Store event.
        """
        event_id = event.get(
            "event_id",
            self.generate_timestamp_id(),
        )
        path = (
            self.get_unit_path(
                unit_type,
                unit_id,
            )
            / "events"
            / f"{event_id}.json"
        )
        self.write_json(path, event)
        return event_id
    # SAVE SIGNAL
    def save_signal(
        self,
        unit_type: str,
        unit_id: str,
        signal: Dict[str, Any],
    ) -> str:
        """
        Store signal.
        """
        signal_id = signal.get(
            "signal_id",
            self.generate_timestamp_id(),
        )
        path = (
            self.get_unit_path(
                unit_type,
                unit_id,
            )
            / "signals"
            / f"{signal_id}.json"
        )
        self.write_json(path, signal)
        return signal_id
    # SAVE PATTERN
    def save_pattern(
        self,
        unit_type: str,
        unit_id: str,
        pattern: Dict[str, Any],
    ) -> str:
        """
        Store pattern.
        """
        pattern_id = pattern.get(
            "pattern_id",
            self.generate_timestamp_id(),
        )
        path = (
            self.get_unit_path(
                unit_type,
                unit_id,
            )
            / "patterns"
            / f"{pattern_id}.json"
        )
        self.write_json(path, pattern)
        return pattern_id
    # SAVE RELATION
    def save_relation(
        self,
        unit_type: str,
        unit_id: str,
        relation: Dict[str, Any],
    ) -> str:
        """
        Store relation.
        """
        relation_id = relation.get(
            "relation_id",
            self.generate_timestamp_id(),
        )
        path = (
            self.get_unit_path(
                unit_type,
                unit_id,
            )
            / "relations"
            / f"{relation_id}.json"
        )
        self.write_json(path, relation)
        return relation_id
    # SAVE SUMMARY
    def save_summary(
        self,
        unit_type: str,
        unit_id: str,
        summary_name: str,
        summary_data: Dict[str, Any],
    ) -> None:
        """
        Store compressed summaries.
        """
        path = (
            self.get_unit_path(
                unit_type,
                unit_id,
            )
            / "summaries"
            / f"{summary_name}.json"
        )
        self.write_json(path, summary_data)
    # SAVE WORKING MEMORY
    def save_working_memory(
        self,
        unit_type: str,
        unit_id: str,
        memory_name: str,
        memory_data: Dict[str, Any],
    ) -> None:
        """
        Store generated working memory packets.
        """
        path = (
            self.get_unit_path(
                unit_type,
                unit_id,
            )
            / "working_memory"
            / f"{memory_name}.json"
        )
        self.write_json(path, memory_data)
    # LIST UNITS
    def list_units(
        self,
        unit_type: Optional[str] = None,
    ) -> List[str]:
        """
        List stored units.
        """
        if unit_type:
            path = self.base_path / unit_type
            if not path.exists():
                return []
            return sorted(
                [
                    p.name
                    for p in path.iterdir()
                    if p.is_dir()
                ]
            )
        all_units = []
        for type_dir in self.base_path.iterdir():
            if not type_dir.is_dir():
                continue
            for unit_dir in type_dir.iterdir():
                if unit_dir.is_dir():
                    all_units.append(
                        f"{type_dir.name}/{unit_dir.name}"
                    )
        return sorted(all_units)
    # UNIT EXISTS
    def unit_exists(
        self,
        unit_type: str,
        unit_id: str,
    ) -> bool:
        return self.get_unit_path(
            unit_type,
            unit_id,
        ).exists()
    # DELETE UNIT
    def delete_unit(
        self,
        unit_type: str,
        unit_id: str,
    ) -> bool:
        """
        Delete unit recursively.
        """
        import shutil
        unit_path = self.get_unit_path(
            unit_type,
            unit_id,
        )
        if not unit_path.exists():
            return False
        shutil.rmtree(unit_path)
        logger.info(
            f"Deleted unit: {unit_type}/{unit_id}"
        )
        return True
    # PATH HELPERS
    def get_unit_path(
        self,
        unit_type: str,
        unit_id: str,
    ) -> Path:
        return (
            self.base_path
            / unit_type
            / unit_id
        )
    # JSON HELPERS
    def write_json(
        self,
        path: Path,
        data: Dict[str, Any],
    ) -> None:
        write_json(path, data)

    def read_json(
        self,
        path: Path,
    ) -> Dict[str, Any]:
        return read_json(path)


# STANDALONE JSON HELPERS (canonical I/O — used by both storage/ and kernel/memory)

def write_json(
    path: Path,
    data: Dict[str, Any],
) -> None:
    path.parent.mkdir(
        parents=True,
        exist_ok=True,
    )
    with open(
        path,
        "w",
        encoding="utf-8",
    ) as f:
        json.dump(
            data,
            f,
            indent=2,
            ensure_ascii=False,
        )


def read_json(
    path: Path,
) -> Dict[str, Any]:
    with open(
        path,
        "r",
        encoding="utf-8",
    ) as f:
        return json.load(f)
    # HELPERS
    @staticmethod
    def utc_now() -> str:
        return datetime.now(
            timezone.utc
        ).isoformat()

    @staticmethod
    def generate_timestamp_id() -> str:
        return datetime.now(
            timezone.utc
        ).strftime(
            "%Y%m%d%H%M%S%f"
        )