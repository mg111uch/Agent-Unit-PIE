# Agent Runtime (Level 1) — how the PIE agent works

> Reconstructed from the module docs before `AGENTS.md` and `codebase/prompt_fragments/` were supplied; where a fact is inferred it is tagged `[INFERRED]`. Master doc: `00_README_master.md`.

## 1. Orchestrator in one paragraph

A tool-driven LLM agent loop (`Observe → Execute → Learn → Store → Evolve`) served by `server.py` (conda env `myenv`), reached from the browser `/agent` page over WebSocket. `ws_handler.py` routes user input (plain chat or slash commands) into the **shared loop** `run_agent_turn()` (common parsing, failure breaker, streaming); `engine.py` yields events (including `question` events that pause the loop for a human answer). Tools are grouped by category; deterministic engines enforce state transitions while the LLM supplies reasoning. Persistent memory is structured markdown/JSON + the kernel; file-size limits are enforced and `..` path traversal is blocked.

**Design philosophy (consistent across docs):** *the LLM thinks inside a workflow; the engine enforces transitions, validation and persistence.* The tool surface is deliberately small (e.g., 9 `develop.*` tools replace shell incantations like `conda run … topic_ops.py`).

## 2. Slash commands

| Command | Behavior |
|---|---|
| `/argu explore <topic>` | debate-moderator mode: LLM calls the `debate_step` tool once per iteration; user answers 3 options + custom; see `debate_argu/README.md` |
| `/auto "<research question>"` | goal-autonomous research via the shared loop; no hard kernel dependency; findings to kernel memory if available; max iterations default 5 |

## 3. Tool families (named in docs)

| Family | Tools / notes |
|---|---|
| Debate | `debate_step` (composite, two-phase prepare/wait; shares `question_ops._pending`) |
| Questions | `question_ops` (`_pending`, `resolve_all_questions`, `cancel_questions`) |
| Kernel | `kernel_retrieve`, `kernel_emit_dev_change`, `kernel_reload`, `hot_reload`, `list_capabilities`, `report_inventory`, `validate_capabilities`, `report_schema_check_tool`, `search_semantic_memory`, `get_neighbors` |
| Development (`CAT_DEVELOP`) | `develop_state`, `develop_orient`, `develop_hypothesis`, `develop_experiment`, `develop_analyze`, `develop_modify_simulator`, `develop_modify_workflow`, `develop_modify_kernel`, `develop_validate`, `develop_commit`; `develop_propose_architecture` (paradigm-search gate) |
| Files/shell | read/write/edit with size limits; shell [INFERRED] |
| Simulation | `SimulationConnector` (`run_and_extract`, `compare_runs`, `inject_policy`, `get_signals`, `list_runs`) |
| Economy / FireFlow | scoring/outreach/revenue job CLIs and HTTP pushes — **no single compressed `economic_*` toolset documented** (INT-05) |

## 4. Workflows (engine-enforced)

| Workflow | Shape | Notes |
|---|---|---|
| `research_development` (unified) | `start→orient→version_sync→hypothesis→decide_branch→{experiment, modify_code}→update_knowledge→evaluate→validate→loop→stop`; meta `subgraphs:[kernel_ops, popu_sim_dev]`; `economic_loop` wired in as a subgraph | `workflow_engine.allowed()/advance(target, produced, success)` enforces allowed edges + success + outputs; prevents `start→experiment` skip; contract validates `id, goal, outputs, success, next` (+ legacy array compat) |
| `kernel_ops` | agent operating loop for kernel work | per-node reference in `kernel_ops.md` |
| `popu_sim_dev` | simulator development | |
| `economic_loop` | observe→discover→estimate→simulate→rank→task→execute→collect→reconcile→twin→learn→scale/abandon/pivot | 12 nodes |
`workflow_graph.html` renders the graphs (handles legacy array + dict contract nodes: `goal/shape/color/mdRef`).

## 5. Autonomy & validation

- **Graduated Autonomy Gate** (`validation_gate`): L0 suggest · L1 edit+test · L2 edit+test+commit · L3 sim_modify · L4 workflow_modify · L5 kernel_propose · L6 kernel_modify. `DEFAULT_CEILING=3` (simulators autonomous); L4+ gated; L5–L6 human approval. `required_level(path)`: `simulators/*→3`, `data/workflows→4`, `kernel→6`. `gate(level, path, human_approved)` runs `contracts, sim_smoke, lineage, retrieval, workflow_conformance, human_approval`; blocks `L3 kernel`, `L1 workflow`, `L6 without approval`.
- **Eval harness** (`run_all()`): workflow_conformance, recovery (missing params → Error), adversarial_lineage (5 invariants: V1 stale/partial/unrelated/no-contradiction/same-version), workflow_evolution (added node still validates), research_loop (`_bytes<2000`).
- **DevelopmentState** (`generate_state(sim)`, <1.9 KB) is what the agent sees each turn: sim, git, sim_commit, sim_version, affected concepts, workflow version/node/allowed edges, hypotheses, gaps, recent runs.
[SUGGESTION STR-05 · P1] Write one **Autonomy Charter** unifying the dev gate (L0–L6) and economic authorization (authorize/deny/needs-approval, spend caps, ledger approval): one vocabulary, one table of "who may do what without a human". [/SUGGESTION]

## 6. Prompt assembly & orientation

Server-assembled prompts inject fragments in `FRAGMENT_ORDER`: `kernel_playbook.md` (rules) and `onboarding.md` (cheap-orientation order: `project_history`, `list_capabilities`/`report_inventory`, reports — avoid full-report reads). Bypass of indexed files is monitored by `detect_tool_bypass.py`.

## 7. Scripts (operator CLI)

`topic_ops.py` · `backfill_topics.py` · `record_removal.py` · `emit_dev_change.py` · `link_gap_blockers.py` · `render_status.py` · `render_recent_changes.py` · `render_index.py` · `prune_kernel_logs.py` · `smoke_kernel.py` · `detect_tool_bypass.py` (details in `kernel/README.md` §2, §6). Smoke harness `smoke_kernel.py` last passed 9/9 (2026-08-29 per manual).

## 8. Known limitations

- Original limits listed "No parallel execution, basic contradiction logic, limited reasoning depth" — partially outdated (contradiction gate is now symbolic + version-aware; debate blocks on a per-session `threading.Event`).
- One SQLite kernel file for all writers (KRN-04). Hot-reload convenient in dev; disable in prod (OPS-02).
- No documented scheduler for unattended economic jobs (discovery → outreach drafting → delivery) ❓.
- LLM provider/model, token budgets and cost logging are not documented (OPS-07). The broken legacy `llm_compiler` shows an earlier Gemini file-based pipeline.

[SUGGESTION OPS-07 · P1] Per-loop token/₹ budget; log model cost per task so unit economics include AI cost. [/SUGGESTION]
[SUGGESTION OPS-02 · P1] CI for all suites (kernel smoke, popula smoke, eval harness, backend jest incl. drift/contract); disable hot-reload outside dev. [/SUGGESTION]
[SUGGESTION INT-05 · P1] Add a ≤15-tool `economic_*` surface mapped to the gateway. [/SUGGESTION]
[VERIFY OPS-07] Which LLM(s) does the loop use and what is the average cost of an `/auto` run? [/VERIFY]
[VERIFY INT-01] Is there a scheduler/daemon that runs discovery/outreach/delivery jobs unattended? [/VERIFY]
