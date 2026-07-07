from __future__ import annotations

from pathlib import Path
from typing import Optional
import os

# ROOT PATHS

CURRENT_FILE = Path(__file__).resolve()

UTILS_DIR = CURRENT_FILE.parent

KERNEL_DIR = UTILS_DIR.parent

PROJECT_ROOT = KERNEL_DIR.parent

# CORE DIRECTORIES

DATA_DIR = PROJECT_ROOT / "data"

MEMORY_DIR = DATA_DIR / "memory"

KB_DIR = DATA_DIR / "kb"

SIMULATION_DIR = DATA_DIR / "simulations"

LOGS_DIR = PROJECT_ROOT / "logs"

CACHE_DIR = PROJECT_ROOT / "cache"

TEMP_DIR = PROJECT_ROOT / "temp"

CONFIG_DIR = PROJECT_ROOT / "config"

# KNOWLEDGE BASE DIRECTORIES

CITY_KB_DIR = KB_DIR / "cities"

COUNTRY_KB_DIR = KB_DIR / "countries"

COMPANY_KB_DIR = KB_DIR / "companies"

HUMAN_KB_DIR = KB_DIR / "humans"

MARKET_KB_DIR = KB_DIR / "markets"

PATTERN_KB_DIR = KB_DIR / "patterns"

GLOBAL_KB_DIR = KB_DIR / "global"

# MEMORY DIRECTORIES

WORKING_MEMORY_DIR = MEMORY_DIR / "working"

EPISODIC_MEMORY_DIR = MEMORY_DIR / "episodic"

SEMANTIC_MEMORY_DIR = MEMORY_DIR / "semantic"

PATTERN_MEMORY_DIR = MEMORY_DIR / "patterns"

HYPOTHESIS_MEMORY_DIR = MEMORY_DIR / "hypotheses"

# SIMULATION DIRECTORIES

CITY_SIM_DIR = SIMULATION_DIR / "cities"

COUNTRY_SIM_DIR = SIMULATION_DIR / "countries"

MARKET_SIM_DIR = SIMULATION_DIR / "markets"

HUMAN_SIM_DIR = SIMULATION_DIR / "humans"

# CREATE DIRECTORIES

DEFAULT_DIRS = [

    DATA_DIR,

    MEMORY_DIR,
    KB_DIR,
    SIMULATION_DIR,

    LOGS_DIR,
    CACHE_DIR,
    TEMP_DIR,

    WORKING_MEMORY_DIR,
    EPISODIC_MEMORY_DIR,
    SEMANTIC_MEMORY_DIR,
    PATTERN_MEMORY_DIR,
    HYPOTHESIS_MEMORY_DIR,

    CITY_KB_DIR,
    COUNTRY_KB_DIR,
    COMPANY_KB_DIR,
    HUMAN_KB_DIR,
    MARKET_KB_DIR,
    PATTERN_KB_DIR,
    GLOBAL_KB_DIR,

    CITY_SIM_DIR,
    COUNTRY_SIM_DIR,
    MARKET_SIM_DIR,
    HUMAN_SIM_DIR,
]

def ensure_directories_exist():
    for directory in DEFAULT_DIRS:
        directory.mkdir(
            parents=True,
            exist_ok=True
        )

# PATH HELPERS

def get_kb_path(
    domain: str,
    entity_name: str
) -> Path:
    """
    Example:
        data/kb/cities/lucknow/
    """

    return KB_DIR / domain / entity_name.lower()

def get_memory_path(
    memory_type: str,
    entity_id: str
) -> Path:
    """
    Example:
        data/memory/semantic/human_abc123/
    """

    return MEMORY_DIR / memory_type / entity_id

def get_simulation_path(
    simulation_type: str,
    simulation_name: str
) -> Path:
    """
    Example:
        data/simulations/cities/lucknow_sim/
    """

    return (
        SIMULATION_DIR
        / simulation_type
        / simulation_name
    )

def get_log_file_path(
    log_name: str = "system.log"
) -> Path:

    return LOGS_DIR / log_name

def get_temp_file_path(
    filename: str
) -> Path:

    return TEMP_DIR / filename

def get_cache_file_path(
    filename: str
) -> Path:

    return CACHE_DIR / filename

# FILE HELPERS

def ensure_parent_dir(
    file_path: Path
):

    file_path.parent.mkdir(
        parents=True,
        exist_ok=True
    )

def path_exists(
    path: Path
) -> bool:

    return path.exists()

def create_dir(
    path: Path
):

    path.mkdir(
        parents=True,
        exist_ok=True
    )

# ENVIRONMENT HELPERS

def get_env(
    key: str,
    default: Optional[str] = None
) -> Optional[str]:

    return os.getenv(key, default)

# INITIALIZATION

ensure_directories_exist()