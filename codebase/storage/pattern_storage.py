"""
storage/pattern_storage.py

Global pattern persistence layer.

Purpose
-------
Stores, indexes, and retrieves higher-order intelligence patterns.

Patterns are one of the most important cognition artifacts
inside agent_unit_pie.

Examples
--------
behavioral patterns
economic patterns
organizational patterns
market patterns
social patterns
temporal patterns
causal patterns
city evolution patterns

This storage layer enables:

- recursive abstraction
- global pattern mining
- cross-unit intelligence
- long-term trend analysis
- simulation guidance
- strategic forecasting
"""

from __future__ import annotations

import json
import logging
from pathlib import Path
from datetime import datetime, timezone
from typing import Dict, Any, Optional, List

logger = logging.getLogger(__name__)

class PatternStorage:
    """
    Global persistent pattern storage manager.
    """
    # INIT
    def __init__(
        self,
        base_path: str = "global_patterns",
    ):
        self.base_path = Path(base_path)
        self.base_path.mkdir(
            parents=True,
            exist_ok=True,
        )
        # STANDARD DIRECTORIES
        self.patterns_path = (
            self.base_path / "patterns"
        )
        self.index_path = (
            self.base_path / "indexes"
        )
        self.summaries_path = (
            self.base_path / "summaries"
        )
        self.patterns_path.mkdir(
            parents=True,
            exist_ok=True,
        )
        self.index_path.mkdir(
            parents=True,
            exist_ok=True,
        )
        self.summaries_path.mkdir(
            parents=True,
            exist_ok=True,
        )
    # SAVE PATTERN
    def save_pattern(
        self,
        pattern: Dict[str, Any],
    ) -> str:
        """
        Persist pattern to storage.
        """
        pattern_id = pattern.get(
            "pattern_id",
            self.generate_pattern_id(),
        )
        pattern["pattern_id"] = pattern_id
        pattern.setdefault(
            "created_at",
            self.utc_now(),
        )
        pattern.setdefault(
            "updated_at",
            self.utc_now(),
        )
        pattern_type = pattern.get(
            "pattern_type",
            "generic",
        )
        pattern_dir = (
            self.patterns_path
            / pattern_type
        )
        pattern_dir.mkdir(
            parents=True,
            exist_ok=True,
        )
        pattern_path = (
            pattern_dir
            / f"{pattern_id}.json"
        )
        self.write_json(
            pattern_path,
            pattern,
        )
        # UPDATE INDEXES
        self.update_indexes(pattern)
        logger.info(
            f"Saved pattern: {pattern_id}"
        )
        return pattern_id
    # LOAD PATTERN
    def load_pattern(
        self,
        pattern_type: str,
        pattern_id: str,
    ) -> Optional[Dict[str, Any]]:
        """
        Load pattern by type + ID.
        """
        path = (
            self.patterns_path
            / pattern_type
            / f"{pattern_id}.json"
        )
        if not path.exists():
            return None
        return self.read_json(path)
    # LIST PATTERNS
    def list_patterns(
        self,
        pattern_type: Optional[str] = None,
    ) -> List[str]:
        """
        List stored patterns.
        """
        results = []
        if pattern_type:
            path = (
                self.patterns_path
                / pattern_type
            )
            if not path.exists():
                return []
            for file in path.glob("*.json"):
                results.append(file.stem)
            return sorted(results)
        # ALL PATTERNS
        for type_dir in self.patterns_path.iterdir():
            if not type_dir.is_dir():
                continue
            for file in type_dir.glob("*.json"):
                results.append(
                    f"{type_dir.name}/{file.stem}"
                )
        return sorted(results)
    # SEARCH PATTERNS
    def search_patterns(
        self,
        pattern_type: Optional[str] = None,
        tags: Optional[List[str]] = None,
        min_confidence: float = 0.0,
    ) -> List[Dict[str, Any]]:
        """
        Basic metadata search over patterns.
        """
        results = []
        pattern_types = []
        if pattern_type:
            pattern_types.append(pattern_type)
        else:
            pattern_types = [
                p.name
                for p in self.patterns_path.iterdir()
                if p.is_dir()
            ]
        # SEARCH
        for ptype in pattern_types:
            path = (
                self.patterns_path
                / ptype
            )
            if not path.exists():
                continue
            for file in path.glob("*.json"):
                try:
                    pattern = self.read_json(file)
                    confidence = float(
                        pattern.get(
                            "confidence",
                            0.0,
                        )
                    )
                    if confidence < min_confidence:
                        continue
                    if tags:
                        pattern_tags = set(
                            pattern.get(
                                "tags",
                                [],
                            )
                        )
                        if not set(tags).intersection(
                            pattern_tags
                        ):
                            continue
                    results.append(pattern)
                except Exception:
                    logger.exception(
                        f"Failed loading pattern file: {file}"
                    )
        return results
    # UPDATE INDEXES
    def update_indexes(
        self,
        pattern: Dict[str, Any],
    ) -> None:
        """
        Update lightweight metadata indexes.
        """
        pattern_type = pattern.get(
            "pattern_type",
            "generic",
        )
        index_file = (
            self.index_path
            / f"{pattern_type}_index.json"
        )
        if index_file.exists():
            index_data = self.read_json(index_file)
        else:
            index_data = {
                "pattern_type": pattern_type,
                "updated_at": self.utc_now(),
                "patterns": [],
            }
        # INDEX ENTRY
        entry = {
            "pattern_id": pattern.get(
                "pattern_id"
            ),
            "title": pattern.get(
                "title",
                "",
            ),
            "confidence": pattern.get(
                "confidence",
                0.0,
            ),
            "tags": pattern.get(
                "tags",
                [],
            ),
            "updated_at": self.utc_now(),
        }
        index_data["patterns"].append(entry)
        index_data["updated_at"] = (
            self.utc_now()
        )
        self.write_json(
            index_file,
            index_data,
        )
    # SAVE SUMMARY
    def save_pattern_summary(
        self,
        summary_name: str,
        summary_data: Dict[str, Any],
    ) -> None:
        """
        Store higher-order pattern summaries.
        """
        path = (
            self.summaries_path
            / f"{summary_name}.json"
        )
        self.write_json(
            path,
            summary_data,
        )
    # DELETE PATTERN
    def delete_pattern(
        self,
        pattern_type: str,
        pattern_id: str,
    ) -> bool:
        """
        Delete pattern file.
        """
        path = (
            self.patterns_path
            / pattern_type
            / f"{pattern_id}.json"
        )
        if not path.exists():
            return False
        path.unlink()
        logger.info(
            f"Deleted pattern: {pattern_id}"
        )
        return True
    # PATTERN EXISTS
    def pattern_exists(
        self,
        pattern_type: str,
        pattern_id: str,
    ) -> bool:
        path = (
            self.patterns_path
            / pattern_type
            / f"{pattern_id}.json"
        )
        return path.exists()
    # JSON HELPERS
    def write_json(
        self,
        path: Path,
        data: Dict[str, Any],
    ) -> None:
        path.parent.mkdir(
            parents=True,
            exist_ok=True,
        )
        with open(
            path,
            "w",
            encoding="utf-8",
        ) as f:
            json.dump(
                data,
                f,
                indent=2,
                ensure_ascii=False,
            )
    def read_json(
        self,
        path: Path,
    ) -> Dict[str, Any]:
        with open(
            path,
            "r",
            encoding="utf-8",
        ) as f:
            return json.load(f)
    # HELPERS
    @staticmethod
    def utc_now() -> str:
        return datetime.now(
            timezone.utc
        ).isoformat()

    @staticmethod
    def generate_pattern_id() -> str:
        return (
            "pattern_"
            + datetime.now(
                timezone.utc
            ).strftime(
                "%Y%m%d%H%M%S%f"
            )
        )