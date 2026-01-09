"""
Main CLI entry point for Gmail Fetcher.

Provides the main argument parser and command routing.
"""

import sys
import argparse
import logging
from pathlib import Path
from typing import List, Optional

# Import command modules
from . import fetch
from . import delete
from . import analyze
from . import config
from . import auth

logger = logging.getLogger(__name__)


def create_parser() -> argparse.ArgumentParser:
    """
    Create the main argument parser with all subcommands.

    Returns:
        Configured ArgumentParser instance
    """
    parser = argparse.ArgumentParser(
        prog="gmail-fetcher",
        description="Gmail Fetcher Suite - Professional email backup and management",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
    gmail-fetcher fetch --query "is:unread" --max 1000
    gmail-fetcher delete unread --dry-run
    gmail-fetcher analyze --yesterday
    gmail-fetcher config show
    gmail-fetcher auth test

For more information on a command:
    gmail-fetcher <command> --help
        """
    )

    # Global options
    parser.add_argument(
        '-v', '--verbose',
        action='store_true',
        help='Enable verbose output'
    )
    parser.add_argument(
        '--debug',
        action='store_true',
        help='Enable debug logging'
    )
    parser.add_argument(
        '--credentials',
        default='credentials.json',
        help='Path to OAuth credentials file (default: credentials.json)'
    )
    parser.add_argument(
        '--version',
        action='version',
        version='Gmail Fetcher 2.0.0'
    )

    # Create subparsers
    subparsers = parser.add_subparsers(
        dest='command',
        title='commands',
        description='Available commands',
        help='Use <command> --help for more information'
    )

    # Register command modules
    fetch.setup_parser(subparsers)
    delete.setup_parser(subparsers)
    analyze.setup_parser(subparsers)
    config.setup_parser(subparsers)
    auth.setup_parser(subparsers)

    return parser


def setup_logging(verbose: bool = False, debug: bool = False) -> None:
    """
    Configure logging based on CLI options.

    Args:
        verbose: Enable verbose output
        debug: Enable debug level logging
    """
    if debug:
        level = logging.DEBUG
        log_format = '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    elif verbose:
        level = logging.INFO
        log_format = '%(levelname)s: %(message)s'
    else:
        level = logging.WARNING
        log_format = '%(message)s'

    logging.basicConfig(
        level=level,
        format=log_format,
        handlers=[logging.StreamHandler()]
    )


def main(args: Optional[List[str]] = None) -> int:
    """
    Main entry point for the CLI.

    Args:
        args: Command line arguments (uses sys.argv if None)

    Returns:
        Exit code (0 for success, non-zero for errors)
    """
    parser = create_parser()

    # Parse arguments
    if args is None:
        args = sys.argv[1:]

    parsed_args = parser.parse_args(args)

    # Show help if no command specified
    if parsed_args.command is None:
        parser.print_help()
        return 1

    # Setup logging
    setup_logging(
        verbose=getattr(parsed_args, 'verbose', False),
        debug=getattr(parsed_args, 'debug', False)
    )

    # Route to appropriate command handler
    try:
        if parsed_args.command == 'fetch':
            return fetch.handle(parsed_args)
        elif parsed_args.command == 'delete':
            return delete.handle(parsed_args)
        elif parsed_args.command == 'analyze':
            return analyze.handle(parsed_args)
        elif parsed_args.command == 'config':
            return config.handle(parsed_args)
        elif parsed_args.command == 'auth':
            return auth.handle(parsed_args)
        else:
            logger.error(f"Unknown command: {parsed_args.command}")
            return 1

    except KeyboardInterrupt:
        print("\nOperation cancelled by user")
        return 130

    except Exception as e:
        logger.error(f"Error: {e}")
        if getattr(parsed_args, 'debug', False):
            import traceback
            traceback.print_exc()
        return 1


if __name__ == "__main__":
    sys.exit(main())
