"""
llm/context_builder.py

Dynamic cognition context builder.

Purpose
-------
Construct optimized LLM context packets from:

- observations
- events
- signals
- patterns
- relations
- timelines
- summaries
- working memory

This is one of the MOST IMPORTANT systems
inside agent_unit_pie.

Why It Exists
-------------
LLMs have limited context windows.

But local knowledge bases can grow infinitely.

This system solves that problem by creating:

dynamic task-focused cognition packets.

Core Idea
---------
Instead of loading entire KB:

retrieve
    → compress
    → prioritize
    → assemble
    → inject

Only the MOST relevant cognition artifacts
enter the LLM context.
"""

from __future__ import annotations

import json
import logging
from datetime import datetime, timezone
from typing import Dict, Any, Optional, List

logger = logging.getLogger(__name__)

class ContextBuilder:
    """
    Dynamic cognition context assembler.
    """
    # INIT
    def __init__(
        self,
        retrieval_engine=None,
        memory_engine=None,
        compression_engine=None,
        token_estimator=None,
        config: Optional[
            Dict[str, Any]
        ] = None,
    ):
        self.retrieval_engine = (
            retrieval_engine
        )
        self.memory_engine = (
            memory_engine
        )
        self.compression_engine = (
            compression_engine
        )
        self.token_estimator = (
            token_estimator
        )
        self.config = config or {}
        # DEFAULTS
        self.max_context_tokens = (
            self.config.get(
                "max_context_tokens",
                12000,
            )
        )
        self.max_patterns = self.config.get(
            "max_patterns",
            20,
        )
        self.max_events = self.config.get(
            "max_events",
            40,
        )
        self.max_observations = (
            self.config.get(
                "max_observations",
                40,
            )
        )
    # MAIN ENTRY
    def build_context(
        self,
        task: str,
        unit_id: Optional[
            str
        ] = None,
        unit_type: Optional[
            str
        ] = None,
        additional_context: Optional[
            Dict[str, Any]
        ] = None,
    ) -> Dict[str, Any]:
        """
        Main context generation pipeline.
        """
        logger.info(
            f"Building context for task: {task}"
        )
        # RETRIEVE MEMORY
        retrieval_result = (
            self.retrieve_relevant_memory(
                task=task,
                unit_id=unit_id,
                unit_type=unit_type,
            )
        )
        # PRIORITIZE
        prioritized = (
            self.prioritize_context(
                retrieval_result,
                task,
            )
        )
        # COMPRESS
        compressed = (
            self.compress_context(
                prioritized
            )
        )
        # ASSEMBLE
        final_context = {
            "task": task,
            "unit_id": unit_id,
            "unit_type": unit_type,
            "generated_at": self.utc_now(),
            "context": compressed,
        }
        if additional_context:
            final_context[
                "additional_context"
            ] = additional_context
        return final_context
    # RETRIEVAL
    def retrieve_relevant_memory(
        self,
        task: str,
        unit_id: Optional[
            str
        ] = None,
        unit_type: Optional[
            str
        ] = None,
    ) -> Dict[str, Any]:
        """
        Retrieve relevant cognition artifacts.
        """
        if self.retrieval_engine is None:
            logger.warning(
                "Retrieval engine missing."
            )
            return {}
        try:
            return (
                self.retrieval_engine.retrieve(
                    query=task,
                    unit_id=unit_id,
                    unit_type=unit_type,
                )
            )
        except Exception:
            logger.exception(
                "Memory retrieval failed."
            )
            return {}
    # PRIORITIZATION
    def prioritize_context(
        self,
        retrieval_result: Dict[str, Any],
        task: str,
    ) -> Dict[str, Any]:
        """
        Rank retrieved artifacts by relevance.
        """
        prioritized = {}
        # PATTERNS
        patterns = retrieval_result.get(
            "patterns",
            [],
        )
        patterns = sorted(
            patterns,
            key=lambda x: float(
                x.get(
                    "relevance_score",
                    0.0,
                )
            ),
            reverse=True,
        )
        prioritized["patterns"] = (
            patterns[: self.max_patterns]
        )
        # EVENTS
        events = retrieval_result.get(
            "events",
            [],
        )
        prioritized["events"] = (
            events[: self.max_events]
        )
        # OBSERVATIONS
        observations = retrieval_result.get(
            "observations",
            [],
        )
        prioritized["observations"] = (
            observations[
                : self.max_observations
            ]
        )
        # SIGNALS
        prioritized["signals"] = (
            retrieval_result.get(
                "signals",
                [],
            )
        )
        # RELATIONS
        prioritized["relations"] = (
            retrieval_result.get(
                "relations",
                [],
            )
        )
        # SUMMARIES
        prioritized["summaries"] = (
            retrieval_result.get(
                "summaries",
                [],
            )
        )
        return prioritized
    # COMPRESSION
    def compress_context(
        self,
        prioritized_context: Dict[str, Any],
    ) -> Dict[str, Any]:
        """
        Compress context intelligently.
        """
        if self.compression_engine is None:
            return prioritized_context
        try:
            compressed = {}
            for key, value in (
                prioritized_context.items()
            ):
                compressed[key] = (
                    self.compress_section(
                        key,
                        value,
                    )
                )
            return compressed
        except Exception:
            logger.exception(
                "Context compression failed."
            )
            return prioritized_context
    # SECTION COMPRESSION
    def compress_section(
        self,
        section_name: str,
        section_data: Any,
    ) -> Any:
        """
        Compress individual context section.
        """
        # --------------------------------------------------------
        # PLACEHOLDER
        # Future:
        # summarization
        # abstraction
        # recursive compression
        # --------------------------------------------------------
        return section_data
    # TOKEN CONTROL
    def trim_to_token_limit(
        self,
        context: Dict[str, Any],
    ) -> Dict[str, Any]:
        """
        Ensure context fits token budget.
        """
        if self.token_estimator is None:
            return context
        current_tokens = (
            self.token_estimator.estimate(
                json.dumps(context)
            )
        )
        if (
            current_tokens
            <= self.max_context_tokens
        ):
            return context
        logger.warning(
            "Context exceeds token limit."
        )
        # SIMPLE TRIMMING STRATEGY
        trimmed = dict(context)
        for key in [
            "observations",
            "events",
            "signals",
        ]:
            if key not in trimmed:
                continue
            section = trimmed[key]
            if isinstance(section, list):
                trimmed[key] = section[
                    : max(1, len(section) // 2)
                ]
                current_tokens = (
                    self.token_estimator
                    .estimate(
                        json.dumps(trimmed)
                    )
                )
                if (
                    current_tokens
                    <= self.max_context_tokens
                ):
                    break
        return trimmed
    # PROMPT CONTEXT
    def build_prompt_context(
        self,
        context: Dict[str, Any],
    ) -> str:
        """
        Convert context into prompt-safe text.
        """
        try:
            return json.dumps(
                context,
                indent=2,
                ensure_ascii=False,
            )
        except Exception:
            logger.exception(
                "Prompt context serialization failed."
            )
            return str(context)
    # HEALTH CHECK
    def health_check(
        self,
    ) -> Dict[str, Any]:
        return {
            "retrieval_engine": (
                self.retrieval_engine
                is not None
            ),
            "memory_engine": (
                self.memory_engine
                is not None
            ),
            "compression_engine": (
                self.compression_engine
                is not None
            ),
            "token_estimator": (
                self.token_estimator
                is not None
            ),
            "max_context_tokens": (
                self.max_context_tokens
            ),
        }
    # HELPERS
    @staticmethod
    def utc_now() -> str:
        return datetime.now(
            timezone.utc
        ).isoformat()