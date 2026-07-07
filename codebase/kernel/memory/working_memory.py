from __future__ import annotations

from dataclasses import dataclass, field
from typing import Dict, List, Any, Optional
from collections import deque
import time

from kernel.utils.logger import get_child_logger

logger = get_child_logger("working_memory")

# WORKING MEMORY ITEM

@dataclass
class WorkingMemoryItem:
    memory_id: str
    memory_type: str
    content: Any
    created_at: float = field(default_factory=time.time)
    updated_at: float = field(default_factory=time.time)
    importance: float = 0.5
    confidence: float = 1.0
    tags: List[str] = field(default_factory=list)
    metadata: Dict[str, Any] = field(default_factory=dict)
    access_count: int = 0
    last_accessed_at: float = field(default_factory=time.time)
    ttl_seconds: Optional[int] = None
    active: bool = True
    # ACCESS
    def touch(self):
        self.access_count += 1
        self.last_accessed_at = time.time()

    # EXPIRY
    def is_expired(self) -> bool:
        if self.ttl_seconds is None:
            return False
        age = time.time() - self.created_at
        return age > self.ttl_seconds

    # SERIALIZATION
    def to_dict(self) -> Dict[str, Any]:
        return {
            "memory_id": self.memory_id,
            "memory_type": self.memory_type,
            "content": self.content,
            "created_at": self.created_at,
            "updated_at": self.updated_at,
            "importance": self.importance,
            "confidence": self.confidence,
            "tags": self.tags,
            "metadata": self.metadata,
            "access_count": self.access_count,
            "last_accessed_at": self.last_accessed_at,
            "ttl_seconds": self.ttl_seconds,
            "active": self.active,
        }

# WORKING MEMORY

class WorkingMemory:
    def __init__(
        self,
        max_items: int = 1000
    ):
        self.max_items = max_items
        self.memories: Dict[str, WorkingMemoryItem] = {}
        self.memory_order = deque()
    # ADD MEMORY
    def add_memory(
        self,
        memory_id: str,
        memory_type: str,
        content: Any,
        importance: float = 0.5,
        confidence: float = 1.0,
        tags: Optional[List[str]] = None,
        metadata: Optional[Dict[str, Any]] = None,
        ttl_seconds: Optional[int] = None,
    ) -> WorkingMemoryItem:
        self.cleanup_expired()
        # Remove old if memory full
        if len(self.memories) >= self.max_items:
            self._evict_oldest()
        item = WorkingMemoryItem(
            memory_id=memory_id,
            memory_type=memory_type,
            content=content,
            importance=importance,
            confidence=confidence,
            tags=tags or [],
            metadata=metadata or {},
            ttl_seconds=ttl_seconds,
        )
        self.memories[memory_id] = item
        self.memory_order.append(memory_id)
        logger.info(
            f"Working memory added: {memory_id}"
        )
        return item
    # GET MEMORY
    def get_memory(
        self,
        memory_id: str
    ) -> Optional[WorkingMemoryItem]:
        item = self.memories.get(memory_id)
        if not item:
            return None
        if item.is_expired():
            self.remove_memory(memory_id)
            return None
        item.touch()
        return item
    # UPDATE MEMORY
    def update_memory(
        self,
        memory_id: str,
        content: Optional[Any] = None,
        importance: Optional[float] = None,
        confidence: Optional[float] = None,
        metadata: Optional[Dict[str, Any]] = None,
    ) -> bool:
        item = self.memories.get(memory_id)
        if not item:
            return False
        if content is not None:
            item.content = content
        if importance is not None:
            item.importance = importance
        if confidence is not None:
            item.confidence = confidence
        if metadata is not None:
            item.metadata.update(metadata)
        item.updated_at = time.time()
        logger.info(
            f"Working memory updated: {memory_id}"
        )
        return True
    # REMOVE MEMORY
    def remove_memory(
        self,
        memory_id: str
    ) -> bool:
        if memory_id not in self.memories:
            return False
        del self.memories[memory_id]
        try:
            self.memory_order.remove(memory_id)
        except ValueError:
            pass
        logger.info(
            f"Working memory removed: {memory_id}"
        )
        return True
    # SEARCH
    def search_by_tag(
        self,
        tag: str
    ) -> List[WorkingMemoryItem]:
        results = []
        for item in self.memories.values():
            if tag in item.tags:
                if not item.is_expired():
                    results.append(item)
        return results
    def search_by_type(
        self,
        memory_type: str
    ) -> List[WorkingMemoryItem]:
        results = []
        for item in self.memories.values():
            if item.memory_type == memory_type:
                if not item.is_expired():
                    results.append(item)
        return results
    def search_by_importance(
        self,
        min_importance: float = 0.5
    ) -> List[WorkingMemoryItem]:
        results = []
        for item in self.memories.values():
            if item.importance >= min_importance:
                if not item.is_expired():
                    results.append(item)
        return results
    # CLEANUP
    def cleanup_expired(self):
        expired_ids = []
        for memory_id, item in self.memories.items():
            if item.is_expired():
                expired_ids.append(memory_id)
        for memory_id in expired_ids:
            self.remove_memory(memory_id)
        if expired_ids:
            logger.info(
                f"Expired memories removed: {len(expired_ids)}"
            )

    # MEMORY PRIORITIZATION
    def get_top_memories(
        self,
        limit: int = 10
    ) -> List[WorkingMemoryItem]:
        items = [
            item
            for item in self.memories.values()
            if not item.is_expired()
        ]
        items.sort(
            key=lambda x: (
                x.importance,
                x.access_count,
                x.updated_at
            ),
            reverse=True
        )
        return items[:limit]
    # STATS
    def stats(self) -> Dict[str, Any]:
        self.cleanup_expired()
        return {
            "total_memories": len(self.memories),
            "max_items": self.max_items,
        }

    # CLEAR
    def clear(self):
        self.memories.clear()
        self.memory_order.clear()
        logger.info(
            "Working memory cleared"
        )

    # INTERNAL
    def _evict_oldest(self):
        while self.memory_order:
            oldest_id = self.memory_order.popleft()
            if oldest_id in self.memories:
                del self.memories[oldest_id]
                logger.warning(
                    f"Evicted oldest memory: {oldest_id}"
                )
                return

# GLOBAL INSTANCE

working_memory = WorkingMemory()