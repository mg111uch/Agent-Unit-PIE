import sys
import os
import json
from unittest.mock import patch, MagicMock

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))

import pytest


def _make_state(**overrides):
    base = {"current_topic": "", "seen_arguments": [], "responses": []}
    base.update(overrides)
    return base


def _make_beliefs(**overrides):
    base = {"arguments": {}}
    base.update(overrides)
    return base


class TestBuildKnowledgeContext:
    @pytest.fixture(autouse=True)
    def setup(self):
        from kernel.memory.semantic_memory import semantic_memory
        semantic_memory.clear()
        semantic_memory.create_node(
            node_id="arg_test_topic_pro", node_type="argument",
            title="Pro Argument", content="This supports the topic",
            concepts=["pro"], tags=["test_topic", "debate"],
            confidence=1.0, importance=0.7,
        )
        semantic_memory.create_node(
            node_id="arg_test_topic_con", node_type="argument",
            title="Con Argument", content="This opposes the topic",
            concepts=["con"], tags=["test_topic", "debate"],
            confidence=1.0, importance=0.7,
        )
        yield
        semantic_memory.clear()

    def test_returns_context_with_existing_nodes(self):
        from modules.argu_god.engine.debate_helpers import _build_knowledge_context
        result = _build_knowledge_context("test_topic")
        assert result["topic"] == "test_topic"
        assert result["existing_nodes"] >= 2
        assert result["has_knowledge"] is True

    def test_returns_no_knowledge_for_unknown_topic(self):
        from modules.argu_god.engine.debate_helpers import _build_knowledge_context
        result = _build_knowledge_context("nonexistent_topic")
        assert result["has_knowledge"] is False
        assert result["existing_nodes"] == 0


class TestCheckNovelty:
    @pytest.fixture(autouse=True)
    def setup(self):
        from kernel.memory.semantic_memory import semantic_memory
        semantic_memory.clear()
        semantic_memory.create_node(
            node_id="arg_test_existing", node_type="argument",
            title="Existing", content="This is existing content for similarity check",
            concepts=["test"], tags=["test"],
            confidence=1.0, importance=0.7,
        )
        yield
        semantic_memory.clear()

    def test_returns_true_for_novel_text(self):
        from modules.argu_god.engine.debate_helpers import _check_novelty
        with patch("modules.argu_god.engine.dedup.is_similar_to_any", return_value=False):
            assert _check_novelty("Completely new content here") is True

    def test_returns_false_for_similar_text(self):
        from modules.argu_god.engine.debate_helpers import _check_novelty
        with patch("modules.argu_god.engine.dedup.is_similar_to_any", return_value=True):
            assert _check_novelty("Existing content") is False


class TestStoreUserKnowledge:
    @pytest.fixture(autouse=True)
    def setup(self):
        from kernel.memory.semantic_memory import semantic_memory
        semantic_memory.clear()
        semantic_memory.create_node(
            node_id="arg_test_ref", node_type="argument",
            title="Ref Arg", content="Reference argument content",
            concepts=["pro"], tags=["test_topic"],
            confidence=1.0, importance=0.7,
        )
        yield
        semantic_memory.clear()

    def test_stores_user_belief_node(self):
        from modules.argu_god.engine.debate_helpers import _store_user_knowledge
        from kernel.memory.semantic_memory import semantic_memory
        with patch("modules.argu_god.engine.vector_store._get_collection") as mock_coll:
            mock_coll.return_value.get.return_value = {"ids": []}
            node_id = _store_user_knowledge(
                argument_name="TestArg",
                stance="agree",
                confidence=0.8,
                topic="test_topic",
            )
        assert node_id is not None
        assert node_id.startswith("user_test_topic_TestArg_")
        assert node_id in semantic_memory.nodes

    def test_stores_with_user_text(self):
        from modules.argu_god.engine.debate_helpers import _store_user_knowledge
        from kernel.memory.semantic_memory import semantic_memory
        with patch("modules.argu_god.engine.vector_store._get_collection") as mock_coll:
            mock_coll.return_value.get.return_value = {"ids": []}
            node_id = _store_user_knowledge(
                argument_name="TestArg",
                stance="agree",
                confidence=0.8,
                topic="test_topic",
                user_text="My custom response text",
            )
        node = semantic_memory.nodes[node_id]
        assert node.content == "My custom response text"
        assert node.node_type == "user_belief"

    def test_creates_edge_to_existing_node(self):
        from modules.argu_god.engine.debate_helpers import _store_user_knowledge
        from kernel.memory.semantic_memory import semantic_memory
        with patch("modules.argu_god.engine.vector_store._get_collection") as mock_coll:
            mock_coll.return_value.get.return_value = {"ids": []}
            node_id = _store_user_knowledge(
                argument_name="Ref Arg",
                stance="agree",
                confidence=0.8,
                topic="test_topic",
            )
        edges = list(semantic_memory.edges.values())
        assert len(edges) >= 1
        assert edges[0].relation_type == "related_to"

    def test_idempotent_same_node(self):
        from modules.argu_god.engine.debate_helpers import _store_user_knowledge
        from kernel.memory.semantic_memory import semantic_memory
        frozen_now = 1000000000
        with patch("modules.argu_god.engine.debate_helpers.datetime") as mock_dt:
            mock_dt.now.return_value.timestamp.return_value = frozen_now
            with patch("modules.argu_god.engine.vector_store._get_collection") as mock_coll:
                mock_coll.return_value.get.return_value = {"ids": []}
                nid1 = _store_user_knowledge(
                    argument_name="IdempotentArg", stance="agree", confidence=0.8, topic="test_topic",
                )
                assert nid1 in semantic_memory.nodes
                count_before = len(semantic_memory.nodes)
                nid2 = _store_user_knowledge(
                    argument_name="IdempotentArg", stance="agree", confidence=0.8, topic="test_topic",
                )
                count_after = len(semantic_memory.nodes)
                assert count_after == count_before


