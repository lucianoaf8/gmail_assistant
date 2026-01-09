"""Authentication sub-package for Gmail Fetcher."""

from .base import AuthenticationBase, AuthenticationError, ReadOnlyGmailAuth, GmailModifyAuth, FullGmailAuth
from .credential_manager import SecureCredentialManager

__all__ = [
    'AuthenticationBase',
    'AuthenticationError',
    'ReadOnlyGmailAuth',
    'GmailModifyAuth',
    'FullGmailAuth',
    'SecureCredentialManager',
]
