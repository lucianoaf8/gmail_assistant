"""
Secure logging wrapper for Gmail Assistant.
Automatically redacts PII from log messages.

Security: Prevents sensitive data exposure in logs (M-4 fix)
"""

import logging
from typing import Any

from .pii_redactor import PIIRedactor


class SecureLogger:
    """Logger wrapper that automatically redacts PII (M-4 security fix)"""

    def __init__(self, name: str):
        """
        Initialize secure logger.

        Args:
            name: Logger name (typically __name__)
        """
        self._logger = logging.getLogger(name)
        self._redactor = PIIRedactor()

    def _redact(self, msg: Any) -> str:
        """Redact PII from message"""
        return self._redactor.redact_log_message(str(msg))

    def debug(self, msg: str, *args, **kwargs):
        """Log debug message with PII redaction"""
        self._logger.debug(self._redact(msg), *args, **kwargs)

    def info(self, msg: str, *args, **kwargs):
        """Log info message with PII redaction"""
        self._logger.info(self._redact(msg), *args, **kwargs)

    def warning(self, msg: str, *args, **kwargs):
        """Log warning message with PII redaction"""
        self._logger.warning(self._redact(msg), *args, **kwargs)

    def error(self, msg: str, *args, **kwargs):
        """Log error message with PII redaction"""
        self._logger.error(self._redact(msg), *args, **kwargs)

    def critical(self, msg: str, *args, **kwargs):
        """Log critical message with PII redaction"""
        self._logger.critical(self._redact(msg), *args, **kwargs)

    def exception(self, msg: str, *args, **kwargs):
        """Log exception with PII redaction"""
        self._logger.exception(self._redact(msg), *args, **kwargs)

    def setLevel(self, level):
        """Set logging level"""
        self._logger.setLevel(level)

    @property
    def level(self):
        """Get logging level"""
        return self._logger.level

    @property
    def logger(self):
        """Get underlying logger for direct access (e.g., adding handlers)."""
        return self._logger


def get_secure_logger(name: str) -> SecureLogger:
    """
    Get a secure logger instance.

    Args:
        name: Logger name (typically __name__)

    Returns:
        SecureLogger instance
    """
    return SecureLogger(name)
