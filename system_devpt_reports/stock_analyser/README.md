# Stock Analyser — domain engine (V1-generated using MuseSpark.1.3)

> Agent rule: this file's features table lists SHIPPED features only.
> Put every unimplemented idea in `roadmap.md` (Next up / Deferred), never here.

| Feature | State | Notes |
|---|---|---|
| Universe (NIFTY_200/OPTIONS_ELIGIBLE/ALL/MY) | done | seed 15 symbols; 200 = data size, no code cap |
| Equity bars store (market.db) | done | raw only, no indicators persisted |
| Option bars schema + recorder | done | NSE chain + Yahoo fallback → normalize→validate→upsert, restart-safe |
| CSV + synthetic + live providers | done | offline-first; live = NSE session (no key) + Yahoo fallback; Upstox = stub |
| Feature algebra (16 ops) | done | LLM emits exprs, kernel evaluates |
| Strategy object + genome mutate | done | no arbitrary Python |
| Backtest 1D/15m, fill open t+1 | done | ATR stops, costs, long-only |
| Validation (stress/perturb/WF/sealed-OOS/falsify) | done | hard OOS seal (MUTATED_AFTER_SEAL); passers-only attacks |
| ResearchScore (multi-objective + complexity) | done | eco/stab/rob − DD/cx/gap/drag; elites rank by score |
| Cheap alpha gate | done | hierarchical L0 (IC/rank-spread/interaction/tiny-ML); any-level pass |
| Adaptive allocator (bandit + priors + novelty) | done | explore/exploit/validate; ML-aware dedup hash |
| ML family (hgb/rf/ridge) + 15-feature pool | done | rank fwd_ret, top-N policy; per-validation attribution |
| Data-quality gate | done | trims live forming bar; adj-mix flag; INSUFFICIENT_DATA |
| Realistic costs + vol sizing | done | STT/stamp/impact breakdown; shared ATR sizing (engine + paper) |
| Determinism + ledger provenance | done | run seed→bars; data_hash + code_version per candidate |
| Paper parity guards | done | max_positions cap; bar-count hold; stale/action guards |
| Research firewall (provenance + seal binding) | done | 7 hashes/candidate incl. signal_hash; sealed lineage frozen to data+code |
| Candidate dedup (canonical + behavioral) | done | normalized-AST hash; identical signal stream → DUPLICATE |
| Liquidity/capacity gate | done | ADV/participation/spread/price; ILLIQUID blocks PAPER_READY |
| Dataset registry + marketdb source | done | `research_datasets` pins; full-history marketdb reads |
| Research episodes (P17) | done | one bounded job + one kernel finding; 1000s evals stay in-engine |
| Paper reality check (P18) | done | backtest-vs-paper deviation → REVALIDATED/DEGRADED/REJECTED |
| PIT universe + snapshots (P19) | done | `resolve_asof`; registry pins members + snapshot hash |
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
| `data/quality.py` | gate: trim live forming bar, flag adj-mix, exclude short/gappy; INSUFFICIENT_DATA | done |
| `data/datasets.py` | named dataset registry (universe/timeframe/window pins) over `research_datasets` | done |
| `tests/test_recorder.py` | offline chain normalize + dup-safety + hours guard | done |
| `tests/test_panel.py` | late entrant keeps full panel; short history excluded | done |
| `features/algebra.py` | expression AST + deterministic evaluator | done |
| `strategies/model.py` | Strategy object (no arbitrary Python) | done |
| `strategies/genome.py` | mutate symbolic + ML (incl. model choice); clears oos_seal (new lineage) | done |
| `backtest/engine.py` | date-aligned union panel; <60-bar symbols excluded+reported; no lookahead | done |
| `backtest/validation.py` | shared-date train/OOS split; eligibility gate on full history | done |
| `backtest/costs.py` | fees, slippage | done |
| `backtest/validation.py` | hard OOS seal (hash+cut; MUTATED_AFTER_SEAL); cost stress, perturbation, walk-forward, locked OOS, falsification gate | done |
| `research/alpha_screen.py` | cheap pre-sim gate (freq/turnover/stability/complexity; ML max-IC) | done |
| `research/scoring.py` | multi-objective ResearchScore (eco/stab/rob − DD/cx/gap); elites rank by score | done |
| `research/allocate.py` | bandit allocator (prior×ready_rate+UCB; explore/exploit/validate) | done |
| `research/falsify.py` | permutation/halves/shift/LOO attacks on passers only; FALSIFIED downgrade | done |
| `research/firewall.py` | provenance fingerprints + execution-layer seal binding (data+code) | done |
| `research/liquidity.py` | ADV/participation/spread gate pre-PAPER_READY | done |
| `paper/reality.py` | backtest-vs-paper deviation check → REVALIDATED/DEGRADED/REJECTED | done |
| Universe PIT + snapshots | done | `resolve_asof`; registry pins members + snapshot hash |
| `ml/family.py` | hgb/rf/ridge registry; shared rank target; attribution for findings | done |
| `kernel_bridge.py` | signals + topic findings + sim_runs | done |
| `connector.py` | `run_and_extract` / `run_episode` / `register_to_kernel` for develop.*; datasets synthetic/csv/marketdb (+registry pin) | done |
| `research/questions.py` | questions from objectives, observations, gaps | done |
| `research/job.py` | day + overnight resumable jobs; bandit allocation; score-ranked elites; seeded RNG; firewall seal binding; ledger in market.db (full strategy_json + 6 provenance hashes) | done |
| `ml/dataset.py` | 15-feature panel on algebra primitives; fwd-5 labels; embargoed splits | done |
| `ml/ranker.py` | family-dispatched ranker (hgb/rf/ridge); top-N signals via engine hook; pickle artifacts | done |
| `ml/strategies.py` | ML validation (screen→dropout→stress→locked test→falsify); sealed embargo; attribution | done |
| `research/job.py` | families compete via bandit; tiered screen (alpha→quick→full); retirement after 25 consecutive REJECTs | done |
| `tests/test_ml_ranker.py` | train→score→backtest on locked test; OOS gating; artifact round-trip | done |
| `tests/test_ml_dataset.py` | panel integrity, causality (no peek), embargo gaps | done |
| `data/universe.py` | `import_universe[_file]` for hand-picked lists; DB-first resolve | done |
| `tests/test_research_ledger.py` | import, resume, hash-dedup | done |
| `paper.py` | PAPER_READY propose; **human_approved required** | done |
| `paper/gate.py` + `paper/trader.py` | proposal gate; paper trader mirroring backtest (next-open fill, frozen ATR, max_positions cap, bar-count hold, stale/action guards); ledger + scale report | done |
| `capital.yaml` + `config.py` | capital 50000, Rs60 flat/trade, max 8 positions, Rs25000 steps | done |
| `backtest/costs.py` | flat Rs/trade (default) or bps fallback; realistic STT/stamp/impact breakdown; ATR vol sizing | done |
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

                 PIE UNIVERSAL RESEARCH LOOP
                           │
                    Research Episode
                           │
             ┌─────────────┴─────────────┐
             │                           │
        Question Generator          Prior Knowledge
             │                           │
             └─────────────┬─────────────┘
                           ↓
                  STOCK RESEARCH ENGINE
                           │
                    LEVEL 0 SCREEN
                           │
              ┌────────────┴────────────┐
              ↓                         ↓
       SYMBOLIC DISCOVERY          ML DISCOVERY
              │                         │
              └────────────┬────────────┘
                           ↓
                 CHEAP CANDIDATE TESTS
                           ↓
                    FULL BACKTEST
                           ↓
                HARD ROBUSTNESS GATES
                           ↓
                   FALSIFICATION
                           ↓
                    LOCKED OOS
                           ↓
               ┌───────────┴───────────┐
               ↓                       ↓
           REJECTED              DISCOVERY
                                       ↓
                              PIE FINDING ENGINE
                                       ↓
                              KNOWLEDGE / PRIORS
                                       ↓
                              NEXT RESEARCH EPISODE

