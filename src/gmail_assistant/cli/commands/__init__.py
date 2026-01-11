"""CLI subcommand modules (C-2 fix)."""
from __future__ import annotations

from .analyze import analyze_emails
from .auth import authenticate, check_auth_status, revoke_auth
from .delete import delete_emails, get_email_count
from .fetch import fetch_emails

__all__ = [
    # Analyze operations
    "analyze_emails",
    # Auth operations
    "authenticate",
    "check_auth_status",
    # Delete operations
    "delete_emails",
    # Fetch operations
    "fetch_emails",
    "get_email_count",
    "revoke_auth",
]
