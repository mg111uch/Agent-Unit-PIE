import sys
import os
import json
import tempfile
import importlib.util
from unittest.mock import patch

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))

import pytest


class TestContradictionDetection:
    """detect_contradictions_for_beliefs flags known contradictions."""

    @pytest.fixture
    def sem_mem(self):
        from kernel.memory.semantic_memory import semantic_memory
        semantic_memory.clear()
        semantic_memory.create_node(
            node_id="arg_test_claim_a", node_type="argument",
            title="Claim A", content="Premise A",
            confidence=0.9, importance=0.7,
        )
        semantic_memory.create_node(
            node_id="arg_test_claim_b", node_type="argument",
            title="Claim B", content="Premise B",
            confidence=0.9, importance=0.7,
        )
        semantic_memory.create_edge(
            edge_id="edge_test_contra",
            source_node_id="arg_test_claim_a",
            target_node_id="arg_test_claim_b",
            relation_type="contradicts",
            weight=1.0, confidence=1.0,
        )
        yield semantic_memory
        semantic_memory.clear()

    def test_detects_contradiction_in_agreed_beliefs(self, sem_mem):
        from kernel.patterns.contradiction_detector import detect_contradictions_for_beliefs
        beliefs = {
            "Claim A": {"stance": "agree", "confidence": 0.8},
            "Claim B": {"stance": "agree", "confidence": 0.8},
        }
        results = detect_contradictions_for_beliefs(beliefs)
        assert len(results) >= 1
        assert results[0].claim_a_title == "Claim A"
        assert results[0].claim_b_title == "Claim B"

    def test_no_false_positive_when_not_agreed(self, sem_mem):
        from kernel.patterns.contradiction_detector import detect_contradictions_for_beliefs
        beliefs = {
            "Claim A": {"stance": "agree", "confidence": 0.8},
            "Claim B": {"stance": "disagree", "confidence": 0.8},
        }
        results = detect_contradictions_for_beliefs(beliefs)
        assert len(results) == 0

    def test_no_false_positive_no_contradiction_edge(self, sem_mem):
        from kernel.patterns.contradiction_detector import detect_contradictions_for_beliefs
        sem_mem.remove_edge("edge_test_contra")
        beliefs = {
            "Claim A": {"stance": "agree", "confidence": 0.8},
            "Claim B": {"stance": "agree", "confidence": 0.8},
        }
        results = detect_contradictions_for_beliefs(beliefs)
        assert len(results) == 0

    def test_no_contradiction_when_filter_matches_only_one_side(self, sem_mem):
        from kernel.patterns.contradiction_detector import detect_contradictions_for_beliefs
        beliefs = {
            "Claim A": {"stance": "agree", "confidence": 0.8},
            "Claim B": {"stance": "agree", "confidence": 0.8},
        }
        results = detect_contradictions_for_beliefs(beliefs, claim_filter="Claim A")
        assert len(results) == 0

    def test_no_results_for_nonexistent_filter(self, sem_mem):
        from kernel.patterns.contradiction_detector import detect_contradictions_for_beliefs
        beliefs = {
            "Claim A": {"stance": "agree", "confidence": 0.8},
            "Claim B": {"stance": "agree", "confidence": 0.8},
        }
        results = detect_contradictions_for_beliefs(beliefs, claim_filter="Nonexistent")
        assert len(results) == 0


class TestSignalPipeline:
    """signal_extractor.extract_and_emit reaches belief_signal_handler."""

    @pytest.fixture(autouse=True)
    def cleanup(self):
        from kernel.signals.signal_engine import signal_engine
        from kernel.memory.working_memory import working_memory
        from kernel.signals.belief_signal_handler import register_handlers, unregister_handlers
        signal_engine.clear_recent_signals()
        working_memory.clear()
        register_handlers()
        yield
        unregister_handlers()
        signal_engine.clear_recent_signals()
        working_memory.clear()

    def test_belief_shift_signal_stored_in_working_memory(self):
        from kernel.extractors.signal_extractor import signal_extractor
        from kernel.memory.working_memory import working_memory
        signal_id = signal_extractor.extract_and_emit(
            input_data={
                "argument_name": "TestArg",
                "stance": "agree",
                "confidence": 0.8,
                "topic": "test_topic",
            },
            source_unit_id="test_unit",
            signal_type_hint="belief_shift",
        )
        assert signal_id is not None
        assert signal_id.startswith("belief_shift_")
        memories = working_memory.search_by_type("belief_shift")
        assert len(memories) >= 1
        assert memories[0].content["argument"] == "TestArg"

    def test_contradiction_signal_triggers_pattern(self):
        from kernel.extractors.signal_extractor import signal_extractor
        from kernel.memory.working_memory import working_memory
        from kernel.signals.signal_engine import signal_engine
        signal_id = signal_extractor.extract_and_emit(
            input_data={
                "contradicted_arguments": [("ArgA", "ArgB")],
                "topic": "test_topic",
            },
            source_unit_id="test_unit",
            signal_type_hint="contradiction_detected",
        )
        assert signal_id is not None
        memories = working_memory.search_by_type("contradiction")
        assert len(memories) >= 1
        pattern_signals = signal_engine.get_recent_signals(
            limit=10, signal_type="pattern_detected"
        )
        assert len(pattern_signals) >= 1

    def test_confidence_change_signal_stored(self):
        from kernel.extractors.signal_extractor import signal_extractor
        from kernel.memory.working_memory import working_memory
        signal_id = signal_extractor.extract_and_emit(
            input_data={
                "argument_name": "TestArg",
                "delta": 0.2,
                "confidence": 0.9,
                "topic": "test_topic",
            },
            source_unit_id="test_unit",
            signal_type_hint="confidence_change",
        )
        assert signal_id is not None
        memories = working_memory.search_by_type("confidence_change")
        assert len(memories) >= 1


