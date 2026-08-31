# Phase Plan — Implemented (Git-backed, Per-Sim Strict Isolation)

## Summary

All phases completed post `FixesIssues.md` V1 (symbolic gate) + V2 (lineage) + `FeatureIdeas.md` (use Git). Core principle: **Git = syntactic lineage (`sim@commit`), Kernel = semantic validity (`ACTIVE→HISTORICAL` per-sim concept-level)**. Strict isolation: findings, versions, topics, retrieval per simulator. **2026-08-30 Review Fix:** Phase 5 consolidated materialized view + declarative ontology. **Phase 6:** Unified `research_development` loop + `workflow_engine`. **Phase 7:** `DevelopmentState` (<2KB) + 8 `develop.*` tools. **Phase 8 (2026-08-30):** Graduated `L0-L6` gate + 5-test eval harness. No new version infra.

## Phase 0 — Git-Backed Lineage + Per-Sim Registry (Done)

**Goal:** Replace `V1_hash` with scoped Git, isolate per simulator.

- **`kernel/git_version.py:1` (99 LOC, new)** RO helpers `is_git_repo()`, `current_commit()`, `parent_commit()`, `current_branch()`, `diff_files(from..to, paths)`, `diff_sim_files(sim)`, `sim_commit(sim)` (last commit touching `simulators/<sim>`), `current_version_id(sim)`. Fallback `compute_code_hash` when not in git repo.
- **`kernel/simulator_registry.py:1` (80 LOC, new)** `discover_simulators()` scans `simulators/*` (`popula_dyn→popu_sim`, `eco_sim→sim_eco_sim` via `manifest.yaml`), `sim_topic()`, `sim_patterns()`.
- **`kernel/schemas/simulation_schema.py:1,52`** `SimulationVersion` now `version_id: sim@commit`, `simulator`, `git_branch/msg`; `SimulationRun/Finding/Validity` add `simulator`.
- **`kernel/simulation_version.py:1`** Refactored to per-sim: `get_or_create_initial_version(sim)`, `sync_from_git(sim)` (scoped `sim_commit` + `diff_sim_files` → `affected_concepts` via `MODULE_CONCEPTS`), `is_compatible(find, query, sim)` walks `sim@commit` lineage, `V*` legacy compat.
- **`kernel/persistence/db.py:144,209,800`** Tables `simulation_versions(simulator, git_branch/msg)` + `simulation_runs(simulator)` + indexes `idx_sim_versions_sim`, `load_* (simulator)` param, `save_* (simulator)`.

Verify: `popula_dyn@1a7d783` (last `popula_dyn` commit) vs `eco_sim@V1_0c8137` (no history → hash fallback), `virtual_silicon` commit does not bump `popula_dyn`.

## Phase 1 — Sharded Runs + Episodic Binding (Done, per user: shard per-sim)

- **`modules/simulators/simulation_connector.py:44,213,234`** `SimulatorConnector(simulator)` shards FS `base_path=units/simulations/{sim}/{run}` (+ `_migrate_legacy_shard()` moves `run_basic→popula_dyn/` once, `_resolve_run_path()` fallback), `_persist_run_lineage()` on `_store_run()`: `kernel_db.save_simulation_run(sim@commit, simulator)` + `episodic_memory.create_episode(simrun_{sim}_{run})` + `data/memory/episodic/{sim}_{run}.json` immutable. `build_observation()` injects `simulator, version_id=sim@commit`.
- **Isolation:** `list_runs()`, `get_params/signals`, `compare_runs` per-sim; `register_to_kernel()` writes per-sim topic.

Verify: `popula_dyn` 3 runs under `popula_dyn/`, `eco_sim` separate, `simulation_runs` per-sim, `episodic` per-sim JSON.

## Phase 2 — Validity Scope (Done, concept-level per-sim)

- **`kernel/validity.py:1` (124 LOC, new)** `mark_stale_findings(sim, new_version)` scoped via `sim_topic`, loads `new_version.affected_concepts`, derives `find_concepts` from `observation.scenario/signals` + premise keywords via `MODULE_CONCEPTS`, `affected_by()` → patches `metadata.validity={status:HISTORICAL, invalidated_by, affected_concepts}` + `observation.validity`, persists via `memory_engine` + `kernel_db` + `write_export`. `active_findings(sim)` helper.
- Hooked in `simulation_version.py:72,92,106` `sync_from_git`/`bump_version` auto-marks when `affected_concepts !=[]`.
- Test: `reproduction` change → 3/3 `popula_dyn` findings `HISTORICAL`, `terrain` → 0/3, `eco_sim` unaffected.

