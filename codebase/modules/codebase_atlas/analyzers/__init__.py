"""
Analyzer modules for Codebase Atlas.

This package contains analyzers that build higher-level insights:
- Dependency graph construction
- Impact analysis (what breaks if X changes)
- Entry point detection and aggregation
"""

from .dependency_analyzer import DependencyAnalyzer
from .impact_analyzer import ImpactAnalyzer
from .entry_point_detector import EntryPointDetector

__all__ = [
    'DependencyAnalyzer',
    'ImpactAnalyzer',
    'EntryPointDetector',
]