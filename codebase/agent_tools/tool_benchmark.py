"""Unified Bonsai tool benchmark — few-shot, minimal, and JSON router modes.

Usage:
  conda run -n myenv python codebase/agent_tools/tool_benchmark.py --mode all
  conda run -n myenv python codebase/agent_tools/tool_benchmark.py --mode fewshot
  conda run -n myenv python codebase/agent_tools/tool_benchmark.py --mode router --url http://host:8080/v1/chat/completions
"""

import argparse
import json
import statistics
import time

import requests

DEFAULT_URL = "http://127.0.0.1:8080/v1/chat/completions"
DEFAULT_MODEL = "Bonsai"

FEWSHOT_SYSTEM = """Classify the user request into exactly ONE label.

Labels:
CREATE_DIRECTORY
READ_FILE
WRITE_FILE
DELETE_FILE
LIST_FILES
EXECUTE_COMMAND

Examples:
"make folder src" -> CREATE_DIRECTORY
"read README.md" -> READ_FILE
"write hello to test.txt" -> WRITE_FILE
"remove old.txt" -> DELETE_FILE
"show files in src" -> LIST_FILES
"run pytest" -> EXECUTE_COMMAND

Output ONLY the label.
No explanation.
No punctuation.
"""

MINIMAL_SYSTEM = """Classify the user request into exactly ONE label.

Labels:
CREATE_DIRECTORY
READ_FILE
WRITE_FILE
DELETE_FILE
LIST_FILES
EXECUTE_COMMAND

Output ONLY the label.
No explanation.
No punctuation.
"""

ROUTER_SYSTEM = """You are a deterministic tool router.

Available tools:
CREATE_DIRECTORY(path)
READ_FILE(path)
WRITE_FILE(path, content)
DELETE_FILE(path)
LIST_FILES(path)
EXECUTE_COMMAND(command)

Rules:
- Return ONLY valid JSON.
- Format: {"tool":"TOOL_NAME", ...arguments}
- Never explain your answer.
- Never invent a tool.
- Extract arguments exactly from the user request.
"""

LABEL_TESTS = [
    ("Create a directory called src", "CREATE_DIRECTORY"),
    ("Make a new folder named tests/unit", "CREATE_DIRECTORY"),
    ("Show me the contents of README.md", "READ_FILE"),
    ("Open and read /tmp/config.json", "READ_FILE"),
    ('Write "hello world" to test.txt', "WRITE_FILE"),
    ('Put "print hello" into scripts/test.py', "WRITE_FILE"),
    ("Delete the file old.txt", "DELETE_FILE"),
    ("Remove the temporary directory", "DELETE_FILE"),
    ("What files are inside the tests directory?", "LIST_FILES"),
    ("Show everything in /home/manigupt/project", "LIST_FILES"),
]

ROUTER_TESTS = [
    {"input": "Create a directory called src", "expected": {"tool": "CREATE_DIRECTORY", "path": "src"}},
    {"input": "Create the directory tests/unit", "expected": {"tool": "CREATE_DIRECTORY", "path": "tests/unit"}},
    {"input": "Show me the contents of README.md", "expected": {"tool": "READ_FILE", "path": "README.md"}},
    {"input": "Read /tmp/config.json", "expected": {"tool": "READ_FILE", "path": "/tmp/config.json"}},
    {"input": 'Write "hello world" to test.txt', "expected": {"tool": "WRITE_FILE", "path": "test.txt", "content": "hello world"}},
    {"input": 'Put "print hello" into scripts/test.py', "expected": {"tool": "WRITE_FILE", "path": "scripts/test.py", "content": "print hello"}},
    {"input": "Delete the file old.txt", "expected": {"tool": "DELETE_FILE", "path": "old.txt"}},
    {"input": "What files are inside the tests directory?", "expected": {"tool": "LIST_FILES", "path": "tests"}},
    {"input": "List everything in /home/manigupt/project", "expected": {"tool": "LIST_FILES", "path": "/home/manigupt/project"}},
    {"input": "Run pytest tests/test_agent.py", "expected": {"tool": "EXECUTE_COMMAND", "command": "pytest tests/test_agent.py"}},
]


def _post(messages, max_tokens, timeout, url, model):
    payload = {
        "model": model,
        "messages": messages,
        "temperature": 0,
        "max_tokens": max_tokens,
        "stream": False,
    }

    start = time.perf_counter()

    response = requests.post(url, json=payload, timeout=timeout)

    latency = time.perf_counter() - start
    response.raise_for_status()

    data = response.json()
    content = data["choices"][0]["message"]["content"].strip()

    return content, latency, data.get("usage", {})


def _check_label(system, user_input, expected):
    actual, latency, usage = _post(
        [{"role": "system", "content": system}, {"role": "user", "content": user_input}],
        max_tokens=5, timeout=60,
    )
    return {
        "input": user_input,
        "expected": expected,
        "actual": actual,
        "raw": actual,
        "correct": actual.strip().upper() == expected,
        "valid_json": None,
        "latency": latency,
        "prompt_tokens": usage.get("prompt_tokens"),
        "completion_tokens": usage.get("completion_tokens"),
    }


