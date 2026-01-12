"""
Asynchronous Gmail fetcher for concurrent operations.

Implements async/await patterns for improved performance.

H-4 refactoring: This module now supports two async operation modes:
1. Native async using httpx (recommended) - True async HTTP operations
2. Sync-over-async fallback - Uses ThreadPoolExecutor when httpx unavailable

M-9 fix: Concurrency settings now configurable via AppConfig:
- max_concurrent_requests: Controls semaphore limit
- max_worker_threads: Controls ThreadPoolExecutor size
- async_batch_size: Controls batch processing size

To use native async mode, install httpx: pip install gmail-assistant[async]
"""

from __future__ import annotations

import asyncio
import functools
import logging
from collections.abc import AsyncIterator
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path
from typing import TYPE_CHECKING, Any

# Local imports
from gmail_assistant.core.auth.credential_manager import SecureCredentialManager
from gmail_assistant.core.config import AppConfig
from gmail_assistant.utils.memory_manager import MemoryTracker
from gmail_assistant.utils.rate_limiter import GmailRateLimiter

# H-4: Check for native async client availability
from gmail_assistant.core.fetch.async_gmail_client import (
    AsyncGmailClient,
    is_async_client_available,
)

if TYPE_CHECKING:
    from google.oauth2.credentials import Credentials

logger = logging.getLogger(__name__)


