"""
Delete command for Gmail Fetcher CLI.

Provides email deletion operations with safety checks.
"""

import logging
from argparse import ArgumentParser, _SubParsersAction
from typing import Any

logger = logging.getLogger(__name__)


def setup_parser(subparsers: _SubParsersAction) -> ArgumentParser:
    """
    Setup the delete command parser with subcommands.

    Args:
        subparsers: Parent subparsers object

    Returns:
        Configured ArgumentParser for delete command
    """
    parser = subparsers.add_parser(
        'delete',
        help='Delete emails from Gmail',
        description='Delete emails from Gmail with safety checks'
    )

    # Create subcommands for delete
    delete_subparsers = parser.add_subparsers(
        dest='delete_action',
        title='delete actions',
        description='Available deletion actions',
        help='Use <action> --help for more information'
    )

    # Delete unread subcommand
    unread_parser = delete_subparsers.add_parser(
        'unread',
        help='Delete all unread emails',
        description='Delete all unread emails with optional filters'
    )
    unread_parser.add_argument(
        '--dry-run',
        action='store_true',
        default=True,
        help='Show what would be deleted (default: True)'
    )
    unread_parser.add_argument(
        '--execute',
        action='store_true',
        help='Actually perform the deletion'
    )
    unread_parser.add_argument(
        '--keep-recent',
        type=int,
        default=0,
        help='Keep emails from the last N days'
    )
    unread_parser.add_argument(
        '--force',
        action='store_true',
        help='Skip confirmation prompts'
    )

    # Delete by query subcommand
    query_parser = delete_subparsers.add_parser(
        'query',
        help='Delete emails by custom query',
        description='Delete emails matching a Gmail search query'
    )
    query_parser.add_argument(
        '--query', '-q',
        required=True,
        help='Gmail search query'
    )
    query_parser.add_argument(
        '--dry-run',
        action='store_true',
        default=True,
        help='Show what would be deleted (default: True)'
    )
    query_parser.add_argument(
        '--execute',
        action='store_true',
        help='Actually perform the deletion'
    )
    query_parser.add_argument(
        '--max-delete',
        type=int,
        help='Maximum number of emails to delete'
    )
    query_parser.add_argument(
        '--force',
        action='store_true',
        help='Skip confirmation prompts'
    )

    # Delete preset subcommand
    preset_parser = delete_subparsers.add_parser(
        'preset',
        help='Use predefined deletion patterns',
        description='Delete emails using predefined patterns'
    )
    preset_parser.add_argument(
        'preset_name',
        choices=['old', 'large', 'newsletters', 'notifications'],
        help='Preset pattern to use'
    )
    preset_parser.add_argument(
        '--dry-run',
        action='store_true',
        default=True,
        help='Show what would be deleted (default: True)'
    )
    preset_parser.add_argument(
        '--execute',
        action='store_true',
        help='Actually perform the deletion'
    )
    preset_parser.add_argument(
        '--force',
        action='store_true',
        help='Skip confirmation prompts'
    )

    return parser


# Preset query mappings
PRESET_QUERIES = {
    'old': 'older_than:1y',
    'large': 'larger:10M',
    'newsletters': 'is:unread (newsletter OR unsubscribe OR digest)',
    'notifications': 'is:unread (notification OR alert OR noreply)'
}


def handle(args: Any) -> int:
    """
    Handle the delete command.

    Args:
        args: Parsed command line arguments

    Returns:
        Exit code (0 for success)
    """
    if args.delete_action is None:
        print("Error: Please specify a delete action (unread, query, or preset)")
        print("Use 'gmail-fetcher delete --help' for more information")
        return 1

    try:
        from gmail_assistant.deletion.deleter import GmailDeleter

        # Initialize deleter
        credentials_file = getattr(args, 'credentials', 'credentials.json')
        deleter = GmailDeleter(credentials_file=credentials_file)

        # Determine dry run mode
        dry_run = not getattr(args, 'execute', False)

        if args.delete_action == 'unread':
            return _handle_unread_delete(deleter, args, dry_run)

        elif args.delete_action == 'query':
            return _handle_query_delete(deleter, args, dry_run)

        elif args.delete_action == 'preset':
            return _handle_preset_delete(deleter, args, dry_run)

        else:
            logger.error(f"Unknown delete action: {args.delete_action}")
            return 1

    except ImportError as e:
        logger.error(f"Import error: {e}")
        print("Error: Deletion modules not found. Check installation.")
        return 1

    except Exception as e:
        logger.error(f"Delete failed: {e}")
        return 1


def _handle_unread_delete(deleter: Any, args: Any, dry_run: bool) -> int:
    """Handle deletion of unread emails."""
    query = "is:unread"

    if args.keep_recent > 0:
        query += f" older_than:{args.keep_recent}d"

    return _execute_deletion(deleter, query, dry_run, args)


def _handle_query_delete(deleter: Any, args: Any, dry_run: bool) -> int:
    """Handle deletion by custom query."""
    return _execute_deletion(
        deleter,
        args.query,
        dry_run,
        args,
        max_delete=getattr(args, 'max_delete', None)
    )


def _handle_preset_delete(deleter: Any, args: Any, dry_run: bool) -> int:
    """Handle deletion using preset patterns."""
    query = PRESET_QUERIES.get(args.preset_name)
    if not query:
        logger.error(f"Unknown preset: {args.preset_name}")
        return 1

    print(f"Using preset '{args.preset_name}': {query}")
    return _execute_deletion(deleter, query, dry_run, args)


def _execute_deletion(
    deleter: Any,
    query: str,
    dry_run: bool,
    args: Any,
    max_delete: int = None
) -> int:
    """Execute the actual deletion operation."""
    # Get count first
    count = deleter.get_email_count(query)
    print(f"Found {count:,} emails matching: {query}")

    if count == 0:
        print("No emails to delete")
        return 0

    if dry_run:
        print("\n[DRY RUN] No emails were actually deleted")
        print("Use --execute to perform actual deletion")
        return 0

    # Confirmation unless forced
    if not getattr(args, 'force', False):
        print(f"\nWARNING: This will permanently delete {count:,} emails!")
        response = input("Type 'DELETE' to confirm: ")
        if response != 'DELETE':
            print("Deletion cancelled")
            return 0

    # Perform deletion
    result = deleter.delete_by_query(
        query=query,
        dry_run=False,
        max_delete=max_delete
    )

    print(f"\nDeleted: {result.get('deleted', 0):,} emails")
    if result.get('failed', 0) > 0:
        print(f"Failed: {result.get('failed', 0):,} emails")

    return 0
