## Codebase size
Total files processed: 158
Total lines of code: 33423
Total tokens: 221363
## End Codebase size

## Directory Structure 
- **Project path:** `python/Agentic_Unit_PIE`
### FILE_MAP Tree
├── codebase/
│   ├── storage/
│   │   ├── unit_storage.py
│   │   └── pattern_storage.py
│   ├── temp/
│   ├── logs/
│   │   ├── agent_unit_pie.pattern_engine.log
│   │   ├── agent_unit_pie.working_memory.log
│   │   ├── agent_unit_pie.log
│   │   ├── agent_unit_pie.semantic_retriever.log
│   │   ├── agent_unit_pie.timeline_engine.log
│   │   ├── agent_unit_pie.retrieval_engine.log
│   │   ├── agent_unit_pie.memory.log
│   │   ├── agent_unit_pie.episodic_memory.log
│   │   ├── agent_unit_pie.event_engine.log
│   │   ├── agent_unit_pie.semantic_memory.log
│   │   └── agent_unit_pie.signal_engine.log
│   ├── cache/
│   ├── kernel/
│   │   ├── config/
│   │   ├── working_memory/
│   │   ├── utils/
│   │   │   ├── logger.py
│   │   │   ├── timestamps.py
│   │   │   ├── paths.py
│   │   │   └── ids.py
│   │   ├── schemas/
│   │   │   ├── unit_schema.json
│   │   │   ├── pattern_schema.py
│   │   │   ├── event_schema.py
│   │   │   ├── unit_schema.py
│   │   │   ├── signal_schema.py
│   │   │   └── relation_schema.py
│   │   ├── hypothesis/
│   │   │   ├── hypothesis_engine.py
│   │   │   └── confidence_engine.py
│   │   ├── ontology/
│   │   │   ├── event_types.py
│   │   │   ├── unit_types.py
│   │   │   ├── behavior_types.py
│   │   │   ├── pattern_types.py
│   │   │   ├── relation_types.py
│   │   │   ├── signal_types.py
│   │   │   └── resource_types.py
│   │   ├── memory/
│   │   │   ├── working_memory.py
│   │   │   ├── memory_engine.py
│   │   │   ├── episodic_memory.py
│   │   │   └── semantic_memory.py
│   │   ├── retrieval/
│   │   │   ├── timeline_retriever.py
│   │   │   ├── semantic_retriever.py
│   │   │   ├── unit_retriever.py
│   │   │   ├── pattern_retriever.py
│   │   │   ├── retrieval_engine.py
│   │   │   ├── hierarchy_retriever.py
│   │   │   └── relation_retriever.py
│   │   ├── signals/
│   │   │   ├── signal_engine.py
│   │   │   └── signal_validator.py
│   │   ├── events/
│   │   │   ├── timeline_engine.py
│   │   │   └── event_engine.py
│   │   ├── patterns/
│   │   │   ├── anomaly_detector.py
│   │   │   ├── trend_detector.py
│   │   │   └── pattern_engine.py
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
│   │   │   │   ├── observation_e5aad657d748.json
│   │   │   │   ├── observation_90164269668c.json
│   │   │   │   ├── observation_737eb999ee33.json
│   │   │   │   ├── action_da516f041311.json
│   │   │   │   ├── observation_d450ee60c695.json
│   │   │   │   ├── observation_1613108eeb97.json
│   │   │   │   ├── observation_29aea45766ca.json
│   │   │   │   ├── action_4acd8d43da08.json
│   │   │   │   ├── observation_2d6b0eb915b1.json
│   │   │   │   ├── action_fb7739b42d01.json
│   │   │   │   ├── observation_3dd72bc77d32.json
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
│   │   │   │   ├── simulations/
│   │   │   │   │   ├── city_growth.yaml
│   │   │   │   │   ├── startup_company.yaml
│   │   │   │   │   ├── agriculture.yaml
│   │   │   │   │   ├── ecosystem.yaml
│   │   │   │   │   └── ai_society.yaml
│   │   │   │   ├── static/
│   │   │   │   │   └── game.html
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
│   │   ├── context_builder.py
│   │   └── llm_orchestrator.py
│   ├── system_instruction.md
│   ├── agent_tools.py
│   ├── agent.py
│   ├── Launcher.md
│   ├── __init__.py
│   └── tui_output.txt
├── Issues_n_ideas.md
├── agent_harness.md
├── code_atlas.md
├── devpt_report.md
├── Minimax_Plan.md
├── code_dump.txt
├── .gitignore
├── README.md
├── project_tools.md
├── Claude_Plan.md
└── README_old.md
### End Tree