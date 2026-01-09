"""
Centralized exception definitions.

CORRECTED: This is the SINGLE SOURCE OF TRUTH for all domain exceptions.
All modules must import exceptions from here, not define their own.
"""
from __future__ import annotations

__all__ = [
    "GmailAssistantError",
    "ConfigError",
    "AuthError",
    "NetworkError",
    "APIError",
]


class GmailAssistantError(Exception):
    """Base exception for Gmail Assistant. All domain exceptions inherit from this."""
    pass


class ConfigError(GmailAssistantError):
    """Configuration-related errors. Maps to exit code 5."""
    pass


class AuthError(GmailAssistantError):
    """Authentication/authorization errors. Maps to exit code 3."""
    pass


class NetworkError(GmailAssistantError):
    """Network connectivity errors. Maps to exit code 4."""
    pass


class APIError(GmailAssistantError):
    """Gmail API errors. Maps to exit code 1 (general)."""
    pass
