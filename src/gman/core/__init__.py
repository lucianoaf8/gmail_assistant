"""
Gman Core Module
===========================

Core functionality for Gmail API operations, configuration, and utilities.

Sub-packages:
- auth: Authentication and credential management
- fetch: Email fetching operations
- processing: Email content processing
- ai: AI-powered email processing

Key exports:
- AppConfig: Configuration loader
- GmailAssistantError: Base exception
- ConfigError, AuthError, NetworkError, APIError: Domain exceptions

C-3 fix: Uses explicit conditional imports instead of __getattr__ for
better static analysis and clearer error messages.
"""

from typing import TYPE_CHECKING

# =============================================================================
# Core Imports (Always Available)
# =============================================================================

from gman.core.config import AppConfig
from gman.core.exceptions import (
    APIError,
    AuthError,
    ConfigError,
    GmailAssistantError,
    NetworkError,
)

# =============================================================================
# Auth Sub-package (Conditional)
# =============================================================================

try:
    from .auth.base import (
        AuthenticationBase,
        FullGmailAuth,
        GmailModifyAuth,
        ReadOnlyGmailAuth,
    )
    from .auth.credential_manager import SecureCredentialManager
    _AUTH_AVAILABLE = True
except ImportError as _auth_err:
    _AUTH_AVAILABLE = False
    _auth_import_error = str(_auth_err)
    # Type stubs for static analysis
    if TYPE_CHECKING:
        from .auth.base import (
            AuthenticationBase,
            FullGmailAuth,
            GmailModifyAuth,
            ReadOnlyGmailAuth,
        )
        from .auth.credential_manager import SecureCredentialManager
    else:
        ReadOnlyGmailAuth = None  # type: ignore[misc, assignment]
        GmailModifyAuth = None  # type: ignore[misc, assignment]
        FullGmailAuth = None  # type: ignore[misc, assignment]
        AuthenticationBase = None  # type: ignore[misc, assignment]
        SecureCredentialManager = None  # type: ignore[misc, assignment]

# H-6: Deprecated AuthenticationError alias
AuthenticationError = AuthError  # Deprecated: Use AuthError directly

# =============================================================================
# Fetch Sub-package (Conditional)
# =============================================================================

try:
    from .fetch.gman import GmailFetcher
    from .fetch.gmail_api_client import GmailAPIClient
    _FETCH_AVAILABLE = True
except ImportError as _fetch_err:
    _FETCH_AVAILABLE = False
    _fetch_import_error = str(_fetch_err)
    if TYPE_CHECKING:
        from .fetch.gman import GmailFetcher
        from .fetch.gmail_api_client import GmailAPIClient
    else:
        GmailFetcher = None  # type: ignore[misc, assignment]
        GmailAPIClient = None  # type: ignore[misc, assignment]

# Optional async fetchers
try:
    from .fetch.async_fetcher import AsyncGmailFetcher
    from .fetch.streaming import StreamingGmailFetcher
    from .fetch.incremental import IncrementalFetcher
    _ASYNC_AVAILABLE = True
except ImportError:
    _ASYNC_AVAILABLE = False
    if TYPE_CHECKING:
        from .fetch.async_fetcher import AsyncGmailFetcher
        from .fetch.streaming import StreamingGmailFetcher
        from .fetch.incremental import IncrementalFetcher
    else:
        AsyncGmailFetcher = None  # type: ignore[misc, assignment]
        StreamingGmailFetcher = None  # type: ignore[misc, assignment]
        IncrementalFetcher = None  # type: ignore[misc, assignment]

# =============================================================================
# Processing Sub-package (Conditional)
# =============================================================================

try:
    from .processing.classifier import EmailClassifier
    from .processing.extractor import EmailDataExtractor
    from .processing.plaintext import EmailPlaintextProcessor
    from .processing.database import EmailDatabaseImporter
    _PROCESSING_AVAILABLE = True
