#!/usr/bin/env python3
"""
Gmail Unread Inbox Cleaner - Backward Compatibility Information
==============================================================

This script provides information about the new unified interface.
The clean inbox functionality is now available through the main.py interface.
"""

import sys
from pathlib import Path

def main():
    """Show information about the new unified interface."""

    print("=" * 60)
    print("Gmail Fetcher - Unified Interface")
    print("=" * 60)
    print()
    print("This script has been replaced by the unified main.py interface.")
    print()
    print("For cleaning unread emails, use one of these commands:")
    print()
    print("  # Fetch unread emails to backup:")
    print("  python main.py fetch --query \"is:unread\" --max 1000")
    print()
    print("  # Run AI newsletter cleanup:")
    print("  python main.py tools ai-cleanup --input your_email_data.json")
    print()
    print("  # Run predefined samples:")
    print("  python main.py samples unread")
    print()
    print("For more options:")
    print("  python main.py --help")
    print("  python main.py fetch --help")
    print("  python main.py tools --help")
    print()
    return 0

if __name__ == "__main__":
    sys.exit(main())