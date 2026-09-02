# Stock Analyser — Implementation Plan

> For a follow-on agent: implement remaining unchecked items only. Do **not** re-read popula_dyn, agent_core, or other domain modules. Kernel files listed below are the only kernel touchpoints. Cap files at 400–500 LOC. One SQLite path: `data/kernel.db`.

## Architecture (do not duplicate PIE)

```
LLM proposes (hypothesis / strategy genome)
        ↓
stock_analyser = domain engine (data, features, strategy, backtest)
        ↓
PIE kernel = cognition (lineage, signals, findings, contradiction, retrieval)
        ↓
research_development workflow = loop (orient → version_sync → hypothesis
  → decide_branch → experiment | modify_code → update_knowledge → evaluate
  → validate → loop)
```

Stock is a **domain engine**, not a second research loop. Reuse:

| Existing PIE | Stock use |
|---|---|
| `data/workflows/research_development.json` | Top-level loop; add subgraph `stock_analyser_dev.json` |
| `development/workflow_engine.py` | `WorkflowEngine(simulator="stock_analyser")` |
| `development/develop_tools.py` | Dispatch `develop_experiment` when `simulator==stock_analyser` |
| `kernel/simulation_version.py` `sync_from_git` | Lineage `stock_analyser@commit` |
| `kernel/simulator_registry.py` | Discover this module (not only `simulators/*`) |
| `kernel/persistence/db.py` | `simulation_runs` / `simulation_versions` + extra market tables in **same** `kernel.db` |
| `argu_god.engine.topic_store` | Findings on topic `sim_stock` |
| `kernel.hypothesis.hypothesis_engine` | WORLD/MODEL hypotheses |
| `kernel.signals.signal_engine` | Emit market signals |
| `kernel.hypothesis.contradiction_gate` | Version-aware, per-sim |
| `development/validation_gate.py` | `modules/stock_analyser` → L3; paper/live never auto |

**Forbidden:** new experiment registry, new finding store, new agent loop, second SQLite file, pandas/numpy (stdlib only unless user approves).

## Simulator identity

- Name: `stock_analyser` (dir spelling)
- Topic: `sim_stock`
- Git pathspec: `codebase/modules/stock_analyser/**`
- Run shard: `data/units/simulations/stock_analyser/{run_id}/` (`params.yaml`, `signals.json`, `summary.json`)
- Ontology: `codebase/modules/stock_analyser/ontology.yaml`

## File map (all new code under `codebase/modules/stock_analyser/` unless noted)

| File | Responsibility | Status |
|---|---|---|
| `manifest.yaml` | topic, git patterns, kind | TODO |
| `ontology.yaml` | concepts for lineage invalidation | TODO |
| `__init__.py` | public API | TODO |
| `constants.py` | SIM_NAME, timeframes, costs | TODO |
| `data/models.py` | Instrument, EquityBar, OptionBar | TODO |
| `data/store.py` | kernel.db tables + queries | TODO |
| `data/universe.py` | named universes, not a 200 hard limit | TODO |
| `data/providers.py` | Historical/Live/CSV/synthetic; Upstox stub | TODO |
| `features/algebra.py` | expression AST + deterministic evaluator | TODO |
| `strategies/model.py` | Strategy object (no arbitrary Python) | TODO |
| `strategies/genome.py` | mutate feature/threshold/exit/hold | TODO |
| `backtest/engine.py` | daily+15m; signal at close t, fill open t+1 | TODO |
| `backtest/costs.py` | fees, slippage | TODO |
| `backtest/validation.py` | cost stress, perturbation, walk-forward, OOS | TODO |
| `kernel_bridge.py` | signals + topic findings + sim_runs | TODO |
| `connector.py` | `run_and_extract` / `register_to_kernel` for develop.* | TODO |
| `research/questions.py` | questions from objectives, observations, gaps | TODO |
| `research/job.py` | overnight job: genome → backtest → kernel | TODO |
| `paper.py` | PAPER_READY propose; **human_approved required** | TODO |
| `tests/test_stock_analyser_smoke.py` | synthetic → backtest → finding | TODO |
| `data/workflows/stock_analyser_dev.json` | subgraph for research_development | TODO |
| `system_devpt_reports/stock_analyser/README.md` | feature table | TODO |

