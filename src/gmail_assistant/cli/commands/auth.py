"""Auth command implementation (C-2 fix)."""
from __future__ import annotations

from pathlib import Path
from typing import Dict, Any, Optional

import click

from gmail_assistant.core.auth.credential_manager import SecureCredentialManager
from gmail_assistant.core.exceptions import AuthError
from gmail_assistant.utils.secure_logger import SecureLogger

logger = SecureLogger(__name__)


def authenticate(
    credentials_path: Path,
    force_reauth: bool = False
) -> Dict[str, Any]:
    """
    Authenticate with Gmail API (C-2 implementation).

    Args:
        credentials_path: Path to OAuth credentials.json file
        force_reauth: Force re-authentication even if credentials exist

    Returns:
        Dict with authentication status and user info

    Raises:
        AuthError: If authentication fails
    """
    click.echo(f"Credentials file: {credentials_path}")

    # Validate credentials file exists
    if not credentials_path.exists():
        click.echo(f"\nCredentials file not found: {credentials_path}")
        click.echo("\nSetup Instructions:")
        click.echo("1. Go to https://console.cloud.google.com/")
        click.echo("2. Create a new project or select existing")
        click.echo("3. Enable Gmail API")
        click.echo("4. Create OAuth 2.0 credentials (Desktop application)")
        click.echo(f"5. Download and save as '{credentials_path}'")
        raise AuthError(f"Credentials file not found: {credentials_path}")

    # Initialize credential manager
    manager = SecureCredentialManager(str(credentials_path))

    # Force re-auth if requested
    if force_reauth:
        click.echo("Clearing existing credentials...")
        manager.reset_credentials()

    # Attempt authentication
    click.echo("Starting authentication...")

    if manager.authenticate():
        click.echo("Authentication successful!")

        # Get user info
        user_info = manager.get_user_info()
        if user_info:
            click.echo(f"\nAuthenticated as: {user_info.get('email', 'unknown')}")
            click.echo(f"Total messages: {user_info.get('messages_total', 0):,}")
            click.echo(f"Total threads: {user_info.get('threads_total', 0):,}")

            return {
                'success': True,
                'email': user_info.get('email'),
                'messages_total': user_info.get('messages_total'),
                'threads_total': user_info.get('threads_total')
            }
        else:
            return {'success': True, 'email': None}
    else:
        raise AuthError("Authentication failed")


def check_auth_status(credentials_path: Path) -> Dict[str, Any]:
    """
    Check current authentication status without triggering OAuth flow.

    Args:
        credentials_path: Path to OAuth credentials.json file

    Returns:
        Dict with current auth status
    """
    manager = SecureCredentialManager(str(credentials_path))

    # Try to load existing credentials
    creds = manager._load_credentials_securely()

    if creds is None:
        return {
            'authenticated': False,
            'status': 'No credentials stored'
        }

    if not creds.valid:
        if creds.expired and creds.refresh_token:
            return {
                'authenticated': False,
                'status': 'Credentials expired (can be refreshed)',
                'refresh_available': True
            }
        return {
            'authenticated': False,
            'status': 'Credentials invalid'
        }

    return {
        'authenticated': True,
        'status': 'Valid credentials'
    }


def revoke_auth() -> Dict[str, Any]:
    """
    Revoke stored authentication credentials.

    Returns:
        Dict with revocation status
    """
    manager = SecureCredentialManager()

    if manager.reset_credentials():
        click.echo("Credentials revoked successfully")
        return {'success': True, 'message': 'Credentials revoked'}
    else:
        click.echo("Failed to revoke credentials")
        return {'success': False, 'message': 'Failed to revoke credentials'}


__all__ = ['authenticate', 'check_auth_status', 'revoke_auth']
