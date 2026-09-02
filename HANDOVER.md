# Handover — Research Development Loop 

Point your agent harness to this file to start autonomous research development. Static pointers (no duplication) — follow links.

## Task — Iter7 (next) — Iter4-6 DONE, post_commit active
Iter4 `popula_dyn@735cf9a` `harvest/produce/trade` double-count fix, Iter5 `a5f9752` `regrow` fertility sync, Iter6 `9ff8ff1` `consume/survival` graded starvation. Workflow `research_development.json@cd57976` adds bottom `post_commit` node (`loop→post_commit→orient/stop`, `research_development.md#post-commit`): handover is pointer only, history via `data/kernel.db` hydration. Next: `develop_orient({"query":"resource/scarcity graded starvation follow-up","simulator":"popula_dyn"})` via unified loop — no history copy.

Follow the unified loop in `data/workflows/research_development.json` (see `research_development.md` for node contracts) strictly via `develop.*` primitives — LLM thinks inside workflow, `workflow_engine` enforces transitions. No steps duplicated here — read workflow files.

## Quick Start (conda env `myenv`)

```bash
cd /home/manigupt/Hello/Agentic_Unit_PIE
conda run -n myenv AGENT_SKIP_AUTH=true python codebase/server.py  # if using agent_core harness (optional)
# Verify state (<2KB) without starting server:
conda run -n myenv python -c "import sys;sys.path.insert(0,'codebase');from development.development_state import state_text;print(state_text('popula_dyn'))"
```

## Context Links (read in order — minimal for new sessions)

1. `data/workflows/research_development.json` + `research_development.md` — **Top-level 12-node loop** `start→orient→version_sync→hypothesis→decide_branch→{experiment,modify_code}→update_knowledge→evaluate→validate→loop→stop` (subgraphs: `kernel_ops.json`, `popu_sim_dev.json`). Contracts: `{id,goal,inputs,preconditions,actions,outputs,success,failure,next,mdRef}` via `development/contracts.py`.
2. `system_devpt_reports/kernel/README.md` + `usage.md` — Kernel capabilities & per-sim lineage/validity/retrieval docs (lazy-load only when task touches `kernel/**`, topics, signals, logs).

Plan-mode rule: do NOT re-verify checklist steps 1-5 by reading 10+ implementation files (`development/*`, `kernel/*`). Trust `workflow_engine.enforces transitions`; read extra files only when hypothesis gated to that path.

## Core Invariants (do not reinvent)

- **Git = syntactic lineage** `sim@commit` via `kernel/git_version.py:sim_commit(sim)` scoped `simulators/<sim>` (prevents `virtual_silicon` bump); fallback hash.
- **Kernel = semantic validity** `ACTIVE→HISTORICAL` per-sim concept-level (`kernel/validity.py:mark_stale_findings` + `affected_by` via ontology-aware `_load_ontology_concepts()` from `modules/simulators/<sim>/ontology.yaml`).
- **Consolidated = materialized view** `kernel/compression_engine.py:recompute_consolidated` (`<2` remaining → `HISTORICAL`, else recomputed `avg_delta`).
- **Single persistence** `data/kernel.db` (SQLite) — no second store (simulation_runs, semantic_nodes, workflow_states all there).
- **Renderer** `data/workflows/workflow_graph.html?graph=research_development.json` handles both legacy array and dict contract nodes.

## Opencode Loop (5 steps, use `develop.*` — hides shell)

```python
# 1. Orient (<1900B DevelopmentState preface, 2KB budget)
import sys; sys.path.insert(0,'codebase')
from development.develop_tools import develop_orient, develop_experiment, develop_analyze, develop_validate, develop_commit
from development.development_state import generate_state
develop_orient({"query":"population collapse birth_rate 0.08","simulator":"popula_dyn"})  # → {context,state,allowed:[hypothesis]}

# 2. Hypothesis via develop_hypothesis (WORLD|MODEL|DEVELOPMENT) — decide_branch: param→experiment (L1-2), model→sim L3, workflow L4, kernel L5 propose/L6 modify
from development.develop_tools import develop_hypothesis
develop_hypothesis({"hypothesis_id":"hyp_pop_collapse_08","title":"MODEL: births bottleneck","type":"MODEL"})  # → decide_branch
# 3a. Experiment L1-2 (uniform: run_basic baseline, run_policy_<param><value> e.g. birth08 for 0.08):
develop_experiment({"run_id":"run_policy_birth08","params":{"birth_rate":0.08},"simulator":"popula_dyn","baseline_run_id":"run_basic"})
# 3b. Code edit (gated):
from development.validation_gate import gate
gate(3,"codebase/modules/simulators/popula_dyn/behaviours/reproduce.py")  # sim L3 ALLOW
develop_modify_simulator({"path":"...","old_string":"x=1","new_string":"x=2"})  # L3
develop_modify_workflow({"path":"data/workflows/research_development.json","old_string":"...","new_string":"..."})  # L4
develop_modify_kernel({"path":"codebase/kernel/...","old_string":"...","new_string":"...","human_approved":True})  # L6

# 4. Analyze + Validate
develop_analyze({"run_id":"run_policy_birth08","simulator":"popula_dyn"})
develop_validate({"simulator":"popula_dyn"})  # sync_from_git + lineage + advance validate→loop
# Docs after any edit: follow docs_update subgraph (detect_stale→identify_scope→update_docs→verify via report_freshness_tool)

# 5. Commit + Loop
develop_commit({"message":"Phase 8: ...","add_all":True})  # → loop→orient
generate_state("popula_dyn")["_bytes"]  # <1900 check
```

## Measure Self-Improvement

Repeat same task from clean context; harness `development/eval_harness.py:run_all()` checks `workflow_conformance/recovery/adversarial_lineage/workflow_evolution/research_loop` (5/5). Goal: `iteration N+1 < N tool_calls` + better simulator.

## Where to Ask

- Kernel/sim isolation, lineage, docs freshness → check `report_freshness_tool` / `report_schema_check_tool` first (via `develop_validate`).
- Never hand-edit `data/topics/*/graph.json` (derived view).

## Execution Mode — Ask First

Fresh agents must ask user before iteration 2+:
`ask_user_question: Which execution mode? [Proceed stepwise with report after each step (inspect anomalies before next step) | Silent steps until validate (report only at loop)]`
Default is stepwise with report (safer for first MODEL fix). Respect choice for all subsequent `develop.*` calls in that iteration.
