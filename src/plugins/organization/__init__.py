"""
File organization plugins for Gmail Fetcher.

Available plugins:
- ByDatePlugin: Organize by year/month
- BySenderPlugin: Organize by sender
- NoneOrganizationPlugin: Flat structure
"""

from .by_date import ByDatePlugin
from .by_sender import BySenderPlugin
from .none import NoneOrganizationPlugin

__all__ = [
    "ByDatePlugin",
    "BySenderPlugin",
    "NoneOrganizationPlugin",
]
