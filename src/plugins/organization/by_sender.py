"""
By-Sender Organization Plugin for Gmail Fetcher.

Organizes emails into subdirectories by sender.
"""

import logging
import re
from typing import Any, Dict
from pathlib import Path

from ..base import OrganizationPlugin

logger = logging.getLogger(__name__)


class BySenderPlugin(OrganizationPlugin):
    """
    Plugin for organizing emails by sender.

    Creates directory structure based on sender email/name.
    Example: john_doe/ or newsletter_example_com/

    Sanitizes sender name for filesystem compatibility.
    """

    def __init__(self, use_domain: bool = False, max_length: int = 50):
        """
        Initialize the by-sender organization plugin.

        Args:
            use_domain: If True, organize by domain only (e.g., 'gmail.com')
            max_length: Maximum length for directory name
        """
        self._use_domain = use_domain
        self._max_length = max_length

    @property
    def name(self) -> str:
        return "sender"

    @property
    def description(self) -> str:
        return "Organize emails by sender name or domain"

    def get_path(
        self,
        email_data: Dict[str, Any],
        base_dir: Path
    ) -> Path:
        """
        Get the directory path based on email sender.

        Args:
            email_data: Dictionary containing email headers with 'from'
            base_dir: Base output directory

        Returns:
            Directory path like base_dir/sender_name/
        """
        headers = email_data.get('headers', {})
        sender = headers.get('from', '') or headers.get('From', '')

        # Extract and sanitize sender
        sender_path = self._extract_sender(sender)

        return base_dir / sender_path

    def _extract_sender(self, sender_str: str) -> str:
        """
        Extract sender identifier from From header.

        Args:
            sender_str: From header value (e.g., 'John Doe <john@example.com>')

        Returns:
            Sanitized sender identifier
        """
        if not sender_str:
            return "unknown_sender"

        # Try to extract email address
        email_match = re.search(r'<([^>]+)>', sender_str)
        if email_match:
            email_addr = email_match.group(1)
        else:
            # Might be just the email address
            email_addr = sender_str.strip()

        if self._use_domain:
            # Extract domain only
            if '@' in email_addr:
                domain = email_addr.split('@')[1]
                return self._sanitize_name(domain)
            return self._sanitize_name(email_addr)

        # Try to extract name from "Name <email>" format
        name_match = re.match(r'^([^<]+)<', sender_str)
        if name_match:
            name = name_match.group(1).strip()
            if name and name not in ['"', "'"]:
                # Clean up quoted names
                name = name.strip('"\'')
                return self._sanitize_name(name)

        # Fall back to email username
        if '@' in email_addr:
            username = email_addr.split('@')[0]
            return self._sanitize_name(username)

        return self._sanitize_name(email_addr)

    def _sanitize_name(self, name: str) -> str:
        """
        Sanitize name for use as directory name.

        Args:
            name: Raw name string

        Returns:
            Filesystem-safe directory name
        """
        if not name:
            return "unknown_sender"

        # Remove/replace invalid characters
        sanitized = re.sub(r'[<>:"/\\|?*\x00-\x1f]', '_', name)

        # Replace spaces and dots with underscores
        sanitized = re.sub(r'[\s.]+', '_', sanitized)

        # Remove consecutive underscores
        sanitized = re.sub(r'_+', '_', sanitized)

        # Remove leading/trailing underscores
        sanitized = sanitized.strip('_')

        # Truncate to max length
        if len(sanitized) > self._max_length:
            sanitized = sanitized[:self._max_length]

        # Ensure we have something valid
        if not sanitized or sanitized == '_':
            return "unknown_sender"

        return sanitized.lower()
