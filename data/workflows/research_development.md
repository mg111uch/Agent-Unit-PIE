# Research Development — Unified Loop (Phase 8 Complete)

Parent orchestrator for `kernel_ops.json` + `popu_sim_dev.json` (subgraphs). LLM thinks *inside* workflow; `codebase/development/workflow_engine.py` enforces allowed transitions, preconditions, required outputs, recovery. Phase 7 added `DevelopmentState` (<2KB) + 9 `develop.*` primitives; Phase 8 adds `validation_gate L0-L6` + `eval_harness` (conformance/recovery/adversarial/workflow-evolution/research_loop). Single persistence path: `data/kernel.db` (SQLite) via `kernel_db` — `workflow_states` per-simulator + `hypotheses`/`semantic_nodes` hydrated on `develop_tools._ensure_paths` so fresh agents resume without handover Steps duplication.

## Start

Resumes persisted state if exists (no duplication in HANDOVER.md).

```python
from codebase.development.workflow_engine import workflow_engine  # loads workflow_states from data/kernel.db
workflow_engine.status()  # {current: start|version_sync|decide_branch, allowed: [...] }
# Fresh agent after crash: hydrate() in develop_tools._ensure_paths auto-loads semantic_memory + hypotheses from DB
```

## Orient

Retrieve per-sim ACTIVE knowledge + git state (hydrated from DB). Generates `DevelopmentState` preface for every turn.

```python
from development.develop_tools import develop_orient, develop_state
from development.development_state import generate_state

# High-level (preferred, <2KB state):
develop_orient({"query": "population", "simulator": "popula_dyn", "limit": 5})
# → {context: {hits: [...]}, state: {sim, git, sim_commit, sim_version, aff_concepts, wf_ver, wf_node, allowed, hyps, gaps, runs}, allowed: ["hypothesis"]}

# Direct (legacy):
# kernel_retrieve(query, simulator), git: sync_from_git(sim)
develop_state({"simulator": "popula_dyn"})  # {state, text: "CURRENT STATE sim=... ALLOWED: ..."}
generate_state("popula_dyn")["_bytes"]  # <1900
```

Success: `context_found` → `version_sync`. Failure: `kernel_unavailable` → retry. `workflow_engine` moves `start/loop→orient→version_sync` automatically.

## Version Sync

`sync_from_git(sim)` → `sim@commit` with ontology-aware `affected_concepts`. Legacy `V1_*` compatible.

## Hypothesis

Form `WORLD|MODEL|DEVELOPMENT` hypothesis (`hypothesis_id`) — keeps `popula_dyn` as lab, not PIE ontology (`FixesIssues #2/#3`). Use `world_hypothesis` (what is true), `model_hypothesis` (sim deficiency), `code/workflow/kernel_hypothesis` (PIE change).

```python
# via hypothesis_engine (category distinguishes epistemic level):
# world_hypothesis / model_hypothesis / workflow_hypothesis / kernel_hypothesis
```

Failure `no_gap` → re-orient with broader query.

## Decide Branch

