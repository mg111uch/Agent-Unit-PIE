# Kernel (Level 1) — the cognitive substrate

> **For future agents:** keep this as wholesome feature docs — one-liner prose rows in §3; **no phase sections or phase-wise history**; no line numbers (file + symbol only). Code is the ultimate source of truth.
> Code: `$PIE_ROOT/codebase/kernel/` (~17k LOC at last count) + `codebase/development/` (dev loop) · Store: `data/kernel.db` · Master doc: `README.md`.

## 1. Role

The kernel owns cognition: schema/ontology, units, memory, retrieval, signals, events, patterns, hypotheses, validity, lineage. **Strategic stance (adopted):** don't write another big module — make kernel events the *universal currency* of PIE so every FireFlow transaction, twin observation and city simulation flows through the same vocabulary: `Observation → Event → Signal → Pattern → Semantic memory → Hypothesis → PIE decision`.

`KernelEvent` fields (target shape): event_id, event_type, actor/unit, object/unit, location, timestamp, source, confidence, evidence, causes[], effects[], economic_delta, metadata. Example types: TaskCreated/Claimed/Verified, PaymentAuthorized/Settled, BusinessOrderReceived, InventoryChanged, PriceObserved, FactoryCapacityObserved, TrafficObserved, WaterDemandObserved, PolicyApplied, SimulationCompleted, OpportunityDiscovered, VentureKilled. [VERIFY KRN-01] Which of these exist as registered event types today? [/VERIFY]

## 2. Documentation map (kernel-related artifacts)

| Artifact | Purpose |
|---|---|
| `kernel/usage.md` | deep manual: architecture, contradiction quickstart, signals, backfill, troubleshooting (summarized in §5–§7) |
| `kernel/roadmap.md` | open kernel questions *(not supplied)* |
| `data/workflows/kernel_ops.json` + `.md` | agent operating loop as workflow graph + per-node reference |
| `data/workflows/research_development.json` + `.md` + `workflow_graph.html` | unified 12-node dev loop; renderer handles legacy array + dict contract nodes |
| `codebase/prompt_fragments/kernel_playbook.md`, `onboarding.md` | rules/cheap-orientation order injected into server prompts *(not supplied)* |
| `codebase/development/` | orchestrator: `workflow_engine`, `contracts`, `development_state`, `develop_tools`, `validation_gate`, `eval_harness` |
| `scripts/` | `topic_ops.py`, `backfill_topics.py`, `prune_kernel_logs.py` (`--keep N`, default 200), `smoke_kernel.py`, `link_gap_blockers.py`, `render_status.py`, `render_recent_changes.py`, `render_index.py`, `record_removal.py`, `emit_dev_change.py`, `detect_tool_bypass.py` |
| Canonical store | `data/kernel.db` via `argu_god/engine/topic_store.py`; `data/topics/*/graph.json` is a **derived view** |

## 3. Features (shipped)

### 3.1 Storage, topics, memory
| Capability | Description |
|---|---|
| Topic-graph kernel store | `topic_store` is the single writer/reader (SQLite canonical, hydration on boot); `graph.json` regenerated on every mutation; CLI `topic_ops.py` + one-shot `backfill_topics.py` (parity check; dangling edges dropped with WARN) |
| Hypothesis → semantic memory export | `export_to_semantic_memory` uses hypothesis_type as node_type (`capability_claim` / `known_gap`), status in metadata; searchable via `search_semantic_memory` |
| Sharded simulations & episodic | `SimulationConnector(simulator)` shards `data/units/simulations/{sim}/{run}` (+ legacy fallback/migration), persists `simulation_runs` and `episodic_memory` + immutable `data/memory/episodic/{sim}_{run}.json` |
| Citation cache | path+symbol+mtime keyed; `validate_capabilities` re-resolves only when cited paths change |
| Removal rationale log | `record_removal.py` records `side=decision` nodes + `contradicts` edges into `project_history` (idempotent, `--dry-run`/`--json`) |
| Supersedes refinements | `add-node --supersedes NAME` bypasses the similarity gate, marks prior node `superseded` (history kept); `--stance` (decisions default `agree`) |
| Cross-topic evidence | `--evidence TOPIC:NAME` pointers (both directions via `neighbors`); `batch --file spec.json` runs many mutations in one hydrate |

