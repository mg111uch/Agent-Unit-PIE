"""
Generator modules for Codebase Atlas.

This package contains generators that produce the atlas output files:
- Base generator: Creates base.md (Layer 1 - overview)
- Detail generator: Creates children/*.md (Layer 2 - detailed breakdown)
"""

from .base_generator import BaseGenerator
from .detail_generator import DetailGenerator

__all__ = [
    'BaseGenerator',
    'DetailGenerator',
]