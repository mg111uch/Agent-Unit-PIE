"""
agent_tools.py - Tool definitions for agent.

Exports:
- TOOLS: Dictionary of available tools
- log_output: Logging function
- KERNEL_AVAILABLE: Kernel integration status
- AUTO_RETRIEVE_CONTEXT: Auto context retrieval flag
- retrieval_engine: Kernel retrieval engine (if available)
- signal_engine: Kernel signal engine (if available)
"""

import os, subprocess, json, re
from typing import Dict, Any, Callable

# ----- CONFIG -----
LOG_FILE = "tui_output.txt"
ALLOWED_COMMANDS = ["ls", "cat", "pwd", "echo", "python"]
BASE_DIR = os.path.abspath("./python/Agentic_Unit_PIE/codebase/rag_pipeline/dummy")
MAX_FILE_SIZE = 200_000

# ----- KERNEL IMPORTS -----
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

# ----- KERNEL CONFIG -----
AUTO_RETRIEVE_CONTEXT = True
RETRIEVE_LIMIT = 5


# ----- HELPERS -----
def log_output(message: str, end: str = "\n", flush: bool = False):
    """Write message to both terminal and log file with timestamp"""
    from datetime import datetime
    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    log_line = f"[{timestamp}] {message}"
    print(log_line, end=end, flush=flush)
    try:
        with open(LOG_FILE, "a") as f:
            f.write(log_line + (end if end else ""))
            if flush:
                f.flush()
    except Exception as e:
        print(f"Warning: Could not write to log file: {e}")


def extract_json(text: str):
    """Extract JSON from text"""
    match = re.search(r'\{.*\}', text, re.DOTALL)
    if match:
        return match.group(0)
    return None


def _resolve_path(path: str) -> str:
    """Resolve path relative to BASE_DIR"""
    full_path = os.path.abspath(os.path.join(BASE_DIR, path))
    if not full_path.startswith(BASE_DIR):
        raise ValueError("Path escapes workspace")
    return full_path


def _ensure_dir(path: str):
    """Ensure directory exists"""
    os.makedirs(os.path.dirname(path), exist_ok=True)


# ----- TOOL FUNCTIONS -----
def read_file(path: str) -> str:
    """Read file contents"""
    try:
        with open(path, "r") as f:
            return f.read()
    except Exception as e:
        return str(e)


def list_files(path: str) -> str:
    """List files in directory"""
    try:
        files = os.listdir(path)
        return "\n".join(sorted(files))
    except Exception as e:
        error_msg = f"Error listing files in {path}: {str(e)}"
        log_output(f"[ERROR] {error_msg}")
        return error_msg


def write_to_file(input_data) -> str:
    """Write to file with modes: create, overwrite, append, patch
    
    input_data = {
        "path": "relative/path.txt",
        "mode": "create|overwrite|append|patch",
        "content": "string (optional)",
        "patch": {"find": "...", "replace": "..."} (optional),
        "dry_run": false
    }
    """
    try:
        if isinstance(input_data, str):
            input_data = json.loads(input_data)

        path = input_data.get("path")
        mode = input_data.get("mode")
        content = input_data.get("content", "")
        patch = input_data.get("patch")
        dry_run = input_data.get("dry_run", False)

        if not path or not mode:
            return "Error: 'path' and 'mode' are required"

        full_path = _resolve_path(path)
        exists = os.path.exists(full_path)

        # --- CREATE ---
        if mode == "create":
            if exists:
                return f"Error: File already exists: {path}"
            _ensure_dir(full_path)
            if not dry_run:
                with open(full_path, "w") as f:
                    f.write(content)
            return f"[CREATE] {path} ({len(content)} chars)"
        
        # --- OVERWRITE ---
        elif mode == "overwrite":
            _ensure_dir(full_path)
            if not dry_run:
                with open(full_path, "w") as f:
                    f.write(content)
            return f"[OVERWRITE] {path} ({len(content)} chars)"

        # --- APPEND ---
        elif mode == "append":
            _ensure_dir(full_path)
            if not dry_run:
                with open(full_path, "a") as f:
                    f.write(content)
            return f"[APPEND] {path} (+{len(content)} chars)"

        # --- PATCH (safe find-replace) ---
        elif mode == "patch":
            if not exists:
                return f"Error: File does not exist for patch: {path}"

            if not patch or "find" not in patch or "replace" not in patch:
                return "Error: patch requires 'find' and 'replace'"

            with open(full_path, "r") as f:
                original = f.read()

            if patch["find"] not in original:
                return "Error: 'find' text not found in file"

            updated = original.replace(patch["find"], patch["replace"])

            if len(updated) > MAX_FILE_SIZE:
                return "Error: file too large after patch"
            
            if not dry_run:
                with open(full_path, "w") as f:
                    f.write(updated)

            return f"[PATCH] {path} (replaced text)"

        else:
            return f"Error: Unknown mode '{mode}'"

    except Exception as e:
        return f"Error: {str(e)}"


