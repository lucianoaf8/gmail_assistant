"""Authentication sub-package for Gmail Fetcher."""

from .base import (
    AuthenticationBase,
    AuthenticationError,
    FullGmailAuth,
    GmailModifyAuth,
    ReadOnlyGmailAuth,
)
from .credential_manager import SecureCredentialManager

__all__ = [
    'AuthenticationBase',
    'AuthenticationError',
    'FullGmailAuth',
    'GmailModifyAuth',
    'ReadOnlyGmailAuth',
    'SecureCredentialManager',
]
