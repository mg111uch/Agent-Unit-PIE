# Kernel Ops — Workflow Reference

Operational companion to `kernel_ops.json` (each node may link here via its
`mdRef`). Deep-dive manual: `system_devpt_reports/kernel/usage.md`.
All commands run from the workspace root in conda env `myenv`.

## Orient Before Exploring

Before reading code or reports for a new task area, recall prior knowledge **per-simulator** (strict isolation):

```
kernel_retrieve(input_data={"query": "<keywords>", "simulator": "popula_dyn"})
# or via retrieval_engine: retrieval_engine.search(query, simulator="popula_dyn", include_historical=False)
```

Only `ACTIVE` findings for that simulator are returned (HISTORICAL filtered). Use `include_historical=True` for audit. If kernel unavailable, proceed normally — never claim a memory operation succeeded when it did not.

## Version Sync

Per-simulator Git lineage (Phase 0 refactor):

```bash
conda run -n myenv python -c "from kernel.simulation_version import sync_from_git; print(sync_from_git('popula_dyn'))"
# git log --oneline -- codebase/modules/simulators/<sim>  → sim@commit
```

`sync_from_git(sim)` is idempotent, creates `simulation_versions` row `sim@commit` with `parent, branch, affected_concepts`. If `diff -- <sim>` empty (e.g., `virtual_silicon` change), **no new version** for `popula_dyn` — prevents sprawl. Legacy `V1_*` rows remain `V*` compatible via `is_compatible()`.

## Apply Prior Decisions

Retrieved context often points at intentional removals. Before re-adding
"missing" code, check the removal rationale log:

```bash
conda run -n myenv python scripts/topic_ops.py list \
  --topic project_history --side decision
```

Nodes carry `premise` (why it was removed) and `contradicts` edges link the
rationale. If your planned change collides with a decision on record, surface
it to the user instead of silently re-implementing.

## Store Context and Signals

After a non-obvious discovery, user decision, or architecture fact:

```
kernel_store_context(...)                     # reusable context, tagged
kernel_emit_signal(...)                       # notable events
```

Only store at importance ≥ 0.5 — do not spam memory every step. Future
sessions find it via `kernel_retrieve`.

## Topic Graphs CLI

All topic graph mutations go through kernel semantic memory; never hand-edit
`data/topics/<topic>/graph.json` (it is a regenerated view):

```bash
conda run -n myenv python scripts/topic_ops.py topics                 # list topics
conda run -n myenv python scripts/topic_ops.py add-node --topic T \
  --name N --premise P [--side decision]                              # create/append node
conda run -n myenv python scripts/topic_ops.py add-edge  --topic T \
  --source A --target B --relation {contradicts,requires,supports}    # append edge
conda run -n myenv python scripts/topic_ops.py list --topic T [--side S]
```

`add-node` bootstraps a new topic on first use; every other command errors
with exit 1 if the topic does not exist. Global flags: `--dry-run`, `--json`,
`--quiet/-q` (before or after the subcommand).

## Contradiction Signals

Adding a `contradicts` edge between two nodes whose stance is `"agree"` in
`data/mindmaps/local_user/belief_state.json` triggers kernel detection:

```
  edge_added   ClaimA
  CONTRADICTION: ClaimA <-> ClaimB  signal=contradiction_detected_<hex>
Recorded 1 change(s) in data/topics/T/graph.json
```

The flag is advisory: exit code stays 0. The signal persists as an
`episodic` object with id prefix `contradiction_detected_`. The debate loop
reports the same pairs in its response JSON (`"contradictions": [...]`).
Do not re-implement detection elsewhere — it is kernel-side by design.

## Compress Per-Sim

Per-simulator strict isolation: `compression_engine.py:147` groups `ACTIVE` findings by `(outcome, horizon)` per `sim_topic`, creates `consolidated_{sim}_{outcome}` node (keeps `episodic` raw runs immutable at `data/memory/episodic/{sim}_*.json` and `units/simulations/{sim}/`). `virtual_silicon` change → `popula_dyn` not compressed.

```bash
conda run -n myenv python -c "from kernel.compression_engine import CompressionEngine; print(CompressionEngine().compress_observations())"
# or via run_cycle: CompressionEngine().run_cycle()
```

## Workflow Learning

When an agent discovers a better workflow pattern or improves an existing workflow,
it should persist this learning so future agents benefit.

**Where to store workflow improvements:**

1. **Workflow JSON/MD files** (`data/workflows/<workflow_name>.json` and `.md`)
   - Update the graph nodes/edges to reflect improved flow
   - Update the markdown reference with better commands or explanations

2. **Simulation findings** should use structured premises (see `popu_sim_dev.md`):
   - Format: `Verdict: {IMPROVED|DEGRADED|STABLE|COLLAPSED}`
   - Enables contradiction detection via kernel

3. **Kernel memory** for cross-session learning:
   ```bash
   # Store workflow improvement as a decision
   conda run -n myenv python scripts/record_removal.py \
     --name "Workflow: improved orient step in popu_sim_dev" \
     --premise "Added gap analysis step before proposing policy" \
     --source "data/workflows/popu_sim_dev.json"
   ```

**Workflow self-improvement loop:**
- Agent runs workflow
- Agent identifies friction/optimization
- Agent updates workflow files (JSON + MD)
- Agent stores decision in kernel memory for audit trail

## Log Hygiene and Pruning

Kernel logging writes every INFO+ record to the `logs` table of
`data/kernel.db`. Hot-path object logs are DEBUG already; only meaningful
events accumulate now. When acting as maintenance agent (or after long
sessions), check the count:

```bash
conda run -n myenv python -c "
import sqlite3; print(sqlite3.connect('file:data/kernel.db?mode=ro',uri=True)
.execute('SELECT COUNT(*) FROM logs').fetchone()[0])"
```

If the count exceeds **200**, prune (keeps newest 200, idempotent below the
threshold):

```bash
conda run -n myenv python scripts/prune_kernel_logs.py --keep 200
# logs: <before> -> 200 rows (kept newest 200)
```

Open the DB read-only for checks (`file:...?mode=ro`) so you never corrupt
WAL state.
