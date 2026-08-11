I reviewed the latest `PlanFixes3.md` and the current implementation status. You are at an important transition point: **the original token-bloat problem is essentially solved, and the local FunctionGemma tier is now implemented but not yet reliable enough to become the default router.**

The next work should therefore be **benchmark-driven**, not another large refactor.

### Current architecture

You now have:

```text
User
 │
 ▼
Deterministic factory ──────────────┐
 │                                  │
 │ obvious                          │ ambiguous
 ▼                                  ▼
Direct executor                FunctionGemma
                                    │
                                    ▼
                              policy/validator
                                    │
                                    ▼
                              tool executor
                                    │
                                    ▼
                               result
                                    │
                                    ▼
                         Cloud Gemini only
                         when reasoning needed
```

This is exactly the architecture I would pursue. The implementation already has the local router, fixed action vocabulary, policy gate, Ollama backend, and zero-cloud live path. 

But there is one major warning: **FunctionGemma 270M is currently misclassifying even simple operations** and CPU inference can be extremely slow under load. 

## What I would do next — in this order

### 1. Finish the deterministic factory first

Before tuning FunctionGemma, expand Tier 1.

You already have the principle:

> obvious filesystem operations should bypass models entirely. 

Make these deterministic:

```text
list directory
find file
check existence
create directory
delete file
read known file
```

The goal:

```text
"create directory X"
        ↓
os.makedirs(X)
        ↓
0 LLM calls
```

and:

```text
"does X exist?"
        ↓
Path.exists()
        ↓
0 LLM calls
```

This is more valuable than improving FunctionGemma for these cases.

---

## 2. Do NOT add `make_directory` just because it was previously suggested

The current design deliberately dropped the dedicated tool and lets the factory use:

```text
execute_command("mkdir -p ...")
```

That decision is reasonable **if the factory handles it before the model**. 

I would keep it that way for now.

The objective should be:

```text
Tier 1:
create_directory → direct Python operation
```

rather than:

```text
Tier 2:
FunctionGemma → create_directory
```

for obvious commands.

---

# 3. Make FunctionGemma accurate before adding more functionality

This is currently your biggest technical blocker.

The live test:

```text
"list the files in /tmp"
```

produced:

```text
act_1 = Read
args = {}
```

which was correctly rejected by the policy layer. 

That's **not good enough for production routing**.

Don't add more actions yet.

Instead build a small routing dataset:

```text
input                                      expected

list files in /tmp                        list
show contents of foo                      list
read foo.py                               read
open foo.py                               read
find fibonacci.py                         glob
search for "TODO"                         grep
create file foo.txt                       write
modify foo.py                             edit
run git status                            execute
does foo.py exist                         exists
```

I'd start with **50–100 examples per action**, including adversarial wording.

Then fine-tune FunctionGemma.

The project's own status already identifies this as the next major local-router task. 

---

# 4. Benchmark FunctionGemma against a stronger small model

Don't assume FunctionGemma 270M is the optimal local model simply because it is designed for function calling.

Your CPU benchmark should compare:

```text
FunctionGemma 270M
Qwen 3 4B
Llama 3.2 3B
```

but only for:

```text
tool classification + argument extraction
```

Measure:

```text
accuracy
cold latency
warm latency
p50
p95
RAM
CPU
invalid-tool rate
argument accuracy
```

The current FunctionGemma result—~55 seconds under load—is obviously unacceptable for an interactive router. 

If FunctionGemma becomes:

```text
warm inference = 100–300 ms
accuracy = 98%+
```

great.

If Qwen/Llama gives:

```text
warm inference = 500 ms
accuracy = 99.5%
```

I'd take the more accurate model.

---

# 5. The most important architectural improvement: batch local actions

This is the next major evolution.

Currently your local router does:

```text
cloud
 ↓
one action
 ↓
FunctionGemma
 ↓
execute
 ↓
cloud
```

Don't stop there.

The desired architecture is:

```text
Cloud Gemini
    │
    │ "ACTION PLAN"
    ▼
┌─────────────────────────────┐
│ Local action interpreter    │
│ FunctionGemma / deterministic│
└──────────────┬──────────────┘
               │
        N validated actions
               │
               ▼
       deterministic executor
               │
               ▼
         aggregated result
               │
               ▼
        Cloud Gemini
```

Your own plan already calls this out as unfinished. 

For example, Gemini should be able to produce:

```text
ACTION find_file fibonacci.py
ACTION read_file <result>
ACTION grep TODO src/
```

The local layer executes the whole batch before Gemini is called again.

That eliminates **Cloud → local → Cloud ping-pong**.

---

# 6. Separate "action generation" from "tool execution"

I would introduce an explicit internal object:

```python
ActionIntent(
    action_id="read",
    arguments={"path": "..."},
    confidence=...,
    source="functiongemma",
)
```

