# Model Routing — how the agent decides which model handles your request

The agent does not send every request to the same model. It uses three layers of
increasing cost and intelligence, and only escalates to the next layer when the
cheaper one cannot solve the request. Expensive reasoning is never wasted on
obvious operations.

## The core principle

> Don't invoke a more expensive or more intelligent layer until the cheaper
> layer cannot solve the problem.

A simple filesystem request should cost almost nothing. A genuinely complex
request — planning, debugging, multi-step reasoning — is where a powerful cloud
model earns its keep. Everything in between is handled by a tiny routing model.

## The three tiers

| Tier | Name | What runs it | Handles | Cost |
|------|------|--------------|---------|------|
| 1 | Deterministic fast path | Code, not a model | Obvious filesystem operations: list a directory, read a file, check existence, create a directory | ~0 tokens |
| 2 | Model router | A small, cheap model (cloud or local) | Requests the fast path can't confidently classify — ambiguous phrasing of a single operation | ~300–400 tokens |
| 3 | Cloud reasoning | The conversational cloud model | Complex, multi-step, or truly unclear requests that need planning and synthesis | Full reasoning |

## How a request flows

```text
                       USER REQUEST
                            │
                            ▼
              ┌─────────────────────────┐
              │  TIER 1  deterministic  │   code, patterns — no model
              │  fast path              │
              └────────────┬────────────┘
                           │
              can it be answered without a model?
                 /                      \
              YES                        NO  (ambiguous)
               │                          │
               ▼                          ▼
        TOOL RUNS            ┌────────────────────────────┐
        directly             │  TIER 2  model router      │   tiny model
        (instant, no         │  one operation from a      │   fixed 9-operation
        model involved)      │  fixed catalog             │   vocabulary
                             └──────────────┬─────────────┘
                                            │
                              classified? + valid?
                                 /             \
                              YES / routes      NO
                               │  to a tool       │
                               ▼                  ▼
                        POLICY GATE        ┌──────────────────────┐
                        validates before   │ TIER 3 cloud         │   reasoning
                        anything runs      │ reasoning model      │   model
                                           └──────────────────────┘
                                                    │
                                                    ▼
                                              FINAL ANSWER
```

Every tier-2 output passes through a **policy gate before any operation runs**:
unknown operations are rejected, destructive commands are blocked, required
parameters must be present. The router is a classifier, never a trusted
executor.

## What each tier sees

A key design property is that a request is never duplicated wholesale to every
layer — higher layers only appear when needed, and the routing layer stays tiny.

| Tier | What it sees | What it never sees |
|------|--------------|--------------------|
| 1 | The request text | Nothing — it is code, not a model |
| 2 | The request + a small fixed 9-operation catalog | Your full system prompt, AGENTS.md, workspace context, and the agent's real tool list |
| 3 | The full system prompt, AGENTS.md, and only the subset of tools relevant to the request | The routing catalog (it never sees routing internals) |

Consequence: an ambiguous request routed by tier 2 costs roughly **0.1%** of a
full reasoning call, and the reasoning model is only involved when a request
genuinely needs it.

## What decides which tier runs

- **Obvious single operations** (list, read, exists, mkdir) → tier 1, no model at all.
- **Ambiguous but still single-operation phrasing** → tier 2 routing model.
- **Complex/multi-step/or the router declines** → tier 3 reasoning model.

The tier-2 model is not permanently fixed to one provider. A single setting
switches it between a small **cloud** model (default) and a **local** model
(offline, but slower). If no key is configured, tier 2 is skipped and the
request goes straight to tier 3 — the agent still works, just more expensively.

## Configuration at a glance

| Setting | Meaning |
|---------|---------|
| Tier-2 router enabled | Turn the routing layer on/off |
| Tier-2 backend | Cloud routing model or local routing model |
| Tier-2 model | Which small model to route with |
| Tier-2 timeout | How long a routing call may take before escalating |
| Tool group routing | Limits which tool definitions the reasoning model sees per request |
| Deterministic fast path | Turn tier 1 on/off |

## Guaranteed properties

- **Deterministic first**: the cheaper the layer, the more often it runs.
- **Routing is never trusted**: every router verdict is validated by the policy gate before execution.
- **Cheap routing, expensive reasoning**: the cloud reasoning model is the last resort, not the default.
- **Graceful degradation**: a disabled or failing route step simply escalates to the next tier; nothing is lost.