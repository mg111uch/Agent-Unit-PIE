"""
agent.py - Main agent entry point.

Minimal file that delegates to agent_tools.py for all tool definitions.
"""

import os, sys, time, json, re, traceback, argparse

from dotenv import load_dotenv
load_dotenv()

from agent_tools import (
    TOOLS,
    log_output,
    KERNEL_AVAILABLE,
    AUTO_RETRIEVE_CONTEXT,
    RETRIEVE_LIMIT,
    retrieval_engine,
    extract_json,
)

if KERNEL_AVAILABLE:
    try:
        from kernel.memory.working_memory import working_memory
    except ImportError:
        working_memory = None

from llm.llm_orchestrator import LLMOrchestrator

# --- CLI ---
parser = argparse.ArgumentParser(description="Agentic Unit PIE Agent")
parser.add_argument("--provider", default="gemini", choices=["gemini", "openrouter"])
parser.add_argument("--model", default=None)
args = parser.parse_args()

# --- Orchestrator ---
orchestrator = LLMOrchestrator(default_provider=args.provider, default_model=args.model)

gemini_key = os.getenv("GEMINI_API_KEY")
if gemini_key:
    from llm.providers.gemini_provider import GeminiProvider
    orchestrator.register_provider("gemini", GeminiProvider(
        api_key=gemini_key,
        model=args.model,
    ))

openrouter_key = os.getenv("OPENROUTER_API_KEY")
if openrouter_key:
    from llm.providers.openrouter_provider import OpenRouterProvider
    orchestrator.register_provider("openrouter", OpenRouterProvider(
        api_key=openrouter_key,
        model=args.model,
    ))

conversation_id = None

try:
    with open("system_instruction.md", "r") as f:
        SYSTEM_PROMPT = f.read()
except FileNotFoundError:
    log_output("ERROR: system_instruction.md not found. Using empty prompt.")
    SYSTEM_PROMPT = "You are a helpful assistant."
except Exception as e:
    log_output(f"ERROR loading system_instruction.md: {e}")
    SYSTEM_PROMPT = "You are a helpful assistant."


def parse_command(user_input: str):
    if not user_input.startswith("/"):
        return {"type": "default", "input": user_input}

    parts = user_input.strip()[1:].split(None, 1)
    command = "/" + parts[0]
    rest = parts[1] if len(parts) > 1 else ""

    if command == "/argu":
        mode_topic = rest.split(None, 1)
        mode = mode_topic[0] if mode_topic else None
        topic = mode_topic[1] if len(mode_topic) > 1 else None
        return {"type": "argu", "mode": mode, "topic": topic}

    if command == "/auto":
        return {"type": "auto", "goal": rest}

    return {"type": "unknown", "input": user_input}


def run_agent(user_input: str) -> str:
    global conversation_id

    context_info = ""
    if AUTO_RETRIEVE_CONTEXT and KERNEL_AVAILABLE and retrieval_engine:
        try:
            results = retrieval_engine.search(query=user_input, limit=RETRIEVE_LIMIT)
            patterns = retrieval_engine.retrieve_patterns(limit=3)
            if results or patterns:
                context_parts = ["## Retrieved Context"]
                for r in results:
                    context_parts.append(f"- {r.content.get('content', {})}")
                for p in patterns:
                    context_parts.append(f"- Pattern: {p.content.get('title', 'unknown')}")
                context_info = "\n" + "\n".join(context_parts)
                log_output(f"[Kernel] Retrieved {len(results)} memories, {len(patterns)} patterns")
        except Exception as e:
            log_output(f"[Kernel] Context retrieval warning: {e}")

    current_input = user_input + context_info

    for step in range(10):
        try:
            result = orchestrator.generate(
                prompt=current_input,
                system_prompt=SYSTEM_PROMPT if conversation_id is None else None,
                conversation_id=conversation_id,
                provider=args.provider,
                model=args.model,
            )

            if result["status"] == "error":
                error_msg = f"LLM call failed: {result.get('error')}"
                log_output(f"[ERROR] {error_msg}")
                return error_msg

            conversation_id = result.get("conversation_id")
            reply = result["response"]
            log_output(f"\n[Agent Step {step}]: {reply}")

            clean_reply = reply.strip()
            if clean_reply.startswith("```"):
                clean_reply = "\n".join(clean_reply.split("\n")[1:])
                clean_reply = clean_reply.rsplit("```", 1)[0].strip()

            try:
                json_str = extract_json(clean_reply)
                if not json_str:
                    return reply
                data = json.loads(json_str)
            except json.JSONDecodeError as e:
                log_output(f"[ERROR] Failed to parse JSON response: {e}")
                return reply

            if "final" in data:
                return data["final"]

            tool = data.get("action")
            if not tool or tool not in TOOLS:
                error_msg = f"Invalid or missing tool: {tool}"
                log_output(f"[ERROR] {error_msg}")
                return error_msg

            tool_input = data.get("input", "")
            result = TOOLS[tool](tool_input)

            current_input = f"""
                Tool used: {tool}
                Input: {tool_input}
                Result: {result}
                Decide next step.
                """

            time.sleep(5)
        except Exception as e:
            error_msg = f"[ERROR] Exception in agent loop step {step}: {str(e)}\n{traceback.format_exc()}"
            log_output(error_msg)
            return error_msg

    return "Max iterations reached"


