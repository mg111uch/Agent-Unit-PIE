"""
llm/providers/openrouter_provider.py

OpenRouter provider adapter for LLMOrchestrator.
Uses the OpenAI-compatible SDK pointed at OpenRouter's API.
Stateless — conversation_id is ignored.
"""

from __future__ import annotations

from typing import Dict, Any, Optional


class OpenRouterProvider:
    def __init__(self, api_key: str, model: str = "openai/gpt-oss-20b:free"):
        from openai import OpenAI
        self.client = OpenAI(
            base_url="https://openrouter.ai/api/v1",
            api_key=api_key,
        )
        self.default_model = model

    def generate(
        self,
        prompt: str,
        model: Optional[str] = None,
        system_prompt: Optional[str] = None,
        conversation_id: Optional[str] = None,
        temperature: float = 0.7,
        max_tokens: int = 2048,
        **kwargs,
    ) -> Dict[str, Any]:
        messages = []
        if system_prompt:
            messages.append({"role": "system", "content": system_prompt})
        messages.append({"role": "user", "content": prompt})

        res = self.client.chat.completions.create(
            model=model or self.default_model,
            messages=messages,
            temperature=temperature,
            max_tokens=max_tokens,
        )

        choice = res.choices[0] if res.choices else None
        response_text = choice.message.content if choice else ""
        token_count = res.usage.total_tokens if res.usage else 0

        return {
            "status": "success",
            "response": response_text,
            "conversation_id": None,
            "usage": {
                "total_tokens": token_count,
                "estimated_cost": 0.0,
            },
        }
