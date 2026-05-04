"""
Codebase Atlas - AI-powered codebase mapping for intelligent agent navigation.

This package generates compact, hierarchical documentation that helps LLM agents
understand codebase structure, dependencies, and impact analysis without reading
every file.

Key Features:
- 3-layer navigation (base.md → children/*.md → source)
- 60-70% context reduction via compact notation
- Inline impact analysis ("what breaks if X changes")
- Multi-language support (Python, JS/TS, React, HTML)

Usage:
    from codebase_atlas.main import generate_atlas
    
    generate_atlas(
        project_dir="/path/to/project",
        output_dir="./atlas_output"
    )
"""

__version__ = "1.0.0"
__author__ = "Codebase Atlas Contributors"
__license__ = "MIT"

# Public API
from .config import (
    AtlasConfig,
    get_default_config,
    load_config,
)

from .models import (
    FileInfo,
    FunctionInfo,
    ClassInfo,
    DependencyGraph,
    ImpactNode,
    AtlasData,
)

__all__ = [
    # Config
    "AtlasConfig",
    "get_default_config",
    "load_config",
    
    # Models
    "FileInfo",
    "FunctionInfo",
    "ClassInfo",
    "DependencyGraph",
    "ImpactNode",
    "AtlasData",
    
    # Metadata
    "__version__",
    "__author__",
    "__license__",
]