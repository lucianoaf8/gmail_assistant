"""
Samples handler for Gmail Fetcher main interface.
Handles predefined sample scenarios with proper error handling.
"""

import sys
import logging
from typing import Any

logger = logging.getLogger(__name__)


def handle_samples_command(args: Any) -> None:
    """
    Handle predefined sample scenarios.

    Args:
        args: Parsed command line arguments
    """
    try:
        from examples.samples import main as samples_main

        if args.scenario == 'list':
            _list_available_scenarios()
            return

        print(f"Running sample scenario: {args.scenario}")
        samples_main(args.scenario, max_emails=args.max)
        print(f"Success: Sample scenario '{args.scenario}' completed")

    except ImportError as e:
        error_msg = f"Error importing samples: {e}"
        logger.error(error_msg)
        print(f"Error: {error_msg}")
        sys.exit(1)

    except Exception as e:
        error_msg = f"Error running sample: {e}"
        logger.error(error_msg)
        print(f"Error: {error_msg}")
        sys.exit(1)


def _list_available_scenarios() -> None:
    """List all available sample scenarios."""
    print("Available sample scenarios:")
    print("  unread     - Download all unread emails")
    print("  newsletters - Download newsletters and subscriptions")
    print("  services   - Download service notifications")
    print("  important  - Download important emails")