# Stock Analyser — roadmap

> Agent rule: this file tracks UNIMPLEMENTED work only (Next up / Deferred).
> When an item ships, move its row to the features table in `README.md` and
> delete it here. Shipped detail lives in README's file map, not here.

## Next up (from `FixesIssues.md`, remaining only)

| Item | Status | Depends on |
|---|---|---|
| Feature-attribution → ROBUST PIE findings (selection/OOS/across-model/across-time frequency + ablation delta) | open (attribution recorded, not aggregated/gated) | findings volume from overnight runs |
| Portfolio-level research (incremental portfolio alpha) | open | portfolio simulator below |
| Declared price basis per dataset (raw/split-adjusted/total-return + corporate-action policy) | open (only adj-mix flag exists) | dataset registry extension |
| Bar immutability metadata (bar_start/end, is_final, observed_at) | open (forming-bar trim exists, no schema) | recorder/store migration |
| Hierarchical allocator (family→feature→model→horizon→policy) | open (family-level bandit only; evidence-based retirement DONE via `family_stalls`) | ledger stats plumbing |
| Hard gates before score (cost-stress kill, single-year concentration) | open (score ranks; gates partial) | validation gates |
| DISCOVERY vs DEPLOYMENT_CANDIDATE statuses | open (single PAPER_READY verdict) | finding/kernel status mapping |
| OOS isolation hardening (rank/allocate on pre-OOS metrics post-reveal) | open (seal binding exists) | score/allocator rewire |

## Deferred (not done)

| Item | Status | Depends on |
|---|---|---|
| Options research (single/chain/multi-leg) | deferred | live history accumulation via recorder |
| Full Upstox live adapter (websocket, reconnect) | stub only (NSE+Yahoo recorder covers V1 needs) | Upstox account + token |
| 2000+ equity universe + sector/index model | deferred | data source for extended symbols |
| 5m/1m timeframes | deferred | intraday data; engine API already generic |
| Cross-sectional / pairs / basket strategies | deferred | universe + regime support in engine |
| Market-regime discovery | deferred | findings volume from overnight runs |
| Portfolio simulator (multi-strategy, correlation-aware) | deferred | validated strategy pool |
| ML predictors (LSTM/Transformer/XGB) | deferred | deliberate: classical ML + features first |
| RL / policy learning | deferred (FixesIssues #10: needs simulator + reward + execution realism first) | validated strategy pool + deep-ML edge |
| Live execution | blocked | human approval boundary; separate permissioned system |

## New (proposed from this session's shipped work)

| Item | Why | Depends on |
|---|---|---|
| Legacy tree completion report | DEMOTING trees need bars-held vs max_hold, expected completion date, auto `reality.check` on DEAD | `paper/trees.py` sweep_dead hook |
| Research timing dashboard | iter-1 showed setup 146s (bars + panel warm) dominating; per-stage JSONL exists but no rollup/persisted panel cache | timing log aggregator |
| Stale RUNNING reaper | killed launches leave `RUNNING` rows with 0 done (e.g. `res_20260910_113737`); auto-mark dead on next run start | run startup check |
| T+0 eligibility routing | T+0 beta covers growing scrip list; route eligible names via T+0 when broker supports, rest T1_EPI | eligible-securities list + broker flag |
| CMP/history adj-mix guard | live CMP is unadjusted, history is `yahoo-adj`; corporate actions silently skew marks and stop levels | declared price-basis item above |
| Scale-gate watch | auto-flag trees nearing ≥10 closed / avg ≥Rs90 instead of manual checks | `report()` thresholds |

(End of file)
