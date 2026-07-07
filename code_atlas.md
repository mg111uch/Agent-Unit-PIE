## Codebase size
Total files processed: 218
Total lines of code: 41263
Total tokens: 262558
## End Codebase size

## Directory Structure 
- **Project path:** `/home/manigupt/Hello/python/Agentic_Unit_PIE`
### FILE_MAP Tree
├── codebase/ [43049 LOC, 216743 tokens]
│   ├── storage/ [792 LOC, 3754 tokens]
│   │   ├── raw_observation_storage.py
│   │   ├── [] unit_storage.py [416 LOC, 1964 tokens]
│   │   ├── timeline_storage.py
│   │   ├── [] pattern_storage.py [376 LOC, 1790 tokens]
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
│   ├── cache/
│   ├── kernel/ [13834 LOC, 67151 tokens]
│   │   ├── config/
│   │   │   ├── kernel_config.py
│   │   │   └── ontology_config.py
│   │   ├── working_memory/
│   │   ├── utils/ [773 LOC, 3186 tokens]
│   │   │   ├── [] logger.py [182 LOC, 739 tokens]
│   │   │   ├── [] timestamps.py [223 LOC, 849 tokens]
│   │   │   ├── [] paths.py [208 LOC, 885 tokens]
│   │   │   └── [] ids.py [160 LOC, 713 tokens]
│   │   ├── schemas/ [928 LOC, 6003 tokens]
│   │   │   ├── hypothesis_schema.py
│   │   │   ├── simulation_schema.py
│   │   │   ├── memory_schema.py
│   │   │   ├── [] pattern_schema.py [252 LOC, 1574 tokens]
│   │   │   ├── [] event_schema.py [219 LOC, 1345 tokens]
│   │   │   ├── [] unit_schema.py [159 LOC, 1075 tokens]
│   │   │   ├── [] signal_schema.py [129 LOC, 899 tokens]
│   │   │   └── [] relation_schema.py [169 LOC, 1110 tokens]
│   │   ├── hypothesis/ [932 LOC, 4740 tokens]
│   │   │   ├── [] hypothesis_engine.py [447 LOC, 2287 tokens]
│   │   │   ├── validation_engine.py
│   │   │   └── [] confidence_engine.py [485 LOC, 2453 tokens]
│   │   ├── ontology/ [3057 LOC, 11867 tokens]
│   │   │   ├── [] event_types.py [401 LOC, 1841 tokens]
│   │   │   ├── [] unit_types.py [370 LOC, 1499 tokens]
│   │   │   ├── [] behavior_types.py [615 LOC, 2149 tokens]
│   │   │   ├── [] pattern_types.py [346 LOC, 1573 tokens]
│   │   │   ├── [] relation_types.py [542 LOC, 1905 tokens]
│   │   │   ├── [] signal_types.py [319 LOC, 1307 tokens]
│   │   │   ├── hypothesis_types.py
│   │   │   └── [] resource_types.py [464 LOC, 1593 tokens]
│   │   ├── memory/ [1210 LOC, 7250 tokens]
│   │   │   ├── [] working_memory.py [247 LOC, 1543 tokens]
│   │   │   ├── [] memory_engine.py [235 LOC, 1428 tokens]
│   │   │   ├── [] episodic_memory.py [308 LOC, 1781 tokens]
│   │   │   ├── [] semantic_memory.py [420 LOC, 2498 tokens]
│   │   │   └── pattern_memory.py
│   │   ├── retrieval/ [2742 LOC, 12941 tokens]
│   │   │   ├── [] timeline_retriever.py [527 LOC, 2351 tokens]
│   │   │   ├── [] semantic_retriever.py [439 LOC, 2189 tokens]
│   │   │   ├── [] unit_retriever.py [407 LOC, 1834 tokens]
│   │   │   ├── [] pattern_retriever.py [551 LOC, 2547 tokens]
│   │   │   ├── [] retrieval_engine.py [401 LOC, 1916 tokens]
│   │   │   ├── [] hierarchy_retriever.py [408 LOC, 1995 tokens]
│   │   │   └── [] relation_retriever.py [9 LOC, 109 tokens]
│   │   ├── signals/ [738 LOC, 4038 tokens]
│   │   │   ├── signal_extractor.py
│   │   │   ├── [] signal_engine.py [322 LOC, 1710 tokens]
│   │   │   ├── [] belief_signal_handler.py [159 LOC, 1039 tokens]
│   │   │   ├── signal_router.py
│   │   │   └── [] signal_validator.py [257 LOC, 1289 tokens]
│   │   ├── events/ [627 LOC, 3371 tokens]
│   │   │   ├── event_extractor.py
│   │   │   ├── [] timeline_engine.py [295 LOC, 1562 tokens]
│   │   │   └── [] event_engine.py [332 LOC, 1809 tokens]
│   │   ├── patterns/ [1174 LOC, 6137 tokens]
│   │   │   ├── [] anomaly_detector.py [398 LOC, 2021 tokens]
│   │   │   ├── contradiction_detector.py
│   │   │   ├── [] trend_detector.py [381 LOC, 2053 tokens]
│   │   │   ├── [] pattern_engine.py [395 LOC, 2063 tokens]
│   │   │   └── causal_engine.py
│   │   ├── [] observation_pipeline.py [289 LOC, 1434 tokens]
│   │   ├── [] compression_engine.py [320 LOC, 1736 tokens]
│   │   ├── [] unit_registry.py [426 LOC, 1921 tokens]
│   │   ├── [] ontology_registry.py [432 LOC, 1750 tokens]
│   │   └── [] __init__.py [186 LOC, 777 tokens]
│   ├── units/ [339 LOC, 1677 tokens]
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
│   │   └── cities/ [339 LOC, 1677 tokens]
│   │       ├── lucknow/
│   │       ├── delhi/
│   │       ├── kanpur/
│   │       ├── city_summary_generator.py
│   │       ├── city_signal_mapper.py
│   │       ├── city_pattern_detector.py
│   │       └── [] city_initializer.py [339 LOC, 1677 tokens]
│   ├── data/
│   │   ├── memory/
│   │   │   ├── semantic/
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
│   ├── modules/ [26277 LOC, 132639 tokens]
│   │   ├── codebase_atlas/ [16604 LOC, 74991 tokens]
│   │   │   ├── generators/ [367 LOC, 2519 tokens]
│   │   │   │   ├── [] detail_generator.py [139 LOC, 880 tokens]
│   │   │   │   ├── [] base_generator.py [213 LOC, 1557 tokens]
│   │   │   │   └── [] __init__.py [15 LOC, 82 tokens]
│   │   │   ├── utils/ [441 LOC, 2941 tokens]
│   │   │   │   ├── [] __init__.py [34 LOC, 123 tokens]
│   │   │   │   ├── [] formatting.py [221 LOC, 1831 tokens]
│   │   │   │   └── [] io_helpers.py [186 LOC, 987 tokens]
│   │   │   ├── analyzers/ [816 LOC, 5475 tokens]
│   │   │   │   ├── [] entry_point_detector.py [210 LOC, 1381 tokens]
│   │   │   │   ├── [] __init__.py [18 LOC, 90 tokens]
│   │   │   │   ├── [] dependency_analyzer.py [269 LOC, 1795 tokens]
│   │   │   │   └── [] impact_analyzer.py [319 LOC, 2209 tokens]
│   │   │   ├── graph/ [12478 LOC, 47749 tokens]
│   │   │   │   ├── backend/ [1615 LOC, 7386 tokens]
│   │   │   │   │   ├── renderers/ [150 LOC, 624 tokens]
│   │   │   │   │   │   ├── [] interactive_renderer.py [150 LOC, 624 tokens]
│   │   │   │   │   │   └── __init__.py
│   │   │   │   │   ├── [] graph_models.py [242 LOC, 1170 tokens]
│   │   │   │   │   ├── [] graph_builder.py [413 LOC, 2025 tokens]
│   │   │   │   │   ├── __init__.py
│   │   │   │   │   ├── [] serve.py [329 LOC, 1606 tokens]
│   │   │   │   │   └── [] graph_serializer.py [481 LOC, 1961 tokens]
│   │   │   │   ├── web/ [10863 LOC, 40363 tokens]
│   │   │   │   │   ├── utils/ [355 LOC, 1277 tokens]
│   │   │   │   │   │   └── [] geometry.js [355 LOC, 1277 tokens]
│   │   │   │   │   ├── viewport/ [658 LOC, 2213 tokens]
│   │   │   │   │   │   ├── [] navigation.js [305 LOC, 959 tokens]
│   │   │   │   │   │   └── [] viewport.js [353 LOC, 1254 tokens]
│   │   │   │   │   ├── layout/ [710 LOC, 3482 tokens]
│   │   │   │   │   │   └── [] layout.js [710 LOC, 3482 tokens]
│   │   │   │   │   ├── core/ [1931 LOC, 7203 tokens]
│   │   │   │   │   │   ├── [] events.js [235 LOC, 878 tokens]
│   │   │   │   │   │   ├── [] constants.js [219 LOC, 667 tokens]
│   │   │   │   │   │   ├── [] types.js [337 LOC, 1278 tokens]
│   │   │   │   │   │   ├── [] storage.js [337 LOC, 1093 tokens]
│   │   │   │   │   │   └── [] state.js [803 LOC, 3287 tokens]
│   │   │   │   │   ├── render/ [3147 LOC, 11637 tokens]
│   │   │   │   │   │   ├── [] edges.js [679 LOC, 2474 tokens]
│   │   │   │   │   │   ├── [] renderer.js [866 LOC, 3427 tokens]
│   │   │   │   │   │   ├── [] clusters.js [387 LOC, 1228 tokens]
│   │   │   │   │   │   ├── [] viewport_culler.js [292 LOC, 1399 tokens]
│   │   │   │   │   │   ├── [] nodes.js [654 LOC, 2117 tokens]
│   │   │   │   │   │   └── [] styles.js [269 LOC, 992 tokens]
│   │   │   │   │   ├── interaction/ [2256 LOC, 7495 tokens]
│   │   │   │   │   │   ├── [] events.js [541 LOC, 1803 tokens]
│   │   │   │   │   │   ├── [] interaction.js [891 LOC, 3106 tokens]
│   │   │   │   │   │   ├── [] drag.js [392 LOC, 1255 tokens]
│   │   │   │   │   │   └── [] selection.js [432 LOC, 1331 tokens]
│   │   │   │   │   ├── [] graph_viewer.js [915 LOC, 3208 tokens]
│   │   │   │   │   ├── [] graph_viewer.html [767 LOC, 3424 tokens]
│   │   │   │   │   └── [] bootstrap.js [124 LOC, 424 tokens]
│   │   │   │   └── __init__.py
│   │   │   ├── parsers/ [1204 LOC, 7725 tokens]
│   │   │   │   ├── [] html_parser.py [110 LOC, 728 tokens]
│   │   │   │   ├── [] config_parser.py [125 LOC, 770 tokens]
│   │   │   │   ├── [] __init__.py [23 LOC, 124 tokens]
│   │   │   │   ├── [] javascript_parser.py [435 LOC, 2932 tokens]
│   │   │   │   ├── [] base_parser.py [94 LOC, 479 tokens]
│   │   │   │   └── [] python_parser.py [417 LOC, 2692 tokens]
│   │   │   ├── [] models.py [332 LOC, 2670 tokens]
│   │   │   ├── [] scanner.py [217 LOC, 1295 tokens]
│   │   │   ├── [] config.py [293 LOC, 1853 tokens]
│   │   │   ├── [] main.py [395 LOC, 2465 tokens]
│   │   │   └── [] __init__.py [61 LOC, 299 tokens]
│   │   ├── simulators/ [5086 LOC, 31617 tokens]
│   │   │   ├── popula_dyn/ [4773 LOC, 29238 tokens]
│   │   │   │   ├── static/ [474 LOC, 3447 tokens]
│   │   │   │   │   └── [] game.html [474 LOC, 3447 tokens]
│   │   │   │   ├── simulations_config/ [15 LOC, 52 tokens]
│   │   │   │   │   ├── city_growth.yaml
│   │   │   │   │   ├── startup_company.yaml
│   │   │   │   │   ├── [] agriculture.yaml [15 LOC, 52 tokens]
│   │   │   │   │   ├── ecosystem.yaml
│   │   │   │   │   └── ai_society.yaml
│   │   │   │   ├── core/ [2682 LOC, 14273 tokens]
│   │   │   │   │   ├── [] unit_agent.py [428 LOC, 2090 tokens]
│   │   │   │   │   ├── [] resource_engine.py [640 LOC, 2851 tokens]
│   │   │   │   │   ├── [] spatial_engine.py [148 LOC, 1055 tokens]
│   │   │   │   │   ├── [] agent_factory.py [204 LOC, 1252 tokens]
│   │   │   │   │   ├── [] event_bridge.py [236 LOC, 1109 tokens]
│   │   │   │   │   ├── [] world_engine.py [668 LOC, 3010 tokens]
│   │   │   │   │   └── [] simulation_model.py [358 LOC, 2906 tokens]
│   │   │   │   ├── behaviours/ [856 LOC, 4445 tokens]
│   │   │   │   │   ├── [] consume.py [66 LOC, 316 tokens]
│   │   │   │   │   ├── [] survival.py [96 LOC, 471 tokens]
│   │   │   │   │   ├── [] idle.py [27 LOC, 96 tokens]
│   │   │   │   │   ├── [] learn.py [38 LOC, 157 tokens]
│   │   │   │   │   ├── [] produce.py [77 LOC, 461 tokens]
│   │   │   │   │   ├── [] __init__.py [53 LOC, 340 tokens]
│   │   │   │   │   ├── [] regrow.py [46 LOC, 222 tokens]
│   │   │   │   │   ├── [] trade.py [132 LOC, 700 tokens]
│   │   │   │   │   ├── [] base_behavior.py [49 LOC, 211 tokens]
│   │   │   │   │   ├── [] harvest.py [62 LOC, 317 tokens]
│   │   │   │   │   ├── [] reproduce.py [84 LOC, 500 tokens]
│   │   │   │   │   ├── [] heal.py [71 LOC, 393 tokens]
│   │   │   │   │   └── [] move.py [55 LOC, 261 tokens]
│   │   │   │   ├── [] constants.py [28 LOC, 291 tokens]
│   │   │   │   ├── [] simulation_game.py [204 LOC, 1466 tokens]
│   │   │   │   ├── [] main.py [16 LOC, 100 tokens]
│   │   │   │   ├── [] behavior_registry.py [133 LOC, 739 tokens]
│   │   │   │   └── [] SimDvptPhases.md [365 LOC, 4425 tokens]
│   │   │   └── [] simulation_connector.py [313 LOC, 2379 tokens]
│   │   ├── argu_god/ [1869 LOC, 13620 tokens]
│   │   │   ├── engine/ [930 LOC, 6004 tokens]
│   │   │   │   ├── [] loop.py [246 LOC, 1785 tokens]
│   │   │   │   ├── [] retriever.py [46 LOC, 252 tokens]
│   │   │   │   ├── [] analyzer.py [19 LOC, 139 tokens]
│   │   │   │   ├── [] question_builder.py [25 LOC, 142 tokens]
│   │   │   │   ├── [] storage.py [53 LOC, 333 tokens]
│   │   │   │   ├── [] cli.py [12 LOC, 78 tokens]
│   │   │   │   ├── [] kernel_bridge.py [488 LOC, 3046 tokens]
│   │   │   │   └── [] vector_store.py [41 LOC, 229 tokens]
│   │   │   ├── static/ [269 LOC, 2249 tokens]
│   │   │   │   ├── [] graph.js [232 LOC, 1842 tokens]
│   │   │   │   └── [] index.html [37 LOC, 407 tokens]
│   │   │   ├── topics/ [372 LOC, 2976 tokens]
│   │   │   │   └── theism_atheism/ [372 LOC, 2976 tokens]
│   │   │   │       ├── wiki/ [7 LOC, 255 tokens]
│   │   │   │       │   └── [] index.md [7 LOC, 255 tokens]
│   │   │   │       ├── raw/
│   │   │   │       ├── [] schema.md [17 LOC, 138 tokens]
│   │   │   │       ├── [] graph.json [348 LOC, 2583 tokens]
│   │   │   │       └── metadata.json
│   │   │   ├── mindmaps/ [88 LOC, 622 tokens]
│   │   │   │   ├── global_aggregated/
│   │   │   │   └── local_user/ [88 LOC, 622 tokens]
│   │   │   │       ├── sessions/ [24 LOC, 163 tokens]
│   │   │   │       │   └── [] session_20260517_181303.json [24 LOC, 163 tokens]
│   │   │   │       ├── [] belief_state.json [10 LOC, 52 tokens]
│   │   │   │       ├── [] human_mind_map.md [6 LOC, 41 tokens]
│   │   │   │       ├── [] interaction_log.json [35 LOC, 277 tokens]
│   │   │   │       └── [] mindmap.json [13 LOC, 89 tokens]
│   │   │   ├── [] main.py [57 LOC, 467 tokens]
│   │   │   ├── [] AGENTS.md [20 LOC, 234 tokens]
│   │   │   ├── [] global_schema.md [33 LOC, 267 tokens]
│   │   │   └── [] llm_compiler.py [100 LOC, 801 tokens]
│   │   └── digital_twins/ [2718 LOC, 12411 tokens]
│   │       ├── [] city_twin.py [692 LOC, 3188 tokens]
│   │       ├── [] digital_twin_manager.py [635 LOC, 2797 tokens]
│   │       ├── [] human_twin.py [624 LOC, 2827 tokens]
│   │       └── [] company_twin.py [767 LOC, 3599 tokens]
│   ├── tests/ [179 LOC, 1156 tokens]
│   │   ├── [] __init__.py [1 LOC, 9 tokens]
│   │   └── [] agent_test.py [178 LOC, 1147 tokens]
│   ├── llm/ [626 LOC, 3289 tokens]
│   │   ├── providers/ [113 LOC, 736 tokens]
│   │   │   ├── [] openrouter_provider.py [57 LOC, 376 tokens]
│   │   │   ├── __init__.py
│   │   │   └── [] gemini_provider.py [56 LOC, 360 tokens]
│   │   ├── extractors/
│   │   │   ├── signal_extractor.py
│   │   │   ├── pattern_extractor.py
│   │   │   └── hypothesis_extractor.py
│   │   ├── [] context_builder.py [400 LOC, 1791 tokens]
│   │   └── [] llm_orchestrator.py [113 LOC, 762 tokens]
│   ├── [] system_instruction.md [99 LOC, 758 tokens]
│   ├── [] agent_tools.py [602 LOC, 4086 tokens]
│   ├── [] agent.py [300 LOC, 2228 tokens]
│   ├── [] __init__.py [1 LOC, 5 tokens]
│   └── tui_output.txt
├── system_devpt_reports/ [1583 LOC, 12924 tokens]
│   ├── codebase_atlas/ [663 LOC, 7421 tokens]
│   │   ├── [] current_status.md [211 LOC, 1311 tokens]
│   │   ├── [] devpt_roadmap.md [202 LOC, 4004 tokens]
│   │   └── [] README.md [250 LOC, 2106 tokens]
│   ├── [] kernel.md [162 LOC, 1110 tokens]
│   ├── [] debate_engine.md [323 LOC, 1739 tokens]
│   ├── [] simulation_engine.md [217 LOC, 1380 tokens]
│   └── [] orchestrator.md [218 LOC, 1274 tokens]
├── [] GPT_5-5_Chat.md [4962 LOC, 18724 tokens]
├── [] Issues_n_ideas.md [11 LOC, 1 tokens]
├── [] agent_harness.md [34 LOC, 395 tokens]
├── [] code_atlas.md [321 LOC, 5652 tokens]
├── [] Devpt_phases.md [333 LOC, 2918 tokens]
├── code_dump.txt
├── [] .gitignore [7 LOC, 23 tokens]
├── [] README.md [953 LOC, 4763 tokens]
└── [] project_tools.md [24 LOC, 909 tokens]
### End Tree