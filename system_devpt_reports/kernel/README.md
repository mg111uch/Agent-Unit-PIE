# Kernel (Level 1) — the cognitive substrate

> **For future agents:** keep this as wholesome feature docs — one-liner prose rows in §3; **no phase sections or phase-wise history**; no line numbers (file + symbol only). Code is the ultimate source of truth.
> **Code:** `$PIE_ROOT/codebase/kernel/` (~17k LOC at last count) + `codebase/development/` (dev loop) · **Store:** `data/kernel.db` · **Master doc:** `00_README_master.md` · **Deep manual:** `kernel/usage.md` (same dir — worked quickstart, expected output, exit codes, backfill notes).

## 1. Role

The kernel owns cognition: schema/ontology, units, memory, retrieval, signals, events, patterns, hypotheses, validity, lineage. **Strategic stance (adopted):** don't write another big module — make kernel events the *universal currency* of PIE so every FireFlow transaction, twin observation and city simulation flows through the same vocabulary: `Observation → Event → Signal → Pattern → Semantic memory → Hypothesis → PIE decision`.

`KernelEvent` fields (target shape): event_id, event_type, actor/unit, object/unit, location, timestamp, source, confidence, evidence, causes[], effects[], economic_delta, metadata. Example types: TaskCreated/Claimed/Verified, PaymentAuthorized/Settled, BusinessOrderReceived, InventoryChanged, PriceObserved, FactoryCapacityObserved, TrafficObserved, WaterDemandObserved, PolicyApplied, SimulationCompleted, OpportunityDiscovered, VentureKilled.

[VERIFY KRN-01] Which of these exist as registered event types today? [/VERIFY]

## 2. Documentation map (kernel-related artifacts)

| Artifact | Purpose |
|---|---|
| `kernel/usage.md` (this dir) | **Deep manual (Level 2):** architecture, contradiction quickstart with expected output, signal verification, backfill, gate internals, API-free CLI usage, troubleshooting. Canonical for worked examples. |
| `kernel/roadmap.md` (this dir) | Open kernel questions and future direction (cross-module view in `02_roadmap_master.md`). |
| `data/workflows/kernel_ops.json` + `kernel_ops.md` | Agent operating loop as a workflow graph + per-node reference. |
| `data/workflows/research_development.json` + `.md` + `workflow_graph.html` | Unified 12-node dev loop; renderer handles legacy array + dict contract nodes (`goal/shape/color/mdRef`). |
| `codebase/prompt_fragments/kernel_playbook.md` | Rules injected into server-assembled agent prompts. |
| `codebase/prompt_fragments/onboarding.md` | Cheap-orientation order for agents (`project_history`, capabilities, reports); in `FRAGMENT_ORDER`. |
| `codebase/development/` | Orchestrator: `workflow_engine.py`, `contracts.py`, `development_state.py`, `develop_tools.py`, `validation_gate.py`, `eval_harness.py`. |
| `scripts/topic_ops.py` | CLI: `add-node` / `add-edge` / `neighbors` / `batch` / `set-stance` / `check` / `signals` / `list` / `topics` / `doctor`. |
| `scripts/backfill_topics.py` | One-shot legacy `graph.json` → kernel migration + parity check. |
| `scripts/prune_kernel_logs.py` | Trim logs table (`--keep N`, default 200). |
| `scripts/smoke_kernel.py` | Regression harness for all of the above (9/9 at last smoke). |
| `scripts/link_gap_blockers.py` · `render_status.py` · `render_recent_changes.py` · `render_index.py` · `record_removal.py` · `emit_dev_change.py` · `detect_tool_bypass.py` | Gap linking · status regeneration · recent-changes from events · health index · removal rationale · `dev_change` emission · tool-bypass detection. |
| Canonical store | `data/kernel.db` via `argu_god/engine/topic_store.py`; `data/topics/*/graph.json` is a **derived view** (one SQLite persistence path). |

## 3. Features (shipped)

### 3.1 Storage, topics, memory

