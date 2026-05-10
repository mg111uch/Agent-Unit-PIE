# PHASE 1 DIRECTORY STRUCTURE

```text id="61sj8x"
agent_unit_pie/
├── kernel/
│   ├── schemas/
│   │   ├── unit_schema.py
│   │   ├── signal_schema.py
│   │   ├── event_schema.py
│   │   ├── pattern_schema.py
│   │   ├── relation_schema.py
│   │   ├── hypothesis_schema.py
│   │   ├── simulation_schema.py
│   │   └── memory_schema.py
│   │
│   ├── ontology/
│   │   ├── unit_types.py
│   │   ├── signal_types.py
│   │   ├── event_types.py
│   │   ├── pattern_types.py
│   │   ├── relation_types.py
│   │   ├── behavior_types.py
│   │   ├── resource_types.py
│   │   └── hypothesis_types.py
│   │
│   ├── memory/
│   │   ├── memory_engine.py
│   │   ├── working_memory.py
│   │   ├── episodic_memory.py
│   │   ├── semantic_memory.py
│   │   ├── pattern_memory.py
│   │   └── memory_compressor.py
│   │
│   ├── signals/
│   │   ├── signal_engine.py
│   │   ├── signal_extractor.py
│   │   ├── signal_router.py
│   │   └── signal_validator.py
│   │
│   ├── events/
│   │   ├── event_engine.py
│   │   ├── event_extractor.py
│   │   └── timeline_engine.py
│   │
│   ├── patterns/
│   │   ├── pattern_engine.py
│   │   ├── trend_detector.py
│   │   ├── anomaly_detector.py
│   │   ├── contradiction_detector.py
│   │   └── causal_engine.py
│   │
│   ├── retrieval/
│   │   ├── retrieval_engine.py
│   │   ├── hierarchy_retriever.py
│   │   ├── temporal_retriever.py
│   │   ├── relation_retriever.py
│   │   └── semantic_retriever.py
│   │
│   ├── hypotheses/
│   │   ├── hypothesis_engine.py
│   │   ├── confidence_engine.py
│   │   └── validation_engine.py
│   │
│   ├── utils/
│   │   ├── ids.py
│   │   ├── timestamps.py
│   │   ├── logger.py
│   │   └── paths.py
│   │
│   └── config/
│       ├── kernel_config.py
│       └── ontology_config.py
```

---

# KERNEL INTEGRATION PHASE

## Priority-Wise File Generation Roadmap

Since your kernel schemas already exist, this phase should focus on:

```text id="dg1k1s"
connecting all systems into one unified cognition pipeline
```

NOT feature expansion.

---

# PHASE GOAL

Transform current architecture from:

```text id="0v1s6r"
disconnected modules
```

into:

# integrated recursive cognition system

---

# MOST IMPORTANT RULE

Generate files in dependency order.

Do NOT randomly generate modules.

Many future systems depend on earlier files.

# PRIORITY ORDER

# PRIORITY 4 — UNIVERSAL UNIT INTEGRATION

Connect old systems to new kernel.

# 23. simulation_engine/resource_engine.py
# 24. simulation_engine/world_engine.py
# 25. simulation_engine/event_bridge.py

# IMPORTANT

Connects simulation outputs to kernel events/signals.

---

# PRIORITY 5 — KB STRUCTURE + STORAGE

Replace fragmented storage.

---

# 26. storage/unit_storage.py
# 27. storage/pattern_storage.py
# 28. storage/timeline_storage.py
# 29. storage/hypothesis_storage.py
# 30. storage/raw_observation_storage.py

---

# PRIORITY 6 — INGESTION SYSTEM

Needed before city/company intelligence.

# 31. ingestion/document_ingestor.py
# 32. ingestion/pdf_ingestor.py
# 33. ingestion/web_ingestor.py
# 34. ingestion/news_ingestor.py
# 35. ingestion/transcript_ingestor.py
# 36. ingestion/observation_extractor.py
Converts raw data into observations/signals.

---

# PRIORITY 8 — LLM ORCHESTRATION

# 43. llm/extractors/signal_extractor.py
# 44. llm/extractors/pattern_extractor.py
# 45. llm/extractors/hypothesis_extractor.py

---

# PRIORITY 9 — ARGU_GOD INTEGRATION

Convert from standalone system into module.

# 46. modules/debate_engine/debate_orchestrator.py
# 47. modules/debate_engine/contradiction_detector.py
# 48. modules/debate_engine/hypothesis_tester.py
# 49. modules/debate_engine/belief_tracker.py

# IMPORTANT

Debate engine becomes:

# epistemic validation layer

NOT main architecture.

---

# PRIORITY 10 — CITY PILOT IMPLEMENTATION

FIRST FULL SYSTEM TEST.

# 50. units/cities/city_initializer.py
# 51. units/cities/city_signal_mapper.py
# 52. units/cities/city_pattern_detector.py
# 53. units/cities/city_summary_generator.py

# WHY CITY FIRST?

Because cities touch:

* economics
* transport
* politics
* population
* infrastructure
* finance
* spatial systems
* organizations

Perfect architecture stress test.

# WHAT YOU SHOULD NOT GENERATE YET

Avoid these until architecture stabilizes:

```text id="vnm44g"
astrology engine
GDP optimizer
stock predictor
corruption detector
autonomous agents
global human DB
```

Those are:

# phase 2+ systems

These 10 files determine whether the architecture succeeds or collapses later.

---------------------------------------------------

```text id="h1k7v9"
01. kernel/observation_pipeline.py
    FIRST integration backbone.
    Connects ingestion → events → signals → patterns.

06. kernel/compression_engine.py
    Critical for infinite KB scaling.
    Prevents memory explosion.

07. kernel/memory/working_memory_generator.py
    MOST IMPORTANT LLM-context file.
    Generates compressed cognition packets.

08. kernel/memory/memory_router.py
    Routes episodic/semantic/pattern memory access.

10. kernel/retrieval/unit_retriever.py
    Enables ontology/unit-aware retrieval.

11. kernel/retrieval/pattern_retriever.py
    Retrieves high-level intelligence abstractions.

12. storage/unit_storage.py
    Converts fragmented storage into unit-centric storage.

13. storage/pattern_storage.py
    Persistent global pattern memory layer.

14. simulation_engine/unit_agent.py
    Replaces FarmerAgent/TraderAgent architecture.

15. simulation_engine/behavior_registry.py
    Enables modular reusable behaviors.

16. simulation_engine/event_bridge.py
    Connects simulation outputs into kernel cognition pipeline.

17. ingestion/observation_extractor.py
    Converts raw docs/web/news into observations/signals.

18. llm/llm_orchestrator.py
    Unified multi-provider cognition orchestration layer.

19. llm/context_builder.py
    Builds optimized context using working memory.

20. units/cities/city_initializer.py
    First real-world pilot unit for architecture validation.
```
