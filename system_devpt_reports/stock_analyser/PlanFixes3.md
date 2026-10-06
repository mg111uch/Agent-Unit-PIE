Before I answer, I'll verify the futures cost schedule and the bulk-deal data source, because both change the "what next" answer.With your constraints as stated, a profitable, validated edge is very unlikely. That means public end-of-day data, long-only delivery trades, and ₹10k-sized positions. In my judgment the odds of finding one by further search on those inputs are under 5%.

I've added a placebo-controlled event study and the data-hygiene helpers for it (11/11 synthetic tests pass), but neither has run against your data.

## Why I'd close the long-book search

- **The ceiling is measured, not theoretical.** Your own numbers imply about +3bps gross per hold for the OHLCV ridge at h=5 (net −42.7 at a 46bps tariff), and −19bps for delivery.
- **The failures are independent.** OHLCV, delivery, breadth, OI and the pre-registered finalist all fail for the same reason: gross per hold is far below cost.
- **Frequency isn't the problem.** Your 97–5000 trades a year result says so directly.
- **A real signal can still be uneconomic.** `dlv_z60` is statistically real (IC 0.039, block-null p 0.002), but its extremes are monotonically negative. A signal that works in the middle of the distribution and fails in the tails can't be harvested with a top-N book.

## The only two levers that could change this

**1. Cheaper execution (futures): ruled out.**
- Futures STT is **0.05% on the sell side** since 1 April 2026, up from 0.02%. Old sources still quote the old rate.
- Round-trip cost is about 5bps STT plus small exchange, stamp and SEBI fees and ₹20 per order. With slippage, I estimate roughly 10–15bps all-in, against 46bps for delivery.
- That would cut costs about 3×, but your measured gross per hold (+3bps, −19bps) is below even that. It also needs lakh-scale margin per lot.
- A 10-minute check: rerun `horizon_scan` with `cost_bps=12` and a long-short leg. I expect it to fail.

**2. New information that is slow to be priced and trades rarely.** This is the one remaining door.
- Insider purchases are the best-evidenced candidate I found. An Indian event study reports a 90-day CAAR of 6.67%, concentrated in smaller firms and consistent with underreaction.
- That's about 14× your round-trip cost, so even a heavily discounted version would clear it. It's an event-study average, though, so liquidity and dating effects can inflate it.
- Bulk deals are the weaker candidate. One working paper finds the price run-up *precedes* disclosure.

## What to do next

1. **Check for an insider-filing source first.** Ask whether NSE's corporate-filings insider-trading page offers a date-range CSV export. I couldn't verify that.
2. **Pre-register the insider test before touching data.** Suggested pass rule, all required, using your own `grant_epoch_override` hash discipline:
   - at least 300 events after filters (open-market purchases only), and the month-clustered test needs at least ~10 events a month, or a null means "unknown", not "no edge";
   - `excess_vs_placebo` of at least 150bps at h=40, with `t_vs_placebo` ≥ 3;
   - positive in at least 70% of calendar years, and robust to dropping the top 5% of events and Mar–Jun 2020.
3. **Run it once, then stop either way.**
4. **Start forward point-in-time snapshots of the feeds today.** Bulk-deal data is revisable at members' request, so history isn't what you'd have seen live. Snapshotting costs almost nothing.
5. **Write a closure memo.** State the verdict, the gross-per-hold ceiling, what was falsified, and the one reopen condition (Q5 below).

My rough odds that insider events survive the placebo, clustering and cost: about 15–25%. That's judgment, not measurement.

If the goal is profit rather than research, a strategy with zero net edge after STT, DP and tax has negative expected value. I'm not a financial advisor, and this isn't personal advice.

## Your 6 questions

1. **Veto overlay:** it's statistically legitimate as one pre-registered test, but I'd drop it.
   - **Little to gain:** if ~1% of name-days are flagged at about −100bps, the gain is ~1–2bps per hold, and only on a book that would otherwise hold those names.
   - **Mechanical spikes:** extreme delivery spikes cluster around ex-dates, OFS, buybacks and index rebalances. Check that before calling it a tail.
   - **Not tradable:** in delivery you can't short the tail, and the F&O names where you could have the weaker edge.
2. **Small-cap delivery edge at 46bps:** structurally unharvestable as a daily flow signal. Real costs there (spreads, circuits, T2T) exceed your model's. The only construction that amortises the tariff is slow, event-driven, small-cap, which is the insider test above.
3. **OI × delivery into expiry:** stop. Market-wide OI timing is null, so another interaction is another hypothesis with no prior.
4. **Bulk/block deals as the event feed:** acceptable and verifiable. NSE publishes both, and exchanges must disseminate block deals the same day after market hours. The traps:
   - Both are disclosed after the close, so enter the next session.
   - Net buy and sell legs by client per day to remove intraday round trips.
   - Use CSV downloads, since the web page shows only 50 records.
   - Block-window timings and thresholds changed over the years. Use the deal flag.
   - Expect a likely null, given the run-up-before-disclosure evidence.
5. **What would reopen the search:** one of two things.
   - A horizon with net long-leg excess whose lower confidence bound is above zero at the 46bps tariff, surviving the block null.
   - An event family with ≥ 300 events, `excess_vs_placebo` ≥ 150bps at h ≥ 20, and `t_vs_placebo` ≥ 3.
6. **Shadow before maturity:** pure patience. At 60 days the standard error of IC is about 0.03 (≈0.1/√12), so you can only exclude an IC above ~0.07. Do a futility check only if it's pre-registered.

## Code this round

| File | What it does |
|---|---|
| `research/events.py` | Same-symbol placebo dates, a `tradable` mask for circuit/T2T entries, month-clustered t on excess-versus-placebo |
| `research/event_prep.py` | Split-safe adjusted prices from `close/prev_close`, a flag for implausibly large moves, disclosure-time to first-tradable-date, bulk-deal netting |

- **The placebo works:** on a synthetic set of events drawn only from persistently rising names (no true event effect), the raw excess was +216bps with month-clustered t = 5.7. After the placebo it fell to +27bps (t = 0.46). A real planted effect still survives.
- **Run `artifact_days()` on your bhav data first.** The adjusted-price chain assumes the exchange re-bases `PREV_CLOSE` on ex-dates. I couldn't verify that on live files, so confirm it on a few known splits and bonuses.

The project's lasting value is the verdict and the validation stack: block-null IC, purged scans, trial counting and placebo-controlled event tests.