## Phase 3 — Version-Aware Retrieval & Gate (Done)

- **`kernel/retrieval/retrieval_engine.py:75`** `_valid_for_retrieval()` checks `simulator` match, `HISTORICAL` skip, `is_compatible(find_ver, query_ver, sim)` vs `get_current_version(sim)`. `search*` now `simulator, include_historical` (default ACTIVE). `build_context()` per-sim.
- **`kernel/retrieval/semantic_retriever.py:139`** Same filter in `_valid_for_retrieval`, `search_by_concept/embedding`, `multi_concept`, `build_semantic_context`.
- **`kernel/hypothesis/contradiction_gate.py:157,266`** `_compatible_for_contradiction()` skips cross-sim / `HISTORICAL` / incompatible versions; `check_observation_contradiction` and `check_topic_contradiction` version-aware; cross-sim `IMPROVED vs COLLAPSED` never contradicts.
- Verify: `search(population, sim=popula_dyn)` 4→1 after HISTORICAL (engine only), `include_historical=True` 4, `eco_sim` 0 popu findings; contradiction vs `HISTORICAL` → False.

## Phase 4 — Per-Sim Compression (Done)

- **`kernel/compression_engine.py:147`** `compress_observations()` per `discover_simulators()`, groups `ACTIVE` findings by `(outcome, horizon//10)` per `sim_topic`, creates/updates `consolidated_{sim}_{outcome}_{bucket}` (`consolidated_observation`, `consolidated_from: [src_ids]`, `avg_delta`), keeps `episodic` raw immutable. Idempotent.

Verify: `popula_dyn` 3 distinct outcomes → 0 groups, after adding 2 `COLLAPSED` dups (5 ACTIVE) → `compressed 3 → 1` consolidated `popula_dyn consolidated COLLAPSED (3 runs)`, second run 0, `eco` 0.

## Phase 5 — Review Recommendations Implemented (2026-08-30, No New Version Infra)

**Problem from Review:** Phase 4 consolidated `ACTIVE findings → group by outcome → consolidated observation` created a second accumulation layer. `Run A+B+C → X`; after `V2` invalidates `A,B`, `X` stayed `ACTIVE` (stale semantic knowledge). Review also flagged `MODULE_CONCEPTS` hardcoded `changed file → concepts` should be declared by the simulator itself.

**Decision:** Keep **Git = syntactic lineage** / **Kernel = semantic validity** unchanged (review: "not add another version-tracking mechanism"). Fix is *materialized-view* + *ontology* within existing infra.

### 5.1 — Consolidated Materialized View (Preferred #2: recompute)

- **`kernel/compression_engine.py:147` (Phase 4 extended)** `compress_observations()` now materialized-view: excludes `consolidated_observation` from grouping, writes full lineage `metadata={simulator, source_findings[], source_versions[] (union of `observation.version_id`/`validity.valid_for_version`), affected_concepts[] (union via `_find_concepts_for_node`), validity={valid_for_version: cur_ver, status: ACTIVE, simulator}, derived_at}` + legacy `consolidated_from`. Concepts include up to 3 `affected` in `concepts` tag.
- **`kernel/compression_engine.py:235` (new)** `recompute_consolidated(simulator, invalidated_ids, new_version_id)` per `sim_topic(sim)`: for each `consolidated_observation` with `metadata.simulator==sim`, if no source overlaps `invalidated_ids` and no source is `HISTORICAL` → skip; else filter `remaining = sources where node exists AND status==ACTIVE`; if `len(remaining)<2` → patch `validity→HISTORICAL{invalidated_by: cur_ver}` (kept for audit, excluded by retrieval); else recompute `avg_delta`, `source_findings/source_versions`, `affected_concepts`, `title/content`, `validity→ACTIVE@cur_ver`, `derived_at=utc_now()`, `observation{source_count, avg_delta, version_id: cur_ver}`; persists via `memory_engine`+`kernel_db` + `write_export`. Idempotent; `<500 LOC` total (482).
- **`kernel/validity.py:1` (extended)** `_find_concepts_for_node()` now ontology-aware (`_load_ontology_concepts()`) and returns `metadata.affected_concepts` directly for consolidated nodes. `mark_stale_findings()` skips `consolidated_observation`/`observation.consolidated` in raw invalidation loop; after marking `HISTORICAL` raw findings calls `CompressionEngine().recompute_consolidated(sim, invalidated, new_version_id)`; if zero invalidated still opportunistic recompute (covers drift). Keeps strict per-sim isolation.
- **Semantics:** `V1: A+B+C→X` → `V2 invalidates A,B` → `remaining C (+ any other ACTIVE in bucket) → X'` recomputed (`avg_delta` updated, `source_findings` pruned, `validity` rebased to `V2`). `V2 invalidates all but 0-1` → `X→HISTORICAL` (retrieval `include_historical=False` hides it; `True` still audit).

