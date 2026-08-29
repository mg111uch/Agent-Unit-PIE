# Kernel Integration — Usage Manual

How topic graphs are stored, how contradiction detection works through the
kernel, and how to verify each piece from the command line.

_Last verified: 2026-08-29 (smoke-tested 9/9; per-sim lineage, validity, version-aware retrieval live)_

## Architecture

```
writers                              canonical store              readers
scripts/topic_ops.py  ─┐                                   ┌─ debate loop (loop.py)
scripts/record_removal ┼──► kernel semantic_memory ────────┤─ GET /api/graph
engine/expand.py      ─┘    (SQLite: data/kernel.db,       └─ scripts/topic_ops.py list
                             generic_memory +               ┌─ retrieval_engine (per-sim)
                             simulation_versions/runs)      └─ semantic_retriever (per-sim)
                                            │
                                            ▼ every mutation regenerates
                       data/topics/<topic>/graph.json  ← DERIVED VIEW ONLY
                               topics per-sim: popu_sim (popula_dyn), sim_eco_sim …
```

- **Single persistence path**: everything goes through
  `codebase/modules/argu_god/engine/topic_store.py`, which wraps
  `kernel.memory.semantic_memory` (SQLite via `memory_engine`); lineage via `kernel/simulation_version.py`.
- **`graph.json` is generated**. Never hand-edit it and never read it as a
  source of truth — it is overwritten on the next mutation.
- Topics are rows partitioned by `topic_id`; per-simulator isolation: `kernel/simulator_registry.py` discovers `simulators/*` → `popula_dyn→popu_sim`.
- **Lineage tables**: `simulation_versions(version_id=sim@commit, simulator, parent, affected_concepts)` + `simulation_runs(version_id, simulator)`; `sync_from_git(sim)` uses `git log -- simulators/<sim>` (scoped).
- **Sharded FS**: `units/simulations/{sim}/{run}` (+ `data/memory/episodic/{sim}_{run}.json` immutable).
- **Validity**: `kernel/validity.py` `ACTIVE→HISTORICAL` per-sim concept-level (`is_compatible` lineage).
- **Retrieval filtering**: default `include_historical=False` + `simulator` + version compatibility.

## Prerequisites

All commands run in the project conda env from the workspace root:

```bash
conda run -n myenv python scripts/topic_ops.py ...
```

> Gotcha: `conda run` does not forward stdin. Use `-c "..."` or write a
> script file — heredocs (`python - <<EOF`) silently produce no output.

## Contradiction quickstart (CLI path)

Detection rule: a `contradicts` edge raises a flag **only when both endpoint
nodes hold stance `"agree"` in `data/mindmaps/local_user/belief_state.json`** (and are version-compatible, same simulator, not `HISTORICAL`).
Adding nodes alone never triggers anything. Cross-simulator findings never contradict (strict isolation).

```bash
# 1. Seed two claims in a topic (any topic name; creates it on first add)
conda run -n myenv python scripts/topic_ops.py add-node --topic demo \
  --name ClaimA --premise "A is true"
conda run -n myenv python scripts/topic_ops.py add-node --topic demo \
  --name ClaimB --premise "not A"

# 2. Mark both agreed (or reach this naturally by answering debate questions)
conda run -n myenv python scripts/topic_ops.py set-stance --topic demo --name ClaimA --stance agree
conda run -n myenv python scripts/topic_ops.py set-stance --topic demo --name ClaimB --stance agree

# 3a. Negative control — non-contradicting edge stays silent
conda run -n myenv python scripts/topic_ops.py add-edge --topic demo \
  --source ClaimA --target ClaimB --relation requires

# 3b. The contradicts edge fires detection
conda run -n myenv python scripts/topic_ops.py add-edge --topic demo \
  --source ClaimA --target ClaimB --relation contradicts
```

Expected output for 3b:

```
  edge_added   ClaimA
  CONTRADICTION: ClaimA <-> ClaimB  signal=contradiction_detected_5277fb775a3b
Recorded 1 change(s) in data/topics/demo/graph.json
```

With `--json`, the same run reports:

```json
{"graph":"...","dry_run":false,
 "changes":[{"kind":"edge_added","source":"ClaimA","target":"ClaimB"}],
 "contradictions":[["ClaimA","ClaimB"]],
 "signal_ids":["contradiction_detected_5277fb775a3b"]}
```

