"""Parse LLM replies into final answer or tool action."""

from __future__ import annotations

import json
import re
from dataclasses import dataclass
from typing import Any, Optional

from agent_core.tools import extract_json


@dataclass
class ParsedReply:
    kind: str  # "final" | "tool" | "raw" | "invalid_tool"
    content: Optional[str] = None
    tool: Optional[str] = None
    tool_input: Any = None
    raw: str = ""


def strip_code_fences(reply: str) -> str:
    clean = (reply or "").strip()
    if clean.startswith("```"):
        clean = "\n".join(clean.split("\n")[1:])
        clean = clean.rsplit("```", 1)[0].strip()
    return clean


def _parse_xml_tool_call(text: str, known_tools: dict) -> Optional[ParsedReply]:
    """Try to parse XML-style function calls (Claude/OpenRouter XML format)."""
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


def parse_agent_reply(reply: Optional[str], known_tools: dict) -> ParsedReply:
    """
    Classify a model reply:
      - final: {"final": "..."}
      - tool:  {"action": tool, "input": ...}
      - raw:   non-JSON or unparseable → treat as user-facing text
      - invalid_tool: JSON action missing or not in TOOLS
    """
    text = reply if isinstance(reply, str) else ("" if reply is None else str(reply))
    clean = strip_code_fences(text)
    if not clean:
        return ParsedReply(
            kind="raw",
            content="(empty model response)",
            raw=text,
        )

    # Try JSON first (hand-rolled JSON format)
    json_str = extract_json(clean)
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

    # Fallback: try XML tool-call format (OpenRouter/Claude native)
    xml_result = _parse_xml_tool_call(clean, known_tools)
    if xml_result:
        return xml_result

    return ParsedReply(kind="raw", content=text, raw=text)
