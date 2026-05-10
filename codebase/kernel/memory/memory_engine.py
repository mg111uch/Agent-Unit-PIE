from __future__ import annotations

import json
from pathlib import Path
from typing import Dict, List, Optional, Any

from kernel.utils.logger import get_child_logger
from kernel.utils.paths import (
    WORKING_MEMORY_DIR,
    EPISODIC_MEMORY_DIR,
    SEMANTIC_MEMORY_DIR,
    PATTERN_MEMORY_DIR,
    HYPOTHESIS_MEMORY_DIR,
    ensure_parent_dir,
)

from kernel.schemas.unit_schema import UnitSchema
from kernel.schemas.signal_schema import SignalSchema
from kernel.schemas.event_schema import EventSchema
from kernel.schemas.pattern_schema import PatternSchema
from kernel.schemas.relation_schema import RelationSchema


logger = get_child_logger("memory")


# =========================================================
# MEMORY ENGINE
# =========================================================

class MemoryEngine:

    def __init__(self):

        self.memory_roots = {
            "working": WORKING_MEMORY_DIR,
            "episodic": EPISODIC_MEMORY_DIR,
            "semantic": SEMANTIC_MEMORY_DIR,
            "pattern": PATTERN_MEMORY_DIR,
            "hypothesis": HYPOTHESIS_MEMORY_DIR,
        }

    # =====================================================
    # GENERIC STORAGE
    # =====================================================

    def save_object(
        self,
        memory_type: str,
        object_id: str,
        data: Dict[str, Any]
    ) -> Path:

        root = self._get_memory_root(memory_type)

        file_path = root / f"{object_id}.json"

        ensure_parent_dir(file_path)

        with open(file_path, "w", encoding="utf-8") as f:
            json.dump(
                data,
                f,
                indent=2,
                ensure_ascii=False
            )

        logger.info(
            f"Saved object: {object_id}"
        )

        return file_path

    def load_object(
        self,
        memory_type: str,
        object_id: str
    ) -> Optional[Dict[str, Any]]:

        root = self._get_memory_root(memory_type)

        file_path = root / f"{object_id}.json"

        if not file_path.exists():
            return None

        with open(file_path, "r", encoding="utf-8") as f:
            return json.load(f)

    def delete_object(
        self,
        memory_type: str,
        object_id: str
    ) -> bool:

        root = self._get_memory_root(memory_type)

        file_path = root / f"{object_id}.json"

        if not file_path.exists():
            return False

        file_path.unlink()

        logger.info(
            f"Deleted object: {object_id}"
        )

        return True

    # =====================================================
    # UNIT MEMORY
    # =====================================================

    def save_unit(
        self,
        unit: UnitSchema,
        memory_type: str = "semantic"
    ) -> Path:

        return self.save_object(
            memory_type=memory_type,
            object_id=unit.identity.unit_id,
            data=unit.to_dict()
        )

    def load_unit(
        self,
        unit_id: str,
        memory_type: str = "semantic"
    ) -> Optional[Dict[str, Any]]:

        return self.load_object(
            memory_type=memory_type,
            object_id=unit_id
        )

    # =====================================================
    # SIGNAL MEMORY
    # =====================================================

    def save_signal(
        self,
        signal: SignalSchema,
        memory_type: str = "episodic"
    ) -> Path:

        return self.save_object(
            memory_type=memory_type,
            object_id=signal.signal_id,
            data=signal.to_dict()
        )

    def load_signal(
        self,
        signal_id: str,
        memory_type: str = "episodic"
    ) -> Optional[Dict[str, Any]]:

        return self.load_object(
            memory_type=memory_type,
            object_id=signal_id
        )

    # =====================================================
    # EVENT MEMORY
    # =====================================================

    def save_event(
        self,
        event: EventSchema,
        memory_type: str = "episodic"
    ) -> Path:

        return self.save_object(
            memory_type=memory_type,
            object_id=event.event_id,
            data=event.to_dict()
        )

    def load_event(
        self,
        event_id: str,
        memory_type: str = "episodic"
    ) -> Optional[Dict[str, Any]]:

        return self.load_object(
            memory_type=memory_type,
            object_id=event_id
        )

    # =====================================================
    # PATTERN MEMORY
    # =====================================================

    def save_pattern(
        self,
        pattern: PatternSchema,
        memory_type: str = "pattern"
    ) -> Path:

        return self.save_object(
            memory_type=memory_type,
            object_id=pattern.pattern_id,
            data=pattern.to_dict()
        )

    def load_pattern(
        self,
        pattern_id: str,
        memory_type: str = "pattern"
    ) -> Optional[Dict[str, Any]]:

        return self.load_object(
            memory_type=memory_type,
            object_id=pattern_id
        )

    # =====================================================
    # RELATION MEMORY
    # =====================================================

    def save_relation(
        self,
        relation: RelationSchema,
        memory_type: str = "semantic"
    ) -> Path:

        return self.save_object(
            memory_type=memory_type,
            object_id=relation.relation_id,
            data=relation.to_dict()
        )

    def load_relation(
        self,
        relation_id: str,
        memory_type: str = "semantic"
    ) -> Optional[Dict[str, Any]]:

        return self.load_object(
            memory_type=memory_type,
            object_id=relation_id
        )

    # =====================================================
    # SEARCH
    # =====================================================

    def list_objects(
        self,
        memory_type: str
    ) -> List[str]:

        root = self._get_memory_root(memory_type)

        if not root.exists():
            return []

        return [
            file.stem
            for file in root.glob("*.json")
        ]

    def search_by_prefix(
        self,
        memory_type: str,
        prefix: str
    ) -> List[str]:

        object_ids = self.list_objects(memory_type)

        return [
            obj_id
            for obj_id in object_ids
            if obj_id.startswith(prefix)
        ]

    # =====================================================
    # FILESYSTEM HELPERS
    # =====================================================

    def object_exists(
        self,
        memory_type: str,
        object_id: str
    ) -> bool:

        root = self._get_memory_root(memory_type)

        file_path = root / f"{object_id}.json"

        return file_path.exists()

    def get_object_path(
        self,
        memory_type: str,
        object_id: str
    ) -> Path:

        root = self._get_memory_root(memory_type)

        return root / f"{object_id}.json"

    # =====================================================
    # INTERNAL
    # =====================================================

    def _get_memory_root(
        self,
        memory_type: str
    ) -> Path:

        if memory_type not in self.memory_roots:

            raise ValueError(
                f"Unknown memory type: {memory_type}"
            )

        return self.memory_roots[memory_type]


# =========================================================
# GLOBAL ENGINE
# =========================================================

memory_engine = MemoryEngine()