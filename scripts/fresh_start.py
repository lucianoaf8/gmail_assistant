#!/usr/bin/env python3
"""
Fresh Start Script - Backward Compatibility Information
======================================================

This script provides information about the new unified interface.
The fresh start functionality is now available through the main.py interface.
"""

import sys
from pathlib import Path

def main():
    """Show information about the new unified interface."""

    print("=" * 60)
    print("Gmail Fetcher - Fresh Start (Unified Interface)")
    print("=" * 60)
    print()
    print("This script has been replaced by the unified main.py interface.")
    print()
    print("For fresh start functionality, use one of these commands:")
    print()
    print("  # Fetch emails for analysis first:")
    print("  python main.py fetch --query \"is:unread\" --max 1000")
    print()
    print("  # Run AI newsletter cleanup (dry run first):")
    print("  python main.py tools ai-cleanup --input your_email_data.json")
    print()
    print("  # Use samples for common scenarios:")
    print("  python main.py samples list")
    print("  python main.py samples unread")
    print()
    print("For more options:")
    print("  python main.py --help")
    print("  python main.py tools --help")
    print()
    return 0

if __name__ == "__main__":
    sys.exit(main())