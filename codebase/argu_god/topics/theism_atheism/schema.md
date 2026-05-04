# Schema for theism_atheism topic (copy of global_schema.md)

## Argument Node Format
- name: string
- side: "pro" | "con" | "neutral"
- premise: string
- evidence: list[str]
- examples: list[str]
- sources: list[str]
- discipline: string
- confidence: float (0.0-1.0)

## Graph JSON Structure (must match)
{
  "nodes": [ { "id", "name", "side", "premise", ... } ],
  "edges": [ { "source", "target", "relation": "supports|refutes|related" } ]
}