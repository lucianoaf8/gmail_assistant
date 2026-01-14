"""Authentication sub-package for Gmail Fetcher."""

from .base import (
    AuthenticationBase,
    AuthenticationError,  # Deprecated: Use AuthError from gman.core.exceptions
    FullGmailAuth,
    GmailModifyAuth,
    ReadOnlyGmailAuth,
)
from .credential_manager import SecureCredentialManager

# H-6: Also export AuthError for migration
from gman.core.exceptions import AuthError

__all__ = [
    'AuthenticationBase',
    'AuthenticationError',  # Deprecated in v2.0.0, removal in v3.0.0
    'AuthError',  # Preferred - use this instead of AuthenticationError
    'FullGmailAuth',
    'GmailModifyAuth',
    'ReadOnlyGmailAuth',
    'SecureCredentialManager',
]
