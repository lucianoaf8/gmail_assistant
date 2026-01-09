"""
By-Date Organization Plugin for Gmail Fetcher.

Organizes emails into year/month subdirectories.
"""

import logging
import re
from typing import Any, Dict
from pathlib import Path
from email.utils import parsedate_to_datetime
from datetime import datetime

from ..base import OrganizationPlugin

logger = logging.getLogger(__name__)


class ByDatePlugin(OrganizationPlugin):
    """
    Plugin for organizing emails by date.

    Creates directory structure: YYYY/MM/
    Example: 2025/03/

    Falls back to 'unknown' for unparseable dates.
    """

    def __init__(self, format_string: str = "%Y/%m"):
        """
        Initialize the by-date organization plugin.

        Args:
            format_string: strftime format for directory path (default: YYYY/MM)
        """
        self._format_string = format_string

    @property
    def name(self) -> str:
        return "date"

    @property
    def description(self) -> str:
        return "Organize emails by year and month (YYYY/MM)"

    def get_path(
        self,
        email_data: Dict[str, Any],
        base_dir: Path
    ) -> Path:
        """
        Get the directory path based on email date.

        Args:
            email_data: Dictionary containing email headers with 'date'
            base_dir: Base output directory

        Returns:
            Directory path like base_dir/2025/03/
        """
        headers = email_data.get('headers', {})
        date_str = headers.get('date', '')

        # Try to parse the date
        date_path = self._parse_date(date_str)

        return base_dir / date_path

    def _parse_date(self, date_str: str) -> str:
        """
        Parse date string and format as directory path.

        Args:
            date_str: RFC 5322 date string from email header

        Returns:
            Formatted directory path (e.g., '2025/03')
        """
        if not date_str:
            return "unknown"

        try:
            # Try standard email date parsing
            date_obj = parsedate_to_datetime(date_str)
            return date_obj.strftime(self._format_string)

        except (ValueError, TypeError) as e:
            logger.debug(f"Failed to parse date '{date_str}': {e}")

            # Try common fallback patterns
            fallback_patterns = [
                r"(\d{4})-(\d{2})-(\d{2})",  # ISO format
                r"(\d{2})/(\d{2})/(\d{4})",   # US format
                r"(\d{1,2})\s+(\w+)\s+(\d{4})",  # 1 Jan 2025
            ]

            for pattern in fallback_patterns:
                match = re.search(pattern, date_str)
                if match:
                    try:
                        groups = match.groups()
                        if len(groups) == 3:
                            # Assume first group is year for ISO, last for others
                            if len(groups[0]) == 4:
                                return f"{groups[0]}/{groups[1]}"
                            elif len(groups[2]) == 4:
                                return f"{groups[2]}/{groups[0].zfill(2)}"
                    except Exception:
                        continue

            return "unknown"

    def get_date_prefix(self, email_data: Dict[str, Any]) -> str:
        """
        Get date prefix for filename.

        Args:
            email_data: Email data dictionary

        Returns:
            Date prefix like '2025-03-15_120000'
        """
        headers = email_data.get('headers', {})
        date_str = headers.get('date', '')

        if not date_str:
            return "unknown_date"

        try:
            date_obj = parsedate_to_datetime(date_str)
            return date_obj.strftime("%Y-%m-%d_%H%M%S")
        except (ValueError, TypeError):
            return "unknown_date"
