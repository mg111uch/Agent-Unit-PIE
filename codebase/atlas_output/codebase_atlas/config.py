"""
Configuration management for Codebase Atlas.

This module contains all configuration settings with sensible defaults.
Settings can be modified directly in this file.
"""

from pathlib import Path
from typing import Set, Dict, List
from dataclasses import dataclass, field


# =============================================================================
# CORE SETTINGS
# =============================================================================

@dataclass
class AtlasConfig:
    """Main configuration class for Codebase Atlas."""
    
    # -------------------------------------------------------------------------
    # Input Settings
    # -------------------------------------------------------------------------
    project_dir: str = "."
    ignore_dirs: Set[str] = field(default_factory=lambda: {
        '.git', '__pycache__', 'venv', 'node_modules', 
        '.ipynb_checkpoints', 'dist', 'build', '.next',
        'coverage', '.pytest_cache', '.mypy_cache'
    })
    ignore_files: Set[str] = field(default_factory=lambda: {
        '.gitignore', '.env', '.DS_Store', 'package-lock.json',
        'yarn.lock', 'poetry.lock'
    })
    
    # -------------------------------------------------------------------------
    # Output Settings
    # -------------------------------------------------------------------------
    output_dir: str = "./atlas_output"
    base_filename: str = "code_atlas.md"
    children_dir: str = "children"
    
    # -------------------------------------------------------------------------
    # Analysis Settings
    # -------------------------------------------------------------------------
    max_files_per_child: int = 10  # Max files per children/*.md
    languages: List[str] = field(default_factory=lambda: [
        'python', 'javascript', 'typescript', 'html'
    ])
    track_external_deps: bool = True  # Include external library calls
    detect_circular_deps: bool = True
    
    # -------------------------------------------------------------------------
    # Budget Limits
    # -------------------------------------------------------------------------
    base_max_loc: int = 100  # Base.md line count limit
    base_max_tokens: int = 1000  # Approximate token limit
    child_max_loc: int = 400  # Children/*.md line limit
    
    # -------------------------------------------------------------------------
    # Impact Analysis
    # -------------------------------------------------------------------------
    impact_depth: int = 3  # Track call chains N levels deep (A→B→C)
    risk_threshold_high: int = 3  # 3+ dependents = HIGH risk
    risk_threshold_medium: int = 2  # 2 dependents = MEDIUM risk
    
    # -------------------------------------------------------------------------
    # Formatting Settings
    # -------------------------------------------------------------------------
    verbose_mode: bool = False  # False = compact, True = verbose
    use_emoji: bool = True  # Use emoji symbols in output
    use_color_codes: bool = False  # Terminal color codes (future)
    
    # Compact notation symbols
    compact_symbols: Dict[str, str] = field(default_factory=lambda: {
        'separator': '│',
        'internal_dep': '►',
        'external_dep': '●',
        'entry_point': '⚡',
        'react_component': '⚛',
        'circular': '↔',
        'impact_arrow': '↳',
        'break_branch': '├─',
        'break_last': '└─',
    })
    
    # Risk level symbols
    risk_symbols: Dict[str, str] = field(default_factory=lambda: {
        'high': '🔴',
        'medium': '🟡',
        'low': '🟢',
        'safe': '⚪',
    })


# =============================================================================
# FILE TYPE EXTENSIONS
# =============================================================================

PYTHON_EXTENSIONS = {'.py'}
JAVASCRIPT_EXTENSIONS = {'.js', '.jsx', '.ts', '.tsx'}
HTML_EXTENSIONS = {'.html', '.htm'}
CONFIG_EXTENSIONS = {'.json', '.yaml', '.yml'}

ALL_EXTENSIONS = (
    PYTHON_EXTENSIONS | 
    JAVASCRIPT_EXTENSIONS | 
    HTML_EXTENSIONS | 
    CONFIG_EXTENSIONS
)


# =============================================================================
# ENTRY POINT DETECTION PATTERNS
# =============================================================================

# Patterns that indicate a file is an entry point
ENTRY_POINT_PATTERNS = {
    'python': [
        'if __name__ == "__main__"',
        'def main(',
        '@app.route',
        '@click.command',
        'app.run(',
        'uvicorn.run(',
    ],
    'javascript': [
        'ReactDOM.render',
        'createRoot(',
        'app.listen(',
        'server.listen(',
        'export default App',
    ]
}


