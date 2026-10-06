# Stock Analyser — Closure Memo (2026-10-04)

Long-book search phase is CLOSED. No construction on any tested information
source clears the tariff with margin. Record: verdict, ceiling, falsifications,
reopen conditions.

## Verdict

No profitable, validated edge exists in OHLCV + delivery + OI data at daily
bars, long-only, ~46bps round-trip tariff. Probability of finding one by
further search on these inputs: <5% (external reviewer concurs).

## Gross-per-hold ceiling (measured, 6y data)

| Source | Best honest read | Net @46bps |
|---|---|---|
| OHLCV ridge h5 | +3bps/hold | −42.7bps |
| Delivery `dlv_z60` h5 | −19bps top-5 | −65bps |
| Delivery h20 top-5 | +48bps once | +2.3bps (t 0.63, noise) |
| Delivery extremes (z≥4, 97/yr) | −199bps gross | −245bps |
| Futures-cost recheck (12bps) | −3/−16bps gross | −15/−28bps |

## Falsified (with evidence)

- OHLCV sweeps (100+ tested, 1 promotable ever; sweeps 6–8 zero PAPER_READY).
- Delivery as long book (real signal IC 0.0386, p 0.002 — uneconomic; tails negative).
- Event/threshold rarity (rarer = worse, monotone; 97–5000 trades/yr all fail).
- OI positioning timing (|ρ| ≤ 0.08).
- Breadth rescue (edge lives in illiquids; N500 `dlv_ret5` h20 = 0.001).
- Pre-registered ridge finalist (SCREENED −38.44, 1 audited trial, no halo).
- Cheaper-execution rescue (fails even at 12bps).

## Still standing (passive or single-shot)

- Shadow book on frozen ridge (matures 60+ days; futility check only if pre-registered).
- Insider-purchase event test (best-evidenced untested source; needs verified bulk route + pre-registered pass rule: ≥300 events, excess_vs_placebo ≥150bps @h40, t≥3, 70% years, ex-top-5% and ex-Mar–Jun-2020 robust).
- Bulk/block-deals feed (verifiable NSE source; expect null — run-up precedes disclosure).
- Delivery-spike veto overlay (legitimate single test; expected gain only ~1–2bps/hold — reviewer advises dropping).

## Reopen conditions (either, else stay closed)

1. A horizon with net long-leg excess whose lower confidence bound exceeds zero
   at 46bps tariff, surviving the block null.
2. An event family with ≥300 events, excess_vs_placebo ≥150bps at h≥20, t_vs_placebo ≥3.

## Data assets retained

- `data/bhav_copy.db` (2020→2026, 1672 delivery-dates, 3.1M rows) + `data/raw_nse/`.
- `data/ind_nifty500list.csv` (501 names).
- Validation stack: block-null IC, purged scans, trial counting, placebo event tests.
- Price-chain guard: `PREV_CLOSE` not rebased on ex-dates (622 artifact-days).

## Open risks / drawbacks

- N500 breadth test carries survivorship bias (today's list on history).
- Bhav starts 2020; 2010+ veto test blocked; bars start 2016.
- OI is market-wide only (no per-symbol breadth).
- Daily bars can't resolve slippage/intraday capture.
