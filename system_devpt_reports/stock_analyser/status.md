# Stock Analyser Status
_Last verified: 2026-09-09_

> Agent rule: Current holds max 5 entries (newest first). Shipped detail lives in README Features — never duplicate the full list here; drop oldest when adding.

## Current State
- Rotation SETTLEMENT-HONEST (T1_EPI, verified NSE T+1 + Oct-24 EPI 100% same-day): `_settled_cash` caps fills, `SKIP funds in settlement` keeps PENDING; `retired_trees` exit-only; `cli.py migrate --from --to` plan (sells@CMP→proceeds→new PENDING). Default live broker has EPI.
- Paper league day-1 DONE (9/09 closed bars, all 200 syms): 12 PENDING orders fill at 9/10 open — t5~top_n8: BSE/COFORGE/GVT&D/INFY; t3~hold12: COFORGE/INFY/SAIL; t3: COFORGE/INFY/SAIL; t4: COFORGE/INFY. `cli.py portfolio` (PnL, PAPER/LIVE split) + `next` (evening step) live.
- Serve fix: ML trains on labeled past, scores label-free frame (`need_label=False`) — was blind to latest 5 sessions (day-1 first run: 0 signals). SIGNAL lines preview `~shares @ ~Rs`; LIVE block shows only for promoted tree(s).
- Batch-3 CLOSED (`res_20260908_rel_b1` COMPLETE, 20/20): 8 tested, 1 in-ledger PAPER_READY `ml_ridge_rel_t5~top_n8` (ridge top-4, IS +66.9/trade, OOS +417.2/trade, robustness 1.0, survived falsify+liquidity). Totals: 1 PAPER_READY, 13 REJECT, 2 SCREENED.
- Perf: iteration 27m → ~12s steady-state (early-kill + pilot LOW_N-only + shared panel cache + val-slice + signal reuse). Batch-3 (budget 8) ran ~25m incl. one-time panel warm.

## Known Issues
- League has 1 day of signals; scale gates need ≥10 closed trades before any promotion.
- LOO falsification probes only 4 alphabetical symbols — weak probe design; attribution (top-2 names 82% of OOS net) supports kills so far, but probe should randomize/broaden.
- ADV measured in shares penalizes high-price names (MRF tradable in reality) — switch to rupee-volume ADV later.

## Next (single source for the next task — agents pull from here, not HANDOVER)
0. FIRST: confirm no background job running (`ps` + `research_runs` status) — one long job at a time.
1. Evening loop (after each close): backfill daily bars → `cli.py next` (fills + new signals) → `cli.py portfolio`. Next run: after 9/10 close.
2. Promote winner to LIVE twin near scale gate (≥10 closed, avg ≥Rs90): human places orders, fills via `log_live_fill`, divergence via `live_vs_paper`.
3. Denser ML sweep (model/features/top-N variants via `seeds=[...]`); then backlog: LEVEL-0 family IC gate → feature-attribution findings → portfolio simulator + allocation.