class TestPopulateSemanticMemory:
    """Semantic population: nodes, edges, and ChromaDB indexing."""

    SAMPLE_GRAPH = {
        "nodes": [
            {"name": "Arg One", "premise": "First premise", "side": "pro"},
            {"name": "Arg Two", "premise": "Second premise", "side": "con"},
        ],
        "edges": [
            {"source": "Arg One", "target": "Arg Two", "relation": "refutes"},
        ],
    }
    TOPIC = "test_topic"

    @pytest.fixture(autouse=True)
    def cleanup_semantic(self):
        from kernel.memory.semantic_memory import semantic_memory
        semantic_memory.clear()
        yield
        semantic_memory.clear()

    def _populate_semantic_memory(self, graph: dict, topic: str):
        from kernel.memory.semantic_memory import semantic_memory
        nodes_map = {}
        for node in graph.get("nodes", []):
            name = node.get("name", "")
            node_id = f"argu_{topic}_{name.replace(' ', '_')}"
            if node_id not in semantic_memory.nodes:
                semantic_memory.create_node(
                    node_id=node_id,
                    node_type="argument",
                    title=name,
                    content=node.get("premise", ""),
                    concepts=[node.get("side", "neutral")],
                    tags=[topic, "debate", "argument"],
                    confidence=1.0,
                    importance=0.7,
                )
            nodes_map[name] = node_id
        for edge in graph.get("edges", []):
            rel = edge.get("relation", "")
            if rel != "refutes":
                continue
            src_name = edge.get("source", "")
            tgt_name = edge.get("target", "")
            src_id = nodes_map.get(src_name)
            tgt_id = nodes_map.get(tgt_name)
            if not src_id or not tgt_id:
                continue
            edge_id = f"edge_contra_{src_name}_{tgt_name}".replace(" ", "_")
            if edge_id not in semantic_memory.edges:
                semantic_memory.create_edge(
                    edge_id=edge_id,
                    source_node_id=src_id,
                    target_node_id=tgt_id,
                    relation_type="contradicts",
                    weight=1.0, confidence=1.0,
                    metadata={"topic": topic, "source_graph": "debate"},
                )
        from modules.argu_god.engine.vector_store import index_graph
        index_graph(graph)

    def test_populates_semantic_nodes_and_edges(self):
        from kernel.memory.semantic_memory import semantic_memory
        self._populate_semantic_memory(self.SAMPLE_GRAPH, self.TOPIC)
        expected_node_ids = [
            f"argu_{self.TOPIC}_Arg_One",
            f"argu_{self.TOPIC}_Arg_Two",
        ]
        for nid in expected_node_ids:
            assert nid in semantic_memory.nodes
            assert semantic_memory.nodes[nid].title in ("Arg One", "Arg Two")
        assert len(semantic_memory.edges) >= 1
        edge = list(semantic_memory.edges.values())[0]
        assert edge.relation_type == "contradicts"

    def test_populates_vector_store(self):
        with patch("modules.argu_god.engine.vector_store.embed") as mock_embed:
            mock_embed.return_value = [0.0] * 384
            self._populate_semantic_memory(self.SAMPLE_GRAPH, self.TOPIC)
        from modules.argu_god.engine.vector_store import _get_collection
        collection = _get_collection()
        all_data = collection.get()
        ids = all_data.get("ids", [])
        assert "Arg One" in ids
        assert "Arg Two" in ids

    def test_populate_handles_duplicate_calls(self):
        from kernel.memory.semantic_memory import semantic_memory
        self._populate_semantic_memory(self.SAMPLE_GRAPH, self.TOPIC)
        count_before = len(semantic_memory.nodes)
        self._populate_semantic_memory(self.SAMPLE_GRAPH, self.TOPIC)
        count_after = len(semantic_memory.nodes)
        assert count_after == count_before
