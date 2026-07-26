import json
import os
import shutil
from pathlib import Path

import pytest


def _find_events(events, etype):
    return [e for e in events if e["type"] == etype]


def _assert_tool_call(event, tool, step=0):
    assert event["type"] == "tool_call"
    assert event["tool"] == tool
    assert event["step"] == step
    assert event.get("call_id", ""), f"missing call_id for {tool}"


def _assert_tool_result(event, tool, ok=True, step=0):
    assert event["type"] == "tool_result"
    assert event["tool"] == tool
    assert event["ok"] is ok
    assert event["step"] == step
    assert event.get("call_id", ""), f"missing call_id for {tool}"
    assert "result" in event


@pytest.fixture
def test_ws(tmp_path, monkeypatch):
    import agent_core.workspace as ws
    monkeypatch.setattr(ws, "WORKSPACE_ROOT", str(tmp_path))

    for mod_name in (
        "agent_core.tools.file_ops",
        "agent_core.tools.undo_ops",
        "agent_core.tools",
    ):
        try:
            mod = __import__(mod_name, fromlist=[""])
            if hasattr(mod, "WORKSPACE_ROOT"):
                monkeypatch.setattr(mod, "WORKSPACE_ROOT", str(tmp_path))
        except ImportError:
            pass

    dummy_src = Path(__file__).parent.parent / "temp" / "dummy"
    if dummy_src.exists():
        shutil.copytree(dummy_src, tmp_path / "temp" / "dummy")

    return tmp_path


@pytest.fixture
def orch_and_mock():
    from agent_core.llm_orchestrator import LLMOrchestrator
    from agent_core.providers.mock_provider import MockProvider
    return LLMOrchestrator, MockProvider


def _run_events(orchestrator, mock, user_input):
    from agent_core.loop import iter_agent_events
    return list(iter_agent_events(
        user_input, orchestrator, provider="mock", model="mock",
    ))


class TestReadFile:
    def test_happy_path(self, test_ws, orch_and_mock):
        LLMOrchestrator, MockProvider = orch_and_mock
        mock = MockProvider(scenario="read_file_happy",
                            debug_path=str(test_ws / "trace_read.log"))
        orch = LLMOrchestrator(providers={"mock": mock},
                               default_provider="mock", default_model="mock")
        events = _run_events(orch, mock, "read calculator.py")

        calls = _find_events(events, "tool_call")
        results = _find_events(events, "tool_result")
        finals = _find_events(events, "final")

        assert len(calls) == 1
        assert len(results) == 1
        assert len(finals) == 1

        _assert_tool_call(calls[0], "read_file")
        _assert_tool_result(results[0], "read_file", ok=True)
        assert "def add" in results[0]["result"] or "calculator" in results[0]["result"]

        assert (test_ws / "trace_read.log").exists()

    def test_file_not_found(self, test_ws, orch_and_mock):
        LLMOrchestrator, MockProvider = orch_and_mock
        mock = MockProvider(scenario="read_file_not_found")
        orch = LLMOrchestrator(providers={"mock": mock},
                               default_provider="mock", default_model="mock")
        events = _run_events(orch, mock, "read nonexistent.py")

        results = _find_events(events, "tool_result")
        assert len(results) >= 1
        assert not results[0]["ok"]
        assert "file not found" in results[0]["result"].lower()

    def test_text_json_fallback(self, test_ws, orch_and_mock):
        LLMOrchestrator, MockProvider = orch_and_mock
        mock = MockProvider(scenario="read_file_text_json")
        orch = LLMOrchestrator(providers={"mock": mock},
                               default_provider="mock", default_model="mock")
        events = _run_events(orch, mock, "read calculator.py via json")

        results = _find_events(events, "tool_result")
        finals = _find_events(events, "final")
        assert len(results) == 1
        assert len(finals) == 1
        assert results[0]["ok"]
        assert results[0]["tool"] == "read_file"


class TestListFiles:
    def test_lists_directory(self, test_ws, orch_and_mock):
        LLMOrchestrator, MockProvider = orch_and_mock
        mock = MockProvider(scenario="list_files")
        orch = LLMOrchestrator(providers={"mock": mock},
                               default_provider="mock", default_model="mock")
        events = _run_events(orch, mock, "list temp/dummy")

        results = _find_events(events, "tool_result")
        assert len(results) == 1
        _assert_tool_result(results[0], "list_files", ok=True)
        assert "calculator.py" in results[0]["result"]

    def test_invalid_path(self, test_ws, orch_and_mock):
        LLMOrchestrator, MockProvider = orch_and_mock
        mock = MockProvider(stanzas=[
            {"response": "", "tool_calls": [{"name": "list_files", "arguments": {"path": "temp/dummy/calculator.py"}}]},
            {"response": '{"final": "done"}', "tool_calls": None},
        ])
        orch = LLMOrchestrator(providers={"mock": mock},
                               default_provider="mock", default_model="mock")
        events = _run_events(orch, mock, "list a file")
        results = _find_events(events, "tool_result")
        assert len(results) == 1
        assert not results[0]["ok"]