| Capability | Description |
|---|---|
| Topic-graph kernel store | `topic_store.py` is the single writer/reader for topic data (SQLite canonical, hydration on boot); every mutation regenerates `graph.json`; generic CLI `topic_ops.py` + one-shot `backfill_topics.py` (idempotent parity check; dangling edges dropped with `WARN`); user manual in `usage.md`. |
| Hypothesis → semantic memory export | `export_to_semantic_memory` uses hypothesis_type as node_type (`capability_claim` / `known_gap`) and stores `status` in metadata; validated capabilities + gaps searchable via `search_semantic_memory`. |
| Sharded simulations & episodic | `modules/simulators/simulation_connector.py:SimulationConnector(simulator)` shards `data/units/simulations/{sim}/{run}` (+ legacy `codebase/units/simulations` fallback/migration), persists `simulation_runs` (per-sim) and `episodic_memory` + `data/memory/episodic/{sim}_{run}.json` (immutable raw). |
| Citation cache | `citation_cache` table (path+symbol+mtime keyed); `validate_capabilities` re-resolves citations only when cited paths change, else marks “cached (mtime unchanged)”. |
| Removal rationale log | `scripts/record_removal.py` records `side=decision` nodes + `contradicts` edges for `project_history` via kernel semantic memory (idempotent, `--dry-run`/`--json`; `graph.json` is a regenerated view); a `contradicts` edge between agreed beliefs emits a kernel `contradiction_detected` signal; `validate_capabilities` FAIL detail suggests the exact `record_removal` command. |
| Supersedes refinements | `topic_ops.py add-node --supersedes NAME` bypasses the similarity gate, marks the prior node `superseded` (exported status, gate-skipped, history kept); `--stance` (decisions default `agree`) lets `contradicts` detection fire. |
| Cross-topic evidence | `--evidence TOPIC:NAME` pointers stored in node metadata, both directions via `topic_ops.py neighbors`; `batch --file spec.json` runs many mutations in one hydrate. |

### 3.2 Lineage, validity, retrieval, compression (per-simulator isolation)

| Capability | Description |
|---|---|
| Per-simulator registry | `kernel/simulator_registry.py` discovers `codebase/modules/simulators/*` (`popula_dyn`→`popu_sim`, `eco_sim`→`sim_eco_sim`); strict isolation: findings, topics, lineage and retrieval scoped per simulator. |
| Simulation lineage (Git-backed) | `kernel/simulation_version.py` + `kernel/git_version.py` + `simulation_schema.py` + `simulation_versions`/`simulation_runs` tables; `sync_from_git(sim)` maps the last commit touching `simulators/<sim>` → `sim@commit` (`sim_commit`, `diff_sim_files`), fallback `V1_hash`; prevents `virtual_silicon` commits from bumping `popula_dyn`; concepts via ontology-aware `_load_ontology_concepts()`. |
| Validity scope | `kernel/validity.py` concept-level `ACTIVE→HISTORICAL` per sim (`affected_by` via ontology-aware `_load_ontology_concepts`); skips `consolidated_observation` (rebuilt via materialized view); `sync_from_git` auto-marks stale raw findings `invalidated_by` then triggers `recompute_consolidated` (e.g., `reproduction` → 3/3 population HISTORICAL, `terrain` → 0/3). |
| Declarative simulation ontology | `codebase/modules/simulators/popula_dyn/ontology.yaml` (per-sim; `modules: {reproduction: {concepts:[..], outputs:[..]}}`) + `simulation_schema.py:_load_ontology_concepts()`/`concepts_for_changed_files()` merges it over fallback `MODULE_CONCEPTS`; slash-aware path handling maps `behaviours/reproduce` → `reproduction`; a simulator declares its own semantic impact, no hardcoded mapping required. |
| Version-aware retrieval | `kernel/retrieval/retrieval_engine.py` + `semantic_retriever.py` filter `simulator` + `HISTORICAL` + `is_compatible(find_ver, query_ver, sim)`; default `include_historical=False` (audit `True`); episodic also per-sim; consolidated `HISTORICAL` auto-excluded. |
| Per-sim compression (materialized view) | `kernel/compression_engine.py` groups `ACTIVE` raw findings per `(sim, outcome, horizon//10)` → `consolidated_{sim}_{outcome}_{bucket}` (`consolidated_observation`) carrying `simulator, source_findings[], source_versions[], affected_concepts[], validity{ACTIVE@cur_ver}, derived_at`; excludes self-grouping; `recompute_consolidated(sim)` rebuilds from remaining ACTIVE (`<2` → `HISTORICAL`, else recomputed `avg_delta`) after invalidation; episodic raw stays immutable. |
| Validity as twin versioning | `validity.py` concept-invalidation reused outside sims: twin `v1→HISTORICAL` on field change with changed-variables recorded. |

### 3.3 Contradiction & hypothesis discipline

