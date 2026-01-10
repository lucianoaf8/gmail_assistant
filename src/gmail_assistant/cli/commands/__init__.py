"""CLI subcommand modules (C-2 fix)."""
from __future__ import annotations

from .fetch import fetch_emails
from .delete import delete_emails, get_email_count
from .analyze import analyze_emails
from .auth import authenticate, check_auth_status, revoke_auth

__all__ = [
    # Fetch operations
    "fetch_emails",
    # Delete operations
    "delete_emails",
    "get_email_count",
    # Analyze operations
    "analyze_emails",
    # Auth operations
    "authenticate",
    "check_auth_status",
    "revoke_auth",
]
