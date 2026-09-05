# Stock Analyser Status
_Last verified: 2026-09-05_

## Current State
- 0 PAPER_READY. Ledger: `market.db:research_runs`.
- `res_20260905_113836` (budget100_day_200sym, MY_UNIVERSE_200 marketdb 1D) COMPLETE 72/100 — 46 SCREENED, 26 DUPLICATE, 0 reached full validation.
- `res_20260905_121931` (ml_rerun_fixed_screen, budget 40, hgb/rf/ridge) COMPLETE 29/40 — 25 SCREENED, 4 REJECT (validation reached; best hgb-features avg_net −270, oos −299). Screen fix verified (ML trades again); edge honestly absent on this window.
- Datasets: `ds_my_universe_200_day` (200 members + snapshot hash) is the pin; `ds_nifty_200_day` (15, seed fallback) superseded.
- Breakout lineage retired, don't revive it. Suite 23/23 green (plus ML 4/4).
- Shards pruned to 50; full record in ledger.

## Known Issues
- ML quick_screen starved training (val-only panel) — FIXED `64a777a`, under rerun validation.
- 36% duplicate rate (mutation revisits; dedup runs post-screen) — open.
- Retirement never fires (needs REJECTs; screens don't count) — open.

## Next (single source for the next task — agents pull from here, not HANDOVER)
1. ML edge absent on 1D/252 window (hgb screens +270s → validates −270s). Next: features/top-N variants or regime-split (bull/bear) datasets before retrying ML.
2. Dedup-before-screen (hash check before backtest) + count SCREENED streaks toward retirement.
3. Denser ML sweep (model/features/top-N variants via `seeds=[...]`).
4. On first PAPER_READY (post-falsification): human approves → `paper.trader.step` daily → `report` → capital.yaml step.
5. Research backlog, in order: LEVEL-0 family IC gate → feature-attribution findings → portfolio simulator + allocation.