| Capability | Description |
|---|---|
| Symbolic contradiction gate | `kernel/hypothesis/contradiction_gate.py` — **opposition-required**: blocks only on negated shared content words (window-2, tri-state, generic-word stoplist) with `sim>0.6`, never on resemblance alone (returned as non-blocking `duplicate_hint`); disjoint gen/run referents never contradict (new measurements = progress); verdict-word inference scoped to pop-sim topics with a metric-noun guard; per-sim, version-aware; cross-sim never contradicts. |
| Dry-run gate verdict | `topic_ops.py --dry-run add-node` runs the gate without writing and reports `would_block` + conflicts (text and `--json`), so agents can pre-check phrasing. |
| Hypothesis primitive | `develop_hypothesis({id,title,type})` creates/attaches a `WORLD`/`MODEL`/`DEVELOPMENT` hypothesis and auto-advances `hypothesis→decide_branch` — code is source. |
| Roadmap–gap linking | `scripts/link_gap_blockers.py` links `known_gap` hypotheses to near-term roadmap bullets with `requires`/`required_by` edges (idempotent ids, `--dry-run`); queryable via `get_neighbors`. |

### 3.4 Event / signal fabric & activation

| Capability | Description |
|---|---|
| Kernel bus | `kernel/kernel_bus.py`: thin `publish_event`/`publish_signal`/`publish_observation` + `subscribe` over existing engines (no new engine logic, `kernel.db` only); revived `events/event_extractor.py` + `signals/signal_router.py` from empty stubs. |
| Capability activation registry | `kernel/capability_registry.yaml`: machine-readable inventory of every kernel module (`ACTIVE`/`PARTIALLY_ACTIVE`/`DORMANT`/`EXPERIMENTAL`/`DEPRECATED`, inputs/outputs/consumers); **66 entries at creation, 16/8/42**; answers “which dormant capabilities fit X”. |
| Versioned unit schema artifact | `schemas/unit_schema.py:UNIT_SCHEMA_VERSION` + `export_json.py` emits `unit_schema.v1.json` (single source; **vendored into FireFlow with drift jest** — the old “vendoring deferred” row is stale, DOC-03). |
| `dev_change` events | `dev_change` event type (`development` category) emitted via `EventEngine.create_event` / `scripts/emit_dev_change.py` / the `kernel_emit_dev_change` agent tool; `timeline_engine.add_event` records summary + paths in the timeline. |
| Capability regression signal | `validate_capabilities` detects regressions (previously-`supported` caps now FAIL, via `citation_cache`) and emits a `capability_regression` kernel signal. |
| Tool-bypass detection | `scripts/detect_tool_bypass.py` surfaces repeated raw Reads on atlas-indexed files via `pattern_engine.detect_repeated_events`. |

[SUGGESTION KRN-01 · P1] Report DORMANT count each iteration; DEPRECATE and archive capabilities with no planned consumer. [/SUGGESTION]
[SUGGESTION KRN-02 · P1] Activate relation/hierarchy retrievers via the city graph first. [/SUGGESTION]

### 3.5 Dev loop & autonomy (details in `agent_runtime/README.md`)

| Capability | Description |
|---|---|
| Unified development loop | `research_development.json` 12-node contract `start→orient→version_sync→hypothesis→decide_branch→{experiment,modify_code}→update_knowledge→evaluate→validate→loop→stop`, meta `subgraphs:[kernel_ops, popu_sim_dev]`; `workflow_engine.py:UNIFIED_NODES` + `load_json/allowed()/advance(target,produced,success)` enforces `allowed` + `success∈node.success` + `outputs` present (prevents `start→experiment` skip); `contracts.py` validates `id,goal,outputs,success,next` + legacy array compat. |
| DevelopmentState | `development_state.py:generate_state(sim)` merges `git_version(sim_commit/current_commit)` + `simulation_version(sim@commit/aff_concepts)` + `workflow_engine(allowed/wf_node)` + `hypothesis_engine(hyps/gaps)` + `simulation_runs(recent)` into a `<1.9 KB` `{sim,git,sim_commit,sim_version,aff_concepts,wf_ver,wf_node,allowed,hyps,gaps,runs,ts,_bytes}` with trim; `state_text()` renders `CURRENT STATE … ALLOWED: …`. |
| `develop.*` primitives | 9 `CAT_DEVELOP` tools (`develop_state/orient/experiment/analyze/modify_simulator/modify_workflow/modify_kernel/validate/commit`) — each composes deterministic ops (`retrieval_engine.search`, `SimulationConnector.run_and_extract+register_to_kernel`, `CompressionEngine.compress_observations`, `git_commit`) and advances `workflow_engine`; hides the `conda run … topic_ops.py` shell; `develop_modify_*` gated via `validation_gate`. |
| Graduated autonomy gate | `validation_gate.py` levels `L0 suggest / L1 edit+test / L2 edit+test+commit / L3 sim_modify / L4 workflow_modify / L5 kernel_propose / L6 kernel_modify` (`DEFAULT_CEILING=3` = sim autonomous; L4+ gated; L5–L6 need human approval); `required_level(path)` (`simulators/*→3`, `data/workflows→4`, `kernel→6`); `gate(level,path,human_approved)` runs `contracts, sim_smoke, lineage, retrieval, workflow_conformance, human_approval` and blocks `L3 kernel` / `L1 workflow` / `L6 without approval`. |
| Agent evaluation harness | `eval_harness.py:run_all()` (FixesIssues 6A/B/E/F + 9): `workflow_conformance` (legal `orient→…→update_knowledge` + illegal `start→experiment` blocked), `recovery` (missing params → Error), `adversarial_lineage` (5 invariants: V1 stale/partial/unrelated/no-contradiction/same-version), `workflow_evolution` (added node still validates), `research_loop` (`_bytes<2000`); helpers `conformance_mini`/`adversarial_mini` reused by the gate. |
| Smoke-guarded modify | `develop_modify_simulator` runs a smoke `2 fertile same-cell birth_rate 1.0 → births_total>=1` before `modify_code→validate` (`tests_pass`). |
| Hot-reload | auto-detect tool-module file changes and reload without restart; explicit `kernel_reload` and `hot_reload` tools. |

