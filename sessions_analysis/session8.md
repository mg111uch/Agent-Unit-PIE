## Session retro: where tokens went & what would have helped

Evidence from this session (4 merge/rename tasks: batch tools, todo, kernel-warning removal, tool-mode design):

**The #1 token hotspot was cross-file tool tracing.** For each task I re-traced the same tool through ~9 files by hand: `__init__.py` (registration) → impl (`meta_ops.py`/`file_ops.py`) → `stepper.py` → `session_state.py` → `audit.py` → `mock_provider.py` → tests → prompt fragments → `mcp_server.py`. I did this ~4× (batch, todo, kernel, mode). That's an estimated 60–70% of session tokens.

**#2: whole-file reads for small slices.** `file_ops.py` (627 lines) read 3+ times; `registry.py`, `stepper.py`, `session_state.py` similar. The existing **codebase atlas** (`get_symbol`, `symbols_by_file`, `file_api`, `batch_file_api`, `call_chain`, `find_impact`, `minimal_context_dump`) would have turned these into single-function fetches — but the `code_rag` pack is **off** in config.json and the atlas DB is **4 days stale** (Jul 27), so it wasn't available. That's the single biggest lever, already built.

---

## Recommendations (each checked against existing tools — no duplicates)

### 4. Post-edit import-check hook — NEW hook, tiny
After any change under `agent_core/tools/`, run `python -c "import agent_core.tools"` automatically. Catches schema/registration errors (the unhashable-type bug) in seconds, not a debug cycle. Nothing like it exists (`hot_reload`/`kernel_reload` are manual).

### 5. Mode-aware prompt trimming — assembly tweak (ties into the tool_mode work)
In `read_only`/`shell_only`, exclude edit-oriented fragments (`file_ops_workflow.md` talks about `edit_file`/`write_to_file`; `meta_playbook.md` about edits/checkpoints). Fewer prompt tokens per call + less drift for smaller LLMs. Not a new tool.

### 6. Hardcode-able chains — reuse, don't build

- **pre-change context prep** → `minimal_context_dump` already chains `get_symbol`+`find_impact`+`batch_file_api` into one capped file. Recommendation: harness auto-invokes it (or a cached lighter variant) before multi-edit tasks instead of the LLM making 4–6 individual atlas calls. Don't duplicate it.

