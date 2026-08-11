import json
import time
import urllib.request
import urllib.error
from typing import Any, Dict, Generator, List, Optional

from agent_core.providers import BaseLLMProvider


class OllamaProvider(BaseLLMProvider):
    def __init__(
        self,
        model: str = "funcGemma",
        endpoint: str = "http://localhost:11434",
        timeout: int = 30,
        keep_alive: Optional[str] = None,
    ):
        self.default_model = model
        self.endpoint = endpoint.rstrip("/")
        self.timeout = timeout
        self.keep_alive = keep_alive

    def _call_ollama(self, payload: dict) -> dict:
        url = f"{self.endpoint}/api/chat"
        data = json.dumps(payload).encode("utf-8")
        req = urllib.request.Request(
            url, data=data,
            headers={"Content-Type": "application/json"},
            method="POST",
        )
        resp = urllib.request.urlopen(req, timeout=self.timeout)
        return json.loads(resp.read().decode("utf-8"))

    def _parse_tool_calls(self, message: dict) -> Optional[List[dict]]:
        raw = message.get("tool_calls")
        if not raw:
            return None
        result = []
        for tc in raw:
            fn = tc.get("function", tc)
            name = fn.get("name", "")
            args = fn.get("arguments", {})
            if isinstance(args, str):
                try:
                    args = json.loads(args)
                except (json.JSONDecodeError, TypeError):
                    args = {"input": args}
            result.append({
                "name": name,
                "arguments": args,
                "id": f"ollama_{name}_{int(time.time())}",
            })
        return result if result else None

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
        started = time.time()
        ollama_messages = []
        if system_prompt:
            ollama_messages.append({"role": "system", "content": system_prompt})
        if messages:
            for m in messages:
                role = m.get("role", "user")
                content = m.get("content", "")
                if content:
                    ollama_messages.append({"role": role, "content": content})
        if prompt and (not messages or not messages[-1].get("content", "").endswith(prompt)):
            ollama_messages.append({"role": "user", "content": prompt})

        payload = {
            "model": model or self.default_model,
            "messages": ollama_messages,
            "stream": False,
            "options": {
                "temperature": temperature,
                "num_predict": max_tokens,
            },
        }
        if self.keep_alive:
            payload["keep_alive"] = self.keep_alive
        if tools:
            payload["tools"] = tools

        try:
            raw = self._call_ollama(payload)
        except (urllib.error.URLError, urllib.error.HTTPError, OSError) as e:
            return {
                "response": "",
                "tool_calls": None,
                "conversation_id": conversation_id,
                "usage": self._build_usage_dict(0),
                "error": f"ollama connection failed: {e}",
                "latency_seconds": round(time.time() - started, 3),
            }

        message = raw.get("message", {})
        content = message.get("content", "") or ""
        tool_calls = self._parse_tool_calls(message)

        prompt_tokens = raw.get("prompt_eval_count", 0) or 0
        completion_tokens = raw.get("eval_count", 0) or 0
        usage = self._build_usage_dict(
            total_tokens=prompt_tokens + completion_tokens,
            prompt_tokens=prompt_tokens,
            completion_tokens=completion_tokens,
        )
        return {
            "response": content,
            "tool_calls": tool_calls,
            "conversation_id": conversation_id,
            "usage": usage,
            "latency_seconds": round(time.time() - started, 3),
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
        **kwargs: Any,
    ) -> Generator[str, None, None]:
        result = self.generate(
            prompt=prompt, model=model, system_prompt=system_prompt,
            conversation_id=conversation_id, temperature=temperature,
            max_tokens=max_tokens, tools=tools, messages=messages,
        )
        text = result.get("response", "")
        yield text