class TestGetUntouchedKnowledge:
    @pytest.fixture(autouse=True)
    def setup(self):
        from kernel.memory.semantic_memory import semantic_memory
        semantic_memory.clear()
        semantic_memory.create_node(
            node_id="arg_topic_unseen", node_type="argument",
            title="Unseen Argument", content="Not yet seen content",
            concepts=["pro"], tags=["test_topic", "debate"],
            confidence=1.0, importance=0.7,
        )
        semantic_memory.create_node(
            node_id="arg_topic_seen", node_type="argument",
            title="Seen Argument", content="Already seen content",
            concepts=["con"], tags=["test_topic", "debate"],
            confidence=1.0, importance=0.7,
        )
        yield
        semantic_memory.clear()

    def test_returns_unseen_node(self):
        from modules.argu_god.engine.debate_helpers import _get_untouched_knowledge
        state = _make_state(current_topic="test_topic", seen_arguments=["Seen Argument"])
        beliefs = _make_beliefs()
        result = _get_untouched_knowledge("test_topic", state, beliefs)
        assert result is not None
        assert result["name"] == "Unseen Argument"

    def test_returns_none_when_all_seen(self):
        from modules.argu_god.engine.debate_helpers import _get_untouched_knowledge
        state = _make_state(
            current_topic="test_topic",
            seen_arguments=["Seen Argument", "Unseen Argument"],
        )
        beliefs = _make_beliefs()
        result = _get_untouched_knowledge("test_topic", state, beliefs)
        assert result is None

    def test_skips_known_beliefs(self):
        from modules.argu_god.engine.debate_helpers import _get_untouched_knowledge
        state = _make_state(current_topic="test_topic", seen_arguments=[])
        beliefs = _make_beliefs(arguments={
            "Unseen Argument": {"stance": "agree", "confidence": 0.8},
        })
        result = _get_untouched_knowledge("test_topic", state, beliefs)
        assert result is not None
        assert result["name"] == "Seen Argument"


class TestGenerateNextQuestion:
    SAMPLE_GRAPH = {
        "nodes": [
            {"name": "Graph Arg", "premise": "From graph", "side": "pro"},
        ],
        "edges": [],
    }

    @pytest.fixture(autouse=True)
    def setup(self):
        from kernel.memory.semantic_memory import semantic_memory
        semantic_memory.clear()
        yield
        semantic_memory.clear()

    def test_returns_from_graph_when_available(self):
        from modules.argu_god.engine.debate_helpers import _generate_next_question
        state = _make_state(current_topic="test", seen_arguments=[])
        beliefs = _make_beliefs()
        with patch("modules.argu_god.engine.debate_helpers.get_next_argument") as mock_get:
            mock_get.return_value = {"name": "Graph Arg", "premise": "From graph", "side": "pro"}
            arg, counter = _generate_next_question("test", state, beliefs, self.SAMPLE_GRAPH, {})
        assert arg is not None
        assert arg["name"] == "Graph Arg"

    def test_returns_none_when_nothing_available(self):
        from modules.argu_god.engine.debate_helpers import _generate_next_question
        state = _make_state(current_topic="test", seen_arguments=[])
        beliefs = _make_beliefs()
        with patch("modules.argu_god.engine.debate_helpers.get_next_argument", return_value=None):
            with patch("modules.argu_god.engine.debate_helpers._get_untouched_knowledge", return_value=None):
                with patch("modules.argu_god.llm_compiler.generate_llm_question", return_value=None):
                    arg, counter = _generate_next_question("test", state, beliefs, self.SAMPLE_GRAPH, {})
        assert arg is None

    def test_falls_back_to_llm_when_graph_exhausted(self):
        from modules.argu_god.engine.debate_helpers import _generate_next_question
        state = _make_state(current_topic="test", seen_arguments=[])
        beliefs = _make_beliefs()
        llm_result = {"name": "LLM Arg", "premise": "Generated by LLM", "side": "con"}
        with patch("modules.argu_god.engine.debate_helpers.get_next_argument", return_value=None):
            with patch("modules.argu_god.engine.debate_helpers._get_untouched_knowledge", return_value=None):
                with patch("modules.argu_god.llm_compiler.generate_llm_question", return_value=llm_result):
                    with patch("modules.argu_god.engine.dedup.is_similar_to_any", return_value=False):
                        arg, counter = _generate_next_question("test", state, beliefs, self.SAMPLE_GRAPH, {})
        assert arg is not None
        assert arg["name"] == "LLM Arg"
