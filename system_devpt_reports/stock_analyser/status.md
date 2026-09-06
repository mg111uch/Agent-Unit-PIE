# Stock Analyser Status
_Last verified: 2026-09-06_

## Current State
- `res_20260906_084915` (ml_retry_regime_features, budget 40, hgb/rf/ridge × top_n, 19 features) COMPLETE 34/40 — 19 REJECT (avg oos −215, all ml), 15 SCREENED, 0 PAPER_READY. Best oos −24 (hgb top10, 15 feats; prior best −299). Winners cluster hgb/top10/reduced-features. Verdict: screens pass now, edge still absent.
- Rank gate pre-check on full window: spread 0.004/hit 0.54/IC 0.02 → FAIL (no XS momentum edge; ML must find residual alpha).
- ML retry REGIME-SCOPED RUNNING (bg, est ~2h): `ml_retry_regime_2020_2023` budget 20, hgb-heavy seeds, window 2020-01→2023-12 (965 bars/sym; 145s/screen measured). `run_job` now takes start/end/n window args.
- Backfill DONE: 10y daily (316k rows, 0 failed) for MY_UNIVERSE_200 + NIFTY/BANKNIFTY/6 sectorals (~2.4k bars each). DB 10→101MB. Regime gates now REAL: 2015–19 fail (spread −0.013, reversal hint), 2020–21 PASS, 2022–23 PASS, 2024–26 fail. Edge is regime-dependent — momentum lived 2020–23, dead since.
- Regime reality check: marketdb holds only 2025-09→2026-09 (252 bars) — 2015–2023 regime datasets are EMPTY until recorder history accumulates. Halves split: H1 PASS (0.010/0.62/0.05), H2 fail — momentum edge decayed. True regimes need live accumulation.
- Registry-popula-only: no stock change (dedup already in ledger).
- Adds-live: cross-sectional `rank_validation` (spread/hit/IC gate vs curve-fit) + `family_stalls` retirement (`screened_retire_after` 40; screens now count).
- Phase3-popula-only: no stock change (regime+ladder+info stack stands).
- Phase2-live: ladder gating (`gate_families` ML needs L2 ic/spread) + info-gain scoring (`score_with_info` = edge + info/compute); no bigger-ML-on-failure.
- Phase1-live: regime datasets (`ensure_regime_datasets` 4 windows) + L0-L2 `baseline_ladder` (buy_hold/momentum/reversal/mom×liq/mom×vol) + 4 ML features (mom_vol_20/dd_high_60/rev_5_20/range_vol); climb baselines before ML retry.
- Phase0-leap live: `propose_architecture` gate (`develop_propose_architecture`) for family jumps rules→factors→ML→deep; incremental path unchanged.
- 0 PAPER_READY. Ledger: `market.db:research_runs`.
- `res_20260905_113836` (budget100_day_200sym, MY_UNIVERSE_200 marketdb 1D) COMPLETE 72/100 — 46 SCREENED, 26 DUPLICATE, 0 reached full validation.
- `res_20260905_121931` (ml_rerun_fixed_screen, budget 40, hgb/rf/ridge) COMPLETE 29/40 — 25 SCREENED, 4 REJECT (validation reached; best hgb-features avg_net −270, oos −299). Screen fix verified (ML trades again); edge honestly absent on this window.
- Datasets: `ds_my_universe_200_day` (200 members + snapshot hash) is the pin; `ds_nifty_200_day` (15, seed fallback) superseded.
- Breakout lineage retired, don't revive it. Suite 23/23 green (plus ML 4/4).
- Shards pruned to 50; full record in ledger.

## Known Issues
- ML quick_screen starved training (val-only panel) — FIXED `64a777a`, under rerun validation.
- 36% duplicate rate (mutation revisits; dedup runs post-screen) — open (dedup-before-screen still to do).
- Retirement never fires — FIXED (this session): `family_stalls` + `screened_retire_after` 40; screens now count.

## Next (single source for the next task — agents pull from here, not HANDOVER)
1. ML retry on regime datasets + 4 new features (mom_vol_20/dd_high_60/rev_5_20/range_vol), gated by `rank_validation` before full validation (regime datasets + features DONE this session).
2. Dedup-before-screen (hash check before backtest).
3. Denser ML sweep (model/features/top-N variants via `seeds=[...]`).
4. On first PAPER_READY (post-falsification): human approves → `paper.trader.step` daily → `report` → capital.yaml step.
5. Research backlog, in order: LEVEL-0 family IC gate → feature-attribution findings → portfolio simulator + allocation.
