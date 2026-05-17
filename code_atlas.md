## Codebase size
Total files processed: 188
Total lines of code: 33822
Total tokens: 224212
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
│   │   │   ├── markets/
│   │   │   ├── humans/
│   │   │   └── cities/
│   │   ├── memory/
│   │   │   ├── semantic/
│   │   │   ├── episodic/
│   │   │   │   ├── episode_e5ff1ebffb52.json
│   │   │   │   ├── observation_a1f1c6cedad1.json
│   │   │   │   ├── observation_a879e5b9449e.json
│   │   │   │   ├── observation_f3bc2de34010.json
│   │   │   │   ├── observation_e5aad657d748.json
│   │   │   │   ├── pattern_detected_1d5d95bf958b.json
│   │   │   │   ├── observation_7ed3741b3632.json
│   │   │   │   ├── belief_shift_c0cf381e041b.json
│   │   │   │   ├── episode_eafc4ade2857.json
│   │   │   │   ├── action_a16ba8343c37.json
│   │   │   │   ├── observation_837626d98a06.json
│   │   │   │   ├── observation_58e47751375a.json
│   │   │   │   ├── contradiction_detected_0f0cd3ed3de5.json
│   │   │   │   ├── observation_90164269668c.json
│   │   │   │   ├── session_start_e20ab0068dc0.json
│   │   │   │   ├── episode_244bc5322987.json
│   │   │   │   ├── episode_d5f153a6d921.json
│   │   │   │   ├── belief_changed_6da37c937e3d.json
│   │   │   │   ├── observation_0cc4f40d044e.json
│   │   │   │   ├── episode_42f9342837ae.json
│   │   │   │   ├── observation_737eb999ee33.json
│   │   │   │   ├── episode_d7c48c6f0455.json
│   │   │   │   ├── user_responded_b096f9dad8b8.json
│   │   │   │   ├── observation_c2bf35c2047d.json
│   │   │   │   ├── action_da516f041311.json
│   │   │   │   ├── observation_d450ee60c695.json
│   │   │   │   ├── episode_ce5c291d2b39.json
│   │   │   │   ├── episode_8ea19425461b.json
│   │   │   │   ├── observation_1613108eeb97.json
│   │   │   │   ├── episode_9cf144f2e5ff.json
│   │   │   │   ├── action_1d0261ba8784.json
│   │   │   │   ├── episode_93e6572ce14d.json
│   │   │   │   ├── action_2e448ed957c8.json
│   │   │   │   ├── observation_4b9de27de49a.json
│   │   │   │   ├── observation_1d8b00feb48c.json
│   │   │   │   ├── session_end_f373879fd0d1.json
│   │   │   │   ├── episode_05fd1371567f.json
│   │   │   │   ├── argument_viewed_f92f452170d8.json
│   │   │   │   ├── observation_29aea45766ca.json
│   │   │   │   ├── observation_77821502da3d.json
│   │   │   │   ├── belief_shift_2c62322d302d.json
│   │   │   │   ├── observation_c5f70f68174e.json
│   │   │   │   ├── contradiction_detected_9506dfac3a83.json
│   │   │   │   ├── action_4acd8d43da08.json
│   │   │   │   ├── episode_30446768a692.json
│   │   │   │   ├── observation_2d6b0eb915b1.json
│   │   │   │   ├── observation_2086537db4f8.json
│   │   │   │   ├── observation_d74f6f3d04bc.json
│   │   │   │   ├── action_6205b1137f7a.json
│   │   │   │   ├── action_fb7739b42d01.json
│   │   │   │   ├── action_bf7b03bf483a.json
│   │   │   │   ├── observation_3dd72bc77d32.json
│   │   │   │   ├── episode_675afbbf280f.json
│   │   │   │   ├── observation_fe0998ed8e69.json
│   │   │   │   ├── action_2eaf80adb982.json
│   │   │   │   ├── observation_4abf011fb542.json
│   │   │   │   ├── observation_434f282628f1.json
│   │   │   │   └── observation_7381166169b2.json
│   │   │   ├── working/
│   │   │   ├── hypotheses/
│   │   │   └── patterns/
│   │   └── kb/
│   │       ├── countries/
│   │       ├── companies/
│   │       ├── global/
│   │       ├── markets/
│   │       ├── humans/
│   │       ├── cities/
│   │       └── patterns/
│   ├── modules/
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
│   │   │   │   ├── old_str/
│   │   │   │   │   ├── agents.py
│   │   │   │   │   ├── base_classes.py
│   │   │   │   │   ├── model.py
│   │   │   │   │   └── simulation.py
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
│   └── simulation_engine.md
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