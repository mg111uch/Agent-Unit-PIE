from __future__ import annotations

from dataclasses import dataclass, field
from typing import Dict, List, Any, Optional
from collections import defaultdict
import time

from kernel.utils.logger import get_child_logger
from kernel.memory.memory_engine import memory_engine


logger = get_child_logger("episodic_memory")


# =========================================================
# EPISODE
# =========================================================

@dataclass
class Episode:
    episode_id: str

    episode_type: str

    timestamp: float = field(default_factory=time.time)

    summary: str = ""

    entities: List[str] = field(default_factory=list)

    events: List[str] = field(default_factory=list)

    signals: List[str] = field(default_factory=list)

    patterns: List[str] = field(default_factory=list)

    relations: List[str] = field(default_factory=list)

    tags: List[str] = field(default_factory=list)

    importance: float = 0.5

    emotional_weight: float = 0.0

    confidence: float = 1.0

    metadata: Dict[str, Any] = field(default_factory=dict)

    # -----------------------------------------------------
    # SERIALIZATION
    # -----------------------------------------------------

    def to_dict(self) -> Dict[str, Any]:

        return {
            "episode_id": self.episode_id,
            "episode_type": self.episode_type,
            "timestamp": self.timestamp,
            "summary": self.summary,
            "entities": self.entities,
            "events": self.events,
            "signals": self.signals,
            "patterns": self.patterns,
            "relations": self.relations,
            "tags": self.tags,
            "importance": self.importance,
            "emotional_weight": self.emotional_weight,
            "confidence": self.confidence,
            "metadata": self.metadata,
        }


# =========================================================
# EPISODIC MEMORY
# =========================================================

