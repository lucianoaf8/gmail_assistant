"""
Delete handler for Gmail Fetcher main interface.
Handles email deletion operations with comprehensive safety checks.
"""

import sys
import logging
from pathlib import Path
from typing import Any

logger = logging.getLogger(__name__)


def handle_delete_command(args: Any) -> None:
    """
    Handle email deletion operations with comprehensive safety checks.

    Args:
        args: Parsed command line arguments
    """
    try:
        # Setup logging for deletion operations
        _setup_deletion_logging()

        # Import deletion modules
        from gmail_assistant.deletion.deleter import GmailDeleter
        from gmail_assistant.deletion.ui import clean_unread_inbox

        # Handle different deletion modes
        if hasattr(args, 'interactive') and args.interactive:
            _handle_interactive_deletion()
        else:
            _handle_direct_deletion(args)

    except ImportError as e:
        error_msg = f"Error importing deletion modules: {e}"
        logger.error(error_msg)
        print(f"Error: {error_msg}")
        sys.exit(1)

    except Exception as e:
        error_msg = f"Error during deletion: {e}"
        logger.error(error_msg)
        print(f"Error: {error_msg}")
        sys.exit(1)


def _setup_deletion_logging() -> None:
    """Set up logging for deletion operations."""
    log_dir = Path(__file__).parent.parent.parent / "logs"
    log_dir.mkdir(exist_ok=True)

    # Configure deletion-specific logging
    log_file = log_dir / "deletion_operations.log"

    deletion_logger = logging.getLogger('deletion')
    deletion_logger.setLevel(logging.INFO)

    if not deletion_logger.handlers:
        file_handler = logging.FileHandler(log_file)
        formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
        file_handler.setFormatter(formatter)
        deletion_logger.addHandler(file_handler)

    logger.info(f"Deletion logging configured: {log_file}")


def _handle_interactive_deletion() -> None:
    """Handle interactive deletion mode."""
    from gmail_assistant.deletion.ui import clean_unread_inbox

    print("Starting interactive deletion mode...")
    clean_unread_inbox()
    print("Interactive deletion completed")


def _handle_direct_deletion(args: Any) -> None:
    """
    Handle direct deletion with command line arguments.

    Args:
        args: Parsed command line arguments
    """
    from gmail_assistant.deletion.deleter import GmailDeleter

    # Initialize deleter
    credentials_file = getattr(args, 'credentials', 'credentials.json')
    deleter = GmailDeleter(credentials_file=credentials_file)

    # Validate deletion parameters
    if not hasattr(args, 'query') or not args.query:
        print("Error: Query required for deletion")
        print("Use --query to specify emails to delete")
        sys.exit(1)

    # Safety check - require confirmation for destructive operations
    if not getattr(args, 'dry_run', False):
        print(f"WARNING: This will permanently delete emails matching: {args.query}")
        response = input("Type 'DELETE' to confirm: ")
        if response != 'DELETE':
            print("Deletion cancelled")
            return

    # Perform deletion
    try:
        if getattr(args, 'dry_run', False):
            print(f"DRY RUN: Would delete emails matching: {args.query}")
            # Implement dry run logic
            _perform_dry_run_deletion(deleter, args)
        else:
            print(f"Deleting emails matching: {args.query}")
            _perform_actual_deletion(deleter, args)

    except Exception as e:
        logger.error(f"Deletion operation failed: {e}")
        raise


def _perform_dry_run_deletion(deleter: Any, args: Any) -> None:
    """
    Perform dry run deletion (show what would be deleted).

    Args:
        deleter: Gmail deleter instance
        args: Command line arguments
    """
    # Get email count for query
    count = deleter.get_email_count(args.query)
    print(f"DRY RUN: Would delete {count} emails")

    if count > 0:
        print("Use --confirm to actually delete these emails")


def _perform_actual_deletion(deleter: Any, args: Any) -> None:
    """
    Perform actual email deletion.

    Args:
        deleter: Gmail deleter instance
        args: Command line arguments
    """
    max_emails = getattr(args, 'max', 1000)  # Safety limit

    # Perform deletion with progress tracking
    result = deleter.delete_emails_by_query(
        query=args.query,
        max_emails=max_emails,
        batch_size=getattr(args, 'batch_size', 100)
    )

    print(f"Deletion completed: {result.get('deleted', 0)} emails deleted")

    if result.get('failed', 0) > 0:
        print(f"Warning: {result['failed']} emails failed to delete")
        logger.warning(f"Failed to delete {result['failed']} emails")