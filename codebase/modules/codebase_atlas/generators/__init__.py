"""
Generator modules for Codebase Atlas.

This package contains generators that produce the atlas output files:
- Base generator: Creates base.md (Layer 1 - overview)
- Detail generator: Creates children/*.md (Layer 2 - detailed breakdown)
- Mermaid generator: Creates Mermaid.js graph visualizations
"""

from .base_generator import BaseGenerator
from .detail_generator import DetailGenerator
from .mermaid_generator import MermaidGenerator

__all__ = [
    'BaseGenerator',
    'DetailGenerator',
    'MermaidGenerator',
]