def run_auto_research(goal: str, max_iterations: int = 5) -> str:
    """
    Autonomous research mode: Goal -> Plan -> Execute -> Learn -> Repeat
    """
    log_output(f"[Auto-Research] Goal: {goal}")

    if not KERNEL_AVAILABLE or not retrieval_engine:
        return "Error: Kernel not available. Enable kernel for auto-research."

    all_findings = []

    system_prompt = """You are an autonomous research agent.
Given a research goal, break it into executable subtasks.
For each subtask, respond with JSON: {"action": "tool_name", "input": {...}}
After getting results, decide next subtask or finish.
When goal is achieved, respond with: {"final": "summary of findings"}"""

    for iteration in range(max_iterations):
        log_output(f"[Auto-Research] Iteration {iteration + 1}/{max_iterations}")

        context_info = ""
        try:
            results = retrieval_engine.search(query=goal, limit=3)
            if results:
                context_parts = ["## Relevant Context"]
                for r in results[:3]:
                    context_parts.append(f"- {r.content.get('content', str(r))}")
                context_info = "\n" + "\n".join(context_parts)
        except:
            pass

        first_input = f"Goal: {goal}\nPrevious findings: {all_findings}\n{context_info}\nWhat subtask next?"

        try:
            result = orchestrator.generate(
                prompt=first_input,
                system_prompt=system_prompt,
                provider=args.provider,
                model=args.model,
            )
            if result["status"] == "error":
                return f"Error in LLM call: {result.get('error')}"
            reply = result["response"]
            clean_reply = reply.strip()
        except Exception as e:
            return f"Error in LLM call: {e}"

        if '"final"' in clean_reply.lower() or "final" in clean_reply.lower():
            try:
                json_str = extract_json(clean_reply)
                data = json.loads(json_str) if json_str else {}
                if "final" in data:
                    all_findings.append(data["final"])
                    break
            except:
                pass
            all_findings.append(clean_reply)
            break

        try:
            json_str = extract_json(clean_reply)
            if not json_str:
                all_findings.append(clean_reply)
                continue
            data = json.loads(json_str)
        except:
            all_findings.append(clean_reply)
            continue

        tool = data.get("action")
        tool_input = data.get("input", "")

        if not tool or tool not in TOOLS:
            all_findings.append(f"Unknown tool: {tool}")
            continue

        try:
            result = TOOLS[tool](tool_input)
            result_str = str(result)[:500]
            all_findings.append(f"[{tool}] {result_str}")
            log_output(f"[Auto] Tool {tool} result: {result_str[:100]}...")
            goal = f"Continue research. Last result: {result_str[:200]}. What next?"
        except Exception as e:
            all_findings.append(f"Tool error: {e}")

    findings_summary = "\n\n".join(all_findings)

    if KERNEL_AVAILABLE and working_memory and all_findings:
        try:
            working_memory.add_memory(
                memory_type="research",
                content=findings_summary,
                importance=0.7,
                confidence=0.8,
                tags=["auto-research", goal[:30]],
                ttl_seconds=86400,
            )
            log_output("[Kernel] Research findings stored")
        except Exception as e:
            log_output(f"[Kernel] Storage warning: {e}")

    return findings_summary or "No findings produced"


if __name__ == "__main__":
    log_output("--- Starting Agent ---", flush=True)

    if KERNEL_AVAILABLE:
        log_output("[Kernel] Integration enabled - auto-retrieval context active")
    else:
        log_output("[Kernel] Modules not found - running without kernel integration")

    while True:
        user_input = input(">> ")

        if user_input.lower() in ["exit", "quit"]:
            log_output("User requested to exit. Shutting down agent.")
            break

        log_output(f"\n[User]: {user_input}", flush=True)
        cmd = parse_command(user_input)

        if cmd["type"] == "argu":
            from modules.argu_god.engine.cli import argu_cli
            output = argu_cli(cmd["mode"], cmd["topic"])
        elif cmd["type"] == "auto":
            output = run_auto_research(cmd["goal"])
        else:
            output = run_agent(user_input)

        log_output(f"\n[Final Output]: {output}", flush=True)
