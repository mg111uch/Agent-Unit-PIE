"""Parse LLM replies into final answer or tool action.

Supports two modes:
  1. Native tool_calls from provider (structured) — primary path
  2. Text-JSON / XML fallback parsing — for providers without function calling
"""

from __future__ import annotations

import json
import re
from dataclasses import dataclass, field
from typing import Any, Optional, List


@dataclass
class ParsedReply:
    kind: str  # "final" | "tool" | "tool_calls" | "raw" | "invalid_tool"
    content: Optional[str] = None
    tool: Optional[str] = None
    tool_input: Any = None
    tool_calls: Optional[List[dict]] = None
    raw: str = ""


@dataclass
class ParsedToolCall:
    name: str
    arguments: dict
    raw: str = ""


def parse_provider_response(
    response_text: Optional[str],
    tool_calls_raw: Optional[List[dict]],
    known_tools: dict,
) -> ParsedReply:
    """Parse a provider response that may contain either text or structured tool_calls.

    Priority:
      1. Structured tool_calls (native function calling) → multi-tool
      2. Text-JSON {"action": ..., "input": ...} → single tool
      3. Text-JSON {"final": ...} → final
      4. XML <tool_call> → single tool (legacy)
      5. Raw text → error/corrective
    """
    if tool_calls_raw:
        valid_calls = []
        for tc in tool_calls_raw:
            name = tc.get("name", "") or tc.get("function", {}).get("name", "")
            raw_args = tc.get("arguments", {}) or tc.get("function", {}).get("arguments", "{}")
            if isinstance(raw_args, str):
                try:
                    args = json.loads(raw_args)
                except json.JSONDecodeError:
                    args = {"input": raw_args}
            else:
                args = raw_args
            if name in known_tools:
                valid_calls.append(ParsedToolCall(name=name, arguments=args))
            else:
                return ParsedReply(
                    kind="invalid_tool",
                    tool=name,
                    raw=str(tool_calls_raw),
                )
        if valid_calls:
            return ParsedReply(
                kind="tool_calls",
                tool_calls=valid_calls,
                raw=str(tool_calls_raw),
            )

    return parse_agent_reply(response_text, known_tools)


def parse_agent_reply(reply: Optional[str], known_tools: dict) -> ParsedReply:
    """
    Classify a model text reply:
      - final: {"final": "..."}
      - tool:  {"action": tool, "input": ...}
      - raw:   non-JSON or unparseable
      - invalid_tool: JSON action missing or not in TOOLS
    """
    text = reply if isinstance(reply, str) else ("" if reply is None else str(reply))
    clean = _strip_code_fences(text)
    if not clean:
        return ParsedReply(
            kind="raw",
            content="(empty model response)",
            raw=text,
        )

    json_str = _extract_json(clean)
    if json_str:
        try:
            data = json.loads(json_str)
            if "final" in data:
                return ParsedReply(kind="final", content=data["final"], raw=text)
            tool = data.get("action")
            if tool and tool in known_tools:
                return ParsedReply(
                    kind="tool",
                    tool=tool,
                    tool_input=data.get("input", ""),
                    raw=text,
                )
            if tool:
                return ParsedReply(kind="invalid_tool", tool=tool, raw=text)
        except json.JSONDecodeError:
            pass

    xml_result = _parse_xml_tool_call(clean, known_tools)
    if xml_result:
        return xml_result

    return ParsedReply(kind="raw", content=text, raw=text)


def _strip_code_fences(reply: str) -> str:
    clean = (reply or "").strip()
    if clean.startswith("```"):
        clean = "\n".join(clean.split("\n")[1:])
        clean = clean.rsplit("```", 1)[0].strip()
    return clean


def _extract_json(text: str):
    match = re.search(r'\{.*\}', text, re.DOTALL)
    return match.group(0) if match else None


def _parse_xml_tool_call(text: str, known_tools: dict) -> Optional[ParsedReply]:
    m = re.search(r"<tool_call>\s*<function=(\w+)>", text)
    if not m:
        return None
    tool = m.group(1)
    if tool not in known_tools:
        return ParsedReply(kind="invalid_tool", tool=tool, raw=text)
    params = {}
    for pm in re.finditer(r"<parameter\s+(\w+)=([^>]+)>([^<]*)</parameter>", text):
        params[pm.group(1)] = pm.group(3).strip()
    for pm in re.finditer(r"<parameter\s+(\w+)>([^<]*)</parameter>", text):
        params[pm.group(1)] = pm.group(2).strip()
    if not params and tool == "read_file":
        m2 = re.search(r"<function=read_file[^>]*>([^<]+)", text)
        if m2:
            params["input"] = m2.group(1).strip()
    return ParsedReply(
        kind="tool",
        tool=tool,
        tool_input=params.get("input") or params.get("path") or "",
        raw=text,
    )