class TestWriteFile:
    def test_create_file(self, test_ws, orch_and_mock):
        LLMOrchestrator, MockProvider = orch_and_mock
        mock = MockProvider(scenario="write_file_create")
        orch = LLMOrchestrator(providers={"mock": mock},
                               default_provider="mock", default_model="mock")
        events = _run_events(orch, mock, "create temp/new.txt")

        results = _find_events(events, "tool_result")
        assert len(results) == 1
        _assert_tool_result(results[0], "write_to_file", ok=True)
        assert "[CREATE]" in results[0]["result"]
        assert (test_ws / "temp" / "new.txt").exists()
        assert (test_ws / "temp" / "new.txt").read_text() == "hello world"

    def test_overwrite_file(self, test_ws, orch_and_mock):
        LLMOrchestrator, MockProvider = orch_and_mock
        mock = MockProvider(scenario="write_file_overwrite")
        orch = LLMOrchestrator(providers={"mock": mock},
                               default_provider="mock", default_model="mock")
        events = _run_events(orch, mock, "overwrite calculator.py")

        results = _find_events(events, "tool_result")
        assert len(results) == 1
        assert results[0]["ok"]
        assert "[OVERWRITE]" in results[0]["result"]
        assert (test_ws / "temp" / "dummy" / "calculator.py").read_text() == "print('hello')"

    def test_append_file(self, test_ws, orch_and_mock):
        LLMOrchestrator, MockProvider = orch_and_mock
        mock = MockProvider(scenario="write_file_append")
        orch = LLMOrchestrator(providers={"mock": mock},
                               default_provider="mock", default_model="mock")
        original = (test_ws / "temp" / "dummy" / "calculator.py").read_text()
        events = _run_events(orch, mock, "append to calculator.py")

        results = _find_events(events, "tool_result")
        assert len(results) == 1
        assert results[0]["ok"]
        assert "[APPEND]" in results[0]["result"]
        assert (test_ws / "temp" / "dummy" / "calculator.py").read_text() == original + "\nprint('done')"


class TestEditFile:
    def test_edit_happy(self, test_ws, orch_and_mock):
        LLMOrchestrator, MockProvider = orch_and_mock
        mock = MockProvider(scenario="edit_file")
        orch = LLMOrchestrator(providers={"mock": mock},
                               default_provider="mock", default_model="mock")
        events = _run_events(orch, mock, "rename n1 to a")

        results = _find_events(events, "tool_result")
        assert len(results) == 1
        assert results[0]["ok"]
        assert "[EDIT]" in results[0]["result"]
        content = (test_ws / "temp" / "dummy" / "calculator.py").read_text()
        assert "def add(a, b):" in content
        assert "def add(n1, n2):" not in content

    def test_edit_not_found(self, test_ws, orch_and_mock):
        LLMOrchestrator, MockProvider = orch_and_mock
        mock = MockProvider(scenario="edit_file_not_found")
        orch = LLMOrchestrator(providers={"mock": mock},
                               default_provider="mock", default_model="mock")
        events = _run_events(orch, mock, "replace nonexistent string")

        results = _find_events(events, "tool_result")
        assert len(results) >= 1
        assert not results[0]["ok"]
        assert "old_string not found" in results[0]["result"].lower()


class TestSearchTools:
    def test_glob_search(self, test_ws, orch_and_mock):
        LLMOrchestrator, MockProvider = orch_and_mock
        mock = MockProvider(scenario="glob_search")
        orch = LLMOrchestrator(providers={"mock": mock},
                               default_provider="mock", default_model="mock")
        events = _run_events(orch, mock, "find all python files")

        results = _find_events(events, "tool_result")
        assert len(results) == 1
        assert results[0]["ok"]
        assert "calculator.py" in results[0]["result"] or "fabonacci.py" in results[0]["result"]

    def test_grep_search(self, test_ws, orch_and_mock):
        LLMOrchestrator, MockProvider = orch_and_mock
        mock = MockProvider(scenario="grep_search")
        orch = LLMOrchestrator(providers={"mock": mock},
                               default_provider="mock", default_model="mock")
        events = _run_events(orch, mock, "search for def")

        results = _find_events(events, "tool_result")
        assert len(results) == 1
        assert results[0]["ok"]
        assert "def " in results[0]["result"]


