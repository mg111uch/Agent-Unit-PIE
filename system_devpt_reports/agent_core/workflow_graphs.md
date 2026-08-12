# Workflow Graph — the agent's living map of how work gets done

Every session leaves a trace: which tools ran, in what order, which repeated
sequences saved effort, and where things went wrong. The **workflow graph** is
what the agent builds from that trace — a structured, browsable picture of how
your work actually gets done, kept up to date across sessions.

## The core principle

> Observe what the agent really does, turn repeated patterns into reusable
> recipes, and let both the agent and you see the result.

The graph is the memory layer behind tool chains: chains are the recipes, the
graph is the map of how they connect to each other and to your observed usage.

## What the graph records

| Element | What it is |
|---------|------------|
| Recipe clusters | Each tool chain appears as a named cluster with its steps shown in order |
| Candidate shortcuts | A repeated sequence not yet a full chain is drawn as a shortcut the agent could promote |
| Usage notes | Learned dos and don'ts, plus per-tool statistics gathered from real sessions |
| Versioning | Every rebuild is stamped, so you can see when the map last evolved |

New information is only ever **added** — patterns become shortcuts, a promoted
shortcut collapses into a full recipe node. Nothing the graph learns is applied
to the live agent automatically; it is surfaced for you and the agent to act on.

## How the agent uses it

The graph closes the loop between past sessions and future work:

```text
  SESSION 1 ─┐
  SESSION 2 ─┼──► observe tool usage ──► build/evolve the graph
  SESSION 3 ─┘                              │
                                            ▼
                 reminds the agent of learned            you see a visual
                 recipes + dos and don'ts                map in your browser
                        │                                    │
                        ▼                                    ▼
                   next session uses                        inspect recipes,
                   what was learned                         approve candidates
```

Dos and don'ts are only injected into the agent's context when the feature is
enabled, and a recipe is only ever mentioned if it is actually exposed as a
tool — the agent is never told to call something it cannot see.

## How you view it

- **In the browser** — a live, interactive graph served locally. Recipe
  clusters are rendered as subgraphs you can expand, notes toggle on and off,
  and the page re-reads the latest state every refresh.
- **Ask the agent** — the **workflow_status** tool answers on demand:
  `summary` for the short version, `full` for the complete map, `candidates`
  for sequences waiting to be promoted, or `evolve` to rebuild from the latest
  data.

## Configuration at a glance

| Setting | Meaning |
|---------|---------|
| Graph evolution | Rebuild the graph from chains, candidates, and session usage on/off |
| Context hints | Inject learned dos/don'ts and recipes into the agent's context on/off |
| Pattern mining | Feed new candidates from session activity into the graph on/off |
| Staleness window | How long unused learned recipes stay before being retired from the map |

## Guaranteed properties

- **Read-only awareness** — the graph only observes what already happened; it never changes your files or runs tools.
- **Promotion is never automatic for writes** — shortcuts affecting files wait for your approval before becoming live chains.
- **The agent is never told to use hidden tools** — learned recipes are referenced only when they're actually available.
- **Nothing destructive** — retiring a recipe keeps it recoverable; handwritten recipes are never removed.
- **See-through** — everything the graph learns is inspectable and rebuildable on demand.