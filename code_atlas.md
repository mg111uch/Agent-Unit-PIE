## Codebase size
Total files processed: 83
Total lines of code: 11109
Total tokens: 103952
## End Codebase size

## Directory Structure 
- **Project path:** `python/Agentic_Unit_PIE`
### FILE_MAP Tree
├── codebase/
│   ├── skills/
│   │   ├── [] interaction_api.md [1161 LOC, 8644 tokens]
│   │   ├── [] write_navigation.md [363 LOC, 1710 tokens]
│   │   └── [] gemini_api_doc.md [29 LOC, 227 tokens]
│   ├── rag_pipeline/
│   │   ├── sql_rag/
│   │   │   ├── [] rag.db [0 LOC, 0 tokens]
│   │   │   ├── [] sqlrag.py [343 LOC, 3033 tokens]
│   │   │   ├── [] retrieve.py [35 LOC, 326 tokens]
│   │   │   └── [] context.txt [4 LOC, 34 tokens]
│   │   ├── graph_rag/
│   │   │   ├── static/
│   │   │   │   └── [] index.html [485 LOC, 3035 tokens]
│   │   │   ├── [] graph_db.py [371 LOC, 3032 tokens]
│   │   │   ├── [] Graph_Features_README.md [126 LOC, 647 tokens]
│   │   │   ├── [] code_graph.db [0 LOC, 0 tokens]
│   │   │   └── [] graph_visualizer.py [207 LOC, 1422 tokens]
│   │   ├── vector_rag/
│   │   │   ├── [] neo4j-auradb-auth.env [3 LOC, 71 tokens]
│   │   │   ├── [] t6_llm_integration.py [49 LOC, 427 tokens]
│   │   │   ├── [] ChunkEmbedChroma.py [277 LOC, 2474 tokens]
│   │   │   ├── [] t4_neo4j.py [311 LOC, 2971 tokens]
│   │   │   └── [] t5_hybrid_retrieval.py [108 LOC, 1093 tokens]
│   │   ├── dummy/
│   │   │   ├── fabo/
│   │   │   │   └── [] fabonacci.py [18 LOC, 176 tokens]
│   │   │   └── [] calculator.py [59 LOC, 451 tokens]
│   │   ├── [] metaFileStr.md [25 LOC, 650 tokens]
│   │   └── [] backupPlans.md [135 LOC, 2142 tokens]
│   ├── sloperator/
│   │   ├── [] post_on_X.py [121 LOC, 776 tokens]
│   │   ├── [] navigation.py [100 LOC, 677 tokens]
│   │   ├── [] post_composer.py [239 LOC, 1591 tokens]
│   │   └── [] conductor.py [282 LOC, 2262 tokens]
│   ├── agent_tools/
│   │   ├── [] record_screen.py [109 LOC, 984 tokens]
│   │   ├── [] screenshot_region.py [34 LOC, 352 tokens]
│   │   ├── [] record_browser.py [66 LOC, 506 tokens]
│   │   ├── [] ask_gemini.py [216 LOC, 1530 tokens]
│   │   ├── [] run_process.py [210 LOC, 1407 tokens]
│   │   ├── [] Llama_test.py [24 LOC, 156 tokens]
│   │   ├── [] run_and_record.py [170 LOC, 1177 tokens]
│   │   ├── [] inference_api_hf.py [25 LOC, 176 tokens]
│   │   ├── [] mini_code_map.py [100 LOC, 857 tokens]
│   │   ├── [] swapFiles.py [53 LOC, 434 tokens]
│   │   ├── [] gemini_api_state.json [1 LOC, 14 tokens]
│   │   ├── [] play_sound.py [13 LOC, 114 tokens]
│   │   └── [] screenRecord.py [144 LOC, 971 tokens]
│   ├── ralph_loop/
│   │   ├── [] readWriteMD.py [50 LOC, 429 tokens]
│   │   ├── [] ralph_agent.py [62 LOC, 663 tokens]
│   │   ├── [] phoenix_helper.py [42 LOC, 434 tokens]
│   │   └── [] orchestrator.md [110 LOC, 1665 tokens]
│   ├── argu_god/
│   │   ├── engine/
│   │   │   ├── [] loop.py [177 LOC, 1123 tokens]
│   │   │   ├── [] retriever.py [46 LOC, 252 tokens]
│   │   │   ├── [] analyzer.py [19 LOC, 139 tokens]
│   │   │   ├── [] question_builder.py [25 LOC, 142 tokens]
│   │   │   ├── [] storage.py [53 LOC, 333 tokens]
│   │   │   ├── [] cli.py [12 LOC, 78 tokens]
│   │   │   └── [] vector_store.py [43 LOC, 227 tokens]
│   │   ├── static/
│   │   │   ├── [] graph.js [232 LOC, 1842 tokens]
│   │   │   └── [] index.html [37 LOC, 407 tokens]
│   │   ├── topics/
│   │   │   └── theism_atheism/
│   │   │       ├── wiki/
│   │   │       │   └── [] index.md [7 LOC, 255 tokens]
│   │   │       ├── raw/
│   │   │       ├── [] schema.md [17 LOC, 138 tokens]
│   │   │       ├── [] graph.json [348 LOC, 2583 tokens]
│   │   │       └── [] metadata.json [0 LOC, 0 tokens]
│   │   ├── mindmaps/
│   │   │   ├── global_aggregated/
│   │   │   └── local_user/
│   │   │       ├── [] belief_state.json [10 LOC, 52 tokens]
│   │   │       ├── [] human_mind_map.md [6 LOC, 41 tokens]
│   │   │       ├── [] interaction_log.json [35 LOC, 277 tokens]
│   │   │       └── [] mindmap.json [13 LOC, 89 tokens]
│   │   ├── [] main.py [57 LOC, 467 tokens]
│   │   ├── [] AGENTS.md [20 LOC, 234 tokens]
│   │   ├── [] global_schema.md [33 LOC, 267 tokens]
│   │   └── [] llm_compiler.py [100 LOC, 805 tokens]
│   ├── popula_dyn/
│   │   ├── static/
│   │   │   └── [] game.html [486 LOC, 3666 tokens]
│   │   ├── [] simulation_plot.png [0 LOC, 0 tokens]
│   │   ├── [] agents.py [331 LOC, 3495 tokens]
│   │   ├── [] constants.py [42 LOC, 407 tokens]
│   │   ├── [] simulation_game.py [217 LOC, 1870 tokens]
│   │   ├── [] Insight.md [33 LOC, 414 tokens]
│   │   ├── [] base_classes.py [173 LOC, 1585 tokens]
│   │   ├── [] main.py [29 LOC, 316 tokens]
│   │   ├── [] model.py [202 LOC, 2444 tokens]
│   │   ├── [] simulation.py [91 LOC, 1134 tokens]
│   │   ├── [X] DevptPhases.md [152 LOC, 2959 tokens]
│   │   ├── [X] README.md [214 LOC, 1484 tokens]
│   │   └── [] feature_list.md [48 LOC, 1234 tokens]
│   ├── utils_files/
│   │   ├── [] recorded_video.mp4 [0 LOC, 0 tokens]
│   │   ├── [] drift_racer.avi [0 LOC, 0 tokens]
│   │   ├── [] gemini_answer.md [351 LOC, 2839 tokens]
│   │   ├── [] censor-beep-1sec-8112.mp3 [0 LOC, 0 tokens]
│   │   ├── [] tools_list.md [109 LOC, 817 tokens]
│   │   ├── [] Modelfile [1 LOC, 29 tokens]
│   │   ├── [] google_functiongemma-270m-it-Q6_K_L.gguf [0 LOC, 0 tokens]
│   │   ├── [] gemini_question.md [50 LOC, 450 tokens]
│   │   └── [] reddit-clone.avi [0 LOC, 0 tokens]
│   ├── atlas_output/
│   │   ├── codebase_atlas/
│   │   │   ├── generators/
│   │   │   │   ├── [] detail_generator.py [302 LOC, 1774 tokens]
│   │   │   │   ├── [] base_generator.py [361 LOC, 2681 tokens]
│   │   │   │   └── [] __init__.py [15 LOC, 82 tokens]
│   │   │   ├── utils/
│   │   │   │   ├── [] __init__.py [35 LOC, 139 tokens]
│   │   │   │   ├── [] formatting.py [323 LOC, 2589 tokens]
│   │   │   │   └── [] io_helpers.py [180 LOC, 967 tokens]
│   │   │   ├── analyzers/
│   │   │   │   ├── [] entry_point_detector.py [210 LOC, 1381 tokens]
│   │   │   │   ├── [] __init__.py [18 LOC, 90 tokens]
│   │   │   │   ├── [] dependency_analyzer.py [269 LOC, 1795 tokens]
│   │   │   │   └── [] impact_analyzer.py [319 LOC, 2209 tokens]
│   │   │   ├── parsers/
│   │   │   │   ├── [] html_parser.py [110 LOC, 728 tokens]
│   │   │   │   ├── [] config_parser.py [125 LOC, 770 tokens]
│   │   │   │   ├── [] __init__.py [23 LOC, 124 tokens]
│   │   │   │   ├── [] javascript_parser.py [435 LOC, 2932 tokens]
│   │   │   │   ├── [] base_parser.py [94 LOC, 479 tokens]
│   │   │   │   └── [] python_parser.py [368 LOC, 2310 tokens]
│   │   │   ├── [] models.py [331 LOC, 2656 tokens]
│   │   │   ├── [] scanner.py [217 LOC, 1295 tokens]
│   │   │   ├── [] config.py [298 LOC, 1909 tokens]
│   │   │   ├── [] main.py [262 LOC, 1643 tokens]
│   │   │   ├── [] __init__.py [61 LOC, 299 tokens]
│   │   │   └── [] README.md [356 LOC, 2577 tokens]
│   │   └── tools/
│   │       ├── [] make_directree.py [184 LOC, 1624 tokens]
│   │       ├── [] token_count.py [152 LOC, 1165 tokens]
│   │       ├── [] run_cmds.py [271 LOC, 1875 tokens]
│   │       ├── [] add_markers.py [148 LOC, 1061 tokens]
│   │       ├── [] gen_tools_file.py [99 LOC, 1080 tokens]
│   │       ├── [] copyContent.py [152 LOC, 1423 tokens]
│   │       ├── [] path_file_exists.py [42 LOC, 245 tokens]
│   │       ├── [] mini_codebase_atlas.py [606 LOC, 5425 tokens]
│   │       ├── [] init_harness.py [290 LOC, 2378 tokens]
│   │       ├── [] codebase_size.py [119 LOC, 1316 tokens]
│   │       └── [] codebase_dump.py [47 LOC, 479 tokens]
│   ├── [] system_instruction.md [99 LOC, 758 tokens]
│   ├── [] agent.py [332 LOC, 2356 tokens]
│   ├── [] Launcher.md [38 LOC, 529 tokens]
│   ├── [] __init__.py [1 LOC, 5 tokens]
│   └── [] tui_output.txt [10 LOC, 142 tokens]
├── [] Issues_n_ideas.md [952 LOC, 3434 tokens]
├── [] agent_harness.md [30 LOC, 287 tokens]
├── [] code_atlas.md [158 LOC, 2598 tokens]
├── [] code_dump.txt [1470 LOC, 11056 tokens]
├── [] .gitignore [6 LOC, 19 tokens]
├── [] README.md [462 LOC, 1795 tokens]
├── [] project_tools.md [22 LOC, 796 tokens]
└── [] README_old.md [0 LOC, 0 tokens]
### End Tree