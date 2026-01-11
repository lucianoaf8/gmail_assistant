"""
Centralized exception definitions.

CORRECTED: This is the SINGLE SOURCE OF TRUTH for all domain exceptions.
All modules must import exceptions from here, not define their own.

H-2 fix: Complete exception hierarchy with all domain-specific exceptions.
"""
from __future__ import annotations

__all__ = [
    "APIError",
    "AuthError",
    "BatchAPIError",
    "CircuitBreakerError",
    "CircularDependencyError",
    "ConfigError",
    "ExportError",
    "GmailAssistantError",
    "NetworkError",
    "ParseError",
    "RateLimitError",
    "ServiceNotFoundError",
    "ValidationError",
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


class BatchAPIError(APIError):
    """
    Batch API operation errors (H-2 fix).

    Tracks failed message IDs for retry handling.
    """

    def __init__(self, message: str, failed_ids: list[str] | None = None):
        self.message = message
        self.failed_ids = failed_ids or []
        super().__init__(message)


class ValidationError(GmailAssistantError):
    """Input validation errors. Maps to exit code 2."""
    pass


class ParseError(GmailAssistantError):
    """Email/content parsing errors."""
    pass


class RateLimitError(APIError):
    """API rate limit exceeded errors."""

    def __init__(self, message: str, retry_after: int | None = None):
        self.retry_after = retry_after
        super().__init__(message)


class ServiceNotFoundError(GmailAssistantError):
    """Dependency injection service not found."""
    pass


class CircularDependencyError(GmailAssistantError):
    """Circular dependency detected in DI container."""
    pass


class ExportError(GmailAssistantError):
    """Data export operation errors."""
    pass


class CircuitBreakerError(GmailAssistantError):
    """Circuit breaker open - service unavailable."""

    def __init__(self, message: str, failure_count: int = 0):
        self.failure_count = failure_count
        super().__init__(message)