def _check_router(system, test):
    content, latency, usage = _post(
        [{"role": "system", "content": system}, {"role": "user", "content": test["input"]}],
        max_tokens=80, timeout=120,
    )
    try:
        actual = json.loads(content)
        valid_json = True
    except json.JSONDecodeError:
        actual = None
        valid_json = False

    return {
        "input": test["input"],
        "expected": test["expected"],
        "actual": actual,
        "raw": content,
        "correct": actual == test["expected"],
        "valid_json": valid_json,
        "latency": latency,
        "prompt_tokens": usage.get("prompt_tokens"),
        "completion_tokens": usage.get("completion_tokens"),
    }


MODES = {
    "fewshot": {
        "title": "Bonsai Few-Shot Tool Classifier Benchmark",
        "system": FEWSHOT_SYSTEM,
        "check": _check_label,
    },
    "minimal": {
        "title": "Bonsai Minimal Tool Classifier Benchmark",
        "system": MINIMAL_SYSTEM,
        "check": _check_label,
    },
    "router": {
        "title": "Bonsai Tool Router Benchmark",
        "system": ROUTER_SYSTEM,
        "check": _check_router,
    },
}


def _print_stats(results):
    latencies = [r["latency"] for r in results]
    correct = sum(r["correct"] for r in results)
    valid_json = sum(r["valid_json"] or 0 for r in results)

    prompt_tokens = [r["prompt_tokens"] for r in results if r["prompt_tokens"] is not None]
    completion_tokens = [r["completion_tokens"] for r in results if r["completion_tokens"] is not None]

    print("\n" + "=" * 70)
    print("RESULTS")
    print("=" * 70)

    print(f"Tests:             {len(results)}")
    print(f"Correct:           {correct}/{len(results)}")
    print(f"Accuracy:          {correct / len(results) * 100:.1f}%")

    if valid_json:
        print(f"Valid JSON:        {valid_json}/{len(results)}")
        print(f"JSON validity:     {valid_json / len(results) * 100:.1f}%")

    print("\nLatency:")
    print(f"  Average:         {statistics.mean(latencies) * 1000:.1f} ms")
    print(f"  Median:          {statistics.median(latencies) * 1000:.1f} ms")
    print(f"  Min:             {min(latencies) * 1000:.1f} ms")
    print(f"  Max:             {max(latencies) * 1000:.1f} ms")
    if len(latencies) >= 2:
        print(f"  P95:             {sorted(latencies)[int(len(latencies) * 0.95) - 1] * 1000:.1f} ms")

    if prompt_tokens:
        print(f"\nPrompt tokens:")
        print(f"  Average:         {statistics.mean(prompt_tokens):.1f}")

    if completion_tokens:
        print("\nOutput tokens:")
        print(f"  Average:         {statistics.mean(completion_tokens):.1f}")

    print("=" * 70)


def run_mode(mode, url, model):
    cfg = MODES[mode]
    results = []

    print("=" * 70)
    print(cfg["title"])
    print("=" * 70)

    print("\nWarm-up...")
    cfg["check"](cfg["system"], LABEL_TESTS[0][0] if mode != "router" else ROUTER_TESTS[0])
    print("Warm-up complete.")

    tests = ROUTER_TESTS if mode == "router" else LABEL_TESTS
    n = len(tests)

    for i, test in enumerate(tests, 1):
        print(f"\n[{i}/{n}] {test['input']}")
        try:
            result = cfg["check"](cfg["system"], test)
            results.append(result)

            status = "PASS" if result["correct"] else "FAIL"
            print(f"  Expected: {result['expected']}")
            print(f"  Actual:   {result['actual']}")
            print(f"  {status}")
            print(f"  Latency:  {result['latency'] * 1000:.1f} ms")

            if result["prompt_tokens"] is not None:
                print(f"  Prompt tokens: {result['prompt_tokens']}")
            if result["completion_tokens"] is not None:
                print(f"  Output tokens: {result['completion_tokens']}")
        except Exception as e:
            print(f"  ERROR: {e}")

    if results:
        _print_stats(results)
    return bool(results)


def main():
    parser = argparse.ArgumentParser(description="Bonsai tool benchmark (few-shot, minimal, router).")
    parser.add_argument("--mode", choices=["fewshot", "minimal", "router", "all"], default="all")
    parser.add_argument("--url", default=DEFAULT_URL, help=f"OpenAI-compatible endpoint (default: {DEFAULT_URL})")
    parser.add_argument("--model", default=DEFAULT_MODEL, help=f"Model name (default: {DEFAULT_MODEL})")
    args = parser.parse_args()

    modes = ["fewshot", "minimal", "router"] if args.mode == "all" else [args.mode]
    for mode in modes:
        run_mode(mode, args.url, args.model)


if __name__ == "__main__":
    main()