### 3.6 Generated status & health

| Capability | Description |
|---|---|
| Status regeneration | `scripts/render_status.py` regenerates Current Capability / Known Gaps / Recent Changes from `capability_claim` + `known_gap` hypotheses and `dev_change` events, preserving other sections; the `_Last verified` header is preserved; idempotent on all 5 status files and passes `report_schema_check_tool`. |
| Status from events | `scripts/render_recent_changes.py` drives status Recent Changes from the last 10 `dev_change` events (hybrid: event bullets + uncovered manual bullets, cap 10); newest-first, idempotent. |
| Generated capability sections | status capability sections carry a generated-cache marker (`> Capability section generated by scripts/render_status.py`); `render_status --write` is idempotent on all 5 status files. |
| Project health index | `scripts/render_index.py` writes a `generated_reports/INDEX.md` health badge from report inventory + schema check + capability validation. |
| Agent onboarding | `onboarding.md` fragment (in `FRAGMENT_ORDER`) points agents at `project_history` + `list_capabilities`/`report_inventory` instead of full-report reads. |

## 4. Architecture (writers → canonical store → readers)

```
topic_ops.py / record_removal.py / engine/expand.py ──► kernel semantic_memory (SQLite: data/kernel.db) ──► debate loop, GET /api/graph, topic_ops list,
                                                        + simulation_versions/runs                         retrieval_engine (per-sim), semantic_retriever
                                         every mutation regenerates data/topics/<topic>/graph.json (DERIVED VIEW ONLY)
                                         topics per-sim: popu_sim (popula_dyn), sim_eco_sim …
```

## 5. Contradiction rules (quick)

- **Edge-time detection:** a `contradicts` edge raises a flag **only when both endpoints hold stance `agree`** in `belief_state.json` and are version-compatible, same simulator, not `HISTORICAL`. Adding nodes alone never fires anything; re-adding an existing triple is skipped. Emits `contradiction_detected_<id>`.
- **Write-time (autonomous) gate:** blocks only on `(opposite polarity AND sim>0.6)` or `sim>0.85` where `sim=max(jaccard,(embedding_cosine+1)/2)`; mere resemblance to a `contradicts` endpoint never blocks (correction-rich topics would self-poison); explicit edges fire detection at `add-edge` time instead. Observations use a **symbolic tier** (`metric, outcome INCREASE|DECREASE, baseline, horizon`); embeddings only retrieve candidates, never decide. Override with `--force` / `force=True` **only after user approval**.
- **Not vector embeddings:** `argu_god/engine/vector_store.py` provides ChromaDB + `all-MiniLM-L6-v2` (`embed()`/`search_similar()`) for semantic retrieval/dedup (`dedup.py`), but the autonomous gate deliberately does not call it (model load/latency).
- Exit codes: `0` success (contradictions are advisory flags), `1` error (`Topic not found`, unknown endpoint), `2` argument error. Relation vocabulary for new edges: `{contradicts, requires, supports, supersedes}` (legacy relations survive only inside backfilled data).

