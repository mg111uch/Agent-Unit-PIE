# Agent Core Roadmap
_Not verified. Never cite as working._

## Near-term
- Kernel-backed project memory across sessions (decisions, architecture facts)
- Simulation-in-the-loop for domain problems
- Belief/debate tools as first-class agent tools

## Later
- Signal → event → memory pipeline guidance in prompts
- Research mode that writes durable memories retrievable via MCP
- Multi-mode persona (coding/research/debate)

## Explicitly deferred
- Rewriting the Next app stack

## Suggestions:

- **Atomic multi-file changes** → this is the one genuine gap. Your `cross_file_edit`/`batch_edit` do per-file checkpoints, not a true all-or-nothing transaction across files. That's a legitimate place to borrow SQLite's ACID guarantees: wrap a multi-file edit's checkpoints in one transaction ID so `undo_last_edit` can roll back the whole group atomically, not file-by-file. That gets you the actual benefit you're after without moving code off disk. If the real itch is "atomic multi-file edits," extend the checkpoint/transaction grouping rather than relocating source code into SQLite.

----

# Plan: Agent_Unit_PIE 

## 1. Strategic goal: pluggable “agent core” without file_ops

### 1.1 Principle

Split into:

1. **Host platform** (your full product or Claude Code / Cursor / OpenCode / another agent): owns filesystem, shell, editor, UX, auth.
2. **PIE core runtime**: loop, parsing/native tools bridge, LLM orchestration (optional), prompts composer, events.
3. **Capability packs** (pluggable): `kernel`, `simulation`, `argu`, future packs—**not** `file_ops` when host already has them.
4. **File pack** (optional): only for your first-party agent.

Other agents should depend on **core + selected packs**, never be forced through your `read_file` / `edit_file` / `workspace.py`.

### 1.2 Target packaging (conceptual layers)

```
pie-sdk/
  pie.runtime          # AgentSession, event bus, step policies
  pie.tools            # ToolSpec, ToolRegistry, invocation, schemas
  pie.llm              # Provider protocol (optional; host may supply LLM)
  pie.kernel           # kernel_ops + memory hooks
  pie.simulation       # sim_ops
  pie.argu             # debate entrypoints
  pie.host.adapters    # Claude/OpenAI tools adapter, MCP, HTTP, in-process
  pie.file             # OPTIONAL file_ops + workspace (your product only)
  pie.prompts          # composable prompt sections by capability set
```

### 1.3 Contracts hosts implement (no code—interfaces only)

**A. Tool registry**

- Register tools by name with: description, JSON Schema, handler, category (`host` | `kernel` | `sim` | `meta`), risk level.
- Capability filter: `include=["kernel","sim"]`, `exclude=["file","shell"]`.

**B. Host filesystem / shell (when not using pie.file)**

Optional protocols hosts can implement *if* a pack needs workspace awareness without your tools:

- `resolve_path`, `read_text`, `write_text`, `list_dir`, `search` — **only if** you later write packs that need them.
- Prefer **never** requiring this for kernel/sim: those packs should not assume your `WORKSPACE_ROOT`.

**C. LLM channel**

Two modes:

1. **Embedded mode** (your server): PIE owns providers + loop.
2. **Delegated mode** (other coding agents): host LLM calls tools; host only imports **tool handlers + schemas** from PIE packs. No PIE agent loop required.

That second mode is how you become “pluggable to all coding agents.”

**D. Event / observability**

Stable event types (already close to yours): `status`, `tool_call`, `tool_result`, `final`, `error`, plus `usage`, `plan_update`. Hosts map these to their UIs.

### 1.4 Integration patterns for other agents

| Pattern | Who runs the loop | What they import | File ops |
|---------|-------------------|------------------|----------|
| **In-process Python tools** | Host agent loop | `pie.kernel` tools as callables + schemas | Host’s tools only |
| **MCP server** | Host MCP client | PIE exposes kernel/sim as MCP tools | Not exposed |
| **HTTP tool gateway** | Host HTTP tools | `POST /tools/kernel_retrieve` etc. | Disabled |
| **Full PIE runtime** | PIE loop | Runtime + packs | Host injects file tools *or* enables `pie.file` |

### 1.5 Tool surface for embedders (recommended default export)

**Always export (differentiator):**

- `kernel_retrieve`, `kernel_emit_signal`, `kernel_store_context`, `kernel_get_memory`, `kernel_create_event`
- `simulation_*` (if installed)
- ArguGod as a tool or slash capability, not as competing file tools

**Never export by default to third parties:**

- `read_file`, `list_files`, `write_to_file`, `edit_file`, `get_workspace_info`, `execute_command` (and future git/shell)

