# Feature Ideas — remaining (implemented A-F moved to readmes)

> Implemented A-F (reproduce, metrics, RNG, age, workflow, kernel) moved to `system_devpt_reports/kernel/README.md` + `populaDyn_simu/README.md` Features Overview (one-liner prose, code is source of truth). This file now holds only non-implemented Phase G.

## Phase G — Later product ideas (not Iter3, keep)

- Cumulative plots in `simulation_plot.png` / game UI (no frontend tests per policy).
- Explicit `ReproductionEngine` in `core/` if behaviors must stay side-effect free (return intended child; model applies spawn).
- `event_bridge.py` / `world_engine.py` / `resource_engine.py` unread — do not redesign yet.
- Self-improvement eval: repeat task from clean context; success is fewer `develop_*` calls.

## What not to do (keep)

- Do not raise `birth_rate` in PARAMS to hide spawn/RNG bugs.
- Do not hand-edit `data/topics/*/graph.json`.
- Do not add a second DB or write findings outside `data/kernel.db`.
