"""
No Organization Plugin for Gmail Fetcher.

Places all emails directly in the base directory without subdirectories.
"""

import logging
from typing import Any, Dict
from pathlib import Path

from ..base import OrganizationPlugin

logger = logging.getLogger(__name__)


class NoneOrganizationPlugin(OrganizationPlugin):
    """
    Plugin for flat file organization.

    All emails are placed directly in the base directory
    without any subdirectory structure.
    """

    @property
    def name(self) -> str:
        return "none"

    @property
    def description(self) -> str:
        return "No organization - all files in base directory"

    def get_path(
        self,
        email_data: Dict[str, Any],
        base_dir: Path
    ) -> Path:
        """
        Get the directory path (always the base directory).

        Args:
            email_data: Dictionary containing email data (unused)
            base_dir: Base output directory

        Returns:
            The base directory unchanged
        """
        return base_dir