[LOOPHOLE DBT-03 · S2] The debate analyzer expects `refutes`; the kernel vocabulary has no `refutes`. [/LOOPHOLE]
[SUGGESTION KRN-03 · P2] Measure the gate's false-negative rate (paraphrases) with the adversarial eval; optional embedding *candidate* retrieval in a sidecar. [/SUGGESTION]
[SUGGESTION KRN-06 · P1] Encode `claim_strength ∈ {HYPOTHESIS, REPLICATED, FALSIFICATION_PASSED, VALIDATED_OOS}` in the gate so “no finding above HYPOTHESIS without multi-seed + falsify” can't be bypassed. [/SUGGESTION]

## 6. CLI reference (`conda run -n myenv python scripts/topic_ops.py …`)

Worked examples, expected stdout/`--json` and exit codes: `usage.md` §Contradiction quickstart. Flags:

| Command | Flags / behaviour |
|---|---|
| `add-node` | `--topic --name --premise [--side decision\|argument\|pro\|con\|neutral] [--source]… [--confidence F] [--type observation\|argument] [--metadata JSON] [--stance agree\|disagree\|neutral] [--supersedes NAME] [--evidence TOPIC:NAME]… [--force]`; idempotent by node name; decisions auto-stance `agree`; per-sim `observation` with `metadata={observation:{simulator,version_id,outcome}, validity:{status}}`. |
| `add-edge` | `--topic --source --target --relation {contradicts,requires,supports,supersedes} [--force]`; idempotent triple; detection on `contradicts`; `supersedes` marks the target superseded. |
| `neighbors` | `--topic --name [--json]` — in-topic edges + cross-topic `evidence` pointers both directions. |
| `batch` | `--file spec.json [--topic T]` — many nodes+edges in one process (single hydrate); spec `{topic?, nodes:[{name,premise,side,sources,confidence,type,metadata,evidence,stance,supersedes,force}], edges:[{source,target,relation,force}]}`. |
| `set-stance` | `--topic --name --stance {agree,disagree,neutral} [--confidence F]` — records stance in `belief_state.json`; stance is **needed** for edge-time contradiction detection. |
| `check` | `--topic --claims A,B [--json]` — CLI wrapper for `check_contradictions`; same detector as the live debate loop. |
| `signals` | `[--json]` — lists `contradiction_detected_*` ids from episodic memory. |
| `list` | `--topic [--side S] [--json]` — serves from kernel memory. |
| `topics` | `[--json]` — distinct topic ids known to the kernel. |
| `doctor` | `[--json]` — health, parity, signal count (`contradiction_signals`, per-topic parity). |

Global: `--dry-run` (no writes), `--json`, `--quiet/-q` — position before or after the subcommand both work. **Gotcha:** `conda run` doesn't forward stdin — use `-c` or a script file (heredocs print nothing).

## 7. Troubleshooting (summary)

`error: Topic not found: X` → no nodes yet/typo, exit 1 · `invalid choice: 'related'` → use the fixed relation vocabulary · detection didn't fire → both endpoints must be exactly `agree` in `belief_state`, titles must match node names, edge must be `contradicts` and newly added · `blocked_contradiction` on `add-node` → gate flagged similarity+negation; resolve the prior node (`set-stance`/`record_removal`) or re-run `--force` after user approval; no write occurred · `graph.json` looks stale/differs → it is derived; any mutation regenerates it (force with `backfill_topics.py <topic>`, idempotent) · blank heredoc output → `conda run` stdin.

## 8. Open questions & suggestions

[LOOPHOLE KRN-05 · S2] `usage.md` says “Last verified 2026-08-29”, before the bus/registry/adapters. Re-run smoke (9/9) and re-stamp. [/LOOPHOLE]
[LOOPHOLE KRN-04 · S2] One SQLite file serves server, CLI scripts, hot-reload and loops — add WAL + busy-timeout + single-writer queue. [/LOOPHOLE]
[SUGGESTION INT-06 · P1] Treat FireFlow as a domain source with `app@commit` + `fee_policy_version`; policy change → concept-level HISTORICAL. [/SUGGESTION]
[SUGGESTION KRN-07 · P2] Make compression min-support configurable and expose `n` to the LLM with each consolidated node. [/SUGGESTION]
[VERIFY KRN-01] Current registry counts by status? [/VERIFY]
[VERIFY KRN-06] Is the above-HYPOTHESIS rule enforced in code or only by convention? [/VERIFY]
Planning-chat items not yet built: hierarchy/relation retrievers; `promote --keep` (parallel ACTIVE trees); full 14-step city loop as a formal workflow (only one slice exists).
