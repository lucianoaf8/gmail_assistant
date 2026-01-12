"""
Standardized logging utilities for Gmail Assistant.

Usage:
    from gmail_assistant.utils.logging_utils import get_logger

    logger = get_logger(__name__)  # Module-level, preferred

This module provides consistent logger creation and configuration.
All modules should use get_logger() instead of direct logging.getLogger() calls.
"""

import logging
from typing import Optional


def get_logger(name: str, level: Optional[int] = None) -> logging.Logger:
    """
    Get a configured logger for the given module.

    Args:
        name: Module name, typically __name__
        level: Optional log level override

    Returns:
        Configured Logger instance.

    Example:
        >>> logger = get_logger(__name__)
        >>> logger.info("Message logged")
    """
    logger = logging.getLogger(name)
    if level is not None:
        logger.setLevel(level)
    return logger


def configure_root_logger(
    level: int = logging.INFO,
    format_string: str = "%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    datefmt: str = "%Y-%m-%d %H:%M:%S"
) -> None:
    """
    Configure the root logger for the application.

    Should be called once at application startup (e.g., in CLI main).

    Args:
        level: Logging level (default: INFO)
        format_string: Log message format
        datefmt: Date format for timestamps
    """
    logging.basicConfig(
        level=level,
        format=format_string,
        datefmt=datefmt
    )


def configure_file_logging(
    log_file: str,
    level: int = logging.DEBUG,
    format_string: str = "%(asctime)s - %(name)s - %(levelname)s - %(message)s"
) -> logging.FileHandler:
    """
    Configure file-based logging.

    Args:
        log_file: Path to log file
        level: Logging level for file (default: DEBUG)
        format_string: Log message format

    Returns:
        FileHandler that was configured and added.
    """
    file_handler = logging.FileHandler(log_file, encoding='utf-8')
    file_handler.setLevel(level)
    file_handler.setFormatter(logging.Formatter(format_string))
    logging.getLogger().addHandler(file_handler)
    return file_handler


def set_package_log_level(level: int) -> None:
    """
    Set log level for all gmail_assistant loggers.

    Args:
        level: Logging level to set
    """
    logging.getLogger('gmail_assistant').setLevel(level)


# Convenience log level constants
DEBUG = logging.DEBUG
INFO = logging.INFO
WARNING = logging.WARNING
ERROR = logging.ERROR
CRITICAL = logging.CRITICAL
