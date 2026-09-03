# Stock Analyser — domain engine (V1-generated using MuseSpark.1.3)

| Feature | State | Notes |
|---|---|---|
| Universe (NIFTY_200/OPTIONS_ELIGIBLE/ALL/MY) | done | seed 15 symbols; 200 = data size, no code cap |
| Equity bars store (market.db) | done | raw only, no indicators persisted |
| Option bars schema + recorder | done | NSE chain + Yahoo fallback → normalize→validate→upsert, restart-safe |
| CSV + synthetic + live providers | done | offline-first; live = NSE session (no key) + Yahoo fallback; Upstox = stub |
| Feature algebra (16 ops) | done | LLM emits exprs, kernel evaluates |
| Strategy object + genome mutate | done | no arbitrary Python |
| Backtest 1D/15m, fill open t+1 | done | ATR stops, costs, long-only |
| Validation (stress/perturb/WF/OOS) | done | locked OOS; no mutate-after-seal by convention |
| Kernel bridge (sim_stock) | done | signals + findings + run shards |
| develop_experiment dispatch | done | no popula import for stock |
| Overnight job | done | 1–100 exps, CPU-first |
| Paper gate | done | human_approved required; live = NotImplemented |

## File map (all code under `codebase/modules/stock_analyser/` unless noted)

| File | Responsibility | Status |
|---|---|---|
| `manifest.yaml` | topic, git patterns, kind | done |
| `ontology.yaml` | concepts for lineage invalidation | done |
| `__init__.py` | public API | done |
| `constants.py` | SIM_NAME, timeframes, costs | done |
| `data/models.py` | Instrument, EquityBar, OptionBar | done |
| `data/store.py` | market.db tables + queries | done |
| `data/universe.py` | named universes, not a 200 hard limit | done |
| `data/providers.py` | Historical/Live/CSV/synthetic; Upstox stub | done |
| `data/nse_session.py` | NSE cookie-handshake session, rate limiter (no key, stdlib) | done |
| `data/recorder.py` | chain/quote fetch → normalize → upsert; market-hours guard; Yahoo fallback (1d backfill, 1h top-ups, refreshes forming bar) | done |
| `tests/test_recorder.py` | offline chain normalize + dup-safety + hours guard | done |
| `tests/test_panel.py` | late entrant keeps full panel; short history excluded | done |
| `features/algebra.py` | expression AST + deterministic evaluator | done |
| `strategies/model.py` | Strategy object (no arbitrary Python) | done |
| `strategies/genome.py` | mutate feature/threshold/exit/hold | done |
| `backtest/engine.py` | date-aligned union panel; <60-bar symbols excluded+reported; no lookahead | done |
| `backtest/validation.py` | shared-date train/OOS split; eligibility gate on full history | done |
| `backtest/costs.py` | fees, slippage | done |
| `backtest/validation.py` | cost stress, perturbation, walk-forward, OOS | done |
| `kernel_bridge.py` | signals + topic findings + sim_runs | done |
| `connector.py` | `run_and_extract` / `register_to_kernel` for develop.* | done |
| `research/questions.py` | questions from objectives, observations, gaps | done |
| `research/job.py` | day + overnight resumable jobs; elitist selection from ledger best; ledger in market.db | done |
| `ml/dataset.py` | cross-sectional panel on algebra primitives; fwd-5 labels; embargoed splits | done |
| `ml/ranker.py` | fixed-default HGB ranker; top-N signals via engine hook; pickle artifacts | done |
| `ml/strategies.py` | ML validation (screen→dropout→stress→locked test); quick_screen; connector dispatch | done |
| `research/job.py` | families compete; screen-first; retirement after 25 consecutive REJECTs | done |
| `tests/test_ml_ranker.py` | train→score→backtest on locked test; OOS gating; artifact round-trip | done |
| `tests/test_ml_dataset.py` | panel integrity, causality (no peek), embargo gaps | done |
| `data/universe.py` | `import_universe[_file]` for hand-picked lists; DB-first resolve | done |
| `tests/test_research_ledger.py` | import, resume, hash-dedup | done |
| `paper.py` | PAPER_READY propose; **human_approved required** | done |
| `paper/gate.py` + `paper/trader.py` | proposal gate; pending-order paper trader mirroring backtest (signal→next-open fill, frozen ATR); ledger + scale report | done |
| `capital.yaml` + `config.py` | capital 50000, Rs60 flat/trade, max 8 positions, Rs25000 steps | done |
| `backtest/costs.py` | flat Rs/trade (default) or bps fallback; per-trade net metrics | done |
| `tests/test_capital.py` | flat costs, config, net tracking, paper ledger | done |
| `tests/test_stock_analyser_smoke.py` | synthetic → backtest → finding | done |
| `data/workflows/stock_analyser_dev.json` | subgraph for research_development | done |

### Kernel / development edits

| File | Change |
|---|---|
| `kernel/simulator_registry.py` | Discovers `modules/stock_analyser` via manifest; `sim_patterns` honors absolute `codebase/...` patterns |
| `development/develop_tools.py` | `sim==stock_analyser` uses `StockConnector`; analyse path uses `get_signals`, skips compression |
| `development/validation_gate.py` | `stock_analyser` path → L3 |
| `kernel/ontology/signal_types.py` | `abnormal_volume`, `momentum_burst`, `drawdown_breach`, `strategy_edge` (market) |
| `data/workflows/research_development.json` | `subgraphs` += `stock_analyser_dev.json` |

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