**Meta tools safe to export:**

- `todo_write` / plan (host-agnostic)
- `kernel` health / memory summary

### 1.6 Prompt composition for plugins

System prompt must be **assembled from sections**, not one monolithic file:

- `base_persona`
- `response_contract` (JSON vs native tools)
- `file_ops_section` — **only if** file pack enabled
- `kernel_section` — only if kernel pack enabled
- `sim_section` — only if sim pack enabled
- `host_tool_appendix` — generated from host tool list

Other coding agents that only load kernel tools get a short kernel prompt fragment, not your full coding agent prompt (which currently steers toward file tools they don’t have).

### 1.7 Versioning & stability

- Semantic version tool schemas (`kernel_retrieve@1`).
- Stable string results vs structured results: move to **structured tool results** internally (`ok`, `error_type`, `data`) and stringify for models only at the edge.
- Document a “host compliance” checklist: auth, timeouts, cancel, secrets redaction.

### 1.8 Migration path inside your monorepo

1. Introduce `ToolRegistry` used by `agent_loop` instead of bare `TOOLS` dict.
2. Split registration: `register_file_tools()`, `register_kernel_tools()`, `register_sim_tools()`.
3. Config flag: `AGENT_TOOL_PACKS=file,kernel,sim` (your app) vs embedder default `kernel,sim`.
4. Publish packages or a single package with extras: `pie[kernel]`, `pie[sim]`, `pie[file]`.
5. Ship **MCP** and **OpenAI tools JSON** exporters from the same registry (one source of truth).

---

## 2. Fix & improvement roadmap 

### Phase 5 — Differentiator depth (not generic parity)

#### Resume Notes (Phase 5 — Differentiator depth)

**Phase 0–4 complete.** Key context for the next session:

**Current architecture state:**
- `ToolRegistry` class with category filtering, middleware, MCP export, schema adaptation
- 27 tools in 5 categories (`file`, `kernel`, `sim`, `meta`, `git`), configurable via `AGENT_TOOL_PACKS`
- MCP server exposing kernel+sim tools, usable by Claude Code / Cursor via stdio
- Capability-aware prompt fragments in `codebase/prompt_fragments/` assembled by pack config
- Agent loop supports native function calling, multi-tool turns, message store, streaming, cancel
- Server: per-user workspace, sandbox shell, rate limits, audit log, secrets redaction
- Adapter guide in `ADAPTERS.md`

**Key files to read:**
- `agent_core/tools/registry.py` — ToolRegistry class, categories
- `agent_core/prompts.py` — fragment-based prompt assembly
- `agent_core/mcp_server.py` — MCP stdio server
- `prompt_fragments/` — 9 markdown fragments by pack
- `ADAPTERS.md` — integration patterns for third-party agents
- `tests/test_phase4_pluggability.py` — 21 integration tests

**Phase 5 implementation approach (recommended order):**

1. **Kernel-backed project memory** that persists across sessions (decisions, architectures, failed approaches), not just RAG dumps:
   - Improve `kernel_retrieve` to surface session histories and patterns
   - Add importance-weighted memory compaction
   - Surface kernel memories in the UI (e.g., "Related past work" panel)
2. **Simulation-in-the-loop** for domain problems:
   - Wire simulation results into agent decision-making more deeply
   - Add simulation result caching and trend analysis
3. **Belief / debate tools** as first-class agent tools:
   - Extract `/argu` from slash-command-only into a proper tool with structured input/output
   - Expose via ToolRegistry as a new category
4. **Signal → event → memory pipeline** in prompts:
   - The model should naturally `kernel_emit_signal` on observations, `kernel_create_event` on actions, `kernel_store_context` on decisions
5. **Research mode** that writes durable memories retrievable by other agents via MCP
6. **Prompt refinements** from Section 3 of this document (persona layering, kernel/sim playbooks already in fragments)<｜end▁of▁thinking｜>

Your roadmap already sketches self-evolution (hypothesis → validate → compress). Prioritize what competitors lack:

1. **Kernel-backed project memory** across sessions (decisions, failed approaches, architecture facts)—not just RAG dumps
2. **Simulation-in-the-loop** for domain problems (already started)
3. **Belief / debate tools** for contested design decisions (`/argu` as a first-class agent tool with structured options)
4. **Signal → event → memory** pipeline guidance in prompts so the model *uses* kernel, not only file tools
5. Research mode that writes durable memories other agents can later retrieve via MCP

---

## 3. System prompt improvements (detailed, no full rewrite files)

### 3.1 Unimplemented prompt improvements

