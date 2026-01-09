"""
Command Line Interface for Gmail Fetcher.

This package provides a structured CLI with subcommands:
- fetch: Download emails from Gmail
- delete: Delete emails from Gmail
- analyze: Analyze email patterns
- config: Configuration management
- auth: Authentication management

Usage:
    python -m src.cli --help
    python -m src.cli fetch --query "is:unread" --max 100
    python -m src.cli delete unread --dry-run
"""

from .main import main, create_parser

__all__ = ["main", "create_parser"]
