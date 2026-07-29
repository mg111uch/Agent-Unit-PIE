import time
from typing import Any, List, Optional

from agent_core.tools.registry import CAT_FILE, CAT_META
from agent_core.tools import registry
from agent_core.response_parse import parse_provider_response
from agent_core.loop.executor import execute_tool_calls
from agent_core.loop.messages import (
    tool_followup, serialize_tool_input, build_tool_calls_msg,
    build_tool_results_msg, build_single_tool_result_msg,
)
from agent_core.loop._helpers import _truncate_result, _QUESTION_TOOLS
from agent_core.tools.types import ToolResult


_LOCAL_CATEGORIES = [CAT_FILE, CAT_META]
_SIMPLE_KEYWORDS = {"check", "list", "find", "where", "read", "show", "look", "search", "grep", "glob", "exists", "ls", "cat"}


class LocalPlanner:
    def __init__(
        self,
        local_provider: Any,
        config: dict,
    ):
        self.provider = local_provider
        self.enabled = config.get("enabled", False)
        self.local_categories = config.get("local_categories", _LOCAL_CATEGORIES)
        self.fallback_to_cloud = config.get("fallback_to_cloud", True)
        self.max_local_steps = config.get("max_local_steps", 3)
        self._consecutive_local = 0
        self._last_local_failed = False

    def reset(self):
        self._consecutive_local = 0
        self._last_local_failed = False

    def should_route_local(
        self,
        step: int,
        tool_calls_history: List[dict],
        user_input: str = "",
    ) -> bool:
        if not self.enabled:
            return False
        if self._last_local_failed:
            self._last_local_failed = False
            return False
        if self._consecutive_local >= self.max_local_steps:
            return False
        if not tool_calls_history:
            is_simple = (
                len(user_input) < 200
                and any(kw in user_input.lower() for kw in _SIMPLE_KEYWORDS)
            )
            if not is_simple:
                return False
            return True
        all_local_cats = all(
            tc.get("_category") in self.local_categories
            for tc in tool_calls_history[-3:]
            if tc.get("_category")
        )
        if not all_local_cats:
            return False
        has_question_tools = any(
            tc.get("name") in _QUESTION_TOOLS
            for tc in tool_calls_history[-3:]
        )
        if has_question_tools:
            return False
        return True

    def generate_local(
        self,
        messages: list,
        system_prompt: str = "",
        cancel_event=None,
    ) -> Optional[dict]:
        try:
            schemas = registry.get_schemas(
                provider_name="ollama",
                categories=self.local_categories,
            )
            result = self.provider.generate(
                prompt="",
                system_prompt=system_prompt,
                tools=schemas,
                messages=messages,
            )
            return result
        except Exception as e:
            return {
                "response": "",
                "tool_calls": None,
                "error": str(e),
            }

    def record_success(self):
        self._consecutive_local += 1
        self._last_local_failed = False

    def record_fallback(self):
        self._consecutive_local = 0
        self._last_local_failed = True
