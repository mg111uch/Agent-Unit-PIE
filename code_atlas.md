## Codebase size
Total files processed: 184
Total lines of code: 33697
Total tokens: 221135
## End Codebase size

## Directory Structure 
- **Project path:** `/home/manigupt/Hello/python/Agentic_Unit_PIE`
### FILE_MAP Tree
├── codebase/
│   ├── storage/
│   │   ├── raw_observation_storage.py
│   │   ├── unit_storage.py
│   │   ├── timeline_storage.py
│   │   ├── pattern_storage.py
│   │   └── hypothesis_storage.py
│   ├── ingestion/
│   ├── sub-agents/
│   │   ├── improvement_agent.py
│   │   ├── debate_agent.py
│   │   ├── observer_agent.py
│   │   ├── summarizer_agent.py
│   │   ├── simulation_agent.py
│   │   └── pattern_agent.py
│   ├── visualization/
│   ├── temp/
│   ├── logs/
│   │   ├── agent_unit_pie.pattern_engine.log
│   │   ├── agent_unit_pie.working_memory.log
│   │   ├── agent_unit_pie.log
│   │   ├── agent_unit_pie.belief_signal_handler.log
│   │   ├── agent_unit_pie.semantic_retriever.log
│   │   ├── agent_unit_pie.timeline_engine.log
│   │   ├── agent_unit_pie.retrieval_engine.log
│   │   ├── agent_unit_pie.memory.log
│   │   ├── agent_unit_pie.episodic_memory.log
│   │   ├── agent_unit_pie.event_engine.log
│   │   ├── agent_unit_pie.hypothesis_engine.log
│   │   ├── agent_unit_pie.semantic_memory.log
│   │   └── agent_unit_pie.signal_engine.log
│   ├── cache/
│   ├── kernel/
│   │   ├── config/
│   │   │   ├── kernel_config.py
│   │   │   └── ontology_config.py
│   │   ├── working_memory/
│   │   ├── utils/
│   │   │   ├── logger.py
│   │   │   ├── timestamps.py
│   │   │   ├── paths.py
│   │   │   └── ids.py
│   │   ├── schemas/
│   │   │   ├── hypothesis_schema.py
│   │   │   ├── simulation_schema.py
│   │   │   ├── memory_schema.py
│   │   │   ├── pattern_schema.py
│   │   │   ├── event_schema.py
│   │   │   ├── unit_schema.py
│   │   │   ├── signal_schema.py
│   │   │   └── relation_schema.py
│   │   ├── hypothesis/
│   │   │   ├── hypothesis_engine.py
│   │   │   ├── validation_engine.py
│   │   │   └── confidence_engine.py
│   │   ├── ontology/
│   │   │   ├── event_types.py
│   │   │   ├── unit_types.py
│   │   │   ├── behavior_types.py
│   │   │   ├── pattern_types.py
│   │   │   ├── relation_types.py
│   │   │   ├── signal_types.py
│   │   │   ├── hypothesis_types.py
│   │   │   └── resource_types.py
│   │   ├── memory/
│   │   │   ├── working_memory.py
│   │   │   ├── memory_engine.py
│   │   │   ├── episodic_memory.py
│   │   │   ├── semantic_memory.py
│   │   │   └── pattern_memory.py
│   │   ├── retrieval/
│   │   │   ├── timeline_retriever.py
│   │   │   ├── semantic_retriever.py
│   │   │   ├── unit_retriever.py
│   │   │   ├── pattern_retriever.py
│   │   │   ├── retrieval_engine.py
│   │   │   ├── hierarchy_retriever.py
│   │   │   └── relation_retriever.py
│   │   ├── signals/
│   │   │   ├── signal_extractor.py
│   │   │   ├── signal_engine.py
│   │   │   ├── belief_signal_handler.py
│   │   │   ├── signal_router.py
│   │   │   └── signal_validator.py
│   │   ├── events/
│   │   │   ├── event_extractor.py
│   │   │   ├── timeline_engine.py
│   │   │   └── event_engine.py
│   │   ├── patterns/
│   │   │   ├── anomaly_detector.py
│   │   │   ├── contradiction_detector.py
│   │   │   ├── trend_detector.py
│   │   │   ├── pattern_engine.py
│   │   │   └── causal_engine.py
│   │   ├── observation_pipeline.py
│   │   ├── compression_engine.py
│   │   ├── unit_registry.py
│   │   ├── ontology_registry.py
│   │   └── __init__.py
│   ├── units/
│   │   ├── simulations/
│   │   │   ├── test_run_003/
│   │   │   │   ├── params.yaml
│   │   │   │   ├── summary.json
│   │   │   │   ├── data.csv
│   │   │   │   └── signals.json
│   │   │   ├── test_run_001/
│   │   │   │   ├── params.yaml
│   │   │   │   ├── summary.json
│   │   │   │   ├── data.csv
│   │   │   │   └── signals.json
│   │   │   └── kernel_test_001/
│   │   │       ├── params.yaml
│   │   │       ├── summary.json
│   │   │       ├── data.csv
│   │   │       └── signals.json
│   │   ├── countries/
│   │   ├── codebases/
│   │   ├── humans/
│   │   │   └── user_001/
│   │   │       ├── development/
│   │   │       ├── finance/
│   │   │       ├── mind/
│   │   │       ├── body/
│   │   │       ├── profile/
│   │   │       └── system_summery.md
│   │   ├── organizations/
│   │   └── cities/
│   │       ├── lucknow/
│   │       ├── delhi/
│   │       ├── kanpur/
│   │       ├── city_summary_generator.py
│   │       ├── city_signal_mapper.py
│   │       ├── city_pattern_detector.py
│   │       └── city_initializer.py
│   ├── data/
│   │   ├── simulations/
│   │   │   ├── countries/
│   │   │   ├── humans/
│   │   │   └── cities/
│   │   ├── memory/
│   │   │   ├── semantic/
│   │   │   ├── working/
│   │   │   ├── hypotheses/
│   │   │   └── patterns/
│   │   └── kb/
│   ├── modules/
│   │   ├── codebase_atlas/
│   │   │   ├── generators/
│   │   │   │   ├── detail_generator.py
│   │   │   │   ├── base_generator.py
│   │   │   │   └── __init__.py
│   │   │   ├── utils/
│   │   │   │   ├── __init__.py
│   │   │   │   ├── formatting.py
│   │   │   │   └── io_helpers.py
│   │   │   ├── analyzers/
│   │   │   │   ├── entry_point_detector.py
│   │   │   │   ├── __init__.py
│   │   │   │   ├── dependency_analyzer.py
│   │   │   │   └── impact_analyzer.py
│   │   │   ├── parsers/
│   │   │   │   ├── html_parser.py
│   │   │   │   ├── config_parser.py
│   │   │   │   ├── __init__.py
│   │   │   │   ├── javascript_parser.py
│   │   │   │   ├── base_parser.py
│   │   │   │   └── python_parser.py
│   │   │   ├── models.py
│   │   │   ├── scanner.py
│   │   │   ├── config.py
│   │   │   ├── main.py
│   │   │   ├── __init__.py
│   │   │   └── README.md
│   │   ├── simulators/
│   │   │   ├── popula_dyn/
│   │   │   │   ├── static/
│   │   │   │   │   └── game.html
│   │   │   │   ├── simulations_config/
│   │   │   │   │   ├── city_growth.yaml
│   │   │   │   │   ├── startup_company.yaml
│   │   │   │   │   ├── agriculture.yaml
│   │   │   │   │   ├── ecosystem.yaml
│   │   │   │   │   └── ai_society.yaml
│   │   │   │   ├── core/
│   │   │   │   │   ├── unit_agent.py
│   │   │   │   │   ├── resource_engine.py
│   │   │   │   │   ├── spatial_engine.py
│   │   │   │   │   ├── agent_factory.py
│   │   │   │   │   ├── event_bridge.py
│   │   │   │   │   ├── world_engine.py
│   │   │   │   │   └── simulation_model.py
│   │   │   │   ├── behaviours/
│   │   │   │   │   ├── consume.py
│   │   │   │   │   ├── survival.py
│   │   │   │   │   ├── idle.py
│   │   │   │   │   ├── learn.py
│   │   │   │   │   ├── produce.py
│   │   │   │   │   ├── __init__.py
│   │   │   │   │   ├── regrow.py
│   │   │   │   │   ├── trade.py
│   │   │   │   │   ├── base_behavior.py
│   │   │   │   │   ├── harvest.py
│   │   │   │   │   ├── reproduce.py
│   │   │   │   │   ├── heal.py
│   │   │   │   │   └── move.py
│   │   │   │   ├── simulation_plot.png
│   │   │   │   ├── constants.py
│   │   │   │   ├── simulation_game.py
│   │   │   │   ├── main.py
│   │   │   │   ├── behavior_registry.py
│   │   │   │   └── SimDvptPhases.md
│   │   │   └── simulation_connector.py
│   │   ├── argu_god/
│   │   │   ├── engine/
│   │   │   │   ├── loop.py
│   │   │   │   ├── retriever.py
│   │   │   │   ├── analyzer.py
│   │   │   │   ├── question_builder.py
│   │   │   │   ├── storage.py
│   │   │   │   ├── cli.py
│   │   │   │   ├── kernel_bridge.py
│   │   │   │   └── vector_store.py
│   │   │   ├── static/
│   │   │   │   ├── graph.js
│   │   │   │   └── index.html
│   │   │   ├── topics/
│   │   │   │   └── theism_atheism/
│   │   │   │       ├── wiki/
│   │   │   │       │   └── index.md
│   │   │   │       ├── raw/
│   │   │   │       ├── schema.md
│   │   │   │       ├── graph.json
│   │   │   │       └── metadata.json
│   │   │   ├── mindmaps/
│   │   │   │   ├── global_aggregated/
│   │   │   │   └── local_user/
│   │   │   │       ├── sessions/
│   │   │   │       │   └── session_20260517_181303.json
│   │   │   │       ├── belief_state.json
│   │   │   │       ├── human_mind_map.md
│   │   │   │       ├── interaction_log.json
│   │   │   │       └── mindmap.json
│   │   │   ├── main.py
│   │   │   ├── AGENTS.md
│   │   │   ├── global_schema.md
│   │   │   └── llm_compiler.py
│   │   └── digital_twins/
│   │       ├── city_twin.py
│   │       ├── digital_twin_manager.py
│   │       ├── human_twin.py
│   │       └── company_twin.py
│   ├── tests/
│   │   ├── __init__.py
│   │   └── agent_test.py
│   ├── llm/
│   │   ├── extractors/
│   │   │   ├── signal_extractor.py
│   │   │   ├── pattern_extractor.py
│   │   │   └── hypothesis_extractor.py
│   │   ├── context_builder.py
│   │   └── llm_orchestrator.py
│   ├── system_instruction.md
│   ├── agent_tools.py
│   ├── agent.py
│   ├── Launcher.md
│   ├── __init__.py
│   └── tui_output.txt
├── system_devpt_reports/
│   ├── kernel.md
│   ├── debate_engine.md
│   ├── simulation_engine.md
│   └── orchestrator.md
├── GPT_5-5_Chat.md
├── Issues_n_ideas.md
├── agent_harness.md
├── code_atlas.md
├── Devpt_phases.md
├── code_dump.txt
├── .gitignore
├── README.md
└── project_tools.md
### End Tree