class EpisodicMemory:

    def __init__(self):

        self.episodes: Dict[str, Episode] = {}

        self.timeline: List[str] = []

        self.tag_index = defaultdict(list)

        self.entity_index = defaultdict(list)

        self.event_index = defaultdict(list)

    # =====================================================
    # ADD EPISODE
    # =====================================================

    def add_episode(
        self,
        episode: Episode,
        persist: bool = True
    ):

        self.episodes[
            episode.episode_id
        ] = episode

        self.timeline.append(
            episode.episode_id
        )

        # Index tags
        for tag in episode.tags:

            self.tag_index[tag].append(
                episode.episode_id
            )

        # Index entities
        for entity_id in episode.entities:

            self.entity_index[
                entity_id
            ].append(
                episode.episode_id
            )

        # Index events
        for event_id in episode.events:

            self.event_index[
                event_id
            ].append(
                episode.episode_id
            )

        # Persist
        if persist:

            memory_engine.save_object(
                memory_type="episodic",
                object_id=episode.episode_id,
                data=episode.to_dict()
            )

        logger.info(
            f"Episode added: {episode.episode_id}"
        )

    # =====================================================
    # CREATE EPISODE
    # =====================================================

    def create_episode(
        self,
        episode_id: str,
        episode_type: str,
        summary: str = "",
        entities: Optional[List[str]] = None,
        events: Optional[List[str]] = None,
        signals: Optional[List[str]] = None,
        patterns: Optional[List[str]] = None,
        relations: Optional[List[str]] = None,
        tags: Optional[List[str]] = None,
        importance: float = 0.5,
        emotional_weight: float = 0.0,
        confidence: float = 1.0,
        metadata: Optional[Dict[str, Any]] = None,
        persist: bool = True,
    ) -> Episode:

        episode = Episode(
            episode_id=episode_id,
            episode_type=episode_type,
            summary=summary,
            entities=entities or [],
            events=events or [],
            signals=signals or [],
            patterns=patterns or [],
            relations=relations or [],
            tags=tags or [],
            importance=importance,
            emotional_weight=emotional_weight,
            confidence=confidence,
            metadata=metadata or {},
        )

        self.add_episode(
            episode,
            persist=persist
        )

        return episode

    # =====================================================
    # RETRIEVAL
    # =====================================================

    def get_episode(
        self,
        episode_id: str
    ) -> Optional[Episode]:

        return self.episodes.get(
            episode_id
        )

    def get_recent_episodes(
        self,
        limit: int = 10
    ) -> List[Episode]:

        episode_ids = self.timeline[-limit:]

        return [
            self.episodes[eid]
            for eid in reversed(episode_ids)
            if eid in self.episodes
        ]

    # =====================================================
    # SEARCH
    # =====================================================

    def search_by_tag(
        self,
        tag: str
    ) -> List[Episode]:

        episode_ids = self.tag_index.get(
            tag,
            []
        )

        return [
            self.episodes[eid]
            for eid in episode_ids
            if eid in self.episodes
        ]

    def search_by_entity(
        self,
        entity_id: str
    ) -> List[Episode]:

        episode_ids = self.entity_index.get(
            entity_id,
            []
        )

        return [
            self.episodes[eid]
            for eid in episode_ids
            if eid in self.episodes
        ]

    def search_by_event(
        self,
        event_id: str
    ) -> List[Episode]:

        episode_ids = self.event_index.get(
            event_id,
            []
        )

        return [
            self.episodes[eid]
            for eid in episode_ids
            if eid in self.episodes
        ]

    def search_by_importance(
        self,
        min_importance: float = 0.5
    ) -> List[Episode]:

        results = []

        for episode in self.episodes.values():

            if episode.importance >= min_importance:
                results.append(episode)

        results.sort(
            key=lambda x: x.importance,
            reverse=True
        )

        return results

    # =====================================================
    # TIMELINE
    # =====================================================

    def get_timeline(
        self
    ) -> List[Episode]:

        return [
            self.episodes[eid]
            for eid in self.timeline
            if eid in self.episodes
        ]

    # =====================================================
    # REMOVE
    # =====================================================

    def remove_episode(
        self,
        episode_id: str
    ) -> bool:

        if episode_id not in self.episodes:
            return False

        episode = self.episodes[
            episode_id
        ]

        # Remove from indexes
        for tag in episode.tags:

            if episode_id in self.tag_index[tag]:

                self.tag_index[tag].remove(
                    episode_id
                )

        for entity_id in episode.entities:

            if episode_id in self.entity_index[entity_id]:

                self.entity_index[entity_id].remove(
                    episode_id
                )

        for event_id in episode.events:

            if episode_id in self.event_index[event_id]:

                self.event_index[event_id].remove(
                    episode_id
                )

        # Remove timeline
        if episode_id in self.timeline:

            self.timeline.remove(
                episode_id
            )

        # Remove object
        del self.episodes[
            episode_id
        ]

        logger.info(
            f"Episode removed: {episode_id}"
        )

        return True

    # =====================================================
    # LOAD FROM DISK
    # =====================================================

    def load_episode_from_disk(
        self,
        episode_id: str
    ) -> Optional[Episode]:

        data = memory_engine.load_object(
            memory_type="episodic",
            object_id=episode_id
        )

        if not data:
            return None

        episode = Episode(**data)

        self.add_episode(
            episode,
            persist=False
        )

        return episode

    # =====================================================
    # STATS
    # =====================================================

    def stats(self) -> Dict[str, Any]:

        return {
            "total_episodes": len(
                self.episodes
            ),
            "timeline_size": len(
                self.timeline
            ),
            "unique_tags": len(
                self.tag_index
            ),
            "unique_entities": len(
                self.entity_index
            ),
            "unique_events": len(
                self.event_index
            ),
        }

    # =====================================================
    # CLEAR
    # =====================================================

    def clear(self):

        self.episodes.clear()

        self.timeline.clear()

        self.tag_index.clear()

        self.entity_index.clear()

        self.event_index.clear()

        logger.warning(
            "Episodic memory cleared"
        )


# =========================================================
# GLOBAL INSTANCE
# =========================================================

episodic_memory = EpisodicMemory()