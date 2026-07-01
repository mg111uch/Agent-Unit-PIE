## Codebase size
Total files processed: 219
Total lines of code: 42535
Total tokens: 266749
## End Codebase size

## Directory Structure 
- **Project path:** `/home/manigupt/Hello/python/Agentic_Unit_PIE`
### FILE_MAP Tree
├── codebase/ [49746 LOC, 304528 tokens]
│   ├── storage/ [1071 LOC, 4056 tokens]
│   │   ├── raw_observation_storage.py
│   │   ├── [] unit_storage.py [553 LOC, 2124 tokens]
│   │   ├── timeline_storage.py
│   │   ├── [] pattern_storage.py [518 LOC, 1932 tokens]
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
│   ├── kernel/ [18412 LOC, 71852 tokens]
│   │   ├── config/
│   │   │   ├── kernel_config.py
│   │   │   └── ontology_config.py
│   │   ├── working_memory/
│   │   ├── utils/ [928 LOC, 3455 tokens]
│   │   │   ├── [] logger.py [222 LOC, 818 tokens]
│   │   │   ├── [] timestamps.py [263 LOC, 919 tokens]
│   │   │   ├── [] paths.py [247 LOC, 955 tokens]
│   │   │   └── [] ids.py [196 LOC, 763 tokens]
│   │   ├── schemas/ [1309 LOC, 6387 tokens]
│   │   │   ├── hypothesis_schema.py
│   │   │   ├── simulation_schema.py
│   │   │   ├── memory_schema.py
│   │   │   ├── [] pattern_schema.py [383 LOC, 1724 tokens]
│   │   │   ├── [] event_schema.py [316 LOC, 1473 tokens]
│   │   │   ├── [] unit_schema.py [190 LOC, 1075 tokens]
│   │   │   ├── [] signal_schema.py [161 LOC, 900 tokens]
│   │   │   └── [] relation_schema.py [259 LOC, 1215 tokens]
│   │   ├── hypothesis/ [1354 LOC, 5009 tokens]
│   │   │   ├── [] hypothesis_engine.py [657 LOC, 2404 tokens]
│   │   │   ├── validation_engine.py
│   │   │   └── [] confidence_engine.py [697 LOC, 2605 tokens]
│   │   ├── ontology/ [3328 LOC, 12540 tokens]
│   │   │   ├── [] event_types.py [459 LOC, 2029 tokens]
│   │   │   ├── [] unit_types.py [403 LOC, 1568 tokens]
│   │   │   ├── [] behavior_types.py [646 LOC, 2210 tokens]
│   │   │   ├── [] pattern_types.py [396 LOC, 1729 tokens]
│   │   │   ├── [] relation_types.py [578 LOC, 1982 tokens]
│   │   │   ├── [] signal_types.py [350 LOC, 1368 tokens]
│   │   │   ├── hypothesis_types.py
│   │   │   └── [] resource_types.py [496 LOC, 1654 tokens]
│   │   ├── memory/ [1761 LOC, 7721 tokens]
│   │   │   ├── [] working_memory.py [391 LOC, 1678 tokens]
│   │   │   ├── [] memory_engine.py [327 LOC, 1529 tokens]
│   │   │   ├── [] episodic_memory.py [437 LOC, 1891 tokens]
│   │   │   ├── [] semantic_memory.py [606 LOC, 2623 tokens]
│   │   │   └── pattern_memory.py
│   │   ├── retrieval/ [3904 LOC, 13941 tokens]
│   │   │   ├── [] timeline_retriever.py [674 LOC, 2492 tokens]
│   │   │   ├── [] semantic_retriever.py [665 LOC, 2338 tokens]
│   │   │   ├── [] unit_retriever.py [593 LOC, 2055 tokens]
│   │   │   ├── [] pattern_retriever.py [754 LOC, 2733 tokens]
│   │   │   ├── [] retrieval_engine.py [593 LOC, 2072 tokens]
│   │   │   ├── [] hierarchy_retriever.py [616 LOC, 2142 tokens]
│   │   │   └── [] relation_retriever.py [9 LOC, 109 tokens]
│   │   ├── signals/ [1023 LOC, 4305 tokens]
│   │   │   ├── signal_extractor.py
│   │   │   ├── [] signal_engine.py [449 LOC, 1853 tokens]
│   │   │   ├── [] belief_signal_handler.py [191 LOC, 1042 tokens]
│   │   │   ├── signal_router.py
│   │   │   └── [] signal_validator.py [383 LOC, 1410 tokens]
│   │   ├── events/ [885 LOC, 3634 tokens]
│   │   │   ├── event_extractor.py
│   │   │   ├── [] timeline_engine.py [418 LOC, 1681 tokens]
│   │   │   └── [] event_engine.py [467 LOC, 1953 tokens]
│   │   ├── patterns/ [1723 LOC, 6473 tokens]
│   │   │   ├── [] anomaly_detector.py [590 LOC, 2107 tokens]
│   │   │   ├── contradiction_detector.py
│   │   │   ├── [] trend_detector.py [568 LOC, 2184 tokens]
│   │   │   ├── [] pattern_engine.py [565 LOC, 2182 tokens]
│   │   │   └── causal_engine.py
│   │   ├── [] observation_pipeline.py [381 LOC, 1571 tokens]
│   │   ├── [] compression_engine.py [448 LOC, 1917 tokens]
│   │   ├── [] unit_registry.py [615 LOC, 2161 tokens]
│   │   ├── [] ontology_registry.py [529 LOC, 1870 tokens]
│   │   └── [] __init__.py [224 LOC, 868 tokens]
│   ├── units/ [469 LOC, 1907 tokens]
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
│   │   └── cities/ [469 LOC, 1907 tokens]
│   │       ├── lucknow/
│   │       ├── delhi/
│   │       ├── kanpur/
│   │       ├── city_summary_generator.py
│   │       ├── city_signal_mapper.py
│   │       ├── city_pattern_detector.py
│   │       └── [] city_initializer.py [469 LOC, 1907 tokens]
│   ├── data/
│   │   ├── memory/
│   │   │   ├── semantic/
│   │   │   ├── working/
│   │   │   ├── hypotheses/
│   │   │   └── patterns/
│   │   └── kb/
│   ├── modules/ [27481 LOC, 213740 tokens]
│   │   ├── codebase_atlas/ [15192 LOC, 69911 tokens]
│   │   │   ├── generators/ [311 LOC, 2105 tokens]
│   │   │   │   ├── [] detail_generator.py [114 LOC, 705 tokens]
│   │   │   │   ├── [] base_generator.py [182 LOC, 1318 tokens]
│   │   │   │   └── [] __init__.py [15 LOC, 82 tokens]
│   │   │   ├── utils/ [407 LOC, 2620 tokens]
│   │   │   │   ├── [] __init__.py [34 LOC, 123 tokens]
│   │   │   │   ├── [] formatting.py [187 LOC, 1510 tokens]
│   │   │   │   └── [] io_helpers.py [186 LOC, 987 tokens]
│   │   │   ├── analyzers/ [816 LOC, 5475 tokens]
│   │   │   │   ├── [] entry_point_detector.py [210 LOC, 1381 tokens]
│   │   │   │   ├── [] __init__.py [18 LOC, 90 tokens]
│   │   │   │   ├── [] dependency_analyzer.py [269 LOC, 1795 tokens]
│   │   │   │   └── [] impact_analyzer.py [319 LOC, 2209 tokens]
│   │   │   ├── graph/ [11212 LOC, 43701 tokens]
│   │   │   │   ├── backend/ [1655 LOC, 7568 tokens]
│   │   │   │   │   ├── renderers/ [455 LOC, 1973 tokens]
│   │   │   │   │   │   ├── [] interactive_renderer.py [150 LOC, 624 tokens]
│   │   │   │   │   │   ├── __init__.py
│   │   │   │   │   │   └── [] mermaid_renderer.py [305 LOC, 1349 tokens]
│   │   │   │   │   ├── [] graph_models.py [237 LOC, 1134 tokens]
│   │   │   │   │   ├── [] graph_builder.py [336 LOC, 1597 tokens]
│   │   │   │   │   ├── __init__.py
│   │   │   │   │   ├── [] serve.py [273 LOC, 1482 tokens]
│   │   │   │   │   └── [] graph_serializer.py [354 LOC, 1382 tokens]
│   │   │   │   ├── web/ [9557 LOC, 36133 tokens]
│   │   │   │   │   ├── utils/ [355 LOC, 1277 tokens]
│   │   │   │   │   │   └── [] geometry.js [355 LOC, 1277 tokens]
│   │   │   │   │   ├── viewport/ [658 LOC, 2213 tokens]
│   │   │   │   │   │   ├── [] navigation.js [305 LOC, 959 tokens]
│   │   │   │   │   │   └── [] viewport.js [353 LOC, 1254 tokens]
│   │   │   │   │   ├── layout/ [354 LOC, 1694 tokens]
│   │   │   │   │   │   └── [] layout.js [354 LOC, 1694 tokens]
│   │   │   │   │   ├── core/ [1642 LOC, 6053 tokens]
│   │   │   │   │   │   ├── [] events.js [227 LOC, 845 tokens]
│   │   │   │   │   │   ├── [] constants.js [219 LOC, 667 tokens]
│   │   │   │   │   │   ├── [] types.js [337 LOC, 1278 tokens]
│   │   │   │   │   │   ├── [] storage.js [366 LOC, 1202 tokens]
│   │   │   │   │   │   └── [] state.js [493 LOC, 2061 tokens]
│   │   │   │   │   ├── render/ [2785 LOC, 10529 tokens]
│   │   │   │   │   │   ├── [] edges.js [624 LOC, 2336 tokens]
│   │   │   │   │   │   ├── [] renderer.js [745 LOC, 3031 tokens]
│   │   │   │   │   │   ├── [] clusters.js [387 LOC, 1228 tokens]
│   │   │   │   │   │   ├── [] viewport_culler.js [244 LOC, 1252 tokens]
│   │   │   │   │   │   ├── [] nodes.js [516 LOC, 1690 tokens]
│   │   │   │   │   │   └── [] styles.js [269 LOC, 992 tokens]
│   │   │   │   │   ├── interaction/ [2152 LOC, 7147 tokens]
│   │   │   │   │   │   ├── [] events.js [520 LOC, 1729 tokens]
│   │   │   │   │   │   ├── [] interaction.js [854 LOC, 2973 tokens]
│   │   │   │   │   │   ├── [] drag.js [346 LOC, 1114 tokens]
│   │   │   │   │   │   └── [] selection.js [432 LOC, 1331 tokens]
│   │   │   │   │   ├── [] graph_viewer.js [575 LOC, 1929 tokens]
│   │   │   │   │   ├── [] graph_viewer.html [744 LOC, 3343 tokens]
│   │   │   │   │   ├── [] bootstrap.js [182 LOC, 635 tokens]
│   │   │   │   │   └── [] mermaid_view.html [110 LOC, 1313 tokens]
│   │   │   │   └── __init__.py
│   │   │   ├── parsers/ [1155 LOC, 7343 tokens]
│   │   │   │   ├── [] html_parser.py [110 LOC, 728 tokens]
│   │   │   │   ├── [] config_parser.py [125 LOC, 770 tokens]
│   │   │   │   ├── [] __init__.py [23 LOC, 124 tokens]
│   │   │   │   ├── [] javascript_parser.py [435 LOC, 2932 tokens]
│   │   │   │   ├── [] base_parser.py [94 LOC, 479 tokens]
│   │   │   │   └── [] python_parser.py [368 LOC, 2310 tokens]
│   │   │   ├── [] models.py [331 LOC, 2656 tokens]
│   │   │   ├── [] scanner.py [217 LOC, 1295 tokens]
│   │   │   ├── [] config.py [293 LOC, 1853 tokens]
│   │   │   ├── [] main.py [389 LOC, 2564 tokens]
│   │   │   └── [] __init__.py [61 LOC, 299 tokens]
│   │   ├── simulators/ [6877 LOC, 116735 tokens]
│   │   │   ├── popula_dyn/ [6514 LOC, 114356 tokens]
│   │   │   │   ├── static/ [474 LOC, 3447 tokens]
│   │   │   │   │   └── [] game.html [474 LOC, 3447 tokens]
│   │   │   │   ├── simulations_config/ [15 LOC, 52 tokens]
│   │   │   │   │   ├── city_growth.yaml
│   │   │   │   │   ├── startup_company.yaml
│   │   │   │   │   ├── [] agriculture.yaml [15 LOC, 52 tokens]
│   │   │   │   │   ├── ecosystem.yaml
│   │   │   │   │   └── ai_society.yaml
│   │   │   │   ├── core/ [3423 LOC, 15020 tokens]
│   │   │   │   │   ├── [] unit_agent.py [590 LOC, 2271 tokens]
│   │   │   │   │   ├── [] resource_engine.py [840 LOC, 3087 tokens]
│   │   │   │   │   ├── [] spatial_engine.py [178 LOC, 1055 tokens]
│   │   │   │   │   ├── [] agent_factory.py [216 LOC, 1252 tokens]
│   │   │   │   │   ├── [] event_bridge.py [305 LOC, 1190 tokens]
│   │   │   │   │   ├── [] world_engine.py [882 LOC, 3259 tokens]
│   │   │   │   │   └── [] simulation_model.py [412 LOC, 2906 tokens]
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
│   │   │   │   ├── [] simulation_plot.png [1000 LOC, 84371 tokens]
│   │   │   │   ├── [] constants.py [28 LOC, 291 tokens]
│   │   │   │   ├── [] simulation_game.py [204 LOC, 1466 tokens]
│   │   │   │   ├── [] main.py [16 LOC, 100 tokens]
│   │   │   │   ├── [] behavior_registry.py [133 LOC, 739 tokens]
│   │   │   │   └── [] SimDvptPhases.md [365 LOC, 4425 tokens]
│   │   │   └── [] simulation_connector.py [363 LOC, 2379 tokens]
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
│   │   └── digital_twins/ [3543 LOC, 13474 tokens]
│   │       ├── [] city_twin.py [903 LOC, 3486 tokens]
│   │       ├── [] digital_twin_manager.py [831 LOC, 2999 tokens]
│   │       ├── [] human_twin.py [814 LOC, 3092 tokens]
│   │       └── [] company_twin.py [995 LOC, 3897 tokens]
│   ├── tests/ [179 LOC, 1156 tokens]
│   │   ├── [] __init__.py [1 LOC, 9 tokens]
│   │   └── [] agent_test.py [178 LOC, 1147 tokens]
│   ├── llm/ [1076 LOC, 4000 tokens]
│   │   ├── extractors/
│   │   │   ├── signal_extractor.py
│   │   │   ├── pattern_extractor.py
│   │   │   └── hypothesis_extractor.py
│   │   ├── [] context_builder.py [548 LOC, 1977 tokens]
│   │   └── [] llm_orchestrator.py [528 LOC, 2023 tokens]
│   ├── [] system_instruction.md [99 LOC, 758 tokens]
│   ├── [] agent_tools.py [601 LOC, 4109 tokens]
│   ├── [] agent.py [297 LOC, 2124 tokens]
│   ├── [] Launcher.md [38 LOC, 529 tokens]
│   ├── [] __init__.py [1 LOC, 5 tokens]
│   └── [] tui_output.txt [22 LOC, 292 tokens]
├── system_devpt_reports/ [1582 LOC, 11663 tokens]
│   ├── codebase_atlas/ [708 LOC, 6618 tokens]
│   │   ├── [] current_status.md [287 LOC, 1975 tokens]
│   │   ├── [] devpt_roadmap.md [137 LOC, 2220 tokens]
│   │   └── [] README.md [284 LOC, 2423 tokens]
│   ├── [] kernel.md [162 LOC, 1110 tokens]
│   ├── [] debate_engine.md [323 LOC, 1739 tokens]
│   ├── [] simulation_engine.md [217 LOC, 1380 tokens]
│   └── [] orchestrator.md [172 LOC, 816 tokens]
├── atlas_output/ [557 LOC, 3794 tokens]
│   ├── children/ [33 LOC, 302 tokens]
│   │   ├── [] fabo.md [10 LOC, 56 tokens]
│   │   └── [] dummy.md [23 LOC, 246 tokens]
│   ├── [] interactive_dep.json [56 LOC, 341 tokens]
│   ├── [] mermaid_dep.txt [9 LOC, 179 tokens]
│   ├── [] code_atlas.md [10 LOC, 56 tokens]
│   ├── [] graphdata_call.json [168 LOC, 1073 tokens]
│   ├── [] node_pos_dep.json [10 LOC, 48 tokens]
│   ├── [] node_pos_call.json [22 LOC, 120 tokens]
│   ├── [] interactive_call.json [185 LOC, 1103 tokens]
│   ├── [] mermaid_call.txt [20 LOC, 280 tokens]
│   └── [] graphdata_dep.json [44 LOC, 292 tokens]
├── [] GPT_5-5_Chat.md [4962 LOC, 18724 tokens]
├── [] Issues_n_ideas.md [123 LOC, 1336 tokens]
├── [] agent_harness.md [34 LOC, 354 tokens]
├── [] code_atlas.md [318 LOC, 5701 tokens]
├── [] Devpt_phases.md [330 LOC, 2917 tokens]
├── code_dump.txt
├── [] .gitignore [7 LOC, 23 tokens]
├── [] README.md [953 LOC, 4763 tokens]
└── [] project_tools.md [24 LOC, 910 tokens]
### End Tree