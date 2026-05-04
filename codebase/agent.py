import os, subprocess, json, time, sys,re, traceback
from google import genai
from dotenv import load_dotenv

load_dotenv()  # Loads variables from .env file
my_api_key = os.getenv("GEMINI_API_KEY")

client = genai.Client(api_key=my_api_key)
MODEL = "gemini-2.5-flash-lite"

interaction_id = None

# Setup output logging to file and terminal
LOG_FILE = "tui_output.txt"
ALLOWED_COMMANDS = ["ls", "cat", "pwd", "echo", "python"]
BASE_DIR = os.path.abspath("./python/Agentic_Unit_PIE/codebase/rag_pipeline/dummy")
MAX_FILE_SIZE = 200_000  # 200 KB safety limit

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

def log_output(message, end="\n", flush=False):
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

# Redirect stderr to also go to log file
sys.stderr = TeeStderr(sys.stderr, LOG_FILE)

# Load system prompt with error handling
try:
    with open("system_instruction.md", "r") as f:
        SYSTEM_PROMPT = f.read()
except FileNotFoundError:
    error_msg = "ERROR: system_instruction.md not found. Using empty system prompt."
    log_output(error_msg)
    SYSTEM_PROMPT = "You are a helpful assistant."
except Exception as e:
    error_msg = f"ERROR loading system_instruction.md: {e}"
    log_output(error_msg)
    SYSTEM_PROMPT = "You are a helpful assistant."

# ----- HELPERS ---
def extract_json(text):
    match = re.search(r'\{.*\}', text, re.DOTALL)
    if match:
        return match.group(0)
    return None

def _resolve_path(path: str):
    full_path = os.path.abspath(os.path.join(BASE_DIR, path))
    if not full_path.startswith(BASE_DIR):
        raise ValueError("Path escapes workspace")
    return full_path


def _ensure_dir(path: str):
    os.makedirs(os.path.dirname(path), exist_ok=True)

# ---- TOOLS ----
def read_file(path: str):
    try:
        with open(path, "r") as f:
            return f.read()
    except Exception as e:
        return str(e)

def list_files(path: str):
    try:
        files = os.listdir(path)
        return "\n".join(sorted(files))
    except Exception as e:
        error_msg = f"Error listing files in {path}: {str(e)}"
        log_output(f"[ERROR] {error_msg}")
        return error_msg
    
def write_to_file(input_data):
    """
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

def execute_command(cmd: str):
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

TOOLS = {
    "read_file": read_file,
    "list_files": list_files,
    "write_to_file": write_to_file,
    "execute_command": execute_command,
}

# ---- AGENT LOOP ----
def run_agent(user_input):
    global interaction_id

    # inject system prompt only once
    if interaction_id is None:
        first_input = SYSTEM_PROMPT + "\n\nUser: " + user_input
    else:
        first_input = user_input

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

            # Strip markdown code fences (```lang ... ``` or ``` ... ```)
            clean_reply = reply.strip()
            if clean_reply.startswith("```"):
                # Remove first line (```json or ```)
                clean_reply = "\n".join(clean_reply.split("\n")[1:])
                # Remove trailing ```
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

# ---- RUN ----
if __name__ == "__main__":
    # Clear log file on fresh start
    try:
        with open(LOG_FILE, "w") as f:
            f.write("")
    except Exception as e:
        print(f"Warning: Could not clear log file: {e}")

    log_output("--- Starting Agent ---", flush=True)

    while True:
        user_input = input(">> ")

        if user_input.lower() in ["exit", "quit"]:
            log_output("User requested to exit. Shutting down agent.")
            break

        log_output(f"\n[User]: {user_input}", flush=True)
        output = run_agent(user_input)

        log_output(f"\n[Final Output]: {output}", flush=True)