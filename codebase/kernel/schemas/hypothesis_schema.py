from __future__ import annotations

from dataclasses import dataclass, field
from typing import Dict, List, Any
import time


@dataclass
class HypothesisSchema:
    hypothesis_id: str
    title: str
    description: str
    hypothesis_type: str
    category: str = "general"
    confidence: float = 0.5
    plausibility: float = 0.5
    novelty: float = 0.5
    status: str = "proposed"
    supporting_evidence: List[str] = field(default_factory=list)
    contradicting_evidence: List[str] = field(default_factory=list)
    related_patterns: List[str] = field(default_factory=list)
    related_concepts: List[str] = field(default_factory=list)
    predictions: List[str] = field(default_factory=list)
    created_at: float = field(default_factory=time.time)
    updated_at: float = field(default_factory=time.time)
    metadata: Dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> Dict[str, Any]:
        return {
            "hypothesis_id": self.hypothesis_id,
            "title": self.title,
            "description": self.description,
            "hypothesis_type": self.hypothesis_type,
            "category": self.category,
            "confidence": self.confidence,
            "plausibility": self.plausibility,
            "novelty": self.novelty,
            "status": self.status,
            "supporting_evidence": self.supporting_evidence,
            "contradicting_evidence": self.contradicting_evidence,
            "related_patterns": self.related_patterns,
            "related_concepts": self.related_concepts,
            "predictions": self.predictions,
            "created_at": self.created_at,
            "updated_at": self.updated_at,
            "metadata": self.metadata,
        }
