"""
Fetch command for Gmail Fetcher CLI.

Downloads emails from Gmail based on search queries.
"""

import logging
import sys
from argparse import ArgumentParser, _SubParsersAction
from typing import Any

logger = logging.getLogger(__name__)


def setup_parser(subparsers: _SubParsersAction) -> ArgumentParser:
    """
    Setup the fetch command parser.

    Args:
        subparsers: Parent subparsers object

    Returns:
        Configured ArgumentParser for fetch command
    """
    parser = subparsers.add_parser(
        'fetch',
        help='Download emails from Gmail',
        description='Download emails from Gmail based on search queries'
    )

    # Required arguments
    parser.add_argument(
        '--query', '-q',
        required=True,
        help='Gmail search query (e.g., "is:unread", "from:example.com")'
    )

    # Optional arguments
    parser.add_argument(
        '--max', '-m',
        type=int,
        default=1000,
        help='Maximum number of emails to download (default: 1000)'
    )

    parser.add_argument(
        '--output', '-o',
        default='gmail_backup',
        help='Output directory (default: gmail_backup)'
    )

    parser.add_argument(
        '--format', '-f',
        choices=['eml', 'markdown', 'json', 'both'],
        default='both',
        help='Output format (default: both = eml + markdown)'
    )

    parser.add_argument(
        '--organize',
        choices=['date', 'sender', 'none'],
        default='date',
        help='How to organize files (default: date)'
    )

    parser.add_argument(
        '--skip',
        type=int,
        default=0,
        help='Skip first N matching emails'
    )

    parser.add_argument(
        '--auth-only',
        action='store_true',
        help='Only test authentication, do not download'
    )

    parser.add_argument(
        '--count-only',
        action='store_true',
        help='Only count matching emails, do not download'
    )

    return parser


def handle(args: Any) -> int:
    """
    Handle the fetch command.

    Args:
        args: Parsed command line arguments

    Returns:
        Exit code (0 for success)
    """
    try:
        # Import here to avoid circular imports
        from gmail_assistant.core.gmail_assistant import GmailFetcher
        from gmail_assistant.utils.input_validator import InputValidator, ValidationError

        # Validate inputs
        validator = InputValidator()

        try:
            query = validator.validate_gmail_query(args.query)
            max_emails = validator.validate_batch_size(args.max, max_allowed=100000)
        except ValidationError as e:
            logger.error(f"Validation error: {e}")
            return 1

        # Initialize fetcher
        credentials_file = getattr(args, 'credentials', 'credentials.json')
        fetcher = GmailFetcher(credentials_file=credentials_file)

        # Authenticate
        print("Authenticating with Gmail API...")
        if not fetcher.authenticate():
            logger.error("Authentication failed")
            return 1

        # Auth-only mode
        if args.auth_only:
            profile = fetcher.get_profile()
            if profile:
                print(f"Authenticated as: {profile.get('email', 'unknown')}")
                print(f"Total messages: {profile.get('total_messages', 'unknown'):,}")
                print(f"Total threads: {profile.get('total_threads', 'unknown'):,}")
                return 0
            else:
                print("Could not retrieve profile information")
                return 1

        # Count-only mode
        if args.count_only:
            message_ids = fetcher.search_messages(query, max_emails)
            print(f"Found {len(message_ids):,} emails matching query: {query}")
            return 0

        # Download emails
        print(f"Downloading emails matching: {query}")
        print(f"Maximum: {max_emails:,}, Format: {args.format}, Organize by: {args.organize}")

        fetcher.download_emails(
            query=query,
            max_emails=max_emails,
            output_dir=args.output,
            format_type=args.format,
            organize_by=args.organize,
            skip=args.skip
        )

        print(f"Download complete. Files saved to: {args.output}")
        return 0

    except ImportError as e:
        logger.error(f"Import error: {e}")
        print("Error: Required modules not found. Check installation.")
        return 1

    except Exception as e:
        logger.error(f"Fetch failed: {e}")
        return 1
