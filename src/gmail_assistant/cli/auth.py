"""
Auth command for Gmail Fetcher CLI.

Manages Gmail API authentication.
"""

import logging
from argparse import ArgumentParser, _SubParsersAction
from pathlib import Path
from typing import Any

logger = logging.getLogger(__name__)


def setup_parser(subparsers: _SubParsersAction) -> ArgumentParser:
    """
    Setup the auth command parser.

    Args:
        subparsers: Parent subparsers object

    Returns:
        Configured ArgumentParser for auth command
    """
    parser = subparsers.add_parser(
        'auth',
        help='Authentication management',
        description='Manage Gmail API authentication'
    )

    # Auth subcommands
    auth_subparsers = parser.add_subparsers(
        dest='auth_action',
        title='auth actions',
        description='Available authentication actions'
    )

    # Test authentication
    test_parser = auth_subparsers.add_parser(
        'test',
        help='Test current authentication',
        description='Verify authentication is working'
    )

    # Refresh token
    refresh_parser = auth_subparsers.add_parser(
        'refresh',
        help='Refresh authentication token',
        description='Force refresh of OAuth token'
    )

    # Reset authentication
    reset_parser = auth_subparsers.add_parser(
        'reset',
        help='Reset authentication',
        description='Clear stored credentials and re-authenticate'
    )
    reset_parser.add_argument(
        '--force',
        action='store_true',
        help='Skip confirmation prompt'
    )

    # Show status
    status_parser = auth_subparsers.add_parser(
        'status',
        help='Show authentication status',
        description='Display current authentication status and info'
    )

    return parser


def handle(args: Any) -> int:
    """
    Handle the auth command.

    Args:
        args: Parsed command line arguments

    Returns:
        Exit code (0 for success)
    """
    if args.auth_action is None:
        # Default to status
        return _handle_status(args)

    if args.auth_action == 'test':
        return _handle_test(args)
    elif args.auth_action == 'refresh':
        return _handle_refresh(args)
    elif args.auth_action == 'reset':
        return _handle_reset(args)
    elif args.auth_action == 'status':
        return _handle_status(args)
    else:
        logger.error(f"Unknown auth action: {args.auth_action}")
        return 1


def _handle_test(args: Any) -> int:
    """Test current authentication."""
    try:
        from gmail_assistant.core.gmail_assistant import GmailFetcher

        credentials_file = getattr(args, 'credentials', 'credentials.json')
        print(f"Testing authentication with: {credentials_file}")

        fetcher = GmailFetcher(credentials_file=credentials_file)

        if fetcher.authenticate():
            profile = fetcher.get_profile()
            if profile:
                print("\nAuthentication successful!")
                print(f"  Email: {profile.get('email', 'unknown')}")
                print(f"  Total messages: {profile.get('total_messages', 'unknown'):,}")
                print(f"  Total threads: {profile.get('total_threads', 'unknown'):,}")
                return 0
            else:
                print("Authentication successful, but could not retrieve profile")
                return 0
        else:
            print("Authentication failed!")
            return 1

    except FileNotFoundError as e:
        print(f"Error: Credentials file not found: {e}")
        print("\nTo set up authentication:")
        print("1. Go to https://console.cloud.google.com/")
        print("2. Create or select a project")
        print("3. Enable the Gmail API")
        print("4. Create OAuth 2.0 credentials")
        print("5. Download and save as 'credentials.json'")
        return 1

    except Exception as e:
        logger.error(f"Test failed: {e}")
        return 1


def _handle_refresh(args: Any) -> int:
    """Refresh authentication token."""
    try:
        from gmail_assistant.core.credential_manager import SecureCredentialManager

        credentials_file = getattr(args, 'credentials', 'credentials.json')
        print(f"Refreshing authentication token...")

        manager = SecureCredentialManager(credentials_file)

        if manager.authenticate():
            print("Token refreshed successfully!")
            return 0
        else:
            print("Token refresh failed - may need to re-authenticate")
            return 1

    except Exception as e:
        logger.error(f"Refresh failed: {e}")
        return 1


def _handle_reset(args: Any) -> int:
    """Reset authentication and re-authenticate."""
    try:
        from gmail_assistant.core.constants import DEFAULT_TOKEN_PATH

        # Confirmation
        if not getattr(args, 'force', False):
            print("This will clear your stored authentication and require re-login.")
            response = input("Continue? (y/n): ")
            if response.lower() != 'y':
                print("Reset cancelled")
                return 0

        # Remove token file
        token_path = Path(DEFAULT_TOKEN_PATH)
        if token_path.exists():
            token_path.unlink()
            print(f"Removed: {token_path}")

        # Re-authenticate
        from gmail_assistant.core.gmail_assistant import GmailFetcher

        credentials_file = getattr(args, 'credentials', 'credentials.json')
        fetcher = GmailFetcher(credentials_file=credentials_file)

        print("Re-authenticating... (browser will open)")

        if fetcher.authenticate():
            print("Re-authentication successful!")
            return 0
        else:
            print("Re-authentication failed!")
            return 1

    except Exception as e:
        logger.error(f"Reset failed: {e}")
        return 1


def _handle_status(args: Any) -> int:
    """Show authentication status."""
    try:
        from gmail_assistant.core.constants import (
            DEFAULT_CREDENTIALS_PATH,
            DEFAULT_TOKEN_PATH,
        )

        print("Authentication Status")
        print("=" * 40)

        # Check credentials file
        creds_path = Path(getattr(args, 'credentials', DEFAULT_CREDENTIALS_PATH))
        print(f"\nCredentials file: {creds_path}")
        if creds_path.exists():
            print("  Status: Found")
            print(f"  Size: {creds_path.stat().st_size} bytes")
        else:
            print("  Status: MISSING")
            print("  Action: Download from Google Cloud Console")

        # Check token file
        token_path = Path(DEFAULT_TOKEN_PATH)
        print(f"\nToken file: {token_path}")
        if token_path.exists():
            print("  Status: Found")
            print(f"  Size: {token_path.stat().st_size} bytes")

            # Check if token is valid
            try:
                from google.oauth2.credentials import Credentials
                creds = Credentials.from_authorized_user_file(str(token_path))

                if creds.valid:
                    print("  Token: Valid")
                elif creds.expired:
                    print("  Token: Expired (will refresh on next use)")
                else:
                    print("  Token: Unknown state")
            except Exception as e:
                print(f"  Token: Could not verify ({e})")
        else:
            print("  Status: Not authenticated")
            print("  Action: Run 'gmail-fetcher auth test' to authenticate")

        return 0

    except Exception as e:
        logger.error(f"Status check failed: {e}")
        return 1