Exit codes: `0` success (contradictions are advisory flags, not failures),
`1` error (`Topic not found`, unknown endpoint node), `2` argument error
(e.g. relation outside `{contradicts, requires, supports}`).

## Verifying the kernel received the signal

Signals persist as objects with id prefix `contradiction_detected_`:

```bash
conda run -n myenv python scripts/topic_ops.py signals --json
conda run -n myenv python scripts/topic_ops.py signals
# also via health check:
conda run -n myenv python scripts/topic_ops.py doctor --json | jq .contradiction_signals
```

## Debate-loop check (same detector, CLI)

```bash
# Check contradictions without writing Python:
conda run -n myenv python scripts/topic_ops.py check --topic demo --claims ClaimA,ClaimB --json
# -> [["ClaimA","ClaimB"]] if contradicts edge exists and both stances are agree
conda run -n myenv python scripts/topic_ops.py doctor --json
# shows contradiction_signals count and per-topic parity
```

The `check` command wraps `topic_store.check_contradictions` (same detector the live debate loop uses) and `signals` wraps `memory_engine.list_objects("episodic")`. No Python imports needed.

## Backfill / migration

Import legacy `graph.json` content into the store once (idempotent):

```bash
conda run -n myenv python scripts/backfill_topics.py            # both topics
conda run -n myenv python scripts/backfill_topics.py my_topic   # one topic
```

Output reads like:

```
theism_atheism: json(n=12,e=24) -> store(n=12,e=24) OK
project_history: json(n=12,e=11) -> store(n=12,e=7) WARN (4 dangling edge(s) dropped)
```

`WARN ... dangling` means the legacy file referenced node names that never
existed; those edges cannot be represented in the canonical store and are
dropped from the regenerated view on purpose.

## Recording intentional removals

```bash
conda run -n myenv python scripts/record_removal.py --name N --premise P \
  [--evidence E]... [--source S]... [--contradicts T] [--dry-run] [--json]
```

Writes a `side=decision` node (+ optional `contradicts` edge) into
`project_history` through the same kernel pipeline; idempotent, and a
contradicts edge between two agreed beliefs emits the same signal.

## Autonomous contradiction gate (blocking on write)

For agents working without a user (simulation hypothesis loop), `belief_state.json` stance check is not usable. A pre-write **version-aware symbolic gate** (`kernel/hypothesis/contradiction_gate.py:67`, per-sim) blocks contradicting claims before they enter `semantic_memory` (cross-sim and `HISTORICAL`/incompatible versions never block):

```bash
# Agent proposes a claim that contradicts an existing one in same topic
conda run -n myenv python scripts/topic_ops.py add-node --topic theism_atheism \
  --name "Moral Argument Rebuttal" --premise "Objective moral values do not exist, not from God"
# -> BLOCKED: New claim contradicts existing claim. Resolve prior claim or re-run with force=True
#    conflicts: [{Moral Argument, similarity 0.67, contradicts edges}]
#    Recorded 0 change(s) — no write, no graph.json regeneration

# Only after user approval:
conda run -n myenv python scripts/topic_ops.py add-node --topic theism_atheism \
  --name "Moral Argument Rebuttal" --premise "..." --force
# -> node_added (requires explicit user approval)
```

Same for simulation hypotheses via `kernel/hypothesis/hypothesis_engine.py:create_hypothesis(..., force=False)` → returns `{"blocked":True,"conflicts":[...]}` until `force=True`. Prior hypothesis state (`supported/rejected` via `add_contradicting_evidence` + `validate_hypothesis` + `export_to_semantic_memory`) is what the second agent checks cross-session.

## How similarity is checked

Gate logic lives in `codebase/kernel/hypothesis/contradiction_gate.py:67`:

- **Symbolic tier** (observations, per-sim): `_symbolic_contradicts` on typed `observation` (`metric, outcome INCREASE vs DECREASE, baseline, horizon`) — embeddings only retrieve candidates, never decide. Guarded by `_compatible_for_contradiction` (same `simulator`, `ACTIVE`, `is_compatible(version)`).
- **Token Jaccard** on title/premise (`set(lower().split())` overlap) + **negation heuristic** (`not`/`no`/`never`/`fail` XOR) for hypotheses/interpretations. Thresholds: `sim>0.3` with opposite polarity, or `title_sim>0.8`, flags `blocked_contradiction`.
- **Per-sim strict isolation**: two findings from different simulators or incompatible Git lineage never contradict, even with opposite outcomes.
- **Not vector embeddings.** `codebase/modules/argu_god/engine/vector_store.py:1-46` does provide ChromaDB + `all-MiniLM-L6-v2` embeddings (`embed()`/`search_similar()`) for semantic retrieval/duplicate detection (`dedup.py`), but the autonomous gate does **not** call it today to avoid model load/latency.

