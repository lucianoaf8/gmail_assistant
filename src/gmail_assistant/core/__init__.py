"""
Gmail Assistant Core Module
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

Lazy imports are used to avoid ImportError when dependencies are not installed.
"""

# Direct imports for core functionality (always available)
from gmail_assistant.core.config import AppConfig
from gmail_assistant.core.exceptions import (
    APIError,
    AuthError,
    ConfigError,
    GmailAssistantError,
    NetworkError,
)


# Use lazy imports to avoid import errors when dependencies are not installed
def __getattr__(name):
    """Lazy import handler for backwards compatibility."""
    # Auth sub-package
    if name == 'ReadOnlyGmailAuth':
        from .auth.base import ReadOnlyGmailAuth
        return ReadOnlyGmailAuth
    elif name == 'GmailModifyAuth':
        from .auth.base import GmailModifyAuth
        return GmailModifyAuth
    elif name == 'FullGmailAuth':
        from .auth.base import FullGmailAuth
        return FullGmailAuth
    elif name == 'AuthenticationBase':
        from .auth.base import AuthenticationBase
        return AuthenticationBase
    elif name == 'AuthenticationError':
        from .auth.base import AuthenticationError
        return AuthenticationError
    elif name == 'SecureCredentialManager':
        from .auth.credential_manager import SecureCredentialManager
        return SecureCredentialManager

    # Fetch sub-package
    elif name == 'GmailFetcher':
        from .fetch.gmail_assistant import GmailFetcher
        return GmailFetcher
    elif name == 'GmailAPIClient':
        from .fetch.gmail_api_client import GmailAPIClient
        return GmailAPIClient
    elif name == 'StreamingGmailFetcher':
        from .fetch.streaming import StreamingGmailFetcher
        return StreamingGmailFetcher
    elif name == 'AsyncGmailFetcher':
        from .fetch.async_fetcher import AsyncGmailFetcher
        return AsyncGmailFetcher
    elif name == 'IncrementalFetcher':
        from .fetch.incremental import IncrementalFetcher
        return IncrementalFetcher

    # Processing sub-package
    elif name == 'EmailClassifier':
        from .processing.classifier import EmailClassifier
        return EmailClassifier
    elif name == 'EmailDataExtractor':
        from .processing.extractor import EmailDataExtractor
        return EmailDataExtractor
    elif name == 'EmailPlaintextProcessor':
        from .processing.plaintext import EmailPlaintextProcessor
        return EmailPlaintextProcessor
    elif name == 'EmailDatabaseImporter':
        from .processing.database import EmailDatabaseImporter
        return EmailDatabaseImporter

    # AI sub-package
    elif name == 'AINewsletterDetector':
        from .ai.newsletter_cleaner import AINewsletterDetector
        return AINewsletterDetector
    elif name == 'AINewsletterCleaner':
        from .ai.newsletter_cleaner import AINewsletterCleaner
        return AINewsletterCleaner
    elif name == 'GmailAnalysisIntegration':
        from .ai.analysis_integration import GmailAnalysisIntegration
        return GmailAnalysisIntegration

    # Top-level modules
    elif name == 'ServiceContainer':
        from .container import ServiceContainer
        return ServiceContainer

    raise AttributeError(f"module {__name__!r} has no attribute {name!r}")


__all__ = [
    # Core - Configuration and Exceptions
    "AppConfig",
    "GmailAssistantError",
    "ConfigError",
    "AuthError",
    "NetworkError",
    "APIError",
    # Auth
    'ReadOnlyGmailAuth',
    'GmailModifyAuth',
    'FullGmailAuth',
    'AuthenticationBase',
    'AuthenticationError',
    'SecureCredentialManager',
    # Fetch
    'GmailFetcher',
    'GmailAPIClient',
    'StreamingGmailFetcher',
    'AsyncGmailFetcher',
    'IncrementalFetcher',
    # Processing
    'EmailClassifier',
    'EmailDataExtractor',
    'EmailPlaintextProcessor',
    'EmailDatabaseImporter',
    # AI
    'AINewsletterDetector',
    'AINewsletterCleaner',
    'GmailAnalysisIntegration',
    # Top-level
    'ServiceContainer',
]
