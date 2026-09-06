# FixesIssues — status (cleaned 2026-09-06; full discussion in git history)

## Prompt (original)
Stock analyser not converging fast — add deep learning? Recommend fast-profitable quant strategies + research-loop gaps. Population sim develops slowly per loop — need agricultural→modern→future leaps while staying grounded.

## Shipped
All items implemented; each lives in its module README (features tables are the shipped record):
- Universal loop leap branch → `data/workflows/research_development.md` + both READMEs (Phase0 rows).
- Stock ladder, regimes, features, info scoring, rank validation, stall retirement → `stock_analyser/README.md` (Phase1/Phase2/Adds rows).
- Sim epoch, falsification, policy lab, robustness → `populaDyn_simu/README.md` (Phase3/A/B/C + Adds rows).

## Remaining (in roadmaps, not here)
- Small deep models (MLP→CNN→GRU→Transformer) + RL/policy learning → `stock_analyser/roadmap.md` Deferred (deliberate: classical ML + residual alpha first).
- Cross-sectional/pairs/basket strategies, portfolio simulator, feature-attribution, OOS hardening → `stock_analyser/roadmap.md` Next up.
- Deep-ML gate stays: `gate_families` blocks family jumps until L2 evidence justifies escalation.

(End of file)
