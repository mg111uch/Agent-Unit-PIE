"""Streaming helpers for the agent loop — real provider streaming with fake-chunk fallback."""

from __future__ import annotations

import threading
from typing import Any, Generator, List, Optional


def stream_final(
    content: str = "",
    step: int = 0,
    conversation_id: Optional[str] = None,
    orchestrator: Any = None,
    *,
    provider: Optional[str] = None,
    model: Optional[str] = None,
    system_prompt: Optional[str] = None,
    messages: Optional[List[dict]] = None,
    cancel_event: Optional[threading.Event] = None,
    temperature: float = 0.7,
    max_tokens: int = 2048,
) -> Generator[dict[str, Any], None, None]:
    if content:
        text = content
        if text:
            for i in range(0, len(text), 56):
                yield {
                    "type": "stream_chunk",
                    "content": text[i: i + 56],
                    "step": step,
                }
    elif orchestrator and provider and model and messages is not None:
        full = []
        try:
            for chunk in orchestrator.generate_stream(
                system_prompt=system_prompt,
                provider=provider,
                model=model,
                messages=messages,
                temperature=temperature,
                max_tokens=max_tokens,
            ):
                if cancel_event and cancel_event.is_set():
                    break
                full.append(chunk)
                yield {
                    "type": "stream_chunk",
                    "content": chunk,
                    "step": step,
                }
        except Exception:
            pass
        text = "".join(full)
    else:
        text = ""

    yield {
        "type": "final",
        "content": "",
        "step": step,
        "conversation_id": conversation_id,
        "full_content": text,
    }


def stream_llm_response(
    orchestrator: Any,
    *,
    prompt: str = "",
    system_prompt: Optional[str] = None,
    provider: Optional[str] = None,
    model: Optional[str] = None,
    messages: Optional[List[dict]] = None,
    conversation_id: Optional[str] = None,
    tools: Optional[List[dict]] = None,
    step: int = 0,
) -> Generator[dict[str, Any], None, None]:
    provider_client = orchestrator.providers.get(provider or orchestrator.default_provider)
    has_stream = hasattr(provider_client, "generate_stream") if provider_client else False

    if has_stream:
        accumulated = []
        try:
            for chunk in orchestrator.generate_stream(
                prompt=prompt,
                system_prompt=system_prompt,
                provider=provider,
                model=model,
                messages=messages,
                tools=tools,
            ):
                if chunk:
                    accumulated.append(chunk)
                    yield {
                        "type": "stream_chunk",
                        "content": chunk,
                        "step": step,
                    }
            full_text = "".join(accumulated)
        except Exception:
            full_text = ""
    else:
        result = orchestrator.generate(
            prompt=prompt,
            system_prompt=system_prompt,
            provider=provider,
            model=model,
            conversation_id=conversation_id,
            messages=messages,
            tools=tools,
        )
        full_text = result.get("response", "") if result.get("status") == "success" else ""

    yield {
        "type": "_llm_done",
        "response": full_text,
        "step": step,
    }