Verify: `4 COLLAPSED (-30..-33) → consolidated avg -31.5`; invalidate `2 → recomputed 2 avg -32.5 ACTIVE`; `3 COLLAPSED → 2 dups (3 runs) → invalidate 2 → 1 left → consolidated HISTORICAL`; `IMPROVED` bucket untouched.

### 5.2 — Declarative Ontology (Simulator Declares Concepts)

- **`codebase/modules/simulators/popula_dyn/ontology.yaml:1` (new, 37 LOC)** Per-module `modules: {reproduction: {concepts:[reproduction,population_growth,fertility,mortality], outputs:[births,population]}, survival, consume, ...}`. `MODULE_CONCEPTS` in `schemas/simulation_schema.py:115` kept as fallback.
- **`kernel/schemas/simulation_schema.py:130`** `_load_ontology_concepts()` merges all `simulators/*/ontology.yaml` (`modules` dict or list shape) over `MODULE_CONCEPTS`. `concepts_for_changed_files(files, _ontology?)` and new `module_concepts_for(module)` use merged registry. Example: `reproduction.py → [fertility,mortality,population_growth,reproduction]` (adds `fertility` from yaml), `regrow.py → [terrain,resource_scarcity]`. No migration needed; missing yaml → fallback.

### 5.3 — Semantic Evolution Loop (No Infra Change)

Review's desired loop now realizable with existing nodes: `Git diff (diff_sim_files)→ concepts_for_changed_files (ontology-aware) → sync_from_git saves affected_concepts → mark_stale_findings (concept filter) → recompute_consolidated (materialized view) → retrieval/contra-gate already version-aware`. Workflows already have `version_sync` + `compress`; loop is `git commit → sync_from_git → invalidate → rebuild → run next experiment`.

## Workflows Updated

- **`data/workflows/kernel_ops.json/md`** added `version_sync` (per-sim `sync_from_git`) + `compress` nodes, `orient`/`topics` per-sim docs.
- **`data/workflows/popu_sim_dev.json/md`** added `version_sync`, `lineage` (sharded + episodic), `validity`, `compress` nodes; `implement`/`register` per-sim sharded.

## Kernel Docs Updated

- **`system_devpt_reports/kernel/README.md`** +7 rows in Feature Overview table (Phase 5 not yet doc-synced; reflects Phase 0-4).
- **`system_devpt_reports/kernel/usage.md`** bumped `_Last verified 2026-08-29 9/9`, architecture per-sim, lineage, sharded FS, validity, retrieval, compression sections (needs Phase 5 addendum).

## Verification (re-verified 2026-08-30)

`smoke_kernel.py 9/9` still passes (clear + topics + contradiction + signals + prune). Added: `concepts_for_changed_files(reproduction.py)→[fertility,mortality,population_growth,reproduction]` ontology override works; `compress 4→1` then `invalidate 2 → recomputed ACTIVE` and `invalidate 2 of 3 → HISTORICAL` as above; no cross-sim bump. Files remain `<500 LOC` (`compression_engine 482`, `validity 149`, `simulation_schema 183`).

## Phase 6 — Unified Development Operating Loop (2026-08-30, FixesIssues Phase 5 Review)

**Goal:** Let LLM think *inside* workflow, not control it. Merge `kernel_ops.json` + `popu_sim_dev.json` as subgraphs of one top-level `research_development` loop; every node is machine-readable contract `{id,goal,inputs,preconditions,actions,outputs,success,failure,next,mdRef,subgraph}` validated deterministically. Prefer new `develop.*` tools (chosen).

