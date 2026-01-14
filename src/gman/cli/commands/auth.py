"""Auth command implementation (C-2 fix, H-1 DI integration)."""
from __future__ import annotations

from pathlib import Path
from typing import TYPE_CHECKING, Any

import click

from gman.core.auth.credential_manager import SecureCredentialManager
from gman.core.container import ServiceContainer, get_global_container
from gman.core.exceptions import AuthError
from gman.utils.secure_logger import SecureLogger

if TYPE_CHECKING:
    from gman.core.container import ServiceContainer

logger = SecureLogger(__name__)


def _get_credential_manager(
    credentials_path: Path,
    container: ServiceContainer | None = None,
) -> SecureCredentialManager:
    """
    Get a SecureCredentialManager instance, preferring DI container when available.

    H-1 fix: Enables testability by allowing mock manager injection.

    Args:
        credentials_path: Path to credentials.json
        container: Optional DI container

    Returns:
        SecureCredentialManager instance
    """
    # Try provided container first
    if container is not None:
        try:
            manager = container.try_resolve(SecureCredentialManager)
            if manager is not None:
                return manager
        except Exception:
            pass

    # Try global container
    global_container = get_global_container()
    if global_container is not None:
        try:
            manager = global_container.try_resolve(SecureCredentialManager)
            if manager is not None:
                return manager
        except Exception:
            pass

    # Fall back to direct instantiation
    return SecureCredentialManager(str(credentials_path))


def authenticate(
    credentials_path: Path,
    force_reauth: bool = False,
    container: ServiceContainer | None = None,
) -> dict[str, Any]:
    """
    Authenticate with Gmail API (C-2 implementation, H-1 DI integration).

    Args:
        credentials_path: Path to OAuth credentials.json file
        force_reauth: Force re-authentication even if credentials exist
        container: Optional DI container for service resolution (H-1 fix)

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

    # H-1: Use container for manager resolution, or fall back to direct instantiation
    manager = _get_credential_manager(credentials_path, container)

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


def check_auth_status(
    credentials_path: Path,
    container: ServiceContainer | None = None,
) -> dict[str, Any]:
    """
    Check current authentication status without triggering OAuth flow.

    Args:
        credentials_path: Path to OAuth credentials.json file
        container: Optional DI container for service resolution (H-1 fix)

    Returns:
        Dict with current auth status
    """
    manager = _get_credential_manager(credentials_path, container)

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


def revoke_auth() -> dict[str, Any]:
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
