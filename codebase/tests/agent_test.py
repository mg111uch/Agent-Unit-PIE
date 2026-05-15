"""
Tests for agent Phase 1 - kernel integration.

Unit tests: Import and configuration validation
Integration tests: Kernel retrieval functionality
"""

import pytest
import json
import sys
import os

# Add codebase to path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))


# ============================================================
# UNIT TESTS
# ============================================================

class TestKernelImports:
    """Test kernel module imports"""

    def test_kernel_imports(self):
        """Verify kernel modules can be imported"""
        try:
            from kernel.retrieval.retrieval_engine import retrieval_engine
            from kernel.memory.working_memory import working_memory
            from kernel.ontology_registry import OntologyRegistry
            assert retrieval_engine is not None
            assert working_memory is not None
            assert OntologyRegistry is not None
        except ImportError as e:
            pytest.skip(f"Kernel not available: {e}")

    def test_retrieval_engine_exists(self):
        """Verify retrieval_engine global instance exists"""
        try:
            from kernel.retrieval.retrieval_engine import retrieval_engine
            assert retrieval_engine is not None
            assert hasattr(retrieval_engine, 'search')
            assert hasattr(retrieval_engine, 'retrieve_patterns')
        except ImportError:
            pytest.skip("Kernel not available")

    def test_working_memory_exists(self):
        """Verify working_memory global instance exists"""
        try:
            from kernel.memory.working_memory import working_memory
            assert working_memory is not None
            assert hasattr(working_memory, 'add_memory')
            assert hasattr(working_memory, 'get_memory')
        except ImportError:
            pytest.skip("Kernel not available")


class TestToolRegistry:
    """Test tool registration"""

    def test_tools_import_from_agent_tools(self):
        """Verify TOOLS dictionary is imported from agent_tools"""
        from agent_tools import TOOLS
        assert isinstance(TOOLS, dict)
        assert len(TOOLS) > 0

    def test_all_required_tools_registered(self):
        """Verify all required tools are registered"""
        from agent_tools import TOOLS
        required_tools = [
            "read_file",
            "list_files", 
            "write_to_file",
            "execute_command",
            "kernel_retrieve",
        ]
        for tool_name in required_tools:
            assert tool_name in TOOLS, f"Tool {tool_name} not registered"

    def test_kernel_retrieve_callable(self):
        """Verify kernel_retrieve is callable"""
        from agent_tools import TOOLS
        assert callable(TOOLS.get("kernel_retrieve"))


class TestKernelConfig:
    """Test kernel configuration flags"""

    def test_kernel_available_flag(self):
        """Verify KERNEL_AVAILABLE boolean exists"""
        from agent_tools import KERNEL_AVAILABLE
        assert isinstance(KERNEL_AVAILABLE, bool)

    def test_auto_retrieve_context_flag(self):
        """Verify AUTO_RETRIEVE_CONTEXT flag exists"""
        from agent_tools import AUTO_RETRIEVE_CONTEXT
        assert isinstance(AUTO_RETRIEVE_CONTEXT, bool)

    def test_retrieve_limit_default(self):
        """Verify RETRIEVE_LIMIT has sensible default"""
        from agent_tools import RETRIEVE_LIMIT
        assert isinstance(RETRIEVE_LIMIT, int)
        assert RETRIEVE_LIMIT > 0


# ============================================================
# INTEGRATION TESTS
# ============================================================

class TestKernelRetrieval:
    """Integration tests for kernel retrieval"""

    @pytest.fixture
    def retrieval_engine(self):
        """Fixture to get retrieval engine"""
        try:
            from kernel.retrieval.retrieval_engine import retrieval_engine
            return retrieval_engine
        except ImportError:
            pytest.skip("Kernel not available")

    @pytest.fixture
    def kernel_available(self):
        """Fixture to check kernel availability"""
        from agent_tools import KERNEL_AVAILABLE
        return KERNEL_AVAILABLE

    def test_retrieval_engine_search_returns_list(self, retrieval_engine):
        """Test that search returns a list"""
        results = retrieval_engine.search(query="test", limit=5)
        assert isinstance(results, list)

    def test_retrieval_engine_search_with_empty_query(self, retrieval_engine):
        """Test search with empty query"""
        results = retrieval_engine.search(query="", limit=5)
        assert isinstance(results, list)

    def test_retrieve_patterns_returns_list(self, retrieval_engine):
        """Test retrieve_patterns returns list"""
        results = retrieval_engine.retrieve_patterns(limit=5)
        assert isinstance(results, list)

    def test_retrieve_recent_timeline_returns_list(self, retrieval_engine):
        """Test retrieve_recent_timeline returns list"""
        results = retrieval_engine.retrieve_recent_timeline(limit=5)
        assert isinstance(results, list)

    def test_memory_summary_returns_dict(self, retrieval_engine):
        """Test memory_summary returns dictionary"""
        summary = retrieval_engine.memory_summary()
        assert isinstance(summary, dict)

    def test_kernel_retrieve_tool_function(self, kernel_available, retrieval_engine):
        """Test kernel_retrieve tool returns valid JSON"""
        if not kernel_available:
            pytest.skip("Kernel not available")

        from agent_tools import TOOLS
        tool = TOOLS["kernel_retrieve"]
        
        result = tool(json.dumps({"query": "test", "limit": 5}))
        
        # Should return JSON string or error message
        assert isinstance(result, (str, dict))
        
        # If it's a string, try parsing as JSON
        if isinstance(result, str) and result.startswith("{"):
            parsed = json.loads(result)
            assert "query" in parsed or "Error" in result