except ImportError:
    _PROCESSING_AVAILABLE = False
    if TYPE_CHECKING:
        from .processing.classifier import EmailClassifier
        from .processing.extractor import EmailDataExtractor
        from .processing.plaintext import EmailPlaintextProcessor
        from .processing.database import EmailDatabaseImporter
    else:
        EmailClassifier = None  # type: ignore[misc, assignment]
        EmailDataExtractor = None  # type: ignore[misc, assignment]
        EmailPlaintextProcessor = None  # type: ignore[misc, assignment]
        EmailDatabaseImporter = None  # type: ignore[misc, assignment]

# =============================================================================
# AI Sub-package (Conditional)
# =============================================================================

try:
    from .ai.newsletter_cleaner import AINewsletterDetector, AINewsletterCleaner
    from .ai.analysis_integration import GmailAnalysisIntegration
    _AI_AVAILABLE = True
except ImportError:
    _AI_AVAILABLE = False
    if TYPE_CHECKING:
        from .ai.newsletter_cleaner import AINewsletterDetector, AINewsletterCleaner
        from .ai.analysis_integration import GmailAnalysisIntegration
    else:
        AINewsletterDetector = None  # type: ignore[misc, assignment]
        AINewsletterCleaner = None  # type: ignore[misc, assignment]
        GmailAnalysisIntegration = None  # type: ignore[misc, assignment]

# =============================================================================
# Container (Conditional)
# =============================================================================

try:
    from .container import ServiceContainer
    _CONTAINER_AVAILABLE = True
except ImportError:
    _CONTAINER_AVAILABLE = False
    if TYPE_CHECKING:
        from .container import ServiceContainer
    else:
        ServiceContainer = None  # type: ignore[misc, assignment]


# =============================================================================
# Availability Status
# =============================================================================

def get_availability_status() -> dict[str, bool]:
    """
    Get availability status of optional components.

    Returns:
        Dictionary mapping component names to availability status.

    Example:
        >>> from gman.core import get_availability_status
        >>> status = get_availability_status()
        >>> if status['auth']:
        ...     from gman.core import ReadOnlyGmailAuth
    """
    return {
        'auth': _AUTH_AVAILABLE,
        'fetch': _FETCH_AVAILABLE,
        'async': _ASYNC_AVAILABLE,
        'processing': _PROCESSING_AVAILABLE,
        'ai': _AI_AVAILABLE,
        'container': _CONTAINER_AVAILABLE,
    }


def require_component(component_name: str) -> None:
    """
    Raise ImportError with helpful message if component unavailable.

    Args:
        component_name: Name of the component to check

    Raises:
        ImportError: If component is not available

    Example:
        >>> from gman.core import require_component, AsyncGmailFetcher
        >>> require_component('async')  # Raises if async deps missing
    """
    status = get_availability_status()
    if not status.get(component_name, False):
        raise ImportError(
            f"Component '{component_name}' is not available. "
            f"Install with: pip install gman[{component_name}]"
        )


# =============================================================================
# Public API
# =============================================================================

__all__ = [
    # Core - Configuration and Exceptions (always available)
    "AppConfig",
    "GmailAssistantError",
    "ConfigError",
    "AuthError",
    "NetworkError",
    "APIError",
    # Auth (conditional)
    "ReadOnlyGmailAuth",
    "GmailModifyAuth",
    "FullGmailAuth",
    "AuthenticationBase",
    "AuthenticationError",  # Deprecated in v2.0.0, removal in v3.0.0
    "SecureCredentialManager",
    # Fetch (conditional)
    "GmailFetcher",
    "GmailAPIClient",
    "AsyncGmailFetcher",
    "StreamingGmailFetcher",
    "IncrementalFetcher",
    # Processing (conditional)
    "EmailClassifier",
    "EmailDataExtractor",
    "EmailPlaintextProcessor",
    "EmailDatabaseImporter",
    # AI (conditional)
    "AINewsletterDetector",
    "AINewsletterCleaner",
    "GmailAnalysisIntegration",
    # Container (conditional)
    "ServiceContainer",
    # Utility
    "get_availability_status",
    "require_component",
]
