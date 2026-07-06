"""
llm/providers/gemini_provider.py

Gemini provider adapter for LLMOrchestrator.
Wraps genai.Client.interactions.create() — supports stateful conversations
via conversation_id -> previous_interaction_id.
"""

from __future__ import annotations

from typing import Dict, Any, Optional


class GeminiProvider:
    def __init__(self, api_key: str, model: str = "gemini-3.1-flash-lite"):
        from google import genai
        self.client = genai.Client(api_key=api_key)
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
        full_input = prompt
        if system_prompt:
            full_input = f"{system_prompt}\n\n{prompt}"

        res = self.client.interactions.create(
            model=model or self.default_model,
            input=full_input,
            previous_interaction_id=conversation_id,
        )

        usage = getattr(res, "usage_metadata", None)
        token_count = 0
        if usage:
            token_count = (
                getattr(usage, "prompt_token_count", 0)
                + getattr(usage, "candidates_token_count", 0)
            )

        return {
            "status": "success",
            "response": res.output_text,
            "conversation_id": res.id,
            "usage": {
                "total_tokens": token_count,
                "estimated_cost": 0.0,
            },
        }