### 3.2 Lineage, validity, retrieval, compression (per-simulator isolation)
| Capability | Description |
|---|---|
| Per-simulator registry | `simulator_registry.py` discovers `codebase/modules/simulators/*` (`popula_dyn`→`popu_sim`, `eco_sim`→`sim_eco_sim`); findings, topics, lineage scoped per simulator |
| Simulation lineage (Git-backed) | `simulation_version.py` + `git_version.py`; `sync_from_git(sim)` maps last commit touching `simulators/<sim>` → `sim@commit` (fallback `V1_hash`); non-sim commits don't bump a sim |
| Validity scope | `validity.py` concept-level ACTIVE→HISTORICAL per sim (e.g., `reproduction` change → population findings HISTORICAL, `terrain` leaves them ACTIVE); skips `consolidated_observation` (rebuilt) |
| Declarative simulation ontology | per-sim `ontology.yaml` (`modules:{reproduction:{concepts,outputs}}`) merged over fallback `MODULE_CONCEPTS` via `_load_ontology_concepts()` / slash-aware `concepts_for_changed_files()` |
| Version-aware retrieval | `retrieval_engine` + `semantic_retriever` filter simulator + HISTORICAL + `is_compatible`; default `include_historical=False` (audit `True`); episodic also per-sim |
| Per-sim compression (materialized view) | groups ACTIVE raw findings per `(sim, outcome, horizon//10)` → `consolidated_{sim}_{outcome}_{bucket}`; `recompute_consolidated(sim)` after invalidation (`<2` → HISTORICAL); episodic raw immutable |
| Validity as twin versioning | `validity.py` reused outside sims: twin `v1→HISTORICAL` on field change with changed-variables recorded |

### 3.3 Contradiction & hypothesis discipline
| Capability | Description |
|---|---|
| Symbolic contradiction gate | `hypothesis/contradiction_gate.py` — **opposition-required**: blocks only on negated shared content words (window-2, tri-state, generic-word stoplist) with sim>0.6, never on resemblance alone (returned as non-blocking `duplicate_hint`); disjoint gen/run referents never contradict; per-sim, version-aware; cross-sim never contradicts |
| Dry-run gate verdict | `topic_ops --dry-run add-node` reports `would_block` + conflicts (text and `--json`) |
| Hypothesis primitive | `develop_hypothesis({id,title,type})` creates/attaches `WORLD|MODEL|DEVELOPMENT` hypothesis and advances workflow |
| Roadmap–gap linking | `link_gap_blockers.py` links `known_gap` hypotheses to near-term roadmap bullets (`requires`/`required_by` edges) |

### 3.4 Event / signal fabric & activation
| Capability | Description |
|---|---|
| Kernel bus | `kernel_bus.py`: thin `publish_event/publish_signal/publish_observation` + `subscribe` over existing engines (kernel.db only); revived `event_extractor` + `signal_router` from stubs |
| Capability activation registry | `kernel/capability_registry.yaml`: machine-readable inventory (ACTIVE / PARTIALLY_ACTIVE / DORMANT / EXPERIMENTAL / DEPRECATED, inputs/outputs/consumers); **66 entries at creation, 16/8/42**; answers "which dormant capabilities fit X" |
| Versioned unit schema artifact | `schemas/unit_schema.py:UNIT_SCHEMA_VERSION` + `export_json.py` → `unit_schema.v1.json` (single source; **vendored into FireFlow with drift tests** — the old row "vendoring deferred" is stale, DOC-03) |
| `dev_change` events | `EventEngine.create_event` / `emit_dev_change.py` / `kernel_emit_dev_change` tool; timeline records summary + paths |
| Capability regression signal | `validate_capabilities` emits `capability_regression` when a previously `supported` capability now FAILs |
| Tool-bypass detection | `detect_tool_bypass.py` surfaces repeated raw Reads on atlas-indexed files via `pattern_engine.detect_repeated_events` |
[SUGGESTION KRN-01 · P1] Report DORMANT count each iteration; DEPRECATE and archive capabilities with no planned consumer. [/SUGGESTION]
[SUGGESTION KRN-02 · P1] Activate relation/hierarchy retrievers via the city graph first. [/SUGGESTION]

### 3.5 Dev loop & autonomy (details in `agent_runtime/README.md`)
| Capability | Description |
|---|---|
| Unified development loop | `research_development.json` 12-node contract; `workflow_engine` enforces `allowed` + `success∈node.success` + `outputs`; prevents `start→experiment` skip |
| DevelopmentState | `generate_state(sim)` merges git/lineage/workflow/hypotheses/gaps/runs into <1.9 KB `{sim,git,sim_commit,sim_version,aff_concepts,wf_ver,wf_node,allowed,hyps,gaps,runs,ts,_bytes}` |
| `develop.*` primitives | 9 `CAT_DEVELOP` tools: state/orient/experiment/analyze/modify_simulator/modify_workflow/modify_kernel/validate/commit |
| Graduated autonomy gate | L0–L6; `DEFAULT_CEILING=3`; `required_level(path)` (`simulators/*→3`, `data/workflows→4`, `kernel→6`) |
| Agent evaluation harness | `run_all()`: workflow_conformance, recovery, adversarial_lineage (5 invariants), workflow_evolution, research_loop (`_bytes<2000`) |
| Smoke-guarded modify | `develop_modify_simulator` runs `2 fertile same-cell birth_rate 1.0 → births_total>=1` before `modify_code→validate` |
| Hot-reload | tool-module changes reload without restart; `kernel_reload`, `hot_reload` tools |

### 3.6 Generated status & health
| Capability | Description |
|---|---|
| Status regeneration | `render_status.py` regenerates Current Capability / Known Gaps / Recent Changes from `capability_claim` + `known_gap` hypotheses and `dev_change` events; idempotent on all 5 status files; passes `report_schema_check_tool` |
| Status from events | `render_recent_changes.py` (last 10 `dev_change` events + uncovered manual bullets, cap 10) |
| Project health index | `render_index.py` → `generated_reports/INDEX.md` badge from inventory + schema check + capability validation |
| Agent onboarding | `onboarding.md` fragment points agents at `project_history` + `list_capabilities`/`report_inventory` instead of full-report reads |

