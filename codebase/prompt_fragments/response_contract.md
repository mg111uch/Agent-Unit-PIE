## RESPONSE FORMAT

Use native function calling when available. Respond with one or more function calls in a single turn. Batch independent calls together — do not sequence them one-at-a-time.

## EFFICIENCY RULES

1. **Step budget:** Aim to answer in at most 3-4 tool calls. If searching or grepping more than twice, stop and re-plan — you are wasting steps.
2. **Deadline:** Produce a final answer promptly. Do not analyze the same file more than twice — read once, follow up once, then answer.

## EXAMPLE OF CORRECT BATCHING

User: "Check temp/dummy/fibo/fibonacci.py exists and show me its imports."
Correct first response (two tool calls in ONE turn, not two turns):
  [get_workspace_info(), read_file(path="temp/dummy/fibo/fibonacci.py")]
Incorrect: calling get_workspace_info alone, waiting for the result, then
calling read_file in a separate turn.
