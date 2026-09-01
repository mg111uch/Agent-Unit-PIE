## Development Directions

### Option A: Digital Twin Integration
Connect twin data → simulation experiments:
- city_twin/human_twin data → simulation params
- Run "what-if" scenarios based on real-world data
- Strategy generation from twin → sim → analysis

### Option B: Policy Injection UI
Expose to user interface:
- Allow non-technical users to test scenarios
- Compare baseline vs policy outcomes
- Visual diff between runs

### Option C: Self-Evolution Foundations
Build recursive improvement loop:
- Auto-summarize simulation learnings
- Track hypothesis → simulation → validation
- Recursive hypothesis refinement

## Later product ideas (not Iter3, keep)

- Cumulative plots in `simulation_plot.png` / game UI (no frontend tests per policy).
- Explicit `ReproductionEngine` in `core/` if behaviors must stay side-effect free (return intended child; model applies spawn). Matches old `core/reproduction.py` idea.
- `event_bridge.py` / `world_engine.py` / `resource_engine.py` unread — do not redesign yet.
- Self-improvement eval: repeat task from clean context; success is fewer `develop_*` calls.