"""
Fetch sub-package for Gmail email fetching operations.

H-2 refactoring: GmailFetcher now delegates to specialized components:
- EmailSearcher: Query execution and pagination
- EmailDownloader: Content retrieval
- EmailWriter: Output file creation
- EmailOrganizer: File organization

H-4 refactoring: AsyncGmailFetcher now supports native async mode:
- AsyncGmailClient: Native async HTTP client using httpx
- is_async_client_available(): Check if httpx is installed
"""

from .async_fetcher import AsyncGmailFetcher
from .async_gmail_client import AsyncGmailClient, is_async_client_available
from .email_downloader import EmailDownloader
from .email_organizer import EmailOrganizer
from .email_searcher import EmailSearcher
from .email_writer import EmailWriter
from .gmail_api_client import GmailAPIClient
from .gman import GmailFetcher
from .incremental import IncrementalFetcher
from .streaming import StreamingGmailFetcher

__all__ = [
    'AsyncGmailClient',
    'AsyncGmailFetcher',
    'EmailDownloader',
    'EmailOrganizer',
    'EmailSearcher',
    'EmailWriter',
    'GmailAPIClient',
    'GmailFetcher',
    'IncrementalFetcher',
    'StreamingGmailFetcher',
    'is_async_client_available',
]
