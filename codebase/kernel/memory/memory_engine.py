from __future__ import annotations

from typing import Dict, List, Optional, Any

from kernel.utils.logger import get_child_logger

from kernel.schemas.unit_schema import UnitSchema
from kernel.schemas.signal_schema import SignalSchema
from kernel.schemas.event_schema import EventSchema
from kernel.schemas.pattern_schema import PatternSchema
from kernel.schemas.relation_schema import RelationSchema

logger = get_child_logger("memory")


class MemoryEngine:
    def __init__(self):
        self._db = None

    @property
    def db(self):
        if self._db is None:
            from kernel.persistence.db import kernel_db
            self._db = kernel_db
        return self._db

    def _persist_structured(self, memory_type: str, object_id: str, data: Dict[str, Any]):
        try:
            if memory_type == "semantic":
                node_type = data.get("node_type", "generic")
                self.db.save_semantic_node(
                    node_id=object_id,
                    node_type=node_type,
                    title=data.get("title", ""),
                    content=data.get("content", ""),
                    concepts=data.get("concepts"),
                    tags=data.get("tags"),
                    importance=data.get("importance", 0.5),
                    confidence=data.get("confidence", 1.0),
                    created_at=data.get("created_at"),
                    updated_at=data.get("updated_at"),
                )
            elif memory_type == "pattern":
                self.db.save_pattern(
                    pattern_id=object_id,
                    pattern_type=data.get("pattern_type", "generic"),
                    category=data.get("category", "general"),
                    title=data.get("title", ""),
                    description=data.get("description", ""),
                    source_ids=data.get("source_ids"),
                    confidence=data.get("confidence", 1.0),
                    importance=data.get("importance", 0.5),
                    created_at=data.get("created_at"),
                )
            elif memory_type == "hypothesis":
                self.db.save_hypothesis(
                    hypothesis_id=object_id,
                    title=data.get("title", ""),
                    description=data.get("description", ""),
                    hypothesis_type=data.get("hypothesis_type", "generic"),
                    category=data.get("category", "general"),
                    confidence=data.get("confidence", 0.5),
                    status=data.get("status", "proposed"),
                    supporting=data.get("supporting_evidence"),
                    contradicting=data.get("contradicting_evidence"),
                    created_at=data.get("created_at"),
                    updated_at=data.get("updated_at"),
                )
            elif memory_type == "working":
                self.db.save_working_memory(
                    memory_id=object_id,
                    memory_type=data.get("memory_type", "generic"),
                    content=data.get("content", {}),
                    importance=data.get("importance", 0.5),
                    confidence=data.get("confidence", 1.0),
                    ttl_seconds=data.get("ttl_seconds", 3600),
                    created_at=data.get("created_at"),
                )
        except Exception:
            logger.warning(f"Structured persist failed for {object_id}", exc_info=True)

    def save_object(
        self,
        memory_type: str,
        object_id: str,
        data: Dict[str, Any],
    ) -> str:
        self.db.save_generic_memory(object_id, memory_type, data)
        self._persist_structured(memory_type, object_id, data)
        logger.info(f"Saved object: {object_id}")
        return object_id

    def load_object(
        self,
        memory_type: str,
        object_id: str,
    ) -> Optional[Dict[str, Any]]:
        result = self.db.load_generic_memory(object_id)
        if not result:
            return None
        return result["data"]

    def delete_object(
        self,
        memory_type: str,
        object_id: str,
    ) -> bool:
        return self.db.delete_generic_memory(object_id)

    def list_objects(
        self,
        memory_type: str,
    ) -> List[str]:
        return self.db.list_generic_memory_ids(memory_type)

    def search_by_prefix(
        self,
        memory_type: str,
        prefix: str,
    ) -> List[str]:
        all_ids = self.list_objects(memory_type)
        return [obj_id for obj_id in all_ids if obj_id.startswith(prefix)]

    def object_exists(
        self,
        memory_type: str,
        object_id: str,
    ) -> bool:
        return self.db.generic_memory_exists(object_id)

    def save_unit(
        self,
        unit: UnitSchema,
        memory_type: str = "semantic",
    ) -> str:
        return self.save_object(
            memory_type=memory_type,
            object_id=unit.identity.unit_id,
            data=unit.to_dict(),
        )

    def load_unit(
        self,
        unit_id: str,
        memory_type: str = "semantic",
    ) -> Optional[Dict[str, Any]]:
        return self.load_object(memory_type=memory_type, object_id=unit_id)

    def save_signal(
        self,
        signal: SignalSchema,
        memory_type: str = "episodic",
    ) -> str:
        return self.save_object(
            memory_type=memory_type,
            object_id=signal.signal_id,
            data=signal.to_dict(),
        )

    def load_signal(
        self,
        signal_id: str,
        memory_type: str = "episodic",
    ) -> Optional[Dict[str, Any]]:
        return self.load_object(memory_type=memory_type, object_id=signal_id)

    def save_event(
        self,
        event: EventSchema,
        memory_type: str = "episodic",
    ) -> str:
        return self.save_object(
            memory_type=memory_type,
            object_id=event.event_id,
            data=event.to_dict(),
        )

    def load_event(
        self,
        event_id: str,
        memory_type: str = "episodic",
    ) -> Optional[Dict[str, Any]]:
        return self.load_object(memory_type=memory_type, object_id=event_id)

    def save_pattern(
        self,
        pattern: PatternSchema,
        memory_type: str = "pattern",
    ) -> str:
        return self.save_object(
            memory_type=memory_type,
            object_id=pattern.pattern_id,
            data=pattern.to_dict(),
        )

    def load_pattern(
        self,
        pattern_id: str,
        memory_type: str = "pattern",
    ) -> Optional[Dict[str, Any]]:
        return self.load_object(memory_type=memory_type, object_id=pattern_id)

    def save_relation(
        self,
        relation: RelationSchema,
        memory_type: str = "semantic",
    ) -> str:
        return self.save_object(
            memory_type=memory_type,
            object_id=relation.relation_id,
            data=relation.to_dict(),
        )

    def load_relation(
        self,
        relation_id: str,
        memory_type: str = "semantic",
    ) -> Optional[Dict[str, Any]]:
        return self.load_object(memory_type=memory_type, object_id=relation_id)


memory_engine = MemoryEngine()