Deterministic branch (FixesIssues #3 + paradigm search):

```
param uncertainty? → experiment (L1-L2)
wrong abstraction? → propose_architecture → modify_code (leap, ARCHITECTURE hypothesis)
model/code deficiency? → modify_code → sim path (L3)
kernel/workflow deficiency? → modify_code → workflow L4 / kernel L5-L6
```

Leap gate: `develop_propose_architecture({hypothesis_id, leap_proposal≥20 chars})` advances `decide_branch→propose_architecture→modify_code`. Use for stock family jumps (rules→factors→ML→deep) and popula epoch jumps (behaviours→macro→epoch engine).

Outputs `branch`. Next is `experiment` or `modify_code`. `validation_gate.required_level(path)` maps `simulators/*→3`, `data/workflows→4`, `kernel→6`; ceiling `DEFAULT_CEILING=3` (sim autonomous, L4+ gated, L5-6 human approval).

## Experiment

Parameter-only run (L1-L2). Preferred via `develop_experiment`; legacy via `SimulationConnector`.

```python
from development.develop_tools import develop_experiment  # uniform: run_basic baseline, run_policy_<param><value> e.g. birth05 for 0.05
develop_experiment({"run_id": "run_policy_birth05", "params": {"birth_rate": 0.05}, "simulator": "popula_dyn", "baseline_run_id": "run_basic"})
# → {status: "completed", run_id, finding, summary, register}
# auto-persist: simulation_runs + data/memory/episodic/{sim}_{run}.json + register_to_kernel (validity ACTIVE)
# baseline params inherited so all policy runs share 50/50; advances decide_branch→experiment→update_knowledge when allowed
```

Failures `sim_crash|invalid_params|contradiction` → recovery node (eval_harness `recovery` verifies graceful Error strings).

## Modify Code (Gated L3/L4/L6 — Phase 8)

Edit simulator/kernel/workflow files; gate enforced before write. Outputs `commit`. Success `tests_pass` → `validate`.

```python
from development.develop_tools import develop_modify_simulator, develop_modify_workflow, develop_modify_kernel, develop_hypothesis
from development.validation_gate import gate  # check before edit

gate(3, "codebase/modules/simulators/popula_dyn/behaviours/reproduce.py")  # L3 sim → ALLOW
gate(1, "data/workflows/research_development.json")  # → GATE (needs L4)

# L3 sim (autonomous, ceiling):
develop_modify_simulator({"path": "codebase/modules/simulators/popula_dyn/behaviours/reproduce.py", "old_string": "x=1", "new_string": "x=2"})
# Hypothesis (Phase E):
develop_hypothesis({"hypothesis_id":"hyp_new","title":"MODEL: ...","type":"MODEL"})  # hypothesis→decide_branch
# L4 workflow (needs contracts+workflow_conformance+sim_smoke):
develop_modify_workflow({"path": "data/workflows/research_development.json", "old_string": "\"id\":\"tmp\"", "new_string": "\"id\":\"tmp2\""})
# L6 kernel (human gate):
develop_modify_kernel({"path": "codebase/kernel/retrieval/retrieval_engine.py", "old_string": "class Foo", "new_string": "class Foo2", "human_approved": True})
# without human_approved → Error: kernel modify requires human_approved=true
```

Levels: `L0 suggest / L1 edit+test / L2 edit+test+commit / L3 sim_modify / L4 workflow_modify / L5 kernel_propose / L6 kernel_modify` (needs: contracts, sim_smoke, lineage, retrieval, workflow_conformance, human_approval). Default ceiling `L3` — L4 gated, L5-6 human.

## Update Knowledge

`contradiction_gate` (per-sim version-aware) + `pattern_detect` + `compress_observations` (materialized view recompute). Outputs `knowledge_updated`.

```python
from development.develop_tools import develop_analyze  # run_id must be uniform run_policy_*
develop_analyze({"run_id": "run_policy_birth05", "simulator": "popula_dyn"})
# → {run_id, signals: [...], compress: {consolidated_groups: 1}, allowed: ["evaluate"]}
# advances update_knowledge→evaluate
```

## Evaluate

`Did model/kernel need improvement?` → if yes to `validate`, else back to `hypothesis` for next question.

## Validate (Phase 8 Gate)

Graduated `L0-L6`: tests, smoke, lineage `is_compatible`, regression, retrieval `HISTORICAL` filter, workflow conformance.

```python
from development.develop_tools import develop_validate
from development.validation_gate import gate
from development.eval_harness import run_all

develop_validate({"simulator": "popula_dyn"})  # sync_from_git + get_current_version + validate→loop
gate(4, "data/workflows/research_development.json")  # check before workflow edit
run_all()  # 5/5: workflow_conformance / recovery / adversarial_lineage / workflow_evolution / research_loop
# python -c "import sys; sys.path.insert(0,'codebase'); import development.eval_harness; print(development.eval_harness.run_all())"
```

Success `validation_pass` → `loop`. Failure `validation_fail` → fix and re-validate (kernel `L6` stays gated until `human_approved`).

## Loop

Gated self-improvement commit (OBSERVATION→PROBLEM→PROPOSED CHANGE→TEST→MEASURE→COMMIT→RECORD, FixesIssues #5). `continue` → `orient` (re-sync), `stop` → terminal. Benchmark: `develop.*` reduces tool surface `10.8k→~2KB`; harness measures `iteration N+1 < N tool_calls` + better simulator.

```python
from development.develop_tools import develop_commit
develop_commit({"message": "Phase 8: gate L3 sim edit, validated", "add_all": True})
# advances loop→orient on success
```

## Post Commit

Handover pointer only — no history duplication. Hydrates `data/kernel.db` via `development_state.generate_state` + `kernel/retrieval/retrieval_engine.search` to emit `next_query` for `HANDOVER.md` bottom task. Previous iteration results fetched from kernel memory, not copied. `HANDOVER.md` task = `develop_orient({"query":next_query,"simulator":"popula_dyn"})`.

```python
from development.development_state import generate_state
generate_state("popula_dyn")  # hydrated loop→post_commit→orient
```

## Stop

`doctor --json` + `list --topic`. Render via `data/workflows/workflow_graph.html?graph=research_development.json` (now handles both legacy array and dict nodes).

## Validation Gate & Eval Harness (Phase 8)

- **Gate:** `codebase/development/validation_gate.py` (`DEFAULT_CEILING=3`, `required_level(path)`, `gate(level,path,human_approved)`). Needs per level: `contracts` (validate_workflow), `sim_smoke` (get_current_version), `lineage` (adversarial_mini), `retrieval` (HISTORICAL filter), `workflow_conformance` (conformance_mini), `human_approval` (L5-6).
- **Harness:** `codebase/development/eval_harness.py` `run_all()` — 5 tests: `workflow_conformance` (legal path + illegal `start→experiment` blocked), `recovery` (missing params → Error), `adversarial_lineage` (5 invariants), `workflow_evolution` (detect inefficiency), `research_loop` (state budget). Extend for `FixesIssues #9` self-improvement benchmark (repeat same task from clean context, measure `iterations_to_solution`, `workflow_violations`).

Contracts: every node `{id,goal,inputs,preconditions,actions,outputs,success,failure,next,mdRef,subgraph}` validated by `development/contracts.py` (`validate_workflow` supports legacy array + dict).
