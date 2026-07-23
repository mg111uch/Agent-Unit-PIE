# Debate Module — Development Roadmap
_Not verified. Never cite as working._

## Current State
- One topic (`theism_atheism`) with 12 arguments, 24 edges
- `debate_step` composite tool drives the loop — one LLM turn per iteration
- Questions from pre-defined `graph.json` (zero LLM cost for generation)
- Belief tracking, contradiction detection, kernel signals active
- Counter-arg retrieval via ChromaDB (vector embeddings)
- Session persistence with resume support

## Near-term
- Topic expansion tool (`/argu add-topic`) — LLM researches and generates graph.json
- LLM-generated question batching when graph.json exhausted
- Circular dependency fix: `question_ops._pending` → blocker for integration tests

## Later
- Multi-person debate with user/perspective tracking
- Debate analytics (session stats, belief changes)
- Argument quality scoring by evidence strength
- Export belief graph as JSON

## Explicitly deferred / rejected
- Recursive counterarguments (explore counter-counterarguments) — complexity too high for current scope
