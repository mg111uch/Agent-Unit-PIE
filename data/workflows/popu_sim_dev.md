# Popu Sim Dev — Workflow Reference

Self-sustaining simulation development loop. Agents orient via kernel,
find parameter gaps, propose policies with structured premises,
detect contradictions, run simulations, and auto-register findings.

## Start

Entry point. Initialize context for popu_sim topic.

```bash
conda run -n myenv python scripts/topic_ops.py topics --json
conda run -n myenv python scripts/topic_ops.py list --topic popu_sim --json
ls codebase/units/simulations/
```

## Orient (Kernel Retrieve)

Retrieve prior **ACTIVE** findings per-simulator (strict isolation) to understand what has been tested.

```bash
conda run -n myenv python -c "
import sys; sys.path.insert(0,'codebase'); sys.path.insert(0,'codebase/modules')
from kernel.retrieval.retrieval_engine import retrieval_engine
print(retrieval_engine.search_semantic_memory('population', simulator='popula_dyn', include_historical=False))
"
# or via CLI (includes only ACTIVE for that sim):
conda run -n myenv python scripts/topic_ops.py list --topic popu_sim --json | python3 -m json.tool
```

Key questions (filtered `simulator=popula_dyn`, `HISTORICAL` hidden):
- What policies have been tested for this simulator?
- Which outcomes were IMPROVED vs DEGRADED vs COLLAPSED (current version only)?
- What interpretations were drawn?

## Version Sync

Per-simulator Git lineage — prevents `virtual_silicon` commits from bumping `popula_dyn`:

```bash
conda run -n myenv python -c "from kernel.simulation_version import sync_from_git; print(sync_from_git('popula_dyn'))"
# → popula_dyn@1a7d783  (last commit touching simulators/popula_dyn)
# eco_sim@V1_0c8137 stays separate
```

If `diff -- simulators/popula_dyn` empty, no new version — no sprawl.

## Find Gaps (Parameter Analysis)

Find untested parameter ranges to identify promising next experiments.

```bash
conda run -n myenv python scripts/find_untested_parameters.py --topic popu_sim --suggest
```

This outputs:
- Tested parameter values
- Gaps in numeric ranges
- Suggested next parameters to test

## Propose Policy

Draft a new policy with structured premise format for contradiction detection.

```bash
# Policy naming: {run_id_prefix} Policy: {param} {old}->{new}
# Example: run_next Policy: birth_rate 0.04->0.05

# Structured premise format (contradiction-friendly):
# Verdict: {IMPROVED|DEGRADED|STABLE|COLLAPSED}
# Claim: {metric} will {improve|degrade|stabilize}
# Justification: {why based on prior findings}
```

Example:
```bash
# Proposed: birth_rate 0.05 (gap between 0.04 and 0.06)
--name "run_next Policy: birth_rate 0.04->0.05"
--premise "Verdict: POLICY_CANDIDATE
Claim: Population will IMPROVE (vs run_basic 5->8 with birth_rate 0.06)
Justification: birth_rate 0.06 worked (IMPROVED); 0.05 is between 0.04(failed) and 0.06(worked), likely to show similar or better results"
```

## Check Contradiction

Dry-run node creation to detect contradictions before committing.

```bash
conda run -n myenv python scripts/topic_ops.py add-node --dry-run --json --topic popu_sim \
  --name "run_next Policy: birth_rate 0.04->0.05" \
  --premise "Verdict: POLICY_CANDIDATE..."
```

If blocked_contradiction: see ## Blocked
If success: proceed to ## Agree

## Blocked

Policy contradicts an existing claim. Options:
1. Refine the policy (different parameter or value)
2. Rephrase the premise to avoid contradiction
3. `record_removal.py` or `set-stance disagree` on conflicting prior claim

```bash
# Check what contradicted
conda run -n myenv python scripts/topic_ops.py check --topic popu_sim \
  --claims "run_next Policy: birth_rate 0.04->0.05,run_policy_birth06 Findings" --json
```

## Agree

Mark policy as agreed (required for contradiction edge detection).