Then the pipeline becomes:

```text
Natural language
      ↓
ActionIntent
      ↓
Validation
      ↓
Policy
      ↓
Executor
```

Never:

```text
FunctionGemma → executor
```

directly.

You already have much of this separation through the policy gate. 

Formalizing it now will make later agent evolution much easier.

---

# 7. Add confidence + deterministic fallback

FunctionGemma shouldn't be treated as:

```text
correct / incorrect
```

Give it:

```json
{
  "action": "list",
  "args": {"path": "/tmp"},
  "confidence": 0.96
}
```

Then:

```text
confidence >= .95
    ↓
execute

.70–.95
    ↓
deterministic validation / retry

< .70
    ↓
cloud reasoning
```

However, don't blindly trust a model-generated confidence score. Ideally combine it with **structural validation**:

```text
valid action ID
+ required arguments present
+ argument types valid
+ path valid
+ policy allows operation
```

That gives you a much better confidence signal.

---

# 8. Don't optimize the system prompt yet

This is now surprisingly low priority.

Your remaining PlanFixes3 item says:

```text
1,288 → target 700–900
```

with core-only already around **831 tokens**. 

I would simply enable/test the core-only variant and measure.

If it works without behavioral regression:

```text
~1,288
   ↓
~831
```

Great.

But don't spend days shaving:

```text
831 → 700
```

while FunctionGemma is taking 55 seconds.

**Latency and routing accuracy are currently much more important.**

---

# 9. Defer irrelevant-history optimization

You correctly identified that prior completed turns are still included, but they're only ~46 tokens. 

Don't touch this now.

The stateful Gemini mechanism is working, and the tool schemas are down to ~237 tokens. 

Those are already good enough.

---

# 10. Your next benchmark should be the decision point

Build one benchmark that compares:

### A — Current Gemini tool calling

```text
Gemini → schemas → tool
```

### B — Gemini → FunctionGemma

```text
Gemini → action
        ↓
FunctionGemma
        ↓
executor
```

### C — Deterministic → FunctionGemma fallback

```text
request
 ↓
factory
 ├── recognized → executor
 └── ambiguous → FunctionGemma → executor
```

This exact three-way benchmark is already identified in your plan. 

Use at least:

```text
20–50 tasks
```

across:

* read
* list
* search
* grep
* write
* edit
* create
* git
* shell
* nonexistent paths
* invalid requests
* ambiguous requests

Measure:

```text
cloud input tokens
cloud output tokens
cloud calls
local calls
local p50
local p95
total latency
CPU
RAM
accuracy
tool failures
false successes
```

---

# 11. The success metric should change

Don't make:

> minimum tokens

your primary objective anymore.

Use:

```text
Agent Efficiency Score =
correctness
× task completion
────────────────────
cloud tokens + latency
```

or simply track a dashboard:

| Metric                       |        Goal |
| ---------------------------- | ----------: |
| Deterministic simple tasks   |        ≥90% |
| Local-router accuracy        |        ≥98% |
| False-success                |       **0** |
| Cloud tool schemas           |       **0** |
| Cloud calls for simple tasks |       **0** |
| Local router p95             | <1s ideally |
| Stateful cloud continuation  |   preserved |
| Cloud tokens/task            |    minimize |

---

# My recommended next 4 phases

### Phase A — **Factory completion**

Implement/verify all obvious filesystem operations.

**Goal: zero LLM for simple tasks.**

### Phase B — **Local-router accuracy**

Create dataset → fine-tune FunctionGemma → test accuracy.

**Goal: ≥98% action + argument accuracy.**

### Phase C — **Latency/model bake-off**

FunctionGemma vs Qwen/Llama on your i3.

**Goal: choose the fastest model that is reliable enough.**

### Phase D — **Batch action plane**

Cloud produces a compact action plan → local router/executor performs multiple actions → cloud synthesizes only when required.

**Goal: eliminate cloud/local ping-pong.**

---

## The key strategic decision

I would **not make FunctionGemma the center of the agent**.

Make the architecture:

```text
             ┌──────────────────────┐
             │   DETERMINISTIC      │
             │   FAST PATH          │
             │   0 LLM              │
             └──────────┬───────────┘
                        │
                     ambiguous
                        │
                        ▼
             ┌──────────────────────┐
             │   LOCAL ROUTER       │
             │   FunctionGemma      │
             └──────────┬───────────┘
                        │
                     complex
                        │
                        ▼
             ┌──────────────────────┐
             │   CLOUD REASONER     │
             │   Gemini             │
             └──────────────────────┘
```

That gives you a **progressive intelligence architecture**: don't invoke a more expensive/intelligent layer until the cheaper layer cannot solve the problem.

Your current code is already very close to this. The next milestone isn't another token optimization—it is **proving that this three-tier architecture is faster and at least as reliable as the original cloud-tool-calling architecture.**
