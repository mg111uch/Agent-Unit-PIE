# PhasePlan — deep integration: Kernel · FireFlow · economy · popula_dyn · digital twins

Status: COMPLETE 2026-09-15 (all gates PASS, see log). Detail bodies removed —
shipped features live in module docs (single source, no duplication):
kernel → `system_devpt_reports/kernel/README.md`,
economy → `.../economy/README.md`,
twins → `.../digital_twins/README.md`,
popula → `.../populaDyn_simu/README.md`,
FireFlow → `README.md` + `roadmap.md` in `/home/manigupt/Hello/reddit-clone`.
Source: `system_devpt_reports/FixesIssues.md` + `FeatureIdeas.md`. Operating rules: `AGENTS.md`.

Scope note: both tracks done in-repo + FireFlow backend (jest only, no frontend).
Moonshot ladder (§27) stays LOCKED.

## Phases (pointers only)

- Phase 0 registry → kernel README (Capability Activation Registry).
- Phase 1 identity → kernel README (Versioned Unit Schema Artifact) + twins README.
- Phase 2 bus + adapter → kernel README (Kernel Bus) + economy README (event adapter).
- Phase 3 signal slice → twins README (capacity slice).
- Phase 4 twin data-models → twins README (CityTwin/CityState/adapters/versioning).
- Phase 5 calibration + experiments → twins + popula READMEs.
- Phase 6 contrast + flywheel → twins README.
- IN-1 truth tiers + IN-2 opportunity evidence → twins + economy READMEs.
- FF-A drift/contract tests → FireFlow README; FF-B gateway (`backend/pie/` + `economy/pie_protocol.py`) → FireFlow README.
- FF-C authoritative ledger → FireFlow README; FF-D settlement + dataset licenses → FireFlow README.
- Sensors (reliability + anti-fraud) → twins README + FireFlow README.

## Phase gates log (append-only)

- Phase 0 (2026-09-15): PASS — `kernel/capability_registry.yaml`, 66 entries (16/8/42), renders via yaml.safe_load.
- Phase 1 (2026-09-15): PASS — `unit_schema.v1.json` renders; 0 live actor refs; twins create+resolve Units; no FireFlow changes.
- Phase 2 (2026-09-15): PASS — shaped PaymentSettled → event → signal → memory read-back on tmp DB.
- Phase 3 (2026-09-15): PASS — Kanpur capacity question answered from cascade (3/3/1 + history), candidates-only causality.
- Phase 4 (2026-09-15): PASS — two versioned JSON/SQLite twins with provenance; kanpur v1 retired HISTORICAL.
- Phase 5 (2026-09-15): PASS — baseline pop err 0.036; one twin→popula→scenario→finding run with lineage (sim@2cac23d).
- Phase 6 (2026-09-15): PASS — contrast table + null Pareto verdict; sensor→twin→scenario→opportunity finding; moonshot ladder stays LOCKED.
- IN-1+2 (2026-09-15): PASS — truth tiers on all 14 fields; evidence-gated opportunity scoring + EV, 7-factor intact.
- FF-A (2026-09-15): PASS — vendored artifact fresh; 8/8 drift + contract jest green.
- FF-B (2026-09-15): PASS — pie gateway envelopes + server-side RBAC; in-repo parity builders; 12/12 jest.
- FF-C (2026-09-15): PASS — authoritative ledger (idempotency, state machine, no double-count, fee splits, gig gate); 18/18 jest.
- FF-D (2026-09-15): PASS — settlement pipeline + dataset licenses; 23/23 jest.
- Sensors (2026-09-15): PASS — in-repo reliability smoke + FireFlow anti-fraud fields/confirm/capability scores; 26/26 jest.

## Open items (not yet built)

- Hierarchy/relation retrievers still DORMANT (cascade is unit/timeline/pattern only).
- Split oversized twin files when next touched (`city_twin.py` 741L); deltas only until then.
- `promote --keep` for parallel ACTIVE trees (stock; rotation is the only path today).
- Real city feeds for conf≤0.35 placeholders; twin water/energy/air scoring dims once fed.
- Multi-seed + falsify for policy experiments before any finding above HYPOTHESIS; calibration caps (pop 400, skill 1.0) on every record.
- Stock: hole closed at 51/0 — no new sweep without a new family/idea; evening loop only until exits land.