class AsyncGmailFetcher:
    """
    Asynchronous Gmail fetcher with concurrent operations.

    H-4 refactoring: Supports two operation modes:
    1. Native async (requires httpx) - Best performance, true async HTTP
    2. Sync-over-async fallback - Uses ThreadPoolExecutor with sync API client

    The mode is automatically selected based on httpx availability and
    the `use_native_async` constructor parameter.
    """

    def __init__(
        self,
        credentials_file: str = 'credentials.json',
        max_concurrent: int = 10,
        max_workers: int = 4,
        use_native_async: bool | None = None,
    ):
        """
        Initialize async Gmail fetcher.

        Args:
            credentials_file: Path to OAuth credentials
            max_concurrent: Maximum concurrent operations
            max_workers: Maximum thread pool workers (sync-over-async fallback)
            use_native_async: Force native async mode (None = auto-detect based on httpx availability)
        """
        self.credential_manager = SecureCredentialManager(credentials_file)
        self.rate_limiter = GmailRateLimiter(requests_per_second=8.0)
        self.memory_tracker = MemoryTracker()
        self.max_concurrent = max_concurrent
        self.max_workers = max_workers
        self.semaphore = asyncio.Semaphore(max_concurrent)
        self.logger = logging.getLogger(__name__)

        # H-4: Determine async mode
        if use_native_async is None:
            use_native_async = is_async_client_available()

        self._use_native_async = use_native_async
        self._native_client: AsyncGmailClient | None = None
        self._credentials: Credentials | None = None

        # Fallback: ThreadPoolExecutor for sync-over-async
        if not self._use_native_async:
            self.executor = ThreadPoolExecutor(max_workers=max_workers)
            self.logger.info(
                "Using sync-over-async mode. Install httpx for better performance: "
                "pip install gmail-assistant[async]"
            )
        else:
            self.executor = None  # type: ignore[assignment]
            self.logger.info("Using native async mode with httpx")

    @classmethod
    def from_config(
        cls,
        config: AppConfig,
        credentials_file: str | None = None,
        use_native_async: bool | None = None,
    ) -> 'AsyncGmailFetcher':
        """
        M-9 fix: Create AsyncGmailFetcher from AppConfig concurrency settings.

        This factory method wires AppConfig's concurrency settings to the fetcher,
        allowing users to configure performance via config files or environment.

        Args:
            config: AppConfig instance with concurrency settings
            credentials_file: Override credentials path (default: from config)
            use_native_async: Force async mode (None = auto-detect)

        Returns:
            Configured AsyncGmailFetcher instance

        Example:
            config = AppConfig.load()
            async with AsyncGmailFetcher.from_config(config) as fetcher:
                emails = await fetcher.fetch_batch(query="is:unread")
        """
        creds = credentials_file or str(config.credentials_path)
        return cls(
            credentials_file=creds,
            max_concurrent=config.max_concurrent_requests,
            max_workers=config.max_worker_threads,
            use_native_async=use_native_async,
        )

    @property
    def service(self):
        """Get Gmail service with authentication."""
        return self.credential_manager.get_service()

    @property
    def is_native_async(self) -> bool:
        """Check if using native async mode."""
        return self._use_native_async

    async def __aenter__(self):
        """Async context manager entry."""
        # H-4: Initialize native client if in native async mode
        if self._use_native_async:
            self._credentials = self.credential_manager._load_credentials_securely()
            if self._credentials:
                self._native_client = AsyncGmailClient(self._credentials)
                await self._native_client.__aenter__()
        return self

    async def __aexit__(self, exc_type, exc_val, exc_tb):
        """Async context manager exit."""
        # H-4: Close native client if used
        if self._native_client:
            await self._native_client.__aexit__(exc_type, exc_val, exc_tb)
            self._native_client = None

        # Shutdown sync executor if used
        if self.executor is not None:
            self.executor.shutdown(wait=True)

    def _sync_api_call(self, func, *args, **kwargs):
        """
        Execute synchronous API call with rate limiting.

        Args:
            func: Function to call
            args: Positional arguments
            kwargs: Keyword arguments

        Returns:
            Function result
        """
        return self.rate_limiter.rate_limited_call(func, *args, **kwargs)

    async def _async_api_call(self, func, *args, **kwargs):
        """
        Execute API call asynchronously with semaphore control.

        Args:
            func: Function to call
            args: Positional arguments
            kwargs: Keyword arguments

        Returns:
            Function result
        """
        async with self.semaphore:
            # Run synchronous API call in thread pool
            loop = asyncio.get_event_loop()
            return await loop.run_in_executor(
                self.executor,
                functools.partial(self._sync_api_call, func, *args, **kwargs)
            )

    async def fetch_email_ids_async(self, query: str, max_results: int = 1000) -> list[str]:
        """
        Fetch email IDs asynchronously.

        Args:
            query: Gmail search query
            max_results: Maximum number of emails

        Returns:
            List of email IDs
        """
        service = self.service
        if not service:
            raise RuntimeError("Gmail service not available")

        email_ids = []
        next_page_token = None
        fetched_count = 0

        while fetched_count < max_results:
            page_size = min(500, max_results - fetched_count)

            try:
                # Prepare API call - bind loop variables to avoid B023
                def list_messages(ps=page_size, npt=next_page_token):
                    params = {
                        'userId': 'me',
                        'q': query,
                        'maxResults': ps,
                        'fields': 'messages(id),nextPageToken'
                    }
                    if npt:
                        params['pageToken'] = npt

                    return service.users().messages().list(**params).execute()

                # Execute async API call
                result = await self._async_api_call(list_messages)

                # Process results
                messages = result.get('messages', [])
                new_ids = [msg['id'] for msg in messages]
                email_ids.extend(new_ids)
                fetched_count += len(new_ids)

                # Check for next page
                next_page_token = result.get('nextPageToken')
                if not next_page_token or fetched_count >= max_results:
                    break

            except Exception as e:
                self.logger.error(f"Error fetching email IDs: {e}")
                break

        self.logger.info(f"Fetched {len(email_ids)} email IDs asynchronously")
        return email_ids

    async def fetch_email_async(self, email_id: str) -> dict[str, Any] | None:
        """
        Fetch single email asynchronously.

        H-4: Uses native async client if available, otherwise falls back
        to sync-over-async pattern.

        Args:
            email_id: Email ID to fetch

        Returns:
            Email data or None if failed
        """
        try:
            # H-4: Use native async client if available
            if self._native_client is not None:
                message = await self._native_client.get_message(email_id, format='full')
            else:
                # Fallback: sync-over-async
                service = self.service
                if not service:
                    return None

                def get_message():
                    return service.users().messages().get(
                        userId='me',
                        id=email_id,
                        format='full'
                    ).execute()

                message = await self._async_api_call(get_message)

            # Extract essential data
            email_data = {
                'id': message['id'],
                'threadId': message['threadId'],
                'labelIds': message.get('labelIds', []),
                'snippet': message.get('snippet', ''),
                'payload': message['payload'],
                'internalDate': message.get('internalDate'),
                'historyId': message.get('historyId')
            }

            return email_data

        except Exception as e:
            self.logger.error(f"Error fetching email {email_id}: {e}")
            return None

    async def fetch_emails_batch_async(self, email_ids: list[str]) -> list[dict[str, Any] | None]:
        """
        Fetch multiple emails concurrently.

        Args:
            email_ids: List of email IDs to fetch

        Returns:
            List of email data (None for failed fetches)
        """
        self.logger.info(f"Fetching {len(email_ids)} emails concurrently")

        # Create tasks for concurrent execution
        tasks = [self.fetch_email_async(email_id) for email_id in email_ids]

        # Execute with progress tracking
        results = []
        batch_size = min(self.max_concurrent, len(tasks))

        for i in range(0, len(tasks), batch_size):
            batch_tasks = tasks[i:i + batch_size]
            batch_results = await asyncio.gather(*batch_tasks, return_exceptions=True)

            # Process batch results
            for result in batch_results:
                if isinstance(result, Exception):
                    self.logger.error(f"Batch fetch error: {result}")
                    results.append(None)
                else:
                    results.append(result)

            # Memory check after each batch
            memory_status = self.memory_tracker.check_memory()
            if memory_status['status'] == 'warning':
                self.logger.info(f"Memory usage: {memory_status['current_mb']:.1f} MB after {len(results)} emails")

        self.logger.info(f"Completed fetching {len(results)} emails")
        return results

    async def process_emails_async(self, query: str, max_results: int = 1000,
                                  output_dir: str = 'gmail_backup',
                                  format_type: str = 'eml') -> AsyncIterator[dict[str, Any]]:
        """
        Process emails asynchronously with streaming results.

        Args:
            query: Gmail search query
            max_results: Maximum number of emails
            output_dir: Output directory
            format_type: Output format

        Yields:
            Processing results for each email
        """
        output_path = Path(output_dir)
        output_path.mkdir(exist_ok=True)

        # Fetch email IDs
        email_ids = await self.fetch_email_ids_async(query, max_results)

        if not email_ids:
            self.logger.info("No emails found for query")
            return

        # Process in batches to manage memory
        batch_size = min(self.max_concurrent * 2, 100)  # Reasonable batch size

        for i in range(0, len(email_ids), batch_size):
            batch_ids = email_ids[i:i + batch_size]
            self.logger.info(f"Processing batch {i//batch_size + 1}: emails {i+1}-{min(i+batch_size, len(email_ids))}")

            # Fetch batch of emails
            email_data_list = await self.fetch_emails_batch_async(batch_ids)

            # Process each email in the batch
            for email_data in email_data_list:
                if email_data:
                    result = await self._save_email_async(email_data, output_path, format_type)
                    yield {
                        "email_id": email_data['id'],
                        "success": result,
                        "format": format_type
                    }
                else:
                    yield {
                        "email_id": "unknown",
                        "success": False,
                        "error": "Failed to fetch email data"
                    }

            # Force garbage collection after each batch
            self.memory_tracker.force_gc()

    async def _save_email_async(self, email_data: dict[str, Any], output_path: Path,
                               format_type: str) -> bool:
        """
        Save email asynchronously.

        Args:
            email_data: Email data dictionary
            output_path: Output directory path
            format_type: Format to save

        Returns:
            True if saved successfully, False otherwise
        """
        def save_email():
            """Synchronous save operation to run in executor."""
            try:
                from ..utils.memory_manager import EmailContentStreamer
                from .gmail_assistant import GmailFetcher

                # Create temporary fetcher for utility methods
                temp_fetcher = GmailFetcher()
                streamer = EmailContentStreamer()

                # Extract data
                headers = temp_fetcher.extract_headers(email_data['payload'].get('headers', []))

                # Generate filename
                date_str = headers.get('date', 'Unknown Date')
                subject = headers.get('subject', 'No Subject')
                filename = temp_fetcher.sanitize_filename(f"{date_str}_{subject}_{email_data['id']}")

                success = True

                # Save based on format
                if format_type in ['eml', 'both']:
                    eml_content = temp_fetcher.create_eml_content(email_data)
                    eml_path = output_path / f"{filename}.eml"
                    success &= streamer.stream_to_file(eml_content, eml_path)

                if format_type in ['markdown', 'both']:
                    md_content = temp_fetcher.create_markdown_content(email_data)
                    md_path = output_path / f"{filename}.md"
                    success &= streamer.stream_to_file(md_content, md_path)

                return success

            except Exception as e:
                logger.error(f"Error saving email {email_data.get('id')}: {e}")
                return False

        # Execute save operation in thread pool
        loop = asyncio.get_event_loop()
        return await loop.run_in_executor(self.executor, save_email)

    async def get_profile_async(self) -> dict[str, Any] | None:
        """
        Get Gmail profile asynchronously.

        Returns:
            Profile data or None if failed
        """
        service = self.service
        if not service:
            return None

        try:
            def get_profile():
                return service.users().getProfile(userId='me').execute()

            profile = await self._async_api_call(get_profile)
            return {
                'email': profile.get('emailAddress'),
                'messages_total': profile.get('messagesTotal'),
                'threads_total': profile.get('threadsTotal')
            }

        except Exception as e:
            self.logger.error(f"Error getting profile: {e}")
            return None

    async def search_emails_async(self, query: str, max_results: int = 100) -> list[dict[str, Any]]:
        """
        Search emails asynchronously with concurrent fetching.

        Args:
            query: Gmail search query
            max_results: Maximum number of results

        Returns:
            List of email metadata
        """
        # Get email IDs
        email_ids = await self.fetch_email_ids_async(query, max_results)

        if not email_ids:
            return []

        # Fetch emails concurrently
        email_data_list = await self.fetch_emails_batch_async(email_ids)

        # Return non-None results
        return [email_data for email_data in email_data_list if email_data]

    def get_performance_stats(self) -> dict[str, Any]:
        """Get performance and memory statistics."""
        memory_stats = self.memory_tracker.check_memory()
        rate_stats = self.rate_limiter.get_stats()

        return {
            'memory': memory_stats,
            'rate_limiting': rate_stats,
            'concurrent_limit': self.max_concurrent,
            'thread_pool_workers': self.max_workers
        }
