"""
Tools handler for Gmail Fetcher main interface.
Handles tool-related commands with proper error handling and validation.
"""

import logging
from typing import Any

logger = logging.getLogger(__name__)


def handle_tools_command(args: Any) -> None:
    """
    Handle tools and utility operations.

    Args:
        args: Parsed command line arguments
    """
    if args.tool == 'cleanup':
        _handle_cleanup_tool(args)
    elif args.tool == 'ai-cleanup':
        _handle_ai_cleanup_tool(args)
    else:
        logger.error(f"Unknown tool: {args.tool}")
        print(f"Error: Unknown tool '{args.tool}'")


def _handle_cleanup_tool(args: Any) -> None:
    """
    Handle cleanup tool operations.

    Args:
        args: Parsed command line arguments
    """
    print(f"Running cleanup on {args.target} (type: {args.type})")

    try:
        if args.type in ['markdown', 'all']:
            from tools.cleanup.cleanup_markdown import main as cleanup_markdown
            cleanup_markdown(args.target)
        print(f"Success: Cleanup completed for {args.target}")

    except ImportError as e:
        error_msg = f"Error importing cleanup tools: {e}"
        logger.error(error_msg)
        print(f"Error: {error_msg}")

    except Exception as e:
        error_msg = f"Error during cleanup: {e}"
        logger.error(error_msg)
        print(f"Error: {error_msg}")


def _handle_ai_cleanup_tool(args: Any) -> None:
    """
    Handle AI cleanup tool operations.

    Args:
        args: Parsed command line arguments
    """
    print(f"Running AI newsletter cleanup on {args.input}")

    try:
        from gmail_assistant.core.gmail_ai_newsletter_cleaner import main as ai_cleaner
        ai_cleaner(args.input, delete=args.delete, threshold=args.threshold)
        print("Success: AI cleanup completed")

    except ImportError as e:
        error_msg = f"Error importing AI cleanup tools: {e}"
        logger.error(error_msg)
        print(f"Error: {error_msg}")

    except Exception as e:
        error_msg = f"Error during AI cleanup: {e}"
        logger.error(error_msg)
        print(f"Error: {error_msg}")