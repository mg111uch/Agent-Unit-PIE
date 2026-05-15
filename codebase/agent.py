"""
agent.py - Main agent entry point.

Minimal file that delegates to agent_tools.py for all tool definitions.
"""

import os, sys, time, json, re, traceback

# Import environment and genai setup
from google import genai
from dotenv import load_dotenv
load_dotenv()

# Import from agent_tools
from agent_tools import (
    TOOLS,
    log_output,
    KERNEL_AVAILABLE,
    AUTO_RETRIEVE_CONTEXT,
    RETRIEVE_LIMIT,
    retrieval_engine,
    extract_json,
)

# ----- CONFIG -----
my_api_key = os.getenv("GEMINI_API_KEY")
client = genai.Client(api_key=my_api_key)
MODEL = "gemini-2.5-flash-lite"

interaction_id = None

# Setup log file and stderr redirect
from agent_tools import LOG_FILE


class TeeStderr:
    """Redirect stderr to both terminal and log file"""
    def __init__(self, original_stderr, log_file):
        self.original_stderr = original_stderr
        self.log_file = log_file

    def write(self, message):
        self.original_stderr.write(message)
        try:
            with open(self.log_file, "a") as f:
                f.write(message)
        except Exception:
            pass

    def flush(self):
        self.original_stderr.flush()


sys.stderr = TeeStderr(sys.stderr, LOG_FILE)

# Load system prompt
try:
    with open("system_instruction.md", "r") as f:
        SYSTEM_PROMPT = f.read()
except FileNotFoundError:
    log_output("ERROR: system_instruction.md not found. Using empty prompt.")
    SYSTEM_PROMPT = "You are a helpful assistant."
except Exception as e:
    log_output(f"ERROR loading system_instruction.md: {e}")
    SYSTEM_PROMPT = "You are a helpful assistant."


# ----- COMMAND PARSING -----
def parse_command(user_input: str):
    if not user_input.startswith("/"):
        return {"type": "default", "input": user_input}

    parts = user_input.strip().split()
    command = parts[0]

    if command == "/argu":
        mode = parts[1] if len(parts) > 1 else None
        topic = parts[2] if len(parts) > 2 else None
        return {"type": "argu", "mode": mode, "topic": topic}

    return {"type": "unknown", "input": user_input}


# ----- AGENT LOOP -----
def run_agent(user_input: str) -> str:
    global interaction_id

    # Auto-retrieve context from kernel
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

    first_input = SYSTEM_PROMPT + "\n\nUser: " + user_input + context_info if interaction_id is None else user_input + context_info
    current_input = first_input

    for step in range(10):
        try:
            res = client.interactions.create(
                model=MODEL,
                input=current_input,
                previous_interaction_id=interaction_id
            )

            interaction_id = res.id
            reply = res.outputs[-1].text
            log_output(f"\n[Agent Step {step}]: {reply}")

            # Parse JSON response
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


# ----- MAIN -----
if __name__ == "__main__":
    try:
        with open(LOG_FILE, "w") as f:
            f.write("")
    except Exception as e:
        print(f"Warning: Could not clear log file: {e}")

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
        else:
            output = run_agent(user_input)

        log_output(f"\n[Final Output]: {output}", flush=True)