def execute_command(cmd: str) -> str:
    """Execute allowed shell commands"""
    if not any(cmd.startswith(c) for c in ALLOWED_COMMANDS):
        return "Command not allowed"
    try:
        result = subprocess.run(
            cmd,
            shell=True,
            capture_output=True,
            text=True,
            timeout=30
        )
        output = result.stdout
        if result.stderr:
            output += f"\n[STDERR]: {result.stderr}"
        if result.returncode != 0:
            output += f"\n[Exit code: {result.returncode}]"
        return output if output else "(No output)"
    except subprocess.TimeoutExpired:
        error_msg = f"Command timed out after 30 seconds: {cmd}"
        log_output(f"[ERROR] {error_msg}")
        return error_msg
    except Exception as e:
        error_msg = f"Error executing command '{cmd}': {str(e)}"
        log_output(f"[ERROR] {error_msg}")
        return error_msg


def kernel_retrieve(input_data) -> str:
    """Retrieve relevant context from kernel memory layers.
    
    Input: {"query": "search terms", "limit": 10}
    Returns: relevant memories, patterns, and timeline from all memory layers.
    """
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
    """Emit a signal to the kernel for observation/finding.
    
    Input: {
        "signal_type": "observation|finding|insight",
        "value": "any value",
        "title": "signal title",
        "description": "details",
        "category": "general",
        "confidence": 1.0,
        "importance": 0.5,
        "tags": []
    }
    Returns: Signal confirmation with signal_id.
    """
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
    """Store context in working memory for later retrieval.
    
    Input: {
        "memory_id": "unique_id (optional, auto-generated if not provided)",
        "memory_type": "context|observation|hypothesis|summary",
        "content": "any content to store",
        "importance": 0.5,
        "confidence": 1.0,
        "tags": [],
        "ttl_seconds": 3600
    }
    Returns: Memory storage confirmation.
    """
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
    """Retrieve specific memory from working memory.
    
    Input: {
        "memory_id": "memory ID to retrieve"
    }
    Returns: Memory content or error.
    """
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
    """Create an event from agent action.
    
    Input: {
        "event_type": "action|discovery|decision|error",
        "title": "event title",
        "description": "what happened",
        "category": "general",
        "confidence": 1.0,
        "importance": 0.5,
        "tags": []
    }
    Returns: Event confirmation with event_id.
    """
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


# ----- TOOLS REGISTRY -----
TOOLS: Dict[str, Callable] = {
    "read_file": read_file,
    "list_files": list_files,
    "write_to_file": write_to_file,
    "execute_command": execute_command,
    "kernel_retrieve": kernel_retrieve,
    "kernel_emit_signal": kernel_emit_signal,
    "kernel_store_context": kernel_store_context,
    "kernel_get_memory": kernel_get_memory,
    "kernel_create_event": kernel_create_event,
}