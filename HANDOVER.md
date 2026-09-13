# Handover — Research Development Loop 

Point your agent harness to this file to start autonomous research development. Static pointers (no duplication) — follow links.

## Modules (co-development — task source is each module's status.md, not here)

| Module | Simulator | Task source (Next) | Roadmap | Shipped docs |
|---|---|---|---|---|
| Population sim | `popula_dyn` | `system_devpt_reports/populaDyn_simu/status.md` → Next | `system_devpt_reports/populaDyn_simu/roadmap.md` | `.../populaDyn_simu/README.md` |
| Stock analyser | `stock_analyser` | `system_devpt_reports/stock_analyser/status.md` → Next | `system_devpt_reports/stock_analyser/roadmap.md` | `.../stock_analyser/README.md` |
| Economy (Moonshot) | `economy` (+`popula_dyn` firm side) | `system_devpt_reports/economy/status.md` → Next | `system_devpt_reports/economy/roadmap.md` | `.../economy/README.md` |
| FireFlow app (external) | `external:/home/manigupt/Hello/reddit-clone` | `roadmap.md` (`Now` marker) in external repo — docs live in-repo | `roadmap.md` in external repo | `README.md` in external repo |
| Control-works (external) | `external:/home/manigupt/Hello/control-works` | `roadmap.md` (`Now` marker) in external repo — docs live in-repo; subdirs may carry `module.json` (topic, commands, gates, e.g. drift_racer→`controlworks_arcade_games`, rocket2D→`controlworks_rocket`) | `roadmap.md` per-subdir slices in external repo | `README.md` in external repo |

Rule: fresh agent picks a module, loads its `module.json` first (`development/module_registry.py:load_module` — native sims at `codebase/modules/simulators/<sim>/module.json`, externals by absolute path), then reads its status.md `## Next` for the task (via `module_task_snippet`), then follows the unified loop below. Status.md is the single task source — never duplicate next-tasks here; history via `data/kernel.db` (+ `data/market.db` ledger for stock) hydration. Exception: external modules (FireFlow, control-works) use their in-repo `roadmap.md` `Now` marker as task source (resolved via the descriptor); lineage is `sim@commit` for native sims, `ch@contenthash` for zero-git externals; worker reaches them via absolute path + `bash workdir` (workspace-relative tools reject outside-root paths); kernel tags `fireflow_app` / `controlworks_<subdir>`; zero git (content-hash lineage); never touch personal files (`ToDo.md`, `name_ideas.md`).

Follow the unified loop in `data/workflows/research_development.json` (see `research_development.md` for node contracts) strictly via `develop.*` primitives — LLM thinks inside workflow, `workflow_engine` enforces transitions. No steps duplicated here — read workflow files.

## Execution Mode — Ask First

Fresh agents must ask user before iteration 2+:
`ask_user_question: Which execution mode? [Proceed stepwise with report after each step (inspect anomalies before next step) | Silent steps until validate (report only at loop)]`
Default is stepwise with report (safer for first MODEL fix). Respect choice for all subsequent `develop.*` calls in that iteration.

## Execution Mode — Ask First (mandatory for fresh agents)

Before starting work, ask the user:
`Which execution mode? [Single session: do module work here directly | Module workers: launch one worker per module on demand (same task_id resumed per module), main session acts as orchestrator only]`
Default if no answer: module workers (proven pattern — one task_id per module: economy `ses_f892f855dffe9TPkdf76m05zG0`). Orchestrator verifies every worker leg (smoke + harness + line limits) before close, syncs status/README/roadmap docs, never bypasses gates.
Worker warmup rule: NEVER auto-initialize workers for all modules at startup. Main session starts with zero workers; only warm up a module worker when the user asks to work in that module. One user request = workers for the named modules only.
Worker efficiency rule: one standing worker per active module with multi-step goals (analyse → edit → verify in ONE session), never one worker per step. Briefs stay lean — last result summary plus file pointers, never full context dumps. Continuity passes through the brief; a new dispatch is a fresh session that re-reads everything. Prefer steering or re-tasking a live worker over spawning a replacement.

## Quick Start (conda env `myenv`)

```bash
cd /home/manigupt/Hello/Agentic_Unit_PIE
conda run -n myenv AGENT_SKIP_AUTH=true python codebase/server.py  # if using agent_core harness (optional)
# Verify state (<2KB) without starting server:
conda run -n myenv python -c "import sys;sys.path.insert(0,'codebase');from development.development_state import state_text;print(state_text('popula_dyn'));print(state_text('stock_analyser'))"
```

## Context Links (read in order — minimal for new sessions)

1. `data/workflows/research_development.json` + `research_development.md` — **Top-level 12-node loop** `start→orient→version_sync→hypothesis→decide_branch→{experiment,modify_code}→update_knowledge→evaluate→validate→loop→stop` (subgraphs: `kernel_ops.json`, `popu_sim_dev.json`, `stock_analyser_dev.json`). Contracts: `{id,goal,inputs,preconditions,actions,outputs,success,failure,next,mdRef}` via `development/contracts.py`.
2. `system_devpt_reports/kernel/README.md` + `usage.md` — Kernel capabilities & per-sim lineage/validity/retrieval docs (lazy-load only when task touches `kernel/**`, topics, signals, logs).