## Simulation lineage & per-sim isolation

- **Registry**: `kernel/simulator_registry.py` discovers `simulators/*` (e.g., `popula_dyn→popu_sim`). Strict isolation: findings, versions, lineage, retrieval per simulator.
- **Git-backed lineage**: `kernel/git_version.py:81` `sim_commit(sim)` = last commit touching `simulators/<sim>`; `diff_sim_files(sim)` scoped. `kernel/simulation_version.py:sync_from_git(sim)` → `sim@commit` (`parent, branch, affected_concepts` via `MODULE_CONCEPTS`). Non-sim commits (e.g., `virtual_silicon`) don't bump `popula_dyn`.
- **Sharded runs**: `SimulationConnector(simulator)` writes `units/simulations/{sim}/{run}` + `data/memory/episodic/{sim}_{run}.json` + `simulation_runs` row (per-sim). Legacy `units/simulations/run_*` auto-migrated on first `popula_dyn` init.
- **Validity scope**: `kernel/validity.py:mark_stale_findings(sim, new_version)` concept-level (`affected_by`): `reproduction` change → population findings `HISTORICAL` (`invalidated_by`), `terrain` leaves them `ACTIVE`. `eco_sim` untouched.
- **Version-aware retrieval**: `retrieval_engine.search(..., simulator, include_historical=False)` + `semantic_retriever.search_by_concept` filter `simulator` + `HISTORICAL` + `is_compatible`. `build_context(..., simulator)` per-sim.
- **Compression**: `kernel/compression_engine.py:147` groups `ACTIVE` findings per `(simulator, outcome, horizon)` → `consolidated_{sim}_{outcome}` node (keeps `episodic` raw immutable).

## CLI reference

| Command | Flags | Notes |
|---|---|---|
| `add-node` | `--topic --name --premise [--side decision\|argument\|pro\|con\|neutral] [--source]... [--confidence F] [--type observation\|argument] [--metadata JSON] [--force]` | idempotent by node name; per-sim `observation` with `metadata={observation:{simulator,version_id,outcome}, validity:{status}}`; without `--force` blocks if `contradiction_gate` finds symbolic/version-aware conflict |
| `add-edge` | `--topic --source --target --relation {contradicts,requires,supports} [--force]` | idempotent triple; detection on `contradicts` |
| `set-stance` | `--topic --name --stance {agree,disagree,neutral} [--confidence F]` | records stance in `belief_state.json` for contradiction detection |
| `check` | `--topic --claims A,B [--json]` | CLI wrapper for `check_contradictions`; same detector as debate loop |
| `signals` | `[--json]` | lists `contradiction_detected_*` ids from episodic memory |
| `list` | `--topic [--side S] [--json]` | serves from kernel memory |
| `topics` | `[--json]` | distinct topic ids known to the kernel |
| `doctor` | `[--json]` | health, parity, signal count |

Global: `--dry-run` (no writes), `--json`, `--quiet/-q` — position before or
after the subcommand both work.

## Troubleshooting

| Symptom | Cause / fix |
|---|---|
| `error: Topic not found: X` | Topic has no nodes yet or name typo; create it with `add-node`. Exit 1. |
| `invalid choice: 'related'` | Fixed vocabulary `{contradicts, requires, supports}` for new edges. Legacy relations survive inside backfilled data only. |
| Detection didn't fire | Both endpoints must be exactly `"agree"` in belief_state; check titles match node names; edge must be `contradicts` and newly *added* (re-adding an existing triple is skipped). |
| `blocked_contradiction` on add-node | Autonomous gate flagged similarity+negation (`contradiction_gate.py`); resolve prior node via `set-stance`/`record_removal` or re-run with `--force` after user approval. No write occurred. |
| Heredoc prints nothing | `conda run` swallows stdin — use `-c` or a script file. |
| `graph.json` looks stale/differs | It's derived; any mutation regenerates it. To force: re-run `backfill_topics.py <topic>` (idempotent). |