Stock is a **domain engine**, not a second research loop. 

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
2. **Data:** CSV ingest + deterministic synthetic provider (offline). Daily history: `fetch_daily_history` — 1y split-adjusted 1D from Yahoo (`yahoo-adj`; 200 NIFTY symbols, ~50k bars in `market.db`). Live: NSE cookie-session recorder (no key, stdlib) with Yahoo chart fallback; quality gate trims the live forming bar, flags adj-mix, excludes short symbols. Upstox adapter stays a stub.
3. **Features:** LLM emits expressions, not code. 15 trailing-only ops-built features (rets, vol/volume, trend/range/position) + agent-invented algebra; ML discovers over the pool.
4. **Strategy:** universe, timeframe, features, entry (bool expr), exit (stop_atr, take_atr, max_hold), position, risk; ML = model+top_n+features+exits. No lookahead.
5. **Backtest metrics:** n, wins, losses, avg/median ret, max DD, Sharpe/Sortino, CAGR, final_equity, costs.
6. **Validation:** cost stress → param perturbation → walk-forward → hard-sealed OOS (MUTATED_AFTER_SEAL enforced) → falsification (permutation/halves/shift/LOO) on passers. Multi-objective ResearchScore ranks elites, not Sharpe alone.
7. **Research job:** families (symbolic + ML hgb/rf/ridge) compete via bandit allocator (priors + UCB, explore/exploit/validate); tiered screen (alpha gate → quick backtest → full pipeline); retirement after 25 consecutive REJECTs; ledger resume in market.db. ~16s/candidate on 200 symbols (i3).
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

## Next

Moved to `status.md` (single task source). Keep the 15m recorder running for future intraday entries; daily remains the research timeframe.
