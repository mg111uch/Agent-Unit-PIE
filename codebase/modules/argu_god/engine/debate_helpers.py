from datetime import datetime
from typing import Any, Optional

from .loop import load_graph, get_next_argument


def _build_knowledge_context(topic: str) -> dict:
    from kernel.memory.semantic_memory import semantic_memory
    from kernel.retrieval.semantic_retriever import SemanticRetriever

    retriever = SemanticRetriever()
    topic_nodes = semantic_memory.search_by_tag(topic) or []
    topic_nodes += semantic_memory.search_content(topic)

    concept_results = retriever.build_semantic_context(topic, limit=10)
    seen_ids = set()
    context_nodes = []
    for result in concept_results.get("results", []):
        nid = result.get("node_id", "")
        if nid not in seen_ids:
            seen_ids.add(nid)
            context_nodes.append(result)

    return {
        "topic": topic,
        "existing_nodes": len(topic_nodes),
        "related_context": context_nodes,
        "has_knowledge": len(topic_nodes) > 0 or len(context_nodes) > 0,
    }


def _check_novelty(text: str, threshold: float = 0.85) -> bool:
    try:
        from .dedup import is_similar_to_any
        from kernel.memory.semantic_memory import semantic_memory

        existing_texts = []
        for node in semantic_memory.nodes.values():
            combined = f"{node.title} {node.content}"
            if combined.strip():
                existing_texts.append(combined)

        if not existing_texts:
            return True
        return not is_similar_to_any(text, existing_texts, threshold=threshold)
    except Exception:
        return True


def _store_user_knowledge(
    argument_name: str,
    stance: str,
    confidence: float,
    topic: str,
    user_text: Optional[str] = None,
):
    from kernel.memory.semantic_memory import semantic_memory

    node_id = f"user_{topic}_{argument_name.replace(' ', '_')}_{int(datetime.now().timestamp())}"
    if node_id in semantic_memory.nodes:
        return node_id

    source_refs = ["user"]
    if user_text:
        provenance = {"source": "user_response", "topic": topic, "timestamp": datetime.now().isoformat()}
    else:
        provenance = {"source": "user_choice", "topic": topic}

    content = f"{argument_name}: {stance} (confidence: {confidence})"
    if user_text:
        content = user_text

    semantic_memory.create_node(
        node_id=node_id,
        node_type="user_belief",
        title=f"User on {argument_name}",
        content=content,
        concepts=[stance, topic],
        tags=[topic, "user", "debate", stance],
        confidence=confidence,
        importance=0.6,
        source_refs=source_refs,
        metadata=provenance,
    )

    existing = semantic_memory.search_content(argument_name)
    for node in existing:
        if node.node_id != node_id:
            edge_id = f"edge_user_{node_id}_to_{node.node_id}"
            if edge_id not in semantic_memory.edges:
                semantic_memory.create_edge(
                    edge_id=edge_id,
                    source_node_id=node_id,
                    target_node_id=node.node_id,
                    relation_type="related_to",
                    weight=confidence,
                    confidence=0.8,
                    metadata={"topic": topic, "provenance": "user_response"},
                )

    try:
        from modules.argu_god.engine.vector_store import _get_collection, embed
        collection = _get_collection()
        try:
            collection.add(
                documents=[content],
                embeddings=[embed(content)],
                metadatas=[{"name": argument_name, "side": stance, "premise": content, "source": "user"}],
                ids=[node_id],
            )
        except Exception:
            pass
    except Exception:
        pass

    return node_id


def _get_untouched_knowledge(topic: str, state: dict, beliefs: dict) -> Optional[dict]:
    from kernel.memory.semantic_memory import semantic_memory
    seen = set(state.get("seen_arguments", []))
    known = set(beliefs.get("arguments", {}).keys())

    for node in semantic_memory.nodes.values():
        if topic not in node.tags:
            continue
        name = node.title or node.node_id
        if name in seen or name in known:
            continue
        return {
            "name": name,
            "premise": node.content,
            "side": node.concepts[0] if node.concepts else "neutral",
        }
    return None


def _generate_next_question(
    topic: str,
    state: dict,
    beliefs: dict,
    graph: dict,
    llm_input: Any,
) -> tuple[Optional[dict], Optional[dict]]:
    knowledge = _build_knowledge_context(topic)

    argument = get_next_argument(topic, graph, state, beliefs)
    if not argument and knowledge["has_knowledge"]:
        argument = _get_untouched_knowledge(topic, state, beliefs)

    if not argument:
        llm_gen = llm_input.get("llm_generated") if isinstance(llm_input, dict) else None
        if llm_gen and isinstance(llm_gen, dict) and llm_gen.get("name"):
            from .dedup import is_similar_to_any
            existing_texts = [
                f"{n.get('name', '')} {n.get('premise', '')}"
                for n in graph.get("nodes", [])
            ]
            gen_text = f"{llm_gen.get('name', '')} {llm_gen.get('premise', '')}"
            if not is_similar_to_any(gen_text, existing_texts):
                argument = llm_gen
                graph.setdefault("llm_generated", []).append(llm_gen)

    if not argument and knowledge["has_knowledge"]:
        argument = knowledge.get("related_context", [None])[0]

    if not argument:
        from ..llm_compiler import generate_llm_question
        llm_arg = generate_llm_question(topic, knowledge)
        if llm_arg and llm_arg.get("name") and llm_arg.get("premise"):
            from .dedup import is_similar_to_any
            existing_texts = [
                f"{n.get('name', '')} {n.get('premise', '')}"
                for n in graph.get("nodes", [])
            ]
            gen_text = f"{llm_arg.get('name', '')} {llm_arg.get('premise', '')}"
            if not is_similar_to_any(gen_text, existing_texts):
                argument = llm_arg

    if not argument:
        return None, None

    try:
        from .retriever import get_best_counter
        counter = get_best_counter(argument)
    except Exception:
        counter = None

    return argument, counter
