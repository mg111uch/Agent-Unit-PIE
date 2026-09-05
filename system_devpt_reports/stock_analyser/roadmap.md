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
| Hierarchical allocator (family→feature→model→horizon→policy) + evidence-based retirement | open (family-level bandit only; 25-reject rule) | ledger stats plumbing |
| Hard gates before score (cost-stress kill, single-year concentration) | open (score ranks; gates partial) | validation gates |
| DISCOVERY vs DEPLOYMENT_CANDIDATE statuses | open (single PAPER_READY verdict) | finding/kernel status mapping |
| Info-gain-per-compute research objective | open | allocator cost model |
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
| Paper-trading live loop + simulator feedback | V1 engine built; awaiting first PAPER_READY strategy | approve strategy → daily `paper.trader.step` → `report` |
| Live execution | blocked | human approval boundary; separate permissioned system |

(End of file)
