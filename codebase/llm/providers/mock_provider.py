"""
llm/providers/mock_provider.py

Mock provider for frontend development.
Returns a pre-saved answer without calling any LLM.
"""

from typing import Dict, Any, Optional


MOCK_RESPONSE = """{"final": "This is a mock response from the development provider. The agent backend is connected and working correctly. You can send messages and see the full WebSocket flow (tool calls, streaming, final response) without consuming any API credits. When you're ready for real LLM calls, set AGENT_PROVIDER=gemini or AGENT_PROVIDER=openrouter and ensure the corresponding API key is configured."}"""


class MockProvider:
    def __init__(self, api_key: str = "", model: str = "mock"):
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
        return {
            "status": "success",
            "response": MOCK_RESPONSE,
            "conversation_id": None,
            "usage": {
                "total_tokens": 0,
                "estimated_cost": 0.0,
            },
        }
