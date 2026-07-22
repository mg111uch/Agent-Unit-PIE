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
