from __future__ import annotations

from typing import Dict, Any, Optional, List, Generator


class BaseLLMProvider:
    default_model: str
    _supports_stateful: bool = False

    @property
    def supports_stateful(self) -> bool:
        return self._supports_stateful

    @staticmethod
    def _build_usage_dict(
        total_tokens: int = 0,
        prompt_tokens: int = 0,
        completion_tokens: int = 0,
    ) -> Dict[str, Any]:
        if not prompt_tokens and not completion_tokens:
            prompt_tokens = int(total_tokens) - int(completion_tokens)
        return {
            "total_tokens": int(total_tokens),
            "prompt_tokens": int(prompt_tokens),
            "completion_tokens": int(completion_tokens),
            "estimated_cost": 0.0,
        }

    @staticmethod
    def _truncate_tool_result(result: str, max_chars: int = 2000) -> str:
        if len(result) <= max_chars:
            return result
        if result.strip().startswith(("{", "[")):
            truncated = result[:max_chars]
            last_close = max(truncated.rfind("}"), truncated.rfind("]"))
            if last_close > max_chars // 2:
                return truncated[:last_close + 1]
        return result[:max_chars]

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
        **kwargs: Any,
    ) -> Dict[str, Any]:
        raise NotImplementedError

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
        **kwargs: Any,
    ) -> Generator[str, None, None]:
        raise NotImplementedError
