# ArguGod Module Status
_Last verified: 2026-07-23_

> Capability claims are hypotheses. Re-validate: `python scripts/validate_capabilities.py`

## Current Capability
- Debate loop with belief tracking, contradiction detection, and kernel signal emission — `modules/argu_god/engine/debate.py:debate_step()`
- Signal bridge emits belief shift, confidence change, and contradiction signals to kernel — `sub-agents/debate_agent.py:emit_belief_signal()`
- Semantic memory populated from topic graph.json for cross-session knowledge — `modules/argu_god/engine/debate.py:_populate_semantic_memory()`
- Contradiction detection via kernel's generalized detector — `kernel/patterns/contradiction_detector.py:detect_contradictions_for_beliefs()`
- LLM-generated question fallback when graph.json arguments exhausted — `modules/argu_god/llm_compiler.py:generate_llm_question()`
- Helper extraction for testable knowledge check, novelty check, and write-back phases — `modules/argu_god/engine/debate_helpers.py:_build_knowledge_context()`

## Known Gaps
- `debate_step()` integration test blocked by circular dependency on `question_ops._pending` — blocker
- LLM generation requires `GEMINI_API_KEY` or `OPENROUTER_API_KEY`; falls back to MockProvider with canned responses — low
- Topic expansion is manual (no `/argu add-topic` tool) — low
- Vector store persist directory hardcoded as `./chroma_db` — low

## Recent Changes (append-only, newest first, keep ~10)
- 2026-07-21: Helper extraction — 5 helpers moved to `debate_helpers.py` with 14 unit tests — `modules/argu_god/engine/debate_helpers.py`, `tests/kernel/test_debate_helpers.py`
- 2026-07-21: Vector_store embedding robustness — graceful fallback when sentence-transformers not installed — `modules/argu_god/engine/vector_store.py`
- 2026-07-21: LLM generation integration — `llm_compiler.py` rewritten to use `LLMOrchestrator`; `generate_llm_question` added — `modules/argu_god/llm_compiler.py`, `modules/argu_god/engine/debate_helpers.py`
- 2026-07-21: Free-text redesign of `debate_step()` — new phases: knowledge check, novelty check, write-back with provenance — `modules/argu_god/engine/debate.py`
- 2026-07-21: Kernel bridge relocated from `modules/argu_god/engine/kernel_bridge.py` to `sub-agents/debate_agent.py` — `sub-agents/debate_agent.py`
- 2026-07-21: `modules/argu_god/engine/analyzer.py` deleted (dead code, no callers) — removed
- 2026-07-21: `modules/argu_god/engine/kernel_bridge.py` deleted (relocated) — removed
- 2026-07-22: Capability claims seeded as Hypothesis objects — `scripts/seed_hypotheses.py`, `scripts/validate_capabilities.py`