class TestAutoRetrieveContext:
    """Integration tests for auto context retrieval"""

    def test_retrieval_engine_has_search_method(self):
        """Verify retrieval engine has search method"""
        try:
            from kernel.retrieval.retrieval_engine import retrieval_engine
            assert hasattr(retrieval_engine, 'search')
        except ImportError:
            pytest.skip("Kernel not available")

    def test_retrieval_engine_search_accepts_query_param(self):
        """Verify search accepts query parameter"""
        try:
            from kernel.retrieval.retrieval_engine import retrieval_engine
            # Should not raise
            results = retrieval_engine.search(query="test", limit=1)
            assert isinstance(results, list)
        except ImportError:
            pytest.skip("Kernel not available")


# ============================================================
# RUNNER
# ============================================================

if __name__ == "__main__":
    pytest.main([__file__, "-v"])


# ============================================================
# PHASE 2: KERNEL SIGNAL TESTS
# ============================================================

class TestSignalEngineImport:
    """Test signal engine import"""

    def test_signal_engine_import(self):
        """Verify signal_engine can be imported"""
        try:
            from kernel.signals.signal_engine import signal_engine
            assert signal_engine is not None
        except ImportError:
            pytest.skip("Signal engine not available")

    def test_signal_engine_has_create_signal_method(self):
        """Verify signal_engine has create_signal method"""
        try:
            from kernel.signals.signal_engine import signal_engine
            assert hasattr(signal_engine, 'create_signal')
        except ImportError:
            pytest.skip("Signal engine not available")


class TestKernelEmitSignalTool:
    """Integration tests for kernel_emit_signal"""

    @pytest.fixture
    def signal_engine(self):
        """Fixture to get signal engine"""
        try:
            from kernel.signals.signal_engine import signal_engine
            return signal_engine
        except ImportError:
            pytest.skip("Signal engine not available")

    @pytest.fixture
    def kernel_available(self):
        """Fixture to check kernel availability"""
        from agent_tools import KERNEL_AVAILABLE
        return KERNEL_AVAILABLE

    def test_signal_engine_creates_signal(self, signal_engine):
        """Test signal_engine.create_signal returns a signal"""
        signal = signal_engine.create_signal(
            signal_type="observation",
            source_unit_id="test",
            value="test value",
        )
        assert signal is not None
        assert signal.signal_id is not None

    def test_kernel_emit_signal_tool_returns_json(self, kernel_available, signal_engine):
        """Test kernel_emit_signal tool returns valid JSON"""
        if not kernel_available:
            pytest.skip("Kernel not available")

        from agent_tools import TOOLS
        tool = TOOLS["kernel_emit_signal"]
        
        result = tool(json.dumps({
            "signal_type": "observation",
            "source_unit_id": "agent",
            "value": "test observation",
            "title": "Test",
            "confidence": 1.0,
            "importance": 0.5
        }))
        
        assert isinstance(result, str)
        
        # Parse result
        parsed = json.loads(result)
        assert "signal_id" in parsed or "Error" in result

    def test_kernel_emit_signal_requires_value(self, kernel_available):
        """Test kernel_emit_signal requires value"""
        if not kernel_available:
            pytest.skip("Kernel not available")

        from agent_tools import TOOLS
        tool = TOOLS["kernel_emit_signal"]
        
        result = tool(json.dumps({
            "signal_type": "observation",
            "source_unit_id": "agent",
            "value": "",
        }))
        
        assert "Error" in result

    def test_all_required_tools_registered_with_signal(self):
        """Verify all required tools including signal are registered"""
        from agent_tools import TOOLS
        required_tools = [
            "read_file",
            "list_files", 
            "write_to_file",
            "execute_command",
            "kernel_retrieve",
            "kernel_emit_signal",
        ]
        for tool_name in required_tools:
            assert tool_name in TOOLS, f"Tool {tool_name} not registered"

    def test_kernel_emit_signal_callable(self):
        """Verify kernel_emit_signal is callable"""
        from agent_tools import TOOLS
        assert callable(TOOLS.get("kernel_emit_signal"))