1. **Multi-mode persona** — Identity should describe the current mode (coding / research / debate), not just "coding agent." Prompt fragments should be selectable by mode.
2. **Hard rule: no inventing tools** — Add explicit rule: "Do not call tools that are not listed in the TOOL USAGE GUIDE. If a tool you need is missing, ask the user."
3. **Examples for enabled tools** — Add an examples section in the fragment system showing workspace-relative paths (e.g., `src/app.py`), only for the tools actually registered. Remove the old orphaned `system_instruction.md` which has contradictory examples.
4. **Dynamic injection** — Inject into the prompt: workspace root label, active provider/model, enabled packs list, and step budget (`max_steps`) via `{...}` placeholders assembled in `prompts.py`.

### 3.2 Tone & length

- Prefer short `thought`s; tool results carry detail.
- Final answers: summary of changes, paths touched, how to verify—no huge dumps.

---

## 4. Feature suggestions (prioritized product lens)

### Should-have (remaining)

- Kernel memory that actually influences later coding sessions  
- Simulation + research modes productized in UI (not only slash)  

### Nice-to-have / later

- Hypothesis generator / self-evolve loops  
- Digital twins (as your orchestrator doc marks planned)  
- Web fetch for docs  
- Lightweight repo map on session start (auto-scan file tree + symbols so the model can orient without several list_files/read_file calls)  
- Diff approve/reject gate in UI (diff preview done; blocking approve/reject before edits applied not implemented — currently auto-approve)  

---

## 5. Success criteria (not yet met)

**Product**

- Kernel memories from one session improve a later session  

---

## 6. Explicit non-goals (for this plan)

- Rewriting the Next app stack  
- Replacing kernel with a third-party vector DB immediately  
- Shipping file_ops as the embedder default  
- Full self-evolution loop before registry + native tools exist  

------------

Here's what's actually going on: this codebase has already built a surprising amount of what you're asking for — a self-evolving chain/graph system (`chain_miner.py`, `graph_evolver.py`, the `workflow_learn` config block) that mines tool-call sequences into deterministic, LLM-free chains and rebuilds a SQLite-backed graph at session end. So a lot of my answer is "here's how to finish and extend what's already 80% built," not "build this from scratch." Let me go through your four asks in order, then flag some gaps I noticed in the dump along the way.## 1. Self-analysis → deciding what to hardcode

This is essentially already built, and it's worth being precise about the mechanism because it's cleverer than a typical "auto-optimize" loop: `chain_miner.py` watches tool-call n-grams (both in-loop via `_feed_chain_miner` and in a session-end batch), and the promotion is **inline in the miner, not an LLM judgment call** — read-only sequences that clear `min_occurrences`/`min_savings_tokens` get auto-registered live (`_register_live`); anything with a write step sits `pending` until `chain_admin approve`. That's the "no LLM involved" decision you're asking for — it's already frequency + determinism + a static safety rule (read vs. write), not a model deciding.

Where I'd extend it is by turning the binary chain/no-chain decision into a **three-tier ladder**, because right now everything that gets promoted still costs a tool-call turn:

| Tier | Trigger | Example | LLM cost |
|---|---|---|---|
| Chain tool | Repeated sequence, some parameter variance | `probe_module`, `orient_symbols` | One tool call, LLM still chooses to invoke it |
| Hook | Same sequence, fires at a fixed point (post-`edit_file`, session-end), zero parameter variance | the `verify_edit`/`report_freshness` pattern from `sessions_analysis/session1.md` | Zero — runs automatically, never enters context |
| Backlog (new tool needed) | Pattern needs logic that doesn't exist in any current tool | `module_profile`, `context_budget` | N/A until someone writes it |

Concretely: add a `variance` and `trigger_position` score alongside the existing `savings_est` in the candidate table. A candidate with zero arg variance and a consistent trigger point (e.g., "always the 2nd call after `edit_file` on a `.py` file") should promote to a **hook wired into `loop/engine.py`**, not a chain tool the LLM has to remember to call — this is literally the "Post-edit import/syntax check hook" idea already sitting in `session1.md`/`session8.md`. Chains save tokens on execution; hooks save the tool-selection decision itself, which is the bigger lever for smaller models per your own `session7.md` note about drift.

## 2. Merging workflow files into the main graph as subgraphs

The mechanism for this is already fully built at the renderer level — `render_graph.py`'s template does `g.setParent(id, clusterId)` and reads a `clusters` array straight out of `graph_clusters`, and P4's plan explicitly says `minimal_context.html`/`implement_fix.html` become cluster nodes this way.