```bash
# Add policy node
conda run -n myenv python scripts/topic_ops.py add-node --topic popu_sim \
  --name "run_next Policy: birth_rate 0.04->0.05" \
  --premise "Verdict: POLICY_CANDIDATE..." --json

# Set stance to agree
conda run -n myenv python scripts/topic_ops.py set-stance --topic popu_sim \
  --name "run_next Policy: birth_rate 0.04->0.05" --stance agree --json
```

## Implement (Run Simulation)

Run simulation **per-simulator, sharded** (`units/simulations/{sim}/{run}`) using `SimulationConnector(simulator=...)`.

```bash
conda run -n myenv python -c "
import sys; sys.path.insert(0,'codebase')
from modules.simulators.simulation_connector import SimulationConnector
conn = SimulationConnector(simulator='popula_dyn')
result = conn.inject_policy('run_basic', {'birth_rate': 0.05}, 'run_next')
print(result)
# → writes codebase/units/simulations/popula_dyn/run_next/ + data/memory/episodic/popula_dyn_run_next.json
"
```

## Lineage Persist

`_store_run()` automatically persists per-sim lineage (Phase 1):

```bash
# DB: simulation_runs (simulator, version_id=sim@commit, params, result)
# Episodic: data/memory/episodic/{sim}_{run}.json + kernel episodic_memory
# Topic: popu_sim for popula_dyn, sim_eco_sim for others (strict isolation)
ls codebase/units/simulations/popula_dyn/
ls data/memory/episodic/
conda run -n myenv python -c "from kernel.persistence.db import kernel_db; print(kernel_db.load_simulation_run('run_next'))"
```

## Auto-Register Findings

Automatically register findings **per-sim topic + validity ACTIVE** (strict isolation).

```bash
conda run -n myenv python -c "
import sys; sys.path.insert(0,'codebase')
from modules.simulators.simulation_connector import SimulationConnector
conn = SimulationConnector(simulator='popula_dyn')
premise = conn.generate_structured_premise('run_next', 'run_basic')
print(premise)
result = conn.register_to_kernel('run_next', premise, 'run_basic')
print(result)  # → metadata.observation={simulator, version_id: popula_dyn@1a7d783, validity: {valid_for_version, status: ACTIVE}}
"
```

## Validity Scope

New `popula_dyn` code version with `affected_concepts=[reproduction]` automatically marks old `popula_dyn` findings with matching concepts as `HISTORICAL` (concept-level, not whole-version). `terrain` change leaves `population` findings `ACTIVE`.

```bash
conda run -n myenv python -c "from kernel.validity import active_findings; print(len(active_findings('popula_dyn')))"
# eco_sim findings unaffected — strict per-sim isolation
```

## Add Contradicts Edge

Decision: Does the new finding contradict any prior **ACTIVE, same-simulator, version-compatible** findings? (HISTORICAL and cross-sim excluded via `contradiction_gate: _compatible_for_contradiction`)

```bash
# Auto-created by register_to_kernel via symbolic gate; manual check:
conda run -n myenv python -c "
from kernel.hypothesis.contradiction_gate import check_topic_contradiction
print(check_topic_contradiction('popu_sim', 'run_next Findings', 'Status: IMPROVED...', {'observation':{'simulator':'popula_dyn','version_id':'popula_dyn@1a7d783'}}))
"
# If contradiction found, add edge:
conda run -n myenv python scripts/topic_ops.py add-edge --topic popu_sim \
  --source "run_next Findings" --target "run_policy_birth06 Findings" \
  --relation contradicts --json
# Cross-sim (popu vs eco) never contradicts — strict isolation
```

## Compress

Per-simulator consolidation (Phase 4): keep episodic raw, consolidate semantic per `(simulator, outcome, horizon)`:

```bash
conda run -n myenv python -c "from kernel.compression_engine import CompressionEngine; print(CompressionEngine().compress_observations())"
# → consolidated_popula_dyn_IMPROVED_5 (n=3, avg +60%) — eco_sim untouched
```

## Loop

Check iterations count.

```bash
echo "iteration $i / MAX"
# if i < MAX -> goto ## Orient (re-syncs per-sim version)
# else -> goto ## Stop
```

## Stop

Terminal. Verify final state.

```bash
conda run -n myenv python scripts/topic_ops.py doctor --json
conda run -n myenv python scripts/topic_ops.py list --topic popu_sim --json
ls -R codebase/units/simulations/
```
