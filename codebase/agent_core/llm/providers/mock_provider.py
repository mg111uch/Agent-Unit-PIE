"""
llm/providers/mock_provider.py

Mock provider for frontend development.
Returns a pre-saved answer without calling any LLM.
"""

import time
from typing import Dict, Any, Optional, List, Generator


MOCK_RESPONSE = """{"final": "This is a mock response from the development provider. The agent backend is connected and working correctly. You can send messages and see the full WebSocket flow (tool calls, streaming, final response) without consuming any API credits. When you're ready for real LLM calls, set AGENT_PROVIDER=gemini or AGENT_PROVIDER=openrouter and ensure the corresponding API key is configured."}"""


class MockProvider:
    def __init__(self, api_key: str = "", model: str = "mock"):
        self.default_model = model

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
        time.sleep(3)
        return {
            "status": "success",
            "response": MOCK_RESPONSE,
            "tool_calls": None,
            "conversation_id": None,
            "usage": {
                "total_tokens": 0,
                "estimated_cost": 0.0,
            },
        }

    def generate_stream(
        self,
        prompt: str = "",
        model: Optional[str] = None,
        system_prompt: Optional[str] = None,
        temperature: float = 0.7,
        max_tokens: int = 2048,
        tools: Optional[List[Dict[str, Any]]] = None,
        messages: Optional[List[Dict[str, Any]]] = None,
        **kwargs,
    ) -> Generator[str, None, None]:
        """Simulate streaming by yielding the mock response character by character."""
        for i in range(0, len(MOCK_RESPONSE), 5):
            yield MOCK_RESPONSE[i:i+5]
            time.sleep(0.02)
