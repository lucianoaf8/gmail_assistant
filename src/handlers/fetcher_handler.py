"""
Fetcher handler for Gmail Fetcher main interface.
Handles email fetching operations with proper validation and error handling.
"""

import sys
import logging
from typing import Any

# Local imports
from src.core.gmail_assistant import GmailFetcher
from src.utils.input_validator import InputValidator, ValidationError

logger = logging.getLogger(__name__)


def handle_fetch_command(args: Any) -> None:
    """
    Handle email fetching operations.

    Args:
        args: Parsed command line arguments
    """
    try:
        # Validate inputs
        validated_args = _validate_fetch_arguments(args)

        # Initialize Gmail fetcher
        fetcher = GmailFetcher(credentials_file=validated_args['credentials'])

        # Authenticate
        if not fetcher.authenticate():
            logger.error("Failed to authenticate with Gmail API")
            print("Error: Authentication failed")
            sys.exit(1)

        # Perform fetch operation
        _execute_fetch(fetcher, validated_args)

    except ValidationError as e:
        error_msg = f"Validation error: {e}"
        logger.error(error_msg)
        print(f"Error: {error_msg}")
        sys.exit(1)

    except Exception as e:
        error_msg = f"Unexpected error during fetch: {e}"
        logger.error(error_msg)
        print(f"Error: {error_msg}")
        sys.exit(1)


def _validate_fetch_arguments(args: Any) -> dict:
    """
    Validate fetch command arguments.

    Args:
        args: Raw command line arguments

    Returns:
        Dictionary of validated arguments

    Raises:
        ValidationError: If validation fails
    """
    validated = {}

    # Validate query
    if hasattr(args, 'query') and args.query:
        validated['query'] = InputValidator.validate_gmail_query(args.query)
    else:
        validated['query'] = 'is:unread'  # Default

    # Validate max emails
    if hasattr(args, 'max') and args.max:
        validated['max'] = InputValidator.validate_batch_size(args.max, max_allowed=10000)
    else:
        validated['max'] = 1000  # Default

    # Validate output directory
    if hasattr(args, 'output') and args.output:
        validated['output'] = InputValidator.validate_file_path(
            args.output, must_exist=False, create_dirs=True
        )
    else:
        validated['output'] = 'gmail_backup'  # Default

    # Validate format
    if hasattr(args, 'format') and args.format:
        if args.format not in ['eml', 'markdown', 'both']:
            raise ValidationError(f"Invalid format: {args.format}")
        validated['format'] = args.format
    else:
        validated['format'] = 'eml'  # Default

    # Validate organization
    if hasattr(args, 'organize') and args.organize:
        if args.organize not in ['date', 'sender', 'none']:
            raise ValidationError(f"Invalid organization: {args.organize}")
        validated['organize'] = args.organize
    else:
        validated['organize'] = 'date'  # Default

    # Validate credentials file
    if hasattr(args, 'credentials') and args.credentials:
        validated['credentials'] = InputValidator.validate_file_path(
            args.credentials, must_exist=True
        )
    else:
        validated['credentials'] = 'credentials.json'  # Default

    return validated


def _execute_fetch(fetcher: GmailFetcher, args: dict) -> None:
    """
    Execute the email fetch operation.

    Args:
        fetcher: Authenticated Gmail fetcher instance
        args: Validated arguments dictionary
    """
    print(f"Fetching emails with query: {args['query']}")
    print(f"Maximum emails: {args['max']}")
    print(f"Output directory: {args['output']}")
    print(f"Format: {args['format']}")
    print(f"Organization: {args['organize']}")

    # Execute the fetch
    success = fetcher.fetch_emails(
        query=args['query'],
        max_results=args['max'],
        output_dir=str(args['output']),
        format_type=args['format'],
        organize_by=args['organize']
    )

    if success:
        print("Success: Email fetch completed")
        logger.info("Email fetch operation completed successfully")
    else:
        print("Error: Email fetch failed")
        logger.error("Email fetch operation failed")
        sys.exit(1)