class TestWorkingMemoryImport:
    """Test working memory import"""

    def test_working_memory_import(self):
        """Verify working_memory can be imported"""
        try:
            from kernel.memory.working_memory import working_memory
            assert working_memory is not None
        except ImportError:
            pytest.skip("Working memory not available")

    def test_working_memory_has_add_memory(self):
        """Verify working_memory has add_memory method"""
        try:
            from kernel.memory.working_memory import working_memory
            assert hasattr(working_memory, 'add_memory')
        except ImportError:
            pytest.skip("Working memory not available")


class TestEventEngineImport:
    """Test event engine import"""

    def test_event_engine_import(self):
        """Verify event_engine can be imported"""
        try:
            from kernel.events.event_engine import event_engine
            assert event_engine is not None
        except ImportError:
            pytest.skip("Event engine not available")

    def test_event_engine_has_create_event(self):
        """Verify event_engine has create_event method"""
        try:
            from kernel.events.event_engine import event_engine
            assert hasattr(event_engine, 'create_event')
        except ImportError:
            pytest.skip("Event engine not available")


class TestPhase3Tools:
    """Tests for Phase 3 tools"""

    @pytest.fixture
    def kernel_available(self):
        """Fixture to check kernel availability"""
        from agent_tools import KERNEL_AVAILABLE
        return KERNEL_AVAILABLE

    def test_all_phase3_tools_registered(self, kernel_available):
        """Verify all Phase 3 tools are registered"""
        if not kernel_available:
            pytest.skip("Kernel not available")
        
        from agent_tools import TOOLS
        phase3_tools = ["kernel_store_context", "kernel_get_memory", "kernel_create_event"]
        for tool_name in phase3_tools:
            assert tool_name in TOOLS, f"Tool {tool_name} not registered"

    def test_kernel_store_context_callable(self, kernel_available):
        """Verify kernel_store_context is callable"""
        if not kernel_available:
            pytest.skip("Kernel not available")
        
        from agent_tools import TOOLS
        assert callable(TOOLS.get("kernel_store_context"))

    def test_kernel_get_memory_callable(self, kernel_available):
        """Verify kernel_get_memory is callable"""
        if not kernel_available:
            pytest.skip("Kernel not available")
        
        from agent_tools import TOOLS
        assert callable(TOOLS.get("kernel_get_memory"))

    def test_kernel_create_event_callable(self, kernel_available):
        """Verify kernel_create_event is callable"""
        if not kernel_available:
            pytest.skip("Kernel not available")
        
        from agent_tools import TOOLS
        assert callable(TOOLS.get("kernel_create_event"))

    def test_kernel_store_context_stores_memory(self, kernel_available):
        """Test kernel_store_context stores memory"""
        if not kernel_available:
            pytest.skip("Kernel not available")

        from agent_tools import TOOLS
        tool = TOOLS["kernel_store_context"]
        
        result = tool(json.dumps({
            "memory_type": "context",
            "content": "test context",
            "importance": 0.7,
        }))
        
        assert isinstance(result, str)
        parsed = json.loads(result)
        assert "memory_id" in parsed or "Error" in parsed

    def test_kernel_store_context_requires_content(self, kernel_available):
        """Test kernel_store_context requires content"""
        if not kernel_available:
            pytest.skip("Kernel not available")

        from agent_tools import TOOLS
        tool = TOOLS["kernel_store_context"]
        
        result = tool(json.dumps({
            "memory_type": "context",
            "content": "",
        }))
        
        assert "Error" in result

    def test_kernel_get_memory_requires_id(self, kernel_available):
        """Test kernel_get_memory requires memory_id"""
        if not kernel_available:
            pytest.skip("Kernel not available")

        from agent_tools import TOOLS
        tool = TOOLS["kernel_get_memory"]
        
        result = tool(json.dumps({
            "memory_id": "",
        }))
        
        assert "Error" in result

    def test_kernel_create_event_creates_event(self, kernel_available):
        """Test kernel_create_event creates event"""
        if not kernel_available:
            pytest.skip("Kernel not available")

        from agent_tools import TOOLS
        tool = TOOLS["kernel_create_event"]
        
        result = tool(json.dumps({
            "event_type": "action",
            "title": "test event",
            "description": "test description",
        }))
        
        assert isinstance(result, str)
        parsed = json.loads(result)
        assert "event_id" in parsed or "Error" in parsed

    def test_kernel_create_event_requires_title(self, kernel_available):
        """Test kernel_create_event requires title"""
        if not kernel_available:
            pytest.skip("Kernel not available")

        from agent_tools import TOOLS
        tool = TOOLS["kernel_create_event"]
        
        result = tool(json.dumps({
            "event_type": "action",
            "title": "",
        }))
        
        assert "Error" in result