class TestBatchTools:
    def test_batch_read(self, test_ws, orch_and_mock):
        LLMOrchestrator, MockProvider = orch_and_mock
        mock = MockProvider(scenario="batch_read")
        orch = LLMOrchestrator(providers={"mock": mock},
                               default_provider="mock", default_model="mock")
        events = _run_events(orch, mock, "read both files")

        results = _find_events(events, "tool_result")
        assert len(results) == 1
        assert results[0]["ok"]

    def test_read_section(self, test_ws, orch_and_mock):
        LLMOrchestrator, MockProvider = orch_and_mock
        mock = MockProvider(scenario="read_section")
        orch = LLMOrchestrator(providers={"mock": mock},
                               default_provider="mock", default_model="mock")
        events = _run_events(orch, mock, "find def add in calculator")

        results = _find_events(events, "tool_result")
        assert len(results) == 1
        assert results[0]["ok"]

    def test_batch_edit(self, test_ws, orch_and_mock):
        LLMOrchestrator, MockProvider = orch_and_mock
        mock = MockProvider(scenario="batch_edit")
        orch = LLMOrchestrator(providers={"mock": mock},
                               default_provider="mock", default_model="mock")
        events = _run_events(orch, mock, "rename n1 to x and n2 to y")

        results = _find_events(events, "tool_result")
        assert len(results) == 1
        assert results[0]["ok"]
        content = (test_ws / "temp" / "dummy" / "calculator.py").read_text()
        assert "def add(x, y):" in content


class TestMultiStep:
    def test_parallel_tools(self, test_ws, orch_and_mock):
        LLMOrchestrator, MockProvider = orch_and_mock
        mock = MockProvider(scenario="parallel_two")
        orch = LLMOrchestrator(providers={"mock": mock},
                               default_provider="mock", default_model="mock")
        events = _run_events(orch, mock, "read calculator and list dir")

        calls = _find_events(events, "tool_call")
        results = _find_events(events, "tool_result")
        assert len(calls) == 2
        assert len(results) == 2

        call_tools = {e["tool"] for e in calls}
        assert call_tools == {"read_file", "list_files"}
        result_tools = {e["tool"] for e in results}
        assert result_tools == {"read_file", "list_files"}

        call_ids = [e["call_id"] for e in calls]
        assert len(set(call_ids)) == len(calls), "call_ids not unique"

        for r in results:
            assert r["ok"]

    def test_sequential_tools(self, test_ws, orch_and_mock):
        LLMOrchestrator, MockProvider = orch_and_mock
        mock = MockProvider(scenario="sequential_list_then_read")
        orch = LLMOrchestrator(providers={"mock": mock},
                               default_provider="mock", default_model="mock")
        events = _run_events(orch, mock, "list then read")

        calls = _find_events(events, "tool_call")
        results = _find_events(events, "tool_result")
        assert len(calls) == 2
        assert len(results) == 2
        assert calls[0]["tool"] == "list_files"
        assert calls[0]["step"] == 0
        assert calls[1]["tool"] == "read_file"
        assert calls[1]["step"] == 1
        assert results[0]["tool"] == "list_files"
        assert results[1]["tool"] == "read_file"
        assert results[0]["ok"]
        assert results[1]["ok"]


class TestErrorHandling:
    def test_invalid_tool_name(self, test_ws, orch_and_mock):
        LLMOrchestrator, MockProvider = orch_and_mock
        mock = MockProvider(scenario="invalid_tool")
        orch = LLMOrchestrator(providers={"mock": mock},
                               default_provider="mock", default_model="mock")
        events = _run_events(orch, mock, "run unknown tool")

        results = _find_events(events, "tool_result")
        assert len(results) >= 1
        assert not results[0]["ok"]
        assert "Unknown tool" in results[0]["result"] or "unknown" in results[0]["result"].lower()


class TestMockProviderInternals:
    def test_called_with_records(self, test_ws, orch_and_mock):
        LLMOrchestrator, MockProvider = orch_and_mock
        mock = MockProvider(scenario="read_file_happy")
        orch = LLMOrchestrator(providers={"mock": mock},
                               default_provider="mock", default_model="mock")
        _run_events(orch, mock, "test")

        assert len(mock.called_with) == 2
        for rec in mock.called_with:
            assert "step" in rec
            assert "messages" in rec
            assert "tool_schemas" in rec
            assert "returned_response" in rec
            assert "returned_tool_calls" in rec

    def test_custom_stanzas(self, test_ws, orch_and_mock):
        LLMOrchestrator, MockProvider = orch_and_mock
        custom = [
            {"response": '{"action": "get_workspace_info", "input": ""}', "tool_calls": None},
            {"response": '{"final": "done"}', "tool_calls": None},
        ]
        mock = MockProvider(stanzas=custom)
        orch = LLMOrchestrator(providers={"mock": mock},
                               default_provider="mock", default_model="mock")
        events = _run_events(orch, mock, "test custom")
        results = _find_events(events, "tool_result")
        assert len(results) == 1
        assert results[0]["tool"] == "get_workspace_info"

    def test_debug_trace_written(self, test_ws, orch_and_mock):
        LLMOrchestrator, MockProvider = orch_and_mock
        debug_path = str(test_ws / "debug_trace.log")
        mock = MockProvider(scenario="read_file_happy", debug_path=debug_path)
        orch = LLMOrchestrator(providers={"mock": mock},
                               default_provider="mock", default_model="mock")
        _run_events(orch, mock, "test debug")
        assert os.path.exists(debug_path)
        content = open(debug_path).read()
        assert "Generate #0" in content
        assert "Generate #1" in content
        assert "→ prompt" in content
        assert "← response" in content
        assert "← tool_calls" in content


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
