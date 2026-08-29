# Phase Plan — Implemented (Git-backed, Per-Sim Strict Isolation)

## Summary

All phases completed post `FixesIssues.md` V1 (symbolic gate) + V2 (lineage) + `FeatureIdeas.md` (use Git). Core principle: **Git = syntactic lineage (`sim@commit`), Kernel = semantic validity (`ACTIVE→HISTORICAL` per-sim concept-level)**. Strict isolation: findings, versions, topics, retrieval per simulator.

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

## Workflows Updated

- **`data/workflows/kernel_ops.json/md`** added `version_sync` (per-sim `sync_from_git`) + `compress` nodes, `orient`/`topics` per-sim docs.
- **`data/workflows/popu_sim_dev.json/md`** added `version_sync`, `lineage` (sharded + episodic), `validity`, `compress` nodes; `implement`/`register` per-sim sharded.

## Kernel Docs Updated

- **`system_devpt_reports/kernel/README.md`** +7 rows in Feature Overview table.
- **`system_devpt_reports/kernel/usage.md`** bumped `_Last verified 2026-08-29 9/9`, architecture per-sim, lineage, sharded FS, validity, retrieval, compression sections.

## Verification

`smoke_kernel.py 9/9`, per-sim `popula_dyn@1a7d783` vs `eco_sim@V1_0c8137` lineage, `virtual_silicon` change no `popula_dyn` bump, strict topic isolation `popu_sim / sim_eco_sim`.

----------

# Phase Plan - Review

This implementation is **much closer to the architecture I would recommend**. Looking at the completed plan, I would **not add another version-tracking mechanism**. Git is now correctly serving as syntactic lineage, while the kernel handles semantic validity.

However, I see one important next-level issue.

### Your current model

You now effectively have:

```text
Git commit
    ↓
Simulation version
    ↓
Simulation runs
    ↓
Findings
    ↓
Validity
    ↓
Semantic retrieval
    ↓
Compression
```

That solves the **accumulation problem** quite well.

Your concept-level invalidation is especially good:

> reproduction change → 3/3 findings historical
> terrain change → 0/3 findings historical

That means you aren't making the overly aggressive mistake of invalidating an entire simulator whenever one module changes.

### The next problem: semantic knowledge can become stale

Your Phase 4 compression currently does:

```text
ACTIVE findings
   ↓
group by outcome + horizon
   ↓
consolidated observation
```

This is useful, but it potentially creates a second form of accumulation:

```text
Run A ─┐
Run B ─┼→ Consolidated Finding X
Run C ─┘

V2 changes reproduction

Consolidated Finding X
        ↓
      ??? 
```

You need to ensure **consolidated nodes participate in the same validity/version system as their source findings**.

I would make:

```text
consolidated_finding
    ├── simulator
    ├── source_findings[]
    ├── source_versions[]
    ├── affected_concepts[]
    ├── validity
    └── derived_at
```

When V2 invalidates the underlying findings, the consolidated knowledge should either:

1. become `HISTORICAL`, or
2. be recomputed from remaining ACTIVE evidence.

I strongly prefer **#2**.

```text
V1:
A + B + C → Consolidated X

V2 invalidates A,B

remaining:
C

→ recompute
C → Consolidated X'
```

Thus semantic memory becomes a **materialized view of experiments**, rather than another permanent accumulation layer.

### One other change I'd make

Your `MODULE_CONCEPTS` approach is currently doing a lot of work. Eventually, don't depend primarily on:

```text
changed file → manually defined concepts
```

Have the simulation itself declare its ontology:

```yaml
module: reproduction.py
concepts:
  - reproduction
  - fertility
  - population_growth
outputs:
  - births
  - population
```

Then code changes can automatically produce semantic impact.

### Overall

I would consider your current architecture:

**Phase 0–4 = foundation complete.**

Don't keep adding infrastructure.

The next phase should be **"semantic evolution"**:

```text
Git diff
   ↓
semantic impact
   ↓
invalidate affected findings
   ↓
rebuild consolidated knowledge
   ↓
derive/update hypotheses
   ↓
identify uncertainty/gaps
   ↓
run next experiment
   ↓
possibly modify code
   ↓
Git commit
   ↺
```

That is where your kernel + simulator becomes genuinely **self-developing**, rather than merely maintaining a history of simulations.
