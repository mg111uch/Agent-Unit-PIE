"""ChainEngine: runs a ChainSpec by invoking registered tools locally.

One exposed tool call -> N internal tool calls -> a single combined JSON result.
Handles ToolResult and raw-string returns, $input/$step binding, per-step collect,
per-step char caps, a total token budget, and optional-step skipping.
"""

from __future__ import annotations

import json
from typing import Any, Dict, Optional

from agent_core.tools.chain.chain_spec import ChainSpec, Step
from agent_core.tools.types import ToolResult

_MISSING = object()


def _extract_path(value: Any, path: str) -> Any:
    """Navigate a dotted path into a parsed result. '$' returns the whole value."""
    if path == "$":
        return value
    cur = value
    for part in path.split("."):
        if isinstance(cur, dict):
            if part not in cur:
                return _MISSING
            cur = cur[part]
        elif isinstance(cur, list):
            try:
                idx = int(part)
            except ValueError:
                return _MISSING
            if idx < 0 or idx >= len(cur):
                return _MISSING
            cur = cur[idx]
        else:
            return _MISSING
    return cur


class ChainEngine:
    def __init__(self, spec: ChainSpec, tools: Optional[Dict[str, Any]] = None):
        self.spec = spec
        self._tools = tools  # optional injected tool dict; else live registry

    def _tools_dict(self) -> Dict[str, Any]:
        if self._tools is not None:
            return self._tools
        from agent_core.tools import registry as _reg
        return _reg.tools_dict

    def _resolve(self, value: Any, params: Dict[str, Any], store: Dict[str, Any]) -> Any:
        if isinstance(value, str):
            if value.startswith("$input."):
                return params.get(value[len("$input."):], _MISSING)
            if value.startswith("$step."):
                rest = value[len("$step."):]
                name, _, path = rest.partition(".")
                if not path:
                    return store.get(name, _MISSING)
                step_val = store.get(name, _MISSING)
                if step_val is _MISSING:
                    return _MISSING
                return _extract_path(step_val, path)
            return value
        if isinstance(value, list):
            out = []
            for item in value:
                r = self._resolve(item, params, store)
                if r is _MISSING:
                    return _MISSING
                out.append(r)
            return out
        if isinstance(value, dict):
            out = {}
            for k, v in value.items():
                r = self._resolve(v, params, store)
                if r is _MISSING:
                    return _MISSING
                out[k] = r
            return out
        return value

    def _call_tool(self, tool: str, args: Dict[str, Any]) -> tuple:
        tools = self._tools_dict()
        fn = tools.get(tool)
        if fn is None:
            return None, f"unknown tool '{tool}'"
        try:
            result = fn(args)
        except Exception as e:  # noqa: BLE001 — any tool failure is a step failure
            return None, f"{tool} raised: {e}"
        if isinstance(result, ToolResult):
            if not result.ok:
                return None, result.message or result.data or f"{tool} failed"
            return result.data, None
        text = str(result)
        if text.startswith("Error"):
            return None, text
        return text, None

    def _parse(self, data: Any) -> Any:
        if isinstance(data, (dict, list)):
            return data
        if isinstance(data, str):
            try:
                return json.loads(data)
            except Exception:  # noqa: BLE001 — plain text is a valid value
                return data
        return data

    def _entry_for(self, step: Step, data: Any) -> Any:
        value = self._parse(data)
        if not step.collect:
            return value
        entry = {}
        for alias, path in step.collect.items():
            got = _extract_path(value, path)
            entry[alias] = None if got is _MISSING else got
        return entry

    @staticmethod
    def _compact(entry: Any) -> int:
        try:
            return len(json.dumps(entry, separators=(",", ":"), default=str))
        except Exception:  # noqa: BLE001
            return len(str(entry))

    @classmethod
    def _cap(cls, entry: Any, cap_chars: int) -> Any:
        if cls._compact(entry) <= cap_chars:
            return entry
        preview = json.dumps(entry, separators=(",", ":"), default=str)[:cap_chars]
        return {"_truncated": True, "_chars": cls._compact(entry), "_preview": preview}

    def run(self, params: Optional[Dict[str, Any]] = None) -> str:
        params = params or {}
        store: Dict[str, Any] = {}
        steps_out: Dict[str, Any] = {}
        skipped: list = []
        errors: list = []
        budget_chars = self.spec.budget_tokens * 4
        used = 0
        budget_hit = False
        for step in self.spec.steps:
            args = self._resolve(step.args, params, store)
            if args is _MISSING:
                if step.optional:
                    skipped.append(step.key)
                else:
                    errors.append(f"{step.key}: missing required input")
                continue
            data, err = self._call_tool(step.tool, args)
            if err is not None:
                if step.optional:
                    skipped.append(step.key)
                else:
                    errors.append(f"{step.key}: {err}")
                continue
            store[step.key] = self._entry_for(step, data)
            if budget_hit:
                steps_out[step.key] = {"_omitted": "chain token budget reached"}
                continue
            entry = self._cap(store[step.key], self.spec.step_cap_chars)
            entry_chars = self._compact(entry)
            if used + entry_chars > budget_chars:
                budget_hit = True
                used = budget_chars
                steps_out[step.key] = {"_omitted": "chain token budget reached"}
                continue
            steps_out[step.key] = entry
            used += entry_chars
        result = {"chain": self.spec.name, "steps": steps_out}
        if skipped:
            result["skipped"] = skipped
        if errors:
            result["errors"] = errors
        if not steps_out and errors:
            return f"Error: chain '{self.spec.name}' failed: {'; '.join(errors)}"
        return json.dumps(result, separators=(",", ":"), default=str)


def make_chain_tool(spec: ChainSpec):
    """Build the tool-callable function for a ChainSpec (returns JSON string)."""
    engine = ChainEngine(spec)

    def fn(params=None):
        try:
            from agent_core.tools.chain.chain_store import chain_store
            chain_store.record_use(spec.name)
        except Exception:
            pass
        return engine.run(params)

    fn.__name__ = f"{spec.name}_tool"
    return fn
