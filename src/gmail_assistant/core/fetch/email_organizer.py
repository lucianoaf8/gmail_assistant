"""
Email file organization functionality.

H-2 refactoring: Extracted from GmailFetcher to follow Single Responsibility Principle.
"""

from __future__ import annotations

import logging
from datetime import datetime
from pathlib import Path
from typing import Any

from gmail_assistant.utils.input_validator import InputValidator

logger = logging.getLogger(__name__)


class EmailOrganizer:
    """
    Organizes email files by date, sender, or flat structure.

    Extracted from GmailFetcher to follow Single Responsibility Principle.
    This class is responsible solely for determining the target directory
    and filename for email files based on organization strategy.
    """

    STRATEGY_DATE = 'date'
    STRATEGY_SENDER = 'sender'
    STRATEGY_NONE = 'none'

    def __init__(self, organize_by: str = 'date') -> None:
        """
        Initialize organizer.

        Args:
            organize_by: Organization strategy ('date', 'sender', or 'none')
        """
        if organize_by not in (self.STRATEGY_DATE, self.STRATEGY_SENDER, self.STRATEGY_NONE):
            logger.warning(f"Unknown organization strategy '{organize_by}', using 'date'")
            organize_by = self.STRATEGY_DATE

        self.organize_by = organize_by
        self.logger = logger

    def get_target_path(self, email: dict[str, Any], base_dir: Path) -> Path:
        """
        Determine target directory path for email based on organization strategy.

        Args:
            email: Parsed email data dict
            base_dir: Base output directory

        Returns:
            Target directory path (created if needed)
        """
        if self.organize_by == self.STRATEGY_DATE:
            target = self._organize_by_date(email, base_dir)
        elif self.organize_by == self.STRATEGY_SENDER:
            target = self._organize_by_sender(email, base_dir)
        else:
            target = base_dir

        # Ensure directory exists
        target.mkdir(parents=True, exist_ok=True)
        return target

    def get_filename(self, email: dict[str, Any]) -> str:
        """
        Generate a safe filename for an email.

        Args:
            email: Parsed email data dict

        Returns:
            Sanitized filename (without extension)
        """
        date_str = email.get('date', '')
        subject = email.get('subject', 'no_subject')
        msg_id = email.get('id', 'unknown')

        # Parse date for filename prefix
        date_prefix = self._parse_date_for_filename(date_str)

        # Sanitize subject
        safe_subject = InputValidator.sanitize_filename(subject, max_length=50)

        # Build filename
        return f"{date_prefix}_{safe_subject}_{msg_id}"

    def _organize_by_date(self, email: dict[str, Any], base_dir: Path) -> Path:
        """
        Organize by year/month directory structure.

        Args:
            email: Parsed email data dict
            base_dir: Base output directory

        Returns:
            Path like base_dir/2025/01/
        """
        date_str = email.get('date', '')
        year, month = self._parse_date_for_folder(date_str)
        return base_dir / year / month

    def _organize_by_sender(self, email: dict[str, Any], base_dir: Path) -> Path:
        """
        Organize by sender directory.

        Args:
            email: Parsed email data dict
            base_dir: Base output directory

        Returns:
            Path like base_dir/sender_name/
        """
        sender = email.get('sender', email.get('from', 'unknown'))

        # Extract username/domain from email address
        if '@' in sender:
            # Try to get the local part before @
            sender_part = sender.split('@')[0]
            # Clean up any name formatting like "Name <email>"
            if '<' in sender_part:
                sender_part = sender_part.split('<')[-1]
        else:
            sender_part = sender

        # Sanitize for filesystem
        safe_sender = InputValidator.sanitize_filename(sender_part, max_length=50)
        return base_dir / safe_sender

    def _parse_date_for_filename(self, date_str: str) -> str:
        """
        Parse email date string into filename-friendly prefix.

        Args:
            date_str: RFC 2822 date string

        Returns:
            String like '2025-01-11_143052' or 'unknown_date'
        """
        try:
            from email.utils import parsedate_to_datetime
            dt = parsedate_to_datetime(date_str)
            return dt.strftime('%Y-%m-%d_%H%M%S')
        except (ValueError, TypeError):
            return 'unknown_date'

    def _parse_date_for_folder(self, date_str: str) -> tuple[str, str]:
        """
        Parse email date string into year/month folder names.

        Args:
            date_str: RFC 2822 date string

        Returns:
            Tuple of (year, month) strings
        """
        try:
            from email.utils import parsedate_to_datetime
            dt = parsedate_to_datetime(date_str)
            return str(dt.year), f"{dt.month:02d}"
        except (ValueError, TypeError):
            return 'unknown', 'unknown'


__all__ = ['EmailOrganizer']
