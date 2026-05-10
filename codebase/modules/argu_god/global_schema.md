# Global Schema for ArguGod Topics & Mindmaps

## Argument Node Format (used in wiki/*.md and graph.json)
- name: string
- side: "pro" | "con" | "neutral"
- premise: string
- evidence: list[str]
- examples: list[str]
- sources: list[str]
- discipline: string (e.g. "philosophy", "cosmology")
- confidence: float (0.0-1.0)

## Graph JSON Structure
{
  "nodes": [ { "id", "name", "side", ... } ],
  "edges": [ { "source", "target", "relation": "supports|refutes|related" } ]
}

## Personal Mindmap Schema (mindmap.json)
{
  "topics": {
    "theism_atheism": {
      "depth_score": 0.0-1.0,
      "confidence": 0.0-1.0,
      "last_interaction": "YYYY-MM-DD",
      "connections": ["ai_alignment", ...]
    }
  },
  "total_topics_explored": int,
  "overall_knowledge_vector": { ... }
}

All LLM outputs for compilation or mindmap updates MUST follow this schema exactly. No human edits allowed.