**Forbidden:** new experiment registry, new finding store, new agent loop, second SQLite file, pandas/numpy (stdlib only unless user approves).

## Simulator identity

- Name: `stock_analyser` (dir spelling)
- Topic: `sim_stock`
- Git pathspec: `codebase/modules/stock_analyser/**`
- Run shard: `data/units/simulations/stock_analyser/{run_id}/` (`params.yaml`, `signals.json`, `summary.json`); auto-pruned to newest 50 successful (ledger in market.db is the complete record)
- Ontology: `codebase/modules/stock_analyser/ontology.yaml`

## SQLite tables (CREATE IF NOT EXISTS on `data/market.db` — never `kernel.db`)

```
instruments(instrument_id PK, symbol, exchange, asset_type, underlying, lot_size, expiry, strike, right, active_from, active_to, meta_json)
equity_bars(instrument_id, ts, timeframe, open, high, low, close, volume, source, PRIMARY KEY(instrument_id, ts, timeframe))
option_bars(... option fields ..., PRIMARY KEY(instrument_id, ts, timeframe))
universes(name, member_id, effective_from, effective_to)
research_datasets(id, name, universe, timeframe, start_ts, end_ts, split_json)
paper_proposals(id, strategy_json, status, human_approved, created_at)
```

Indexes: `(instrument_id, ts)`, `(ts, instrument_id)`. Raw bars only — never persist indicators. OHLC rounded to paise (2 decimals) at ingest; Greeks keep full precision.

## V1 behavior

1. **Universe:** `NIFTY_200`, `OPTIONS_ELIGIBLE`, `ALL_EQUITIES`, `MY_RESEARCH_UNIVERSE`. Seed ~15 Indian symbols in YAML; 200 is a dataset size, not a code cap.
2. **Data:** CSV ingest + deterministic synthetic provider (offline). Daily history: `fetch_daily_history` — 1y split-adjusted 1D from Yahoo (`yahoo-adj`; 200 NIFTY symbols, ~50k bars in `market.db`). Live: NSE cookie-session recorder (no key, stdlib) with Yahoo chart fallback for equities/indices; Upstox adapter stays a stub (normalize → validate → upsert; restart-safe, skip dups).
3. **Features:** LLM emits expressions, not code. Ops: lag, diff, rolling_mean/std/min/max, rank, zscore, percentile, correlation, covariance, slope, ratio, abs, log.
4. **Strategy:** universe, timeframe, features, entry (bool expr), exit (stop_atr, take_atr, max_hold), position, risk. No lookahead.
5. **Backtest metrics:** n, wins, losses, avg/median ret, max DD, Sharpe/Sortino, CAGR, final_equity, costs.
6. **Validation:** cost stress → param perturbation → walk-forward → locked OOS. No-mutate-after-OOS is convention-only (see roadmap).
7. **Research job:** families (symbolic + ML) compete; screen-first, retirement after 25 consecutive REJECTs, ledger resume in market.db. ~16s/candidate on 200 symbols (i3).
8. **Findings:** claim, experiments, metrics, universe, timeframe, regime, confidence, status in `{HYPOTHESIS,SUPPORTED,ROBUST,REFUTED,REGIME_DEPENDENT,INSUFFICIENT_DATA,SUPERSEDED}`.
9. **Paper:** `propose_paper(..., human_approved=False)` always blocked. Live execution interface exists as raise-NotImplemented; research agent must not call it.
10. **Options:** instrument + chain models + recorder schema in V1; no options research until live history exists.

## develop_experiment contract

`params` for stock:

```
{"strategy": <Strategy dict>, "dataset": "synthetic"|"csv", "start", "end", "timeframe": "1D"|"15m"}
```

`run_id` still `run_basic` or `run_policy_<param><int>` (existing validator).

## Manual market data recording

```python
cd /home/manigupt/Hello/Agentic_Unit_PIE
conda run -n myenv python -c "
import sys; sys.path.insert(0,'codebase'); sys.path.insert(0,'.')
from modules.stock_analyser.data.recorder import Recorder
r = Recorder(index_symbols=('NIFTY','BANKNIFTY'),
             equity_symbols=('RELIANCE','TCS','INFY','HDFCBANK'),
             timeframe='15m', poll_s=180)
print(r.run_once())   # single snapshot; use r.loop() to poll till close
"
```

## Next (new session pickup)

Status: 0 PAPER_READY after ~180 candidates (breakout + ML-top3 families both negative net of ₹60/trade). Ledger: `market.db:research_runs` (`res_20260903_113818`, PAUSED_USER), shards pruned to 50, suite 23/23 green.
1. Seed new families — mean-reversion and MA-trend symbolic + ML depth/top_n variants via `seeds=[...]`; breakout lineage is retired, don't revive it.
2. Launch bounded day/overnight `run_job` on `MY_UNIVERSE_200`; monitor with `run_status`.
3. On first PAPER_READY: human approves → `paper.trader.step` daily on live bars → `report` scale verdict → capital.yaml step.
4. Keep 15m recorder running for future intraday entries; daily remains the research timeframe.
