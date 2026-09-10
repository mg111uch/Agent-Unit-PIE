# popula_dyn — roadmap

> Agent rule: this file tracks UNIMPLEMENTED work only (Next up / Deferred).
> When an item ships, move it to `README.md` Features Overview and delete it here.
> Sim is a **domain engine** (resource flows + signals + composable behaviours), not a second research loop. Kernel owns cognition; every item must map to ontology + emit signals.

## Next up (project-aligned: signal-centric, ontology-first, modular, emergent — not hardcoded civ roles)

| Item | Status | Depends on |
|---|---|---|
| Twin → params what-if (city/human twin data → sim params, real-data scenarios) | open (was Option A) | twin modules + kernel retrieve |
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
