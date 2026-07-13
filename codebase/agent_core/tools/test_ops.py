"""Test execution tools: discover and run tests."""

from __future__ import annotations

import os
import subprocess
from pathlib import Path

from agent_core.workspace import WORKSPACE_ROOT, PathEscapeError, resolve, to_relative


def _discover_test_files(root: str, pattern: str | None = None) -> list[str]:
    test_files = []
    for f in sorted(Path(root).rglob("test_*.py")):
        test_files.append(str(f.relative_to(WORKSPACE_ROOT)))
    for f in sorted(Path(root).rglob("*_test.py")):
        if str(f.relative_to(WORKSPACE_ROOT)) not in test_files:
            test_files.append(str(f.relative_to(WORKSPACE_ROOT)))
    return test_files


def _run_pytest(paths: list[str], timeout: int = 60) -> str:
    cmd = ["pytest", "-v", "--tb=short", "-q"] + paths
    try:
        result = subprocess.run(cmd, capture_output=True, text=True, timeout=timeout, cwd=WORKSPACE_ROOT)
        output = result.stdout
        if result.stderr:
            output += f"\n[STDERR]\n{result.stderr}"
        if result.returncode != 0:
            output += f"\n[Exit code: {result.returncode}]"
        return output if output else "(No output)"
    except FileNotFoundError:
        return "pytest not found. Try using python -m unittest instead."
    except subprocess.TimeoutExpired:
        return f"Tests timed out after {timeout}s."
    except Exception as e:
        return f"Error running tests: {e}"


def _run_unittest(paths: list[str], timeout: int = 60) -> str:
    cmd = ["python", "-m", "unittest", "discover", "-s", WORKSPACE_ROOT, "-t", WORKSPACE_ROOT]
    try:
        result = subprocess.run(cmd, capture_output=True, text=True, timeout=timeout, cwd=WORKSPACE_ROOT)
        output = result.stdout
        if result.stderr:
            output += f"\n[STDERR]\n{result.stderr}"
        if result.returncode != 0:
            output += f"\n[Exit code: {result.returncode}]"
        return output if output else "(No output)"
    except subprocess.TimeoutExpired:
        return f"Tests timed out after {timeout}s."
    except Exception as e:
        return f"Error running tests: {e}"


def run_tests(input_data) -> str:
    """Discover and run tests.

    input_data = {
        "pattern": "test_*.py",       # optional glob filter
        "path": "tests/",             # optional specific directory
        "framework": "pytest",        # optional: pytest (default) or unittest
        "timeout": 60                 # optional timeout in seconds
    }
    """
    try:
        if isinstance(input_data, str):
            import json
            input_data = json.loads(input_data)

        pattern = input_data.get("pattern", "")
        path = input_data.get("path", "")
        framework = input_data.get("framework", "pytest")
        timeout = int(input_data.get("timeout", 60))

        if path:
            test_root = resolve(path)
            if not os.path.isdir(test_root):
                return f"Error: directory not found: {path}"
        else:
            test_root = WORKSPACE_ROOT

        if pattern:
            test_files = [str(f.relative_to(WORKSPACE_ROOT)) for f in sorted(Path(test_root).rglob(pattern)) if f.is_file()]
        else:
            test_files = _discover_test_files(test_root)

        if not test_files:
            return "No test files found."

        if framework == "unittest":
            return _run_unittest(test_files, timeout)

        return _run_pytest(test_files, timeout)
    except PathEscapeError as e:
        return f"Error: {e}"
    except Exception as e:
        return f"Error running tests: {e}"