## 4. Architecture (writers → canonical store → readers)

```
topic_ops.py / record_removal.py / engine/expand.py ──► kernel semantic_memory (SQLite: data/kernel.db) ──► debate loop, GET /api/graph, topic_ops list,
                                                         + simulation_versions/runs                         retrieval_engine (per-sim), semantic_retriever
                                         every mutation regenerates data/topics/<topic>/graph.json (DERIVED VIEW ONLY)
```

## 5. Contradiction rules (quick)

- **Edge-time detection:** a `contradicts` edge raises a flag **only when both endpoints hold stance `agree`** in `belief_state.json` and are version-compatible, same simulator, not HISTORICAL. Adding nodes alone never fires anything; re-adding an existing triple is skipped. Emits `contradiction_detected_<id>` signal.
- **Write-time (autonomous) gate:** blocks only on `(opposite polarity AND sim>0.6)` or `sim>0.85` where `sim=max(jaccard,(cosine+1)/2)`; mere resemblance to a `contradicts` endpoint never blocks. Observations use a **symbolic tier** (`metric, outcome INCREASE|DECREASE, baseline, horizon`); embeddings only retrieve candidates, never decide. Override with `--force` / `force=True` **only after user approval**.
- Exit codes: 0 success (contradictions are advisory), 1 error, 2 argument error. Relation vocabulary for new edges: `{contradicts, requires, supports, supersedes}`.
[LOOPHOLE DBT-03 · S2] The debate analyzer expects `refutes`; the kernel vocabulary has no `refutes`. [/LOOPHOLE]
[SUGGESTION KRN-03 · P2] Measure the gate's false-negative rate (paraphrases) with the adversarial eval; optional embedding *candidate* retrieval in a sidecar. [/SUGGESTION]
[SUGGESTION KRN-06 · P1] Encode `claim_strength ∈ {HYPOTHESIS, REPLICATED, FALSIFICATION_PASSED, VALIDATED_OOS}` in the gate so "no finding above HYPOTHESIS without multi-seed + falsify" can't be bypassed. [/SUGGESTION]

## 6. CLI reference (`conda run -n myenv python scripts/topic_ops.py …`)

| Command | Purpose |
|---|---|
| `add-node` | `--topic --name --premise [--side …] [--source]… [--confidence F] [--type observation|argument] [--metadata JSON] [--stance …] [--supersedes NAME] [--evidence TOPIC:NAME]… [--force]`; idempotent by name; decisions auto-`agree` |
| `add-edge` | `--topic --source --target --relation {contradicts,requires,supports,supersedes} [--force]` |
| `neighbors` / `batch` / `list` / `topics` | in-topic + cross-topic edges · many mutations in one hydrate · serve from kernel memory · distinct topic ids |
| `set-stance` | records stance in `belief_state.json` (needed for edge-time detection) |
| `check` | `--topic --claims A,B` — same detector as the live debate loop |
| `signals` / `doctor` | list `contradiction_detected_*` ids · health, parity, signal count |
Global flags: `--dry-run`, `--json`, `-q`. **Gotcha:** `conda run` doesn't forward stdin — use `-c` or a script file.

## 7. Troubleshooting (summary)

`Topic not found` → no nodes yet/typo (exit 1) · `invalid choice: 'related'` → use the fixed relation vocabulary · detection didn't fire → both endpoints must be exactly `agree`, titles must match node names, edge must be `contradicts` and newly added · `blocked_contradiction` → gate flagged similarity+negation; resolve prior node (`set-stance`/`record_removal`) or `--force` after user approval; no write occurred · stale `graph.json` → it's derived; re-run `backfill_topics.py <topic>` · blank heredoc output → `conda run` stdin.

## 8. Open questions & suggestions

[LOOPHOLE KRN-05 · S2] `usage.md` says "Last verified 2026-08-29", before the bus/registry/adapters. Re-run smoke (9/9) and re-stamp. [/LOOPHOLE]
[LOOPHOLE KRN-04 · S2] One SQLite file serves server, CLI scripts, hot-reload and loops — add WAL + busy-timeout + single-writer queue. [/LOOPHOLE]
[SUGGESTION INT-06 · P1] Treat FireFlow as a domain source with `app@commit` + `fee_policy_version`; policy change → concept-level HISTORICAL. [/SUGGESTION]
[SUGGESTION KRN-07 · P2] Make compression min-support configurable and expose `n` to the LLM with each consolidated node. [/SUGGESTION]
[VERIFY KRN-01] Current registry counts by status? [/VERIFY]
[VERIFY KRN-06] Is the above-HYPOTHESIS rule enforced in code or only by convention? [/VERIFY]
Planning-chat items not yet built: hierarchy/relation retrievers; `promote --keep` (parallel ACTIVE trees); full 14-step city loop as a formal workflow (only one slice exists).