# =============================================================================
# PRIORITY SYSTEM FOR BASE.MD TRUNCATION
# =============================================================================

# When base.md exceeds limits, items are included by priority
PRIORITY_LEVELS = {
    'critical': [
        'entry_points',      # Always include
        'high_risk_functions',  # Functions with 5+ dependents
        'circular_deps',     # Warning items
    ],
    'high': [
        'medium_risk_functions',  # Functions with 3-4 dependents
        'main_modules',      # Core application modules
    ],
    'medium': [
        'low_risk_functions',  # Functions with 2 dependents
        'utility_modules',   # Helper/utility modules
    ],
    'low': [
        'safe_functions',    # Functions with 0-1 dependents
        'test_modules',      # Test files
        'config_files',      # Configuration files
    ]
}


# =============================================================================
# MODULE CATEGORIZATION
# =============================================================================

# Heuristics for categorizing modules by directory/file names
MODULE_CATEGORIES = {
    'core': ['core', 'main', 'app', 'models', 'entities', 'components', 'systems'],
    'api': ['api', 'routes', 'handlers', 'endpoints', 'controllers', 'views'],
    'data': ['data', 'database', 'db', 'models', 'schema', 'migrations'],
    'utils': ['utils', 'helpers', 'common', 'lib', 'shared'],
    'tests': ['test', 'tests', 'spec', 'specs', '__tests__'],
    'config': ['config', 'settings', 'constants', 'env'],
}


# =============================================================================
# IMPACT ANALYSIS SETTINGS
# =============================================================================

# What to track for impact analysis
IMPACT_TRACKING = {
    'function_calls': True,      # Track who calls what
    'variable_reads': True,      # Track what reads variables
    'variable_writes': True,     # Track what writes variables
    'class_usage': True,         # Track class instantiation
    'external_calls': True,      # Track external library calls
}


# =============================================================================
# HELPER FUNCTIONS
# =============================================================================

def get_default_config() -> AtlasConfig:
    """Get default configuration."""
    return AtlasConfig()


def load_config(config_path: str = None) -> AtlasConfig:
    """
    Load configuration from file or return default.
    
    Args:
        config_path: Path to config file (future: YAML support)
    
    Returns:
        AtlasConfig instance
    """
    # For now, just return default config
    # Future: Load from YAML file and merge with defaults
    return get_default_config()


def get_file_category(file_path: Path) -> str:
    """
    Categorize a file based on its path.
    
    Args:
        file_path: Path to the file
    
    Returns:
        Category string ('core', 'api', 'utils', etc.)
    """
    path_str = str(file_path).lower()
    
    for category, keywords in MODULE_CATEGORIES.items():
        if any(keyword in path_str for keyword in keywords):
            return category
    
    return 'other'


def get_priority_level(risk_level: str, is_entry: bool) -> str:
    """
    Get priority level for base.md inclusion.
    
    Args:
        risk_level: 'high', 'medium', 'low', or 'safe'
        is_entry: Whether this is an entry point
    
    Returns:
        Priority level: 'critical', 'high', 'medium', or 'low'
    """
    if is_entry:
        return 'critical'
    
    if risk_level == 'high':
        return 'high'
    elif risk_level == 'medium':
        return 'medium'
    elif risk_level == 'low':
        return 'medium'
    else:  # safe
        return 'low'


def estimate_tokens(text: str) -> int:
    """
    Rough token estimation (1 token ≈ 4 characters).
    
    Args:
        text: Text to estimate
    
    Returns:
        Approximate token count
    """
    return len(text) // 4


# =============================================================================
# VALIDATION
# =============================================================================

def validate_config(config: AtlasConfig) -> bool:
    """
    Validate configuration settings.
    
    Args:
        config: Configuration to validate
    
    Returns:
        True if valid
    
    Raises:
        ValueError: If configuration is invalid
    """
    if config.max_files_per_child < 1:
        raise ValueError("max_files_per_child must be >= 1")
    
    if config.impact_depth < 1:
        raise ValueError("impact_depth must be >= 1")
    
    if config.base_max_loc < 50:
        raise ValueError("base_max_loc should be >= 50 for useful output")
    
    return True