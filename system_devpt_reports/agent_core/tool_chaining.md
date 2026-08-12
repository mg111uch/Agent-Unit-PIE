# Tool Chains — turning repeated multi-step operations into one call

Some tasks always run the same sequence of tools. Instead of letting the agent
walk through those steps every time — spending tokens on each decision — a
**tool chain** packages the sequence so the whole thing runs as a single,
named call.

## The core principle

> When the same sequence of tools reliably produces the same outcome, stop
> paying for it step by step. Run it as one unit.

A chain is not a faster model. It is a deterministic recipe: step A, then B,
then C, with each step fed by the results of the one before it. The agent makes
one decision ("use this recipe") instead of re-deciding at every step.

## What makes up a chain

| Piece | What it is |
|-------|------------|
| Handwritten chain | A recipe bundled with the agent (read a module's structure, run a doc health check, apply and verify a safe edit) |
| Learned chain | A recipe the agent discovered by watching your sessions and noticing the same sequence happens again and again |
| Step | One tool call inside the recipe, bound to the chain's inputs and to values produced by earlier steps |

The agent ships with a few useful handwritten recipes out of the box. Learned
recipes grow over time as it observes real usage.

## How a chain runs

```text
     USER REQUEST
          │
          ▼
  "read a module's structure"      instead of:  pick tool → run → pick tool →
          │                                      run → pick tool → run
          ▼
  CHAIN "probe_module" ──► step 1 ► step 2 ► step 3
          │                  │        │        │
          ▼                  ▼        ▼        ▼
   ONE RESULT           each step binds inputs from the
   returned to the      request and from earlier steps
   model
```

To the model it looks like a single, self-contained operation. The per-step
decisions and intermediate bookkeeping happen inside the chain, and the
chain's total output is bounded so a recipe can never blow up the context.

## How learning works

The agent watches the tool calls made across your sessions. When a sequence
appears often enough, it becomes a **candidate** recipe:

- **Read-only recipes** — sequences that only inspect the workspace — are safe
  to reuse instantly and go live automatically.
- **Recipes that write or edit** can change your files, so they are kept as
  candidates until you explicitly approve them.

Once live, a learned chain is persisted and reloaded on the next start; it
behaves like any other tool. Recipes that stop being used are quietly
retired. Approve or delete candidates with the **chain_admin** tool
(`list`, `candidates`, `approve`, `activate`, `delete`).

## Configuration at a glance

| Setting | Meaning |
|---------|---------|
| Chaining enabled | Expose tool chains to the agent on/off |
| Pattern mining | Let the agent learn new recipes from your sessions on/off |
| When to mine | At the end of a session, mid-session, both, or neither |
| Candidate frequency | How often a sequence must occur to become a candidate |
| Sequence length | How many steps a learned recipe may span |
| Minimum savings | Don't promote a recipe unless it saves at least this many tokens per use |
| Context hints | Remind the agent of learned recipes and usage notes in its context |
| Staleness window | Retire learned recipes not used within this many days |

## Guaranteed properties

- **Deterministic, not guessed** — a chain is a fixed recipe; no model decides its steps at runtime.
- **Read-only recipes are safe by default** — only inspection sequences auto-activate; anything that writes or edits waits for your approval.
- **Bounded output** — a recipe can never fill the context; total output is capped.
- **The agent only mentions recipes it can use** — a learned chain is never suggested to the agent while chaining is turned off.
- **Nothing is deleted unrecoverably** — retired recipes can be reactivated; handwritten recipes are never touched.