# Kernel Status
_Last verified: 2026-07-23_

> Capability claims are hypotheses. Re-validate: `python scripts/validate_capabilities.py`

## Current Capability
- Debate signal bridge emits belief/confidence/contradiction signals to kernel — `sub-agents/debate_agent.py:emit_belief_signal()`
- Signal extraction and emission pipeline — `kernel/extractors/signal_extractor.py:extract_and_emit()`
- Belief signal handlers for pattern detection and working memory — `kernel/signals/belief_signal_handler.py:handle_belief_shift_signal()`
- Contradiction detection via semantic memory edge analysis — `kernel/patterns/contradiction_detector.py:detect_contradictions_for_beliefs()`
- Hypothesis engine for capability/gap tracking with validation — `kernel/hypothesis/hypothesis_engine.py:create_hypothesis()`
- SQLite persistence as sole backend — `kernel/persistence/db.py:save_generic_memory()`
- Cross-session retrieval via ChromaDB embedding — `kernel/retrieval/semantic_retriever.py:search_by_embedding()`
- Config constants used by hypothesis engine for TTL/confidence defaults — `kernel/hypothesis/hypothesis_engine.py:create_hypothesis()`

## Known Gaps
- Dream cycle / TTL sweep for working memory not implemented — low
- Hypothesis auto-generation from patterns not wired — low
- No self-contradiction detection across sessions — low

## Recent Changes (newest first, max 10)
- 2026-07-21: Kernel improvements: analyzer.py removed, vector_store consolidated, config constants centralized, kernel_bridge relocated, MCP code RAG tools added, SQLite sole persistence backend
- 2026-07-21: Test suite created: tests/kernel/test_integration.py — 11 tests covering contradiction detection, signal pipeline, semantic population
- 2026-07-22: Capability claims seeded as Hypothesis objects — `scripts/seed_hypotheses.py`, `scripts/validate_capabilities.py`