- **`codebase/development/contracts.py:1` (85 LOC, new)** `validate_node()` checks `id,goal,outputs,success,next` + list types; `validate_workflow()` checks duplicate ids, edge targets exist, `next ⊆ edges`, legacy `[id,label,shape,...]` array compat. `_to_dict` synthesizes minimal contracts for legacy workflows.
- **`codebase/development/workflow_engine.py:1` (98 LOC, new)** Deterministic executor: `UNIFIED_NODES` = `start→orient→version_sync→hypothesis→decide_branch→{experiment,modify_code}→update_knowledge→evaluate→validate→loop→stop` (mirrors `FixesIssues.md:MAIN DEVELOPMENT LOOP`). `load_json(path)` validates then adopts `nodes/edges`; `allowed()` = `edges[current]`; `advance(target, produced, success)` enforces `target ∈ allowed`, `success ∈ node.success`, `outputs` present, skips strict `precondition` check (Phase 8 `validation_gate` will tighten); stores `outputs`, advances `history`. Persistent `workflow_engine` singleton. Prevents skipping: `start→experiment` blocked (`allowed: [orient]`), `orient→hypothesis` blocked (`allowed: [version_sync]`).
- **`data/workflows/research_development.json:1` (new)** Meta `{id: research_development, subgraphs: [kernel_ops.json, popu_sim_dev.json]}` + 12 contracted nodes (x/y/color/shape/mdRef) + 14 edges with `branch==experiment|model_or_kernel` labels. Node goals/actions map to high-level `develop.*` primitives (`kernel_retrieve/sim.inspect/git_state/hypothesis_form/branch_decide/simulation.run/code_edit/contradiction_check/pattern_detect/compress/eval_gap/run_tests`).
- **`data/workflows/research_development.md:1` (new)** Companion guide per node (python snippet for `workflow_engine.status/advance`).

**Alignment with original docs:** Preserves `project_docs/README.md` universal PIE hierarchy (Kernel→real-world modules + simulation modules + development intelligence) vs sim-centric drift; implements `WORLD/MODEL/DEVELOPMENT` cognition via `hypothesis` node branching (`experiment` vs `modify_code`); graduated autonomy deferred to Phase 8.

**Next:** Phase 7 `DevelopmentState` + `develop.orient/experiment/...` high-level tools; Phase 8 `validation_gate L0-L6` + agent evaluation harness (`workflow conformance/recovery/adversarial lineage/workflow evolution` tests per `FixesIssues.md:6`).

Verify: `validate_workflow(research_development.json)=True`; `start→orient→version_sync(context)→hypothesis(version_id)→decide_branch(hypothesis_id)→experiment(branch)` succeeds; missing `outputs` raises; illegal `start→experiment` rejected. No extra version infra.

## Phase 7 — DevelopmentState + develop.* Tools (2026-08-30)

**Goal:** Give LLM `CURRENT STATE + RELEVANT KNOWLEDGE + ALLOWED ACTIONS + SUCCESS CRITERIA` (<2KB) instead of two procedural docs; hide shell. Introduces `DevelopmentState` generator + 8 `develop.*` high-level primitives (compose existing deterministic ops, drive `workflow_engine`).

- **`codebase/development/development_state.py:1` (92 LOC, new)** `generate_state(simulator)` derives: `sim/git/sim_commit` via `git_version`, `sim_version+aff_concepts` via `simulation_version.get_current_version`, `wf_ver` hash of `research_development.json`, `wf_node/allowed` via `workflow_engine`, `hyps` (id/title/type/cat/status/conf, 4 max), `gaps` (known_gap, 3 max), `runs` (5 recent `simulation_runs` ordered `created_at DESC`), `ts`; trims to <1900 bytes (drops hyps/gaps/runs detail, keeps `_bytes`). `state_text()` renders compact lines `CURRENT STATE sim=… git=… ALLOWED: … VERSION … HYPS: …`. Used as preface for every agent turn.
- **`codebase/development/develop_tools.py:1` (168 LOC, new)** 8 tools registered as `CAT_DEVELOP` via `agent_core/tools/__init__.py::_register_develop_tools` (now 67 tools total):
  - `develop_state{simulator}` → `{state,text}` (budget checked).
  - `develop_orient{query,simulator,limit}` → per-sim `retrieval_engine.search(include_historical=False)` + `workflow_engine: start/loop→orient→version_sync(context)`, returns `{context,state,allowed}`.
  - `develop_experiment{run_id,params,simulator,baseline_run_id}` → `SimulationConnector(sim).run_and_extract` + `generate_structured_premise` + `register_to_kernel` (+ episodic/lineage), advances `decide_branch→experiment→update_knowledge` when allowed.
  - `develop_analyze{run_id,simulator}` → signals + `CompressionEngine.compress_observations()` + advance `update_knowledge→evaluate`.
  - `develop_modify_simulator|develop_modify_kernel{path,old_string,new_string,replace_all}` → gated single-file edit (`old_string` must match once), advances `decide_branch→modify_code`.
  - `develop_validate{simulator}` → `sync_from_git` + `get_current_version` + `validate→loop` advance.
  - `develop_commit{message,add_all}` → `git_commit` + `loop→orient` advance.
  All hide `conda run … topic_ops.py / simulation_connector` shell; LLM decides WHAT (hypothesis/params), engine decides HOW (transition, required outputs).

