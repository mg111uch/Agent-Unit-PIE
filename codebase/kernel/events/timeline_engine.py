from __future__ import annotations

from dataclasses import dataclass, field
from typing import Dict, List, Optional, Any
from collections import defaultdict
import bisect
import time

from kernel.utils.logger import get_child_logger

from kernel.schemas.event_schema import EventSchema
from kernel.schemas.signal_schema import SignalSchema

logger = get_child_logger("timeline_engine")

# TIMELINE ENTRY

@dataclass
class TimelineEntry:
    entry_id: str
    entry_type: str
    timestamp: float
    source_id: str
    title: str = ""
    description: str = ""
    importance: float = 0.5
    tags: List[str] = field(default_factory=list)
    metadata: Dict[str, Any] = field(default_factory=dict)
    # SERIALIZATION
    def to_dict(self) -> Dict[str, Any]:
        return {
            "entry_id": self.entry_id,
            "entry_type": self.entry_type,
            "timestamp": self.timestamp,
            "source_id": self.source_id,
            "title": self.title,
            "description": self.description,
            "importance": self.importance,
            "tags": self.tags,
            "metadata": self.metadata,
        }

# TIMELINE ENGINE

class TimelineEngine:
    def __init__(self):
        self.timeline: List[TimelineEntry] = []
        self.entry_map: Dict[
            str,
            TimelineEntry
        ] = {}
        self.type_index = defaultdict(list)
        self.tag_index = defaultdict(list)

    # ADD ENTRY
    def add_entry(
        self,
        entry: TimelineEntry
    ):
        timestamps = [
            e.timestamp
            for e in self.timeline
        ]
        insert_index = bisect.bisect(
            timestamps,
            entry.timestamp
        )
        self.timeline.insert(
            insert_index,
            entry
        )
        self.entry_map[
            entry.entry_id
        ] = entry
        self.type_index[
            entry.entry_type
        ].append(
            entry.entry_id
        )
        for tag in entry.tags:
            self.tag_index[tag].append(
                entry.entry_id
            )
        logger.info(
            f"Timeline entry added: "
            f"{entry.entry_id}"
        )
    # EVENT -> TIMELINE
    def add_event(
        self,
        event: EventSchema
    ) -> TimelineEntry:
        entry = TimelineEntry(
            entry_id=event.event_id,
            entry_type="event",
            timestamp=event.timestamps.created_at_unix,
            source_id=event.source_unit_id or "",
            title=event.title,
            description=event.description,
            importance=event.metrics.importance,
            tags=event.metadata.tags,
            metadata={
                "event_type":
                event.event_type,
                "category":
                event.category,
            },
        )
        self.add_entry(entry)
        return entry
    # SIGNAL -> TIMELINE
    def add_signal(
        self,
        signal: SignalSchema
    ) -> TimelineEntry:
        entry = TimelineEntry(
            entry_id=signal.signal_id,
            entry_type="signal",
            timestamp=signal.timestamps.created_at_unix,
            source_id=signal.source_unit_id,
            title=signal.title,
            description=signal.description,
            importance=signal.metrics.importance,
            tags=signal.metadata.tags,
            metadata={
                "signal_type":
                signal.signal_type,
                "category":
                signal.category,
            },
        )
        self.add_entry(entry)
        return entry
    # CREATE CUSTOM ENTRY
    def create_entry(
        self,
        entry_id: str,
        entry_type: str,
        source_id: str,
        title: str = "",
        description: str = "",
        importance: float = 0.5,
        timestamp: Optional[float] = None,
        tags: Optional[List[str]] = None,
        metadata: Optional[Dict] = None,
    ) -> TimelineEntry:
        entry = TimelineEntry(
            entry_id=entry_id,
            entry_type=entry_type,
            timestamp=timestamp or time.time(),
            source_id=source_id,
            title=title,
            description=description,
            importance=importance,
            tags=tags or [],
            metadata=metadata or {},
        )
        self.add_entry(entry)
        return entry
    # RETRIEVAL
    def get_entry(
        self,
        entry_id: str
    ) -> Optional[TimelineEntry]:
        return self.entry_map.get(
            entry_id
        )
    def get_recent_entries(
        self,
        limit: int = 20
    ) -> List[TimelineEntry]:
        return self.timeline[-limit:]
    def get_entries_between(
        self,
        start_timestamp: float,
        end_timestamp: float
    ) -> List[TimelineEntry]:
        results = []
        for entry in self.timeline:
            if (
                start_timestamp
                <= entry.timestamp
                <= end_timestamp
            ):
                results.append(entry)
        return results
    # SEARCH
    def search_by_type(
        self,
        entry_type: str
    ) -> List[TimelineEntry]:
        entry_ids = self.type_index.get(
            entry_type,
            []
        )
        return [
            self.entry_map[eid]
            for eid in entry_ids
            if eid in self.entry_map
        ]
    def search_by_tag(
        self,
        tag: str
    ) -> List[TimelineEntry]:
        entry_ids = self.tag_index.get(
            tag,
            []
        )
        return [
            self.entry_map[eid]
            for eid in entry_ids
            if eid in self.entry_map
        ]
    def search_by_source(
        self,
        source_id: str
    ) -> List[TimelineEntry]:
        results = []
        for entry in self.timeline:
            if entry.source_id == source_id:
                results.append(entry)
        return results
    # IMPORTANCE FILTER
    def get_important_entries(
        self,
        min_importance: float = 0.7
    ) -> List[TimelineEntry]:
        return [
            entry
            for entry in self.timeline
            if (
                entry.importance
                >= min_importance
            )
        ]
    # REMOVE
    def remove_entry(
        self,
        entry_id: str
    ) -> bool:
        if entry_id not in self.entry_map:
            return False
        entry = self.entry_map[
            entry_id
        ]
        self.timeline = [
            e for e in self.timeline
            if e.entry_id != entry_id
        ]
        if (
            entry_id
            in self.type_index[
                entry.entry_type
            ]
        ):
            self.type_index[
                entry.entry_type
            ].remove(entry_id)
        for tag in entry.tags:
            if entry_id in self.tag_index[tag]:
                self.tag_index[tag].remove(
                    entry_id
                )
        del self.entry_map[
            entry_id
        ]
        logger.info(
            f"Timeline entry removed: "
            f"{entry_id}"
        )
        return True
    # STATS
    def stats(self) -> Dict[str, Any]:
        return {
            "total_entries":
            len(self.timeline),
            "entry_types":
            len(self.type_index),
            "unique_tags":
            len(self.tag_index),
        }

    # CLEAR
    def clear(self):
        self.timeline.clear()
        self.entry_map.clear()
        self.type_index.clear()
        self.tag_index.clear()
        logger.warning(
            "Timeline cleared"
        )

# GLOBAL ENGINE

timeline_engine = TimelineEngine()