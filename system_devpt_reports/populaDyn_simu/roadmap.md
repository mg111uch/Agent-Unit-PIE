# popula_dyn — roadmap

> Agent rule: this file tracks UNIMPLEMENTED work only (Next up / Deferred).
> When an item ships, move it to `README.md` Features Overview and delete it here.
> Sim is a **domain engine** (resource flows + signals + composable behaviours), not a second research loop. Kernel owns cognition; every item must map to ontology + emit signals.

## Next up (project-aligned: signal-centric, ontology-first, modular, emergent — not hardcoded civ roles)

| Item | Status | Depends on |
|---|---|---|
| Promote urban levers: multi-seed + falsification (SIM-03) | ✅ 3 levers `FALSIFICATION_PASSED` (3 seeds, n=37.2k); Kanpur transport stays `HYPOTHESIS` | `stability(seeds=…)` + `falsify_policy` |
| Deterministic hire order (Kanpur transport noise) | ✅ true-nearest pick with `unit_id` tie-break; dividend payout moved to step end (mid-step payout drained hiring cash) | urban labour loop |
| Baseline-vs-policy compare + visual diff (non-technical policy UI) | open (was Option B) | connector compare_runs |
| Self-evolution loop (auto-summarize learnings, hypothesis→sim→validate, recursive refinement) | open (was Option C) | hypothesis engine + compression |
| Seasonal yields + soil degradation/fallow + weather shocks + pollution feedback | open (top realism upgrades) | regrow + environment |
| Specialist reproduction with role mutation + overwork deaths | open | agent factory |
| Innovator agent (learn/optimize: R&D boosts skill caps) + Ecologist (heals fertility, forecasts yield) | open (composable behaviours only) | behaviour registry |
| Meso agents on demand (household/institution layers only when a policy needs them, e.g. taxation) | deferred (micro+macro answer current questions) | driving policy question |

## Deferred (not done — game layer / hardcoded civ / heavy geo)

| Item | Status | Depends on |
|---|---|---|
| Community/City/Group/Civilization entities + leadership/culture/diplomacy/war/expansion/tech-tree | deferred (violates emergent-not-hardcoded rule until behaviours prove it) | Group class + conflict design |
| Warrior raiding + Ruler taxation/revolt + Merchant Guild caravans | deferred (needs compete/coordinate behaviours + Group) | conflict + trade graph |
| Gender auto-balance, litter-size 1–2, migration votes | deferred | trait schema |
| Real GIS/GeoGrid world map (Natural Earth/OSM, rivers/mountains, NOAA climate, Dijkstra paths) | deferred | GeoGrid subclass + data feeds |
| Civ game shell (victory paths, multiplayer, scenario editor, achievements, zoomable Pygame/Plotly/Leaflet) | deferred product layer, no frontend tests per policy | game server |
| Cumulative plots in game UI | deferred (was Later idea) | UI policy change |
| Pharma-style modules (event_bridge/world_engine/resource_engine redesign) | deferred (unread, do not redesign yet) | code reading |

(End of file)
