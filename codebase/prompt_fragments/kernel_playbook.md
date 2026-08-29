## KERNEL MEMORY

The kernel provides persistent memory across sessions. Use it to recall past work and store important context.

- **Before** exploring a new area, call `kernel_retrieve` with keywords about the task to find relevant past decisions, architectures, or findings.
- **After** a non-obvious discovery, user decision, or important architecture fact, call `kernel_store_context` or `kernel_emit_signal` with descriptive tags so future sessions can retrieve it.
- Do not spam memory every step. Only store information at or above a moderate importance threshold (0.5+).
- If the kernel is unavailable, proceed normally — do not claim memory operations succeeded when they did not.
- **Kernel owns cognition; modules orchestrate** — argu_god (and any future module) calls into kernel; it does not reimplement.
- **Topic graphs live in kernel memory** — all topic node/edge writes go through `argu_god/engine/topic_store.py` (SQLite, canonical); `data/topics/*/graph.json` is a regenerated view, never hand-edit or read it as truth. Mutate via `scripts/topic_ops.py`, query via its `list` subcommand (see `system_devpt_reports/kernel/usage.md`).
- **Contradiction detection is kernel-side** — adding a `contradicts` edge between two nodes whose stance is `"agree"` in belief_state raises a `contradiction_detected` signal automatically (CLI output flags it; debate responses include it). Do not duplicate this logic elsewhere.
- **Don't build empty kernel files ahead of a real consumer** — Tier 5 stubs stay empty until a second module genuinely needs them.

## SIMULATION TOPICS

For simulation development topics (e.g., `popu_sim`):

- **Structured premises are required** for contradiction detection to work
- Format:
  ```
  Status: {IMPROVED|DEGRADED|STABLE|COLLAPSED}
  Population: X (baseline Y) +Z%
  Deaths: N (REDUCED|SPIKED|STABLE vs baseline M)
  Interpretation: {why it happened}
  ```
- Use `SimulationConnector.generate_structured_premise()` to auto-generate
- **Gap analysis**: Run `scripts/find_untested_parameters.py --topic <name> --suggest` before proposing new policies
- **Self-sustaining loop**: See `data/workflows/popu_sim_dev.json` for the simulation development workflow
