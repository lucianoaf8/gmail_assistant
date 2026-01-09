"""
Gmail Deletion Module
====================

Safe bulk deletion tools with multiple validation layers and rich CLI interfaces.
"""

from .deleter import GmailDeleter
from .ui import clean_unread_inbox

__all__ = [
    'GmailDeleter',
    'clean_unread_inbox'
]