"""Streaming helpers for the agent loop — real provider streaming with fake-chunk fallback."""

from __future__ import annotations

import time
from typing import Any, Generator, List, Optional

_STREAM_CHUNK_CHARS = 28
_STREAMING_ENABLED = True


def stream_final(
    content: str,
    step: int,
    conversation_id: Optional[str],
    orchestrator: Any = None,
    *,
    provider: Optional[str] = None,
    model: Optional[str] = None,
    system_prompt: Optional[str] = None,
    messages: Optional[List[dict]] = None,
) -> Generator[dict[str, Any], None, None]:
    text = content or ""

    if _STREAMING_ENABLED and orchestrator and content:
        provider_client = (
            orchestrator.providers.get(provider or orchestrator.default_provider)
            if hasattr(orchestrator, 'providers') else None
        )
        if provider_client and hasattr(provider_client, "generate_stream"):
            try:
                streamed_full = []
                for chunk in orchestrator.generate_stream(
                    prompt="",
                    system_prompt=system_prompt,
                    provider=provider,
                    model=model,
                    messages=messages,
                ):
                    if chunk:
                        streamed_full.append(chunk)
                        yield {
                            "type": "stream_chunk",
                            "content": chunk,
                            "step": step,
                        }
                yield {
                    "type": "final",
                    "content": "",
                    "step": step,
                    "conversation_id": conversation_id,
                    "full_content": "".join(streamed_full) or text,
                }
                return
            except Exception:
                pass

    if text:
        for i in range(0, len(text), _STREAM_CHUNK_CHARS):
            yield {
                "type": "stream_chunk",
                "content": text[i: i + _STREAM_CHUNK_CHARS],
                "step": step,
            }
            time.sleep(0.012)
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
