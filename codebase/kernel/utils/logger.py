from __future__ import annotations

import logging
from logging.handlers import RotatingFileHandler
from pathlib import Path
from typing import Optional

from kernel.utils.paths import LOGS_DIR

# LOGGER CACHE

_LOGGER_CACHE = {}

# LOG FORMAT

LOG_FORMAT = (
    "[%(asctime)s] "
    "[%(levelname)s] "
    "[%(name)s] "
    "%(message)s"
)

DATE_FORMAT = "%Y-%m-%d %H:%M:%S"

# LOG LEVELS

VALID_LOG_LEVELS = {
    "debug": logging.DEBUG,
    "info": logging.INFO,
    "warning": logging.WARNING,
    "error": logging.ERROR,
    "critical": logging.CRITICAL,
}

# CREATE LOGGER

def get_logger(
    name: str = "agent_unit_pie",
    level: str = "info",
    log_to_console: bool = True,
    log_to_file: bool = True,
    max_bytes: int = 10 * 1024 * 1024,
    backup_count: int = 5,
) -> logging.Logger:
    """
    Create or retrieve cached logger.
    """

    cache_key = f"{name}_{level}"

    if cache_key in _LOGGER_CACHE:
        return _LOGGER_CACHE[cache_key]

    logger = logging.getLogger(name)

    logger.setLevel(
        VALID_LOG_LEVELS.get(
            level.lower(),
            logging.INFO
        )
    )

    logger.propagate = False

    # Prevent duplicate handlers
    if logger.handlers:
        logger.handlers.clear()

    formatter = logging.Formatter(
        LOG_FORMAT,
        datefmt=DATE_FORMAT
    )

    # CONSOLE HANDLER

    if log_to_console:

        console_handler = logging.StreamHandler()

        console_handler.setFormatter(formatter)

        logger.addHandler(console_handler)

    # FILE HANDLER

    if log_to_file:

        log_file = LOGS_DIR / f"{name}.log"

        file_handler = RotatingFileHandler(
            filename=log_file,
            maxBytes=max_bytes,
            backupCount=backup_count,
            encoding="utf-8"
        )

        file_handler.setFormatter(formatter)

        logger.addHandler(file_handler)

    _LOGGER_CACHE[cache_key] = logger

    return logger

# ROOT LOGGER

root_logger = get_logger()

# SHORTCUT FUNCTIONS

def debug(message: str):
    root_logger.debug(message)

def info(message: str):
    root_logger.info(message)

def warning(message: str):
    root_logger.warning(message)

def error(message: str):
    root_logger.error(message)

def critical(message: str):
    root_logger.critical(message)

# EXCEPTION LOGGER

def log_exception(
    exception: Exception,
    context: Optional[str] = None
):
    """
    Logs exception with traceback.
    """

    if context:
        root_logger.exception(
            f"{context}: {str(exception)}"
        )
    else:
        root_logger.exception(
            str(exception)
        )

# STRUCTURED LOGGING

def structured_log(
    level: str,
    event_type: str,
    data: dict
):
    """
    Structured event logging.
    """

    message = (
        f"[EVENT={event_type}] "
        f"{data}"
    )

    logger_method = getattr(
        root_logger,
        level.lower(),
        root_logger.info
    )

    logger_method(message)

# CHILD LOGGER

def get_child_logger(
    child_name: str
) -> logging.Logger:
    """
    Example:
        kernel.memory
        kernel.simulation
    """

    return get_logger(
        name=f"agent_unit_pie.{child_name}"
    )