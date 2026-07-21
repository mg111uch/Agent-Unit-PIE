import json
import os


_LLM_ORCHESTRATOR = None


def _get_orchestrator():
    global _LLM_ORCHESTRATOR
    if _LLM_ORCHESTRATOR is not None:
        return _LLM_ORCHESTRATOR
    try:
        from agent_core.providers_setup import build_orchestrator
        orch, _, _ = build_orchestrator(include_mock=True)
        _LLM_ORCHESTRATOR = orch
        return orch
    except Exception:
        return None


def _parse_json_from_response(response: str) -> dict | None:
    text = response.strip()
    for marker in ["```json", "```"]:
        if marker in text:
            parts = text.split(marker, 1)
            if len(parts) > 1:
                text = parts[1].split("```")[0].strip()
    try:
        return json.loads(text)
    except json.JSONDecodeError:
        return None


def compile_topic_llm(topic: str) -> dict:
    orch = _get_orchestrator()
    if orch is None:
        return {
            "status": "error",
            "message": "No LLM provider configured. Set GEMINI_API_KEY or OPENROUTER_API_KEY.",
        }

    prompt = (
        f"You are a debate graph generator. Generate a structured debate graph for the topic: {topic}\n\n"
        "Return ONLY valid JSON with:\n"
        '- "nodes": a list of arguments, each with "name" (short label), "premise" (1-2 sentence argument), '
        '"side" ("pro", "con", or "neutral")\n'
        '- "edges": a list of relations, each with "source" (matching a node name), '
        '"target" (matching a node name), "relation" (use "refutes" for contradictions)\n\n'
        "Include at least 6 arguments covering both sides of the debate.\n"
        "Do NOT wrap in markdown. Return raw JSON only."
    )

    result = orch.generate(prompt=prompt, max_tokens=4096, temperature=0.8)
    if result.get("status") != "success":
        return {"status": "error", "message": result.get("error", "LLM call failed")}

    parsed = _parse_json_from_response(result.get("response", ""))
    if parsed and "nodes" in parsed:
        return {"status": "success", "graph": parsed, "topic": topic}
    return {
        "status": "error",
        "message": "Failed to parse LLM response as graph JSON",
        "raw": result.get("response", ""),
    }


def generate_llm_question(topic: str, knowledge_context: dict) -> dict | None:
    orch = _get_orchestrator()
    if orch is None:
        return None

    context_text = ""
    related = knowledge_context.get("related_context", [])
    if related:
        snippets = []
        for c in related[:5]:
            node = c.get("node", {})
            title = node.get("title", "")
            content = node.get("content", "")[:100]
            snippets.append(f"{title}: {content}")
        context_text = "\n".join(snippets)

    prompt = (
        f'You are generating a single debate argument for the topic "{topic}".\n\n'
        "Accumulated knowledge from prior responses:\n"
        f'{context_text or "No prior knowledge available."}\n\n'
        "Generate one novel argument, counterargument, or exploratory point that:\n"
        "- Has NOT been covered yet\n"
        "- Encourages critical thinking\n"
        "- Is concise (1-2 sentences)\n\n"
        "Return ONLY valid JSON with:\n"
        '- "name": a short label for this argument\n'
        '- "premise": the argument text\n'
        '- "side": "pro", "con", or "neutral"\n\n'
        "Raw JSON only, no markdown."
    )

    result = orch.generate(prompt=prompt, max_tokens=1024, temperature=0.9)
    if result.get("status") != "success":
        return None

    parsed = _parse_json_from_response(result.get("response", ""))
    if parsed and parsed.get("name") and parsed.get("premise"):
        return parsed
    return None
