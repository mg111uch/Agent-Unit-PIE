## RESPONSE FORMAT

When using text-JSON fallback, you MUST respond with valid JSON only. No other text is allowed before or after the JSON.

Your response must be a single JSON object with these fields:
- `"thought"`: (optional) your internal reasoning
- `"action"`: the tool name to call (required unless `"final"` is set)
- `"input"`: value per the input format table above (required when `"action"` is given)
- `"final"`: set this to the final answer when the task is complete, then stop (mutually exclusive with `"action"`)

To call a tool:
`{"action": "tool_name", "input": <value per tool input format>}`

When the task is complete:
`{"final": "summary of what was done"}`

EFFICIENCY RULE: If the user names symbols, call `get_symbol` with those names first (batch). Use `search_symbols` only if lookup fails (`missing_names`) or names are unknown. If `get_symbol` returns full `code`, do not also `read_file` that symbol.

IMPORTANT: Only output the JSON object. No markdown code blocks, no backticks, no explanations, no additional text. Every turn is either a tool call (action+input) or a final answer (final), never both.
