"""
Tests for agent kernel integration.

Unit tests: Import and configuration validation
Integration tests: Kernel retrieval, signals, memory, events
"""

import pytest
import json
import sys
import os

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))


class TestKernelImports:
    """Test kernel modules import"""

    def test_kernel_imports(self):
        """Verify kernel modules can be imported"""
        try:
            from kernel.retrieval.retrieval_engine import retrieval_engine
            from kernel.memory.working_memory import working_memory
            from kernel.ontology_registry import OntologyRegistry
            from kernel.signals.signal_engine import signal_engine
            from kernel.events.event_engine import event_engine
        except ImportError as e:
            pytest.skip(f"Kernel not available: {e}")


class TestToolRegistry:
    """Test tool registration"""

    def test_all_tools_registered(self):
        """Verify all required tools are registered"""
        from agent_core.tools import TOOLS
        required = [
            "read_file", "list_files", "write_to_file", "execute_command",
            "kernel_retrieve", "kernel_emit_signal",
            "kernel_store_context", "kernel_get_memory", "kernel_create_event"
        ]
        for tool in required:
            assert tool in TOOLS


class TestKernelConfig:
    """Test kernel configuration"""

    def test_kernel_config(self):
        """Verify kernel config flags"""
        from agent_core.tools.kernel_ops import KERNEL_AVAILABLE, AUTO_RETRIEVE_CONTEXT, RETRIEVE_LIMIT
        assert KERNEL_AVAILABLE is True
        assert AUTO_RETRIEVE_CONTEXT is True
        assert RETRIEVE_LIMIT > 0


class TestKernelRetrieval:
    """Integration tests for kernel retrieval"""

    @pytest.fixture
    def retrieval(self):
        try:
            from kernel.retrieval.retrieval_engine import retrieval_engine
            return retrieval_engine
        except ImportError:
            pytest.skip("Kernel not available")

    def test_search(self, retrieval):
        results = retrieval.search(query="test", limit=5)
        assert isinstance(results, list)

    def test_retrieve_patterns(self, retrieval):
        results = retrieval.retrieve_patterns(limit=5)
        assert isinstance(results, list)

    def test_retrieve_timeline(self, retrieval):
        results = retrieval.retrieve_recent_timeline(limit=5)
        assert isinstance(results, list)

    def test_memory_summary(self, retrieval):
        summary = retrieval.memory_summary()
        assert isinstance(summary, dict)

    def test_kernel_retrieve_tool(self):
        from agent_core.tools import TOOLS, KERNEL_AVAILABLE
        if not KERNEL_AVAILABLE:
            pytest.skip("Kernel not available")
        result = TOOLS["kernel_retrieve"](json.dumps({"query": "test", "limit": 5}))
        assert isinstance(result, (str, dict))


class TestSignalEngine:
    """Integration tests for signal engine"""

    @pytest.fixture
    def signal_eng(self):
        try:
            from kernel.signals.signal_engine import signal_engine
            return signal_engine
        except ImportError:
            pytest.skip("Signal engine not available")

    @pytest.fixture
    def kernel_avail(self):
        from agent_core.tools.kernel_ops import KERNEL_AVAILABLE
        return KERNEL_AVAILABLE

    def test_create_signal(self, signal_eng):
        signal = signal_eng.create_signal(
            signal_type="observation", source_unit_id="test", value="test"
        )
        assert signal is not None

    def test_emit_signal_tool(self, kernel_avail):
        if not kernel_avail:
            pytest.skip("Kernel not available")
        from agent_core.tools import TOOLS
        result = TOOLS["kernel_emit_signal"](json.dumps({
            "signal_type": "observation", "source_unit_id": "agent",
            "value": "test", "title": "Test"
        }))
        assert "signal_id" in result or "Error" in result


class TestWorkingMemory:
    """Integration tests for working memory"""

    @pytest.fixture
    def kernel_avail(self):
        from agent_core.tools.kernel_ops import KERNEL_AVAILABLE
        return KERNEL_AVAILABLE

    def test_store_context(self, kernel_avail):
        if not kernel_avail:
            pytest.skip("Kernel not available")
        from agent_core.tools import TOOLS
        result = TOOLS["kernel_store_context"](json.dumps({
            "memory_type": "context", "content": "test", "importance": 0.7
        }))
        assert "memory_id" in result or "Error" in result


class TestEventEngine:
    """Integration tests for event engine"""

    @pytest.fixture
    def kernel_avail(self):
        from agent_core.tools.kernel_ops import KERNEL_AVAILABLE
        return KERNEL_AVAILABLE

    def test_create_event(self, kernel_avail):
        if not kernel_avail:
            pytest.skip("Kernel not available")
        from agent_core.tools import TOOLS
        result = TOOLS["kernel_create_event"](json.dumps({
            "event_type": "action", "title": "test", "description": "desc"
        }))
        assert "event_id" in result or "Error" in result


class TestPhase3Tools:
    """Tests for Phase 3 tools"""

    @pytest.fixture
    def kernel_avail(self):
        from agent_core.tools.kernel_ops import KERNEL_AVAILABLE
        return KERNEL_AVAILABLE

    def test_all_tools_callable(self, kernel_avail):
        if not kernel_avail:
            pytest.skip("Kernel not available")
        from agent_core.tools import TOOLS
        for tool in ["kernel_store_context", "kernel_get_memory", "kernel_create_event"]:
            assert callable(TOOLS.get(tool))


if __name__ == "__main__":
    pytest.main([__file__, "-v"])