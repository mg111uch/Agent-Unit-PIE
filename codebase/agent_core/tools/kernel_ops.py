import json

try:
    from kernel.retrieval.retrieval_engine import retrieval_engine
    from kernel.memory.working_memory import working_memory
    from kernel.ontology_registry import OntologyRegistry
    from kernel.signals.signal_engine import signal_engine
    from kernel.events.event_engine import event_engine
    from kernel.signals.belief_signal_handler import register_handlers
    register_handlers()
    KERNEL_AVAILABLE = True
except ImportError:
    KERNEL_AVAILABLE = False
    retrieval_engine = None
    working_memory = None
    OntologyRegistry = None
    signal_engine = None
    event_engine = None

AUTO_RETRIEVE_CONTEXT = True
RETRIEVE_LIMIT = 5


def kernel_retrieve(input_data) -> str:
    if not KERNEL_AVAILABLE:
        return "Error: Kernel modules not available. Check kernel installation."

    try:
        if isinstance(input_data, str):
            input_data = json.loads(input_data)

        query = input_data.get("query", "")
        limit = input_data.get("limit", 10)

        if not query:
            return "Error: 'query' is required"

        results = retrieval_engine.search(query=query, limit=limit)
        patterns = retrieval_engine.retrieve_patterns(limit=5)
        timeline = retrieval_engine.retrieve_recent_timeline(limit=10)

        output = {
            "query": query,
            "retrieved_memories": [r.to_dict() for r in results],
            "patterns": [p.to_dict() for p in patterns],
            "recent_timeline": [t.to_dict() for t in timeline],
            "memory_stats": retrieval_engine.memory_summary()
        }

        return json.dumps(output, indent=2)

    except Exception as e:
        return f"Error in kernel_retrieve: {str(e)}"


def kernel_emit_signal(input_data) -> str:
    if not KERNEL_AVAILABLE or signal_engine is None:
        return "Error: Kernel modules not available. Check kernel installation."

    try:
        if isinstance(input_data, str):
            input_data = json.loads(input_data)

        signal_type = input_data.get("signal_type", "observation")
        value = input_data.get("value", "")
        title = input_data.get("title", "")
        description = input_data.get("description", "")
        category = input_data.get("category", "general")
        confidence = input_data.get("confidence", 1.0)
        importance = input_data.get("importance", 0.5)
        tags = input_data.get("tags", [])

        if not value:
            return "Error: 'value' is required"

        signal = signal_engine.create_signal(
            signal_type=signal_type,
            source_unit_id="agent",
            value=value,
            category=category,
            title=title,
            description=description,
            confidence=confidence,
            importance=importance,
            tags=tags if tags else None,
        )

        output = {
            "status": "emitted",
            "signal_id": signal.signal_id,
            "signal_type": signal.signal_type,
            "value": signal.value,
        }

        return json.dumps(output, indent=2)

    except Exception as e:
        return f"Error in kernel_emit_signal: {str(e)}"


def kernel_store_context(input_data) -> str:
    if not KERNEL_AVAILABLE or working_memory is None:
        return "Error: Kernel modules not available. Check kernel installation."

    try:
        if isinstance(input_data, str):
            input_data = json.loads(input_data)

        memory_id = input_data.get("memory_id")
        memory_type = input_data.get("memory_type", "context")
        content = input_data.get("content", "")
        importance = input_data.get("importance", 0.5)
        confidence = input_data.get("confidence", 1.0)
        tags = input_data.get("tags", [])
        ttl_seconds = input_data.get("ttl_seconds", 3600)

        if not content:
            return "Error: 'content' is required"

        from kernel.utils.ids import generate_id
        if not memory_id:
            memory_id = generate_id("mem")

        working_memory.add_memory(
            memory_id=memory_id,
            memory_type=memory_type,
            content=content,
            importance=importance,
            confidence=confidence,
            tags=tags if tags else None,
            ttl_seconds=ttl_seconds,
        )

        output = {
            "status": "stored",
            "memory_id": memory_id,
            "memory_type": memory_type,
        }

        return json.dumps(output, indent=2)

    except Exception as e:
        return f"Error in kernel_store_context: {str(e)}"


def kernel_get_memory(input_data) -> str:
    if not KERNEL_AVAILABLE or working_memory is None:
        return "Error: Kernel modules not available. Check kernel installation."

    try:
        if isinstance(input_data, str):
            input_data = json.loads(input_data)

        memory_id = input_data.get("memory_id", "")

        if not memory_id:
            return "Error: 'memory_id' is required"

        memory = working_memory.get_memory(memory_id)

        if memory is None:
            return json.dumps({"status": "not_found", "memory_id": memory_id})

        output = {
            "status": "found",
            "memory_id": memory.memory_id,
            "memory_type": memory.memory_type,
            "content": memory.content,
            "importance": memory.importance,
            "confidence": memory.confidence,
            "tags": memory.tags,
        }

        return json.dumps(output, indent=2)

    except Exception as e:
        return f"Error in kernel_get_memory: {str(e)}"


def kernel_create_event(input_data) -> str:
    if not KERNEL_AVAILABLE or event_engine is None:
        return "Error: Kernel modules not available. Check kernel installation."

    try:
        if isinstance(input_data, str):
            input_data = json.loads(input_data)

        event_type = input_data.get("event_type", "action")
        title = input_data.get("title", "")
        description = input_data.get("description", "")
        category = input_data.get("category", "general")
        confidence = input_data.get("confidence", 1.0)
        importance = input_data.get("importance", 0.5)
        tags = input_data.get("tags", [])

        if not title:
            return "Error: 'title' is required"

        event = event_engine.create_event(
            event_type=event_type,
            title=title,
            description=description,
            source_unit_id="agent",
            category=category,
            confidence=confidence,
            importance=importance,
            tags=tags if tags else None,
        )

        output = {
            "status": "created",
            "event_id": event.event_id,
            "event_type": event.event_type,
            "title": event.title,
        }

        return json.dumps(output, indent=2)

    except Exception as e:
        return f"Error in kernel_create_event: {str(e)}"


def kernel_reload(input_data) -> str:
    """Reload tool modules from disk to pick up code changes without restart."""
    import importlib, sys
    modules = [
        "agent_core.tools.sim_ops",
        "agent_core.tools.kernel_ops",
        "agent_core.tools.code_rag",
        "agent_core.tools",
    ]
    for mod_name in modules:
        if mod_name in sys.modules:
            importlib.reload(sys.modules[mod_name])
    from agent_core.tools import _register_all
    _register_all()
    return json.dumps({"status": "reloaded", "modules": modules})