To make that automatic rather than one-off:
- Write a small ingester that parses each `data/workflows/*.html` file's embedded `const data = {...}` JS block (it's just JSON — `re.search(r'const data = ({.*?});', text)`), inserts a `graph_clusters` row keyed by filename, and tags each node/edge with that `cluster_id` + a `source_file` field.
- Run it as part of `graph_evolver.evolve()`, gated by `workflow_learn.graph_evolve` like everything else, so any new file dropped into `data/workflows/` gets absorbed on the next evolve — you never hand-maintain the merge.
- Keep chain-mined clusters and hand-authored workflow-file clusters visually distinct (solid border for hand-authored, dashed for mined) so a human glancing at the graph can tell "this part is documented convention" from "this part the agent invented."

## 3. Turning session-file optimizations into agent-driven work

This is the interesting gap. `chain_miner.py` mines **tool-call telemetry** — structured `{tool, args, ts}` events. But most of the value in `sessions_analysis/*.md` is **prose recommendations for tools that don't exist yet** (`tool_surface`, `md_outline`, `smart_read`, `file_facts`, `module_profile`, `context_budget`, `compact_history`). I checked the current Meta Tools table against these — `tool_anatomy` made it in, but `tool_surface`/`md_outline`/`smart_read`/`file_facts` were each proposed independently in sessions 1, 4, and 7 and are *still* not implemented. That's a real, visible cost of the current setup: the agent keeps re-discovering the same gap across sessions because nothing persists the recommendation itself, only the raw telemetry.

The fix parallels what already exists for chains, applied one level up:
- A lightweight "proposal miner" (mostly regex over the `.md` tables, since these files are already structured — you don't need an LLM call for this) that extracts `{proposed_name, category, replaces_pattern, est_savings}` from each session file and writes it into a `tool_proposals` table, deduping by name so a 3rd mention of `tool_surface` increments a `times_proposed` counter instead of being lost again.
- Render these as **ghost nodes** in the same graph — dashed grey diamonds like the existing mining-candidate convention, but labeled with the proposed tool name and a `×N proposed` badge. This reuses `graph_evolver`'s existing dashed-diamond idiom instead of inventing a second UI.
- Keep code-writing itself outside the auto-loop. Your own `config.json`/AGENTS.md principles already say "ask before installing modules," "ask before running tests" — a genuinely new primitive tool is exactly the kind of change that should stay human-gated, same as write-chains today. What the agent *can* do autonomously is the surfacing and deduplication, not the implementation.

## 4. Graph as a state machine with per-node prompt injection

Right now `workflow_hints()` already injects live chains + top DO/AVOID notes into every turn — but it's a **blanket broadcast**, the same list regardless of where in the workflow the agent actually is. What you're describing is closer to giving each graph node its own scoped prompt fragment, injected only when the agent is inferred to be "at" that node.

Two pieces needed:
- **Schema**: add a `prompt_fragment` column to `graph_nodes` (or a pointer into `prompt_fragments/*.md`). The AVOID notes already living in the `Agent_graph.html` side panel — "don't recurse `get_callers_callees` past depth 2," "check `get_symbols_meta` before `get_symbol`" — are natural candidates to move from the always-shown panel into per-node fragments.
- **State inference**: reuse `chain_miner`'s n-gram matching logic in "lookup" mode instead of "mine" mode — after each tool call, match the trailing window against known chain/graph paths and set a `current_node`. Then swap `workflow_hints()`'s static list for `graph_nodes[current_node].prompt_fragment`, capped small (~100-200 tokens).

One guardrail I'd insist on: keep this a **soft hint, not a hard gate**. State inference from a tool-call window is a heuristic, not ground truth — if you let the FSM state restrict which tools are callable, a legitimately unusual task will fight the graph instead of being served by it. The existing chain-promotion pipeline already draws this line correctly (deterministic *promotion*, but the LLM still chooses whether to call the resulting tool) — the state-scoped injection should follow the same pattern: advisory, never load-bearing.

## Risks worth flagging

- **Runaway self-modification**: `graph_state.version` already increments on every evolve and `sweep_stale_chains()` demotes unused chains after 14 days — good instincts already in place. I'd add an explicit node/cluster cap and a "diff before commit" step (show what `evolve()` is about to add/remove) rather than silent auto-apply, especially once ghost proposals and hook promotion widen what evolve can touch.
- **Validate against real sessions**: your own `FixesIssues.md` already flags this — "mining was validated with synthetic feeds; validating against the 8 real transcripts in `sessions_analysis/` is a natural next step." That's the single highest-leverage thing to do before adding any of the above, since it'll tell you whether the existing miner even fires correctly on real usage.
- **`tool_packs.chain` is off by default**, which makes the whole pipeline invisible to the LLM until someone flips it — worth reconsidering as "on once N approved chains exist and token budget allows" rather than a static default.