### Kernel / development edits (small)

| File | Change |
|---|---|
| `kernel/simulator_registry.py` | Also discover `modules/stock_analyser` if `manifest.yaml` exists; `sim_patterns` honor absolute `codebase/...` patterns |
| `development/develop_tools.py` | If `sim==stock_analyser`, use `StockConnector` not popula `SimulationConnector`; set `workflow_engine._sim` |
| `development/validation_gate.py` | `stock_analyser` path → L3 |
| `kernel/ontology/signal_types.py` | Add `abnormal_volume`, `momentum_burst`, `drawdown_breach`, `strategy_edge` (market) |
| `data/workflows/research_development.json` | `subgraphs` += `stock_analyser_dev.json` |

Do **not** patch `simulation_connector.py` (popula-specific `SimulationModel`).

## SQLite tables (CREATE IF NOT EXISTS on `data/kernel.db`)

```
instruments(instrument_id PK, symbol, exchange, asset_type, underlying, lot_size, expiry, strike, right, active_from, active_to, meta_json)
equity_bars(instrument_id, ts, timeframe, open, high, low, close, volume, source, PRIMARY KEY(instrument_id, ts, timeframe))
option_bars(... option fields ..., PRIMARY KEY(instrument_id, ts, timeframe))
universes(name, member_id, effective_from, effective_to)
research_datasets(id, name, universe, timeframe, start_ts, end_ts, split_json)
paper_proposals(id, strategy_json, status, human_approved, created_at)
```

Indexes: `(instrument_id, ts)`, `(ts, instrument_id)`. Raw bars only — never persist indicators.

## V1 behavior

1. **Universe:** `NIFTY_200`, `OPTIONS_ELIGIBLE`, `ALL_EQUITIES`, `MY_RESEARCH_UNIVERSE`. Seed ~15 Indian symbols in YAML; 200 is a dataset size, not a code cap.
2. **Data:** CSV ingest + deterministic synthetic provider (offline). Live Upstox adapter is a stub (normalize → validate → upsert; restart-safe, skip dups).
3. **Features:** LLM emits expressions, not code. Ops: lag, diff, rolling_mean/std/min/max, rank, zscore, percentile, correlation, covariance, slope, ratio, abs, log.
4. **Strategy:** universe, timeframe, features, entry (bool expr), exit (stop_atr, take_atr, max_hold), position, risk. No lookahead.
5. **Backtest metrics:** n, wins, losses, avg/median ret, max DD, Sharpe/Sortino, turnover, costs.
6. **Validation:** cost stress → param perturbation → walk-forward → locked OOS. Researcher cannot mutate after seeing locked OOS.
7. **Research job:** 20–100 experiments/run (i3). Numerical engine only; compact metrics to LLM.
8. **Findings:** claim, experiments, metrics, universe, timeframe, regime, confidence, status in `{HYPOTHESIS,SUPPORTED,ROBUST,REFUTED,REGIME_DEPENDENT,INSUFFICIENT_DATA,SUPERSEDED}`.
9. **Paper:** `propose_paper(..., human_approved=False)` always blocked. Live execution interface exists as raise-NotImplemented; research agent must not call it.
10. **Options:** instrument + chain models + recorder schema in V1; no options research until live history exists.

## develop_experiment contract

`params` for stock:

```
{"strategy": <Strategy dict>, "dataset": "synthetic"|"csv", "start", "end", "timeframe": "1D"|"15m"}
```

`run_id` still `run_basic` or `run_policy_<param><int>` (existing validator).

## Test (smoke only)

`conda run -n myenv python -m pytest codebase/modules/stock_analyser/tests/test_stock_analyser_smoke.py -q`

Must: seed synthetic 1D bars → feature eval → backtest long strategy fills next bar → mutate genome → register finding (kernel optional if import fails, but try).

## Implementation order (if interrupted)

M1 store+universe → M2 ingest → M3 algebra → M4 strategy+backtest → M5 validation → M6 kernel_bridge+connector+registry → M7 questions+job → M8 findings → M9 live stub → M10 paper gate.

## Done when

Smoke passes; `discover_simulators()` includes `stock_analyser`; `develop_experiment({"simulator":"stock_analyser",...})` does not import popula `SimulationModel`.