Plan-mode rule: do NOT re-verify checklist steps 1-5 by reading 10+ implementation files (`development/*`, `kernel/*`). Trust `workflow_engine.enforces transitions`; read extra files only when hypothesis gated to that path.

## Core Invariants (do not reinvent)

- **Git = syntactic lineage** `sim@commit` via `kernel/git_version.py:sim_commit(sim)` scoped per-sim patterns (`simulators/<sim>/**`, `modules/stock_analyser/**` via manifest); fallback hash.
- **Kernel = semantic validity** `ACTIVE→HISTORICAL` per-sim concept-level (`kernel/validity.py:mark_stale_findings` + `affected_by` via ontology-aware `_load_ontology_concepts()` from `modules/simulators/<sim>/ontology.yaml`).
- **Consolidated = materialized view** `kernel/compression_engine.py:recompute_consolidated` (`<2` remaining → `HISTORICAL`, else recomputed `avg_delta`).
- **Single persistence** `data/kernel.db` (SQLite) — no second store (simulation_runs, semantic_nodes, workflow_states all there; stock research ledger lives in `data/market.db` as domain store, findings mirrored to kernel).
- **Kernel in the loop** every research batch auto-registers one episode finding (`register_episode_finding(episode_summary(rid))` at `run_job` end; topic `sim_stock`); retrieve via `topic_store` hydrate→find/list before new research so contradictions (`contradiction_gate`) and prior evidence guide hypotheses. Durable record is `generic_memory`, not `graph.json` (regenerated view).
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

## Module Loop (native + external, preferred entry)

```python
import sys; sys.path.insert(0,'codebase')
from development.develop_tools import develop_orient
# native sim by name, or external by absolute path (descriptor loaded at runtime)
develop_orient({"query":"drift reward","module":"/home/manigupt/Hello/control-works/arcade_games/drift_racer"})
# → {module:{kind,topic,version,task,memory,commands,skip_nodes,metric_gates}, applicable:[...], allowed:[...]}
develop_orient({"query":"population","module":"popula_dyn"})
```

`applicable` = engine `allowed` minus descriptor `skip_nodes` (no engine change). Run descriptor `commands` via `bash workdir` (externals) or `develop.*` (native). Close every run with one kernel node (`scripts/topic_ops.py add-node`, decision/argument) on the module topic, plus playbook entries for cross-module lessons.

Loop mandate: ALL module work — native sims AND external dirs — runs inside the `research_development` loop via `develop.*` primitives (orient → hypothesis → decide_branch → experiment/modify → analyze → validate → loop). No raw execution outside the loop: no direct training launches, no manual experiment runs, no hand-written kernel nodes. Descriptor `commands` execute as loop experiment steps with the worker reporting back through `develop_analyze`/`develop_validate`, so gates, lineage sync, and docs-freshness apply to externals exactly as to native sims. Direct terminal use is for read-only inspection (logs, plots, `ps`) only.

## Training discipline — one at a time (host is CPU-bound)

- Host runs ONE training at a time. Before any launch check `ps` for `train_nn/train/puffer` processes; if one is up, queue the next run, never parallelize.
- Direct myenv binary (`/home/manigupt/miniconda3/envs/myenv/bin/python`), never the `conda run` wrapper (broken: pygame missing + plugin error). Note `train_nn.py --generations` is an ABSOLUTE total, not additional (checkpoint at gen N needs `--generations N+k`).

### Opencode (blocking sessions — no async workers)

- Always launch via detached launcher (`run_train.sh` / `LOG=... ... &` / `nohup`), never block the session polling. Report PID + LOG path and return immediately; keep session free.
- User pings when training finishes — only then profile the log, estimate remaining time, and log the kernel node. Never run long blocking waits alongside another job.

### Hermes (async agents + auto-notify)

- Main session owns the training PID via `terminal(background=true)` with notify on complete — runtime pings the session on exit, no polling, no user ping needed.
- Dispatch one watcher subagent per run (PID + LOG + target gens in context). It tails the LOG, does CPU-light prep work meanwhile, and its finish report re-enters automatically.
- A subagent-owned background PID dies with the subagent unless `handoff` to parent — so the parent owns training PIDs, watchers only read.

## Measure Self-Improvement

Repeat same task from clean context; harness `development/eval_harness.py:run_all()` checks `workflow_conformance/recovery/adversarial_lineage/workflow_evolution/research_loop` (5/5). Goal: `iteration N+1 < N tool_calls` + better simulator.

## Where to Ask

- Kernel/sim isolation, lineage, docs freshness → check `report_freshness_tool` / `report_schema_check_tool` first (via `develop_validate`).
- Never hand-edit `data/topics/*/graph.json` (derived view).


