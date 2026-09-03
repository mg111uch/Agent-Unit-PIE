# Stock Analyser — roadmap (not done / deferred)

| Item | Status | Depends on |
|---|---|---|
| Options research (single/chain/multi-leg) | deferred | live history accumulation via recorder |
| Full Upstox live adapter (websocket, reconnect) | stub only (NSE+Yahoo recorder covers V1 needs) | Upstox account + token |
| 2000+ equity universe + sector/index model | deferred | data source for extended symbols |
| 5m/1m timeframes | deferred | intraday data; engine API already generic |
| Cross-sectional / pairs / basket strategies | deferred | universe + regime support in engine |
| Market-regime discovery | deferred | findings volume from overnight runs |
| Portfolio simulator (multi-strategy) | deferred | validated strategy pool |
| ML predictors (LSTM/Transformer/XGB) | deferred | deliberate: symbolic research first |
| Paper-trading live loop + simulator feedback | V1 engine built; awaiting first PAPER_READY strategy | approve strategy → daily `paper.trader.step` → `report` |
| Live execution | blocked | human approval boundary; separate permissioned system |
| `research_datasets` split registry use | schema only | wire splits into validation/job |
| Mutate-after-OOS hard seal | convention only | enforce lineage tag check |
