"""Mock LLM provider with configurable response stanzas for testing and frontend dev."""

import json
import os
import time
from typing import Any, Dict, Generator, List, Optional

from agent_core.providers import BaseLLMProvider


class MockProvider(BaseLLMProvider):
    SCENARIOS: Dict[str, List[dict]] = {
        "read_file_happy": [
            {"response": "", "tool_calls": [{"name": "Read", "arguments": {"path": "temp/dummy/calculator.py"}}]},
            {"response": '{"final": "Here is the calculator code."}', "tool_calls": None},
        ],
        "read_file_not_found": [
            {"response": "", "tool_calls": [{"name": "Read", "arguments": {"path": "temp/nonexistent.py"}}]},
            {"response": '{"final": "File not found."}', "tool_calls": None},
        ],
        "read_file_text_json": [
            {"response": '{"action": "Read", "input": "temp/dummy/calculator.py"}', "tool_calls": None},
            {"response": '{"final": "Content retrieved."}', "tool_calls": None},
        ],
        "list_files": [
            {"response": "", "tool_calls": [{"name": "Read", "arguments": {"path": "temp/dummy"}}]},
            {"response": '{"final": "Directory listed."}', "tool_calls": None},
        ],
        "write_file_create": [
            {"response": "", "tool_calls": [{"name": "Write", "arguments": {"path": "temp/new.txt", "mode": "create", "content": "hello world"}}]},
            {"response": '{"final": "File created."}', "tool_calls": None},
        ],
        "write_file_overwrite": [
            {"response": "", "tool_calls": [{"name": "Write", "arguments": {"path": "temp/dummy/calculator.py", "mode": "overwrite", "content": "print('hello')"}}]},
            {"response": '{"final": "File overwritten."}', "tool_calls": None},
        ],
        "write_file_append": [
            {"response": "", "tool_calls": [{"name": "Write", "arguments": {"path": "temp/dummy/calculator.py", "mode": "append", "content": "\nprint('done')"}}]},
            {"response": '{"final": "Content appended."}', "tool_calls": None},
        ],
        "edit_file": [
            {"response": "", "tool_calls": [{"name": "edit_file", "arguments": {"path": "temp/dummy/calculator.py", "old_string": "def add(n1, n2):", "new_string": "def add(a, b):"}}]},
            {"response": '{"final": "Function renamed."}', "tool_calls": None},
        ],
        "edit_file_not_found": [
            {"response": "", "tool_calls": [{"name": "edit_file", "arguments": {"path": "temp/dummy/calculator.py", "old_string": "NOT_IN_FILE", "new_string": "never"}}]},
            {"response": '{"final": "Edit failed."}', "tool_calls": None},
        ],
        "glob_search": [
            {"response": "", "tool_calls": [{"name": "glob_search", "arguments": {"pattern": "**/*.py"}}]},
            {"response": '{"final": "Found python files."}', "tool_calls": None},
        ],
        "grep_search": [
            {"response": "", "tool_calls": [{"name": "grep_search", "arguments": {"pattern": "def ", "include": "*.py"}}]},
            {"response": '{"final": "Found definitions."}', "tool_calls": None},
        ],
        "batch_read": [
            {"response": "", "tool_calls": [{"name": "Read", "arguments": {"paths": ["temp/dummy/calculator.py", "temp/dummy/fabo/fabonacci.py"]}}]},
            {"response": '{"final": "Read both files."}', "tool_calls": None},
        ],
        "read_section": [
            {"response": "", "tool_calls": [{"name": "read_section", "arguments": {"path": "temp/dummy/calculator.py", "pattern": "def add"}}]},
            {"response": '{"final": "Section found."}', "tool_calls": None},
        ],
        "batch_edit": [
            {"response": "", "tool_calls": [{"name": "edit_file", "arguments": {"path": "temp/dummy/calculator.py", "edits": [{"old_string": "def add(n1, n2):", "new_string": "def add(x, y):"}]}}]},
            {"response": '{"final": "Edits applied."}', "tool_calls": None},
        ],
        "parallel_two": [
            {"response": "", "tool_calls": [
                {"name": "Read", "arguments": {"path": "temp/dummy/calculator.py"}},
                {"name": "Read", "arguments": {"path": "temp/dummy"}},
            ]},
            {"response": '{"final": "Both operations completed."}', "tool_calls": None},
        ],
        "sequential_list_then_read": [
            {"response": "", "tool_calls": [{"name": "Read", "arguments": {"path": "temp/dummy"}}]},
            {"response": "", "tool_calls": [{"name": "Read", "arguments": {"path": "temp/dummy/calculator.py"}}]},
            {"response": '{"final": "Done."}', "tool_calls": None},
        ],
        "invalid_tool": [
            {"response": "", "tool_calls": [{"name": "nonexistent_tool", "arguments": {}}]},
        ],
        "full_chat": [
            {"response": "", "tool_calls": [{"name": "Read", "arguments": {"path": "."}}]},
            {"response": "", "tool_calls": [{"name": "Read", "arguments": {"path": "temp/dummy/calculator.py"}}]},
            {"response": "", "tool_calls": [{"name": "grep_search", "arguments": {"pattern": "def", "include": "*.py"}}]},
            {"response": '{"final": "Analysis complete. The project contains a calculator module and fibonacci module."}', "tool_calls": None},
        ],
    }

    def __init__(
        self,
        api_key: str = "",
        model: str = "mock",
        scenario: Optional[str] = None,
        stanzas: Optional[List[dict]] = None,
        delay: bool = False,
        debug_path: Optional[str] = None,
    ):
        self.default_model = model
        self.delay = delay
        self.debug_path = debug_path
        self.called_with: List[dict] = []
        self._step = 0

        if scenario:
            base = list(self.SCENARIOS.get(scenario, []))
            self._stanzas = [dict(s) for s in base]
        elif stanzas is not None:
            self._stanzas = [dict(s) for s in stanzas]
        else:
            self._stanzas = [{"response": '{"final": "Mock response."}', "tool_calls": None}]

    @property
    def _is_default_stanzas(self) -> bool:
        return (
            len(self._stanzas) == 1
            and self._stanzas[0].get("response") == '{"final": "Mock response."}'
            and self._stanzas[0].get("tool_calls") is None
        )

    def _select_from_prompt(self, prompt: str = "", messages=None) -> None:
        if self._step >= len(self._stanzas):
            self._step = 0
            self._stanzas = [{"response": '{"final": "Mock response."}', "tool_calls": None}]
        if self._step > 0 or not self._is_default_stanzas:
            return

        source = ""
        if prompt.strip():
            source = prompt
        elif messages:
            for m in reversed(messages):
                if m.get("role") == "user" and m.get("content", "").strip():
                    source = m["content"]
                    break

        if not source:
            return

        key = source.strip().lower().replace(" ", "_")
        if key in self.SCENARIOS:
            self._stanzas = [dict(s) for s in self.SCENARIOS[key]]
            print(f"[MOCK-DIAG] matched scenario '{key}' from source='{source[:60]}'", flush=True)
            return
        for prefix in ("run_", "test_", "use_", "try_"):
            stripped = key.removeprefix(prefix)
            if stripped in self.SCENARIOS:
                self._stanzas = [dict(s) for s in self.SCENARIOS[stripped]]
                print(f"[MOCK-DIAG] matched scenario '{stripped}' (prefix '{prefix}') from source='{source[:60]}'", flush=True)
                return
        print(f"[MOCK-DIAG] NO match for key='{key}' source='{source[:60]}' len(messages)={len(messages) if messages else 0}", flush=True)

    def _write_debug(self, entry: str):
        if not self.debug_path:
            return
        os.makedirs(os.path.dirname(self.debug_path) or ".", exist_ok=True)
        with open(self.debug_path, "a") as f:
            f.write(entry)

    def _dump_messages(self, messages: Optional[List[dict]], max_chars: int = 2000) -> str:
        if not messages:
            return "(none)"
        text = json.dumps(messages, indent=2, ensure_ascii=False, default=str)
        if len(text) > max_chars:
            text = text[:max_chars] + "\n... (truncated)"
        return text

    def _dump_tools(self, tools: Optional[List[dict]], max_chars: int = 1500) -> str:
        if not tools:
            return "(none)"
        summary = []
        for t in tools:
            fn = t.get("function", t)
            summary.append(fn.get("name", "?"))
        text = json.dumps([t.get("function", t) for t in tools], indent=2, ensure_ascii=False, default=str)
        if len(text) > max_chars:
            text = text[:max_chars] + "\n... (truncated)"
        return text

    def generate(
        self,
        prompt: str = "",
        model: Optional[str] = None,
        system_prompt: Optional[str] = None,
        conversation_id: Optional[str] = None,
        temperature: float = 0.7,
        max_tokens: int = 2048,
        tools: Optional[List[Dict[str, Any]]] = None,
        messages: Optional[List[Dict[str, Any]]] = None,
        **kwargs,
    ) -> Dict[str, Any]:
        self._select_from_prompt(prompt, messages)
        if self.delay:
            time.sleep(3)

        step = self._step
        stanza = self._stanzas[step] if step < len(self._stanzas) else {"response": '{"final": "done"}', "tool_calls": None}
        print(f"[MOCK-DIAG] step={step} stanzas_len={len(self._stanzas)} returning_tool_calls={bool(stanza.get('tool_calls'))}", flush=True)

        record = {
            "step": step,
            "prompt": prompt,
            "system_prompt": system_prompt,
            "messages": messages,
            "tool_schemas": tools,
            "returned_response": stanza.get("response", ""),
            "returned_tool_calls": stanza.get("tool_calls"),
        }
        self.called_with.append(record)

        debug = [
            f"\n[{self.__class__.__name__}] === Generate #{step} ===\n",
            f"→ prompt: {prompt or '(empty)'}\n",
        ]
        if system_prompt:
            debug.append(f"→ system_prompt: {system_prompt[:300]}{'...' if len(system_prompt) > 300 else ''}\n")
        debug.append(f"→ messages:\n{self._dump_messages(messages)}\n")
        debug.append(f"→ tools:\n{self._dump_tools(tools)}\n")
        debug.append(f"← response: {stanza.get('response', '')[:300]}\n")
        debug.append(f"← tool_calls: {json.dumps(stanza.get('tool_calls'), default=str)}\n")
        self._write_debug("".join(debug))

        self._step += 1

        return {
            "response": stanza.get("response", ""),
            "tool_calls": stanza.get("tool_calls"),
            "conversation_id": conversation_id,
            "usage": self._build_usage_dict(0),
        }

    def generate_stream(
        self,
        prompt: str = "",
        model: Optional[str] = None,
        system_prompt: Optional[str] = None,
        conversation_id: Optional[str] = None,
        temperature: float = 0.7,
        max_tokens: int = 2048,
        tools: Optional[List[Dict[str, Any]]] = None,
        messages: Optional[List[Dict[str, Any]]] = None,
        **kwargs,
    ) -> Generator[str, None, None]:
        result = self.generate(
            prompt=prompt, model=model, system_prompt=system_prompt,
            conversation_id=conversation_id, temperature=temperature,
            max_tokens=max_tokens, tools=tools, messages=messages,
        )
        text = result.get("response", "")
        for i in range(0, len(text), 5):
            yield text[i:i+5]
            if self.delay:
                time.sleep(0.02)
