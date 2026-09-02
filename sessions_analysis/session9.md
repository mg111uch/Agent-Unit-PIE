# Session 9 Analysis — Co-development Loop (Kernel + popula_dyn) Iter3–4

## Scope
Iter3 MODEL `hyp_pop_collapse_08` births 0 at 0.08–0.12 (pop 2–11 vs 5) → Iter4 WORLD elasticity validated. Commits `06d914a→e61996e` (A: reproduce placement `behaviours/reproduce.py:44` origin, B: `births_total/deaths_total` `simulation_model.py:52`, C: age after `execute` + init 15-40, D: `mate_radius`/`mate_global_fallback` `constants.py:13`, E: `develop_hypothesis` + smoke-hardened `develop_tools.py:215`, F: `concepts_for_changed_files` slash fix `simulation_schema.py:172` + `HISTORICAL` 5 old findings, plus docs wholesome `kernel/README`/`populaDyn_simu/README` + `PhasePlan` archived + `FeatureIdeas` pruned to G).

## Token Spend (measured via `tool_stats` + manual)
- **40% `Read`** — full `simulation_model.py:370`, `simulation_connector.py:683`, `develop_tools.py:375` re-read per step (2000-line window)
- **30% `Bash python -c`** — inline `state_text`, `run_policy_*` ladder (5 runs × ~11s), `sync_from_git`, `eval_harness` repeats
- **15% `Grep/Glob`** — repeated pattern searches for `read` after edit
- **10% `Edit`** — multi-file L3 patches (reproduce + model)
- **5% `develop_*`** — actual workflow advances (cheap, ~2KB state)

**Most expensive step:** `step()` → `develop_experiment` ladder (4 runs) + `Read` full model before each `Edit`. Saving trick: `bulk_state` one-call hydrate + `batch_read` with `line_numbers` instead of full read.

## Repeated Tool Patterns (harness-chain candidates)
1. `Read(simulation_model.py) → Edit → Read → Edit` ×4 (reproduce, model, survival, connector) — chain as `safe_edit_chain`
2. `develop_orient → hypothesis → decide_branch → modify_code → validate → experiment → analyze` — 7-step chain, LLM drift when `version_id` manual. Now `develop_hypothesis` + auto `orient` sync reduces 3 calls.
3. `Bash python -c "state_text"` + `Bash python -c "sync_from_git"` + `Bash python -c "develop_experiment"` inline — chain as `sim_run_chain`
4. `Grep → Read → Edit` for same file — chain as `grep_edit_chain`

Harness `chain` pack (`probe_module`, `safe_edit`) already chains `file_skeleton→who_imports` etc., but not these sim-specific chains. Hardcode via `chain` category `sim_smoke_chain` so smaller LLMs skip drift.

## Hooks Needed (not in `agent_core/README.md:26`)
- **Pre-chat:** `pre_orient_hydrate` — auto load `workflow_states` + `semantic_nodes` + `sim@commit` (<2KB) before first LLM turn (currently manual `develop_orient` does it; should be hook, not tool)
- **Mid-chat (post-edit):** `post_edit_sim_smoke` — after `simulators/*` edit, run `2-agent same-cell birth_rate 1.0 → births_total>=1` smoke (`tests/test_popula_dyn_smoke.py:1`) via `post_edit_import_check` extension (existing `post_edit_import_check:344` only import-checks, not sim smoke). Prevents `modify_code→validate` lie (`tests_pass` without birth check)
- **Post-chat (session_end):** `post_session_compress` — auto `mark_stale_findings` + `recompute_consolidated` + `report_freshness` (kernel/docs) without LLM remembering

## Novel Tools (vs `agent_core/README.md:66` existing)
Existing: `Read/Write/edit_file/grep_search/glob_search/file_skeleton/who_imports/probe_module/orient_symbols/kernel_* /simulation_* /git_* /chain` — do not duplicate.

**Propose:**
- `bulk_state` (vs `develop_state` + `state_text` separate Bash): one call returns `{state, version_id, allowed, hyps, runs}` with `_bytes` trim — saves 2 tool calls per turn, not `get_workspace_info`
- `attach_evidence` (vs `hypothesis_engine.create_hypothesis` raw): `hyp_id + evidence_id` → `conf bump` + `validity ACTIVE` — avoids `hyp_pop_collapse_08` duplicate block without `force=True` hack
- `human_occupied_summary` (vs `spatial_engine.summary` raw): `human_units/human_occupied_cells` vs `occupied_cells 2500` land — not in `sim` pack, complements `simulation_run`
- `sim_smoke_chain` (vs generic `chain`): `modify_simulator → birth smoke → validate` composite — smaller LLMs execute 1 tool not 3, less drift

**Not proposing:** `find_tool/get_tool_schema` duplicates `Tool Search` (`agent_core/README.md:93`), `doc_audit` duplicates `report_freshness` etc.

## File Access Speedups
- `codebase_atlas` `file_api` + `get_symbols_meta` (cheap browse) before `Read` full file — use `minimal_context_dump` for periphery
- `citation_cache` `validate_capabilities` mtime-keyed — skip re-read if unchanged (currently re-reads full model)
- Persist `state_text` in `DevelopmentState` preface — agent should not `Bash python -c` it each turn; tool should auto-inject (<2KB budget)

## Next Validation
`eval_harness.run_all 5/5` + `tests/test_popula_dyn_smoke 3/3` + `smoke_kernel 9/9` already. Next harness should measure `iterations_to_solution` clean-context repeat (N+1 < N tool_calls).