**Alignment:** Implements `FixesIssues.md:4` DevelopmentState (was missing), `FixesIssues.md:5` high-level `develop.*` vs 15 low-level ops (10.8k token reduction), and `project_docs/README.md` self-compression (`<2KB` working memory). Keeps `WORLD→MODEL→DEVELOPMENT` categories via `hyps.cat`.

**Next:** Phase 8 `validation_gate L0-L6` + evaluation harness (`research_loop/self-improvement/adversarial lineage/workflow evolution` per `FixesIssues.md:6`).

Verify: `generate_state('popula_dyn')._bytes=232 (<1900)`; `develop_orient` moves `start→orient→version_sync` and `allowed=['hypothesis']`; `develop_modify_simulator` without `old_string` returns Error; `registry.tool_names` includes 8 `develop_*`.

## Phase 8 — Graduated Autonomy + Evaluation Harness (2026-08-30)

**Goal:** Enforce `World→Model→Development→PIE` hierarchy with gated self-modification and agent-level evolutionary tests (FixesIssues #7-#9). No new persistence; one SQLite path; sim allowed autonomously, kernel/workflow human-gated.

- **`codebase/development/validation_gate.py:1` (92 LOC, new)** Defines `LEVELS 0 suggest /1 edit+test /2 edit+test+commit /3 sim_modify /4 workflow_modify /5 kernel_propose /6 kernel_modify` with `DEFAULT_CEILING=3`. `required_level(path)` maps `data/workflows→4`, `codebase/kernel→6`, `codebase/modules/simulators→3`. `gate(level,path,human_approved)` checks required vs requested, runs `needs=[contracts,sim_smoke,lineage,retrieval,workflow_conformance,human_approval]` via lightweight helpers (`validate_workflow`, `get_current_version`, `adversarial_mini`, `retrieval.search`, `conformance_mini`), returns `{allowed,required_level,needs,results,message}`. `can_edit()` convenience. Blocks: `L3 kernel` → GATE, `L6 kernel without approval` → GATE, `L1 workflow` → GATE; allows `L3 sim`, `L4 workflow`, `L6 kernel + human_approved`.

- **`codebase/development/eval_harness.py:1` (85 LOC, new)** Agent-behavior suite `run_all()→{total,passed,results,benchmark}`:
  - `workflow_conformance` (FixesIssues 6A): legal `orient→version_sync→hypothesis→decide_branch→experiment→update_knowledge` + illegal `start→experiment` blocked.
  - `recovery` (6B): inject `missing run_id`, `missing old_string`, contradiction, invalid params → error strings not crash.
  - `adversarial_lineage` (6E): 5 invariants `V1 stale / partial / unrelated→no invalidation / opposite V1/V2 not contradiction / same-version opposite contradiction` via `concepts_for_changed_files` + `affected_by` + `is_compatible`.
  - `workflow_evolution` (6F): base workflow validates, added `tmp_doc` node still validates (detect inefficiency via token cost).
  - `research_loop` (6C): `generate_state` has `sim/git/wf_node/allowed/hyps/runs` and `_bytes<2000`.
  Benchmark placeholder tracks `tool_surface_tokens 10.8k→2KB`, `iterations_to_solution` (run `develop_orient→experiment→analyze` from clean context repeatedly).

- **`codebase/development/develop_tools.py` (extended, +38 LOC)** `develop_modify_simulator` now L3 gated (`_gated_write` → `gate(L3)`), `develop_modify_kernel` L6 gate (`human_approved==true` required else suggest), new `develop_modify_workflow` L4 gated (`data/workflows/*.json` only). All advance `decide_branch→modify_code` on success. Registry now 9 `develop_*` (`develop_state/orient/experiment/analyze/modify_simulator/modify_kernel/modify_workflow/validate/commit`).

**Alignment:** Implements graduated autonomy (`L0-L6`, sim `L3` autonomous, kernel `L5-6` gated) and `FixesIssues #8` `development/` layout (`workflow_engine/development_state/validation_gate/eval_harness`). Prepares for universal PIE (`World/Model/Development` hypotheses remain simulator-lab, not ontology).

Verify: `gate(3,sim)=ALLOW`, `gate(3,kernel)=GATE`, `gate(6,kernel+human_approved)=ALLOW` (5 checks pass); `run_all()=5/5 passed`; `develop_modify_kernel without approval → Error human_approved required`, `develop_modify_workflow → edited gate pass`; workflow bypass file reverted.

----------
