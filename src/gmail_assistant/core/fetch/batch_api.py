"""
Gmail Batch API implementation for high-performance bulk operations.
Reduces API latency by 80-90% compared to sequential calls.

Usage:
    client = GmailBatchClient(service)
    emails = client.batch_get_messages(message_ids)
"""

import logging
from collections.abc import Callable
from dataclasses import dataclass, field
from typing import Any

try:
    from googleapiclient.errors import HttpError
    from googleapiclient.http import BatchHttpRequest
    GMAIL_API_AVAILABLE = True
except ImportError:
    GMAIL_API_AVAILABLE = False
    BatchHttpRequest = None
    HttpError = Exception

from gmail_assistant.core.exceptions import BatchAPIError  # H-2 fix: Use centralized exception
from gmail_assistant.core.schemas import Email

logger = logging.getLogger(__name__)


@dataclass
class BatchResult:
    """Result of a batch operation."""
    successful: int = 0
    failed: int = 0
    errors: list[dict[str, Any]] = field(default_factory=list)


class GmailBatchClient:
    """
    Gmail Batch API client for efficient bulk operations.

    The Gmail API supports batching up to 100 requests per batch call,
    significantly reducing HTTP overhead and latency.

    Example:
        >>> client = GmailBatchClient(gmail_service)
        >>> emails = client.batch_get_messages(['id1', 'id2', 'id3'])
        >>> print(f"Fetched {len(emails)} emails")
    """

    MAX_BATCH_SIZE = 100  # Gmail API limit

    def __init__(
        self,
        service,
        rate_limiter: Any | None = None,
        on_error: Callable[[str, Exception], None] | None = None
    ):
        """
        Initialize batch client.

        Args:
            service: Authenticated Gmail API service
            rate_limiter: Optional rate limiter for quota management
            on_error: Optional error callback(message_id, exception)
        """
        if not GMAIL_API_AVAILABLE:
            raise ImportError(
                "google-api-python-client required. "
                "Install with: pip install google-api-python-client"
            )

        self.service = service
        self.rate_limiter = rate_limiter
        self.on_error = on_error

        # Internal state for batch callbacks
        self._results: dict[str, Any] = {}
        self._errors: dict[str, Exception] = {}

    def batch_get_messages(
        self,
        message_ids: list[str],
        format: str = 'metadata',
        metadata_headers: list[str] | None = None,
        progress_callback: Callable[[int, int], None] | None = None
    ) -> list[Email]:
        """
        Fetch multiple messages in batched requests.

        Args:
            message_ids: List of Gmail message IDs
            format: Message format ('minimal', 'metadata', 'full', 'raw')
            metadata_headers: Headers to include when format='metadata'
            progress_callback: Optional callback(current, total) for progress

        Returns:
            List of Email objects

        Raises:
            BatchAPIError: If entire batch fails
        """
        if not message_ids:
            return []

        if metadata_headers is None:
            metadata_headers = ['From', 'To', 'Subject', 'Date', 'Cc', 'Bcc']

        emails = []
        total = len(message_ids)

        logger.info(f"Batch fetching {total} messages in chunks of {self.MAX_BATCH_SIZE}")

        # Process in batches
        for i in range(0, total, self.MAX_BATCH_SIZE):
            batch_ids = message_ids[i:i + self.MAX_BATCH_SIZE]
            batch_num = (i // self.MAX_BATCH_SIZE) + 1
            total_batches = (total + self.MAX_BATCH_SIZE - 1) // self.MAX_BATCH_SIZE

            logger.debug(f"Processing batch {batch_num}/{total_batches} ({len(batch_ids)} messages)")

            # Rate limiting
            if self.rate_limiter:
                self.rate_limiter.wait_if_needed(len(batch_ids))

            # Create batch request
            batch = self.service.new_batch_http_request()
            self._results.clear()
            self._errors.clear()

            for msg_id in batch_ids:
                request = self.service.users().messages().get(
                    userId='me',
                    id=msg_id,
                    format=format,
                    metadataHeaders=metadata_headers if format == 'metadata' else None
                )
                batch.add(request, callback=self._create_get_callback(msg_id))

            # Execute batch
            try:
                batch.execute()
            except HttpError as e:
                logger.error(f"Batch request failed: {e}")
                raise BatchAPIError(str(e), batch_ids)
            except Exception as e:
                logger.error(f"Unexpected batch error: {e}")
                raise BatchAPIError(str(e), batch_ids)

            # Process results
            for msg_id in batch_ids:
                if msg_id in self._results:
                    try:
                        email = Email.from_gmail_message(self._results[msg_id])
                        emails.append(email)
                    except Exception as e:
                        logger.warning(f"Failed to parse message {msg_id}: {e}")
                        if self.on_error:
                            self.on_error(msg_id, e)
                elif msg_id in self._errors:
                    logger.warning(f"Failed to fetch {msg_id}: {self._errors[msg_id]}")
                    if self.on_error:
                        self.on_error(msg_id, self._errors[msg_id])

            # Progress callback
            if progress_callback:
                progress_callback(min(i + self.MAX_BATCH_SIZE, total), total)

        logger.info(f"Batch fetch complete: {len(emails)}/{total} messages retrieved")
        return emails

    def batch_get_messages_raw(
        self,
        message_ids: list[str],
        progress_callback: Callable[[int, int], None] | None = None
    ) -> dict[str, dict[str, Any]]:
        """
        Fetch multiple messages and return raw API responses.

        Args:
            message_ids: List of Gmail message IDs
            progress_callback: Optional progress callback

        Returns:
            Dictionary mapping message_id to raw response
        """
        if not message_ids:
            return {}

        results = {}
        total = len(message_ids)

        for i in range(0, total, self.MAX_BATCH_SIZE):
            batch_ids = message_ids[i:i + self.MAX_BATCH_SIZE]

            if self.rate_limiter:
                self.rate_limiter.wait_if_needed(len(batch_ids))

            batch = self.service.new_batch_http_request()
            self._results.clear()
            self._errors.clear()

            for msg_id in batch_ids:
                request = self.service.users().messages().get(
                    userId='me',
                    id=msg_id,
                    format='full'
                )
                batch.add(request, callback=self._create_get_callback(msg_id))

            try:
                batch.execute()
            except Exception as e:
                logger.error(f"Batch failed: {e}")
                continue

            results.update(self._results)

            if progress_callback:
                progress_callback(min(i + self.MAX_BATCH_SIZE, total), total)

        return results

    def _create_get_callback(self, msg_id: str) -> Callable:
        """Create callback for get message request."""
        def callback(request_id, response, exception):
            if exception:
                self._errors[msg_id] = exception
            else:
                self._results[msg_id] = response
        return callback

    def batch_delete_messages(
        self,
        message_ids: list[str],
        progress_callback: Callable[[int, int], None] | None = None
    ) -> BatchResult:
        """
        Delete multiple messages in batched requests.

        WARNING: This permanently deletes messages!

        Args:
            message_ids: List of message IDs to delete
            progress_callback: Optional progress callback

        Returns:
            BatchResult with operation stats
        """
        if not message_ids:
            return BatchResult()

        result = BatchResult()
        total = len(message_ids)

        logger.warning(f"Batch deleting {total} messages")

        for i in range(0, total, self.MAX_BATCH_SIZE):
            batch_ids = message_ids[i:i + self.MAX_BATCH_SIZE]

            if self.rate_limiter:
                self.rate_limiter.wait_if_needed(len(batch_ids))

            batch = self.service.new_batch_http_request()

            for msg_id in batch_ids:
                request = self.service.users().messages().delete(
                    userId='me',
                    id=msg_id
                )
                batch.add(request, callback=self._create_delete_callback(msg_id, result))

            try:
                batch.execute()
            except HttpError as e:
                logger.error(f"Batch delete failed: {e}")
                result.failed += len(batch_ids)
                result.errors.append({'batch': batch_ids, 'error': str(e)})
                continue

            if progress_callback:
                progress_callback(min(i + self.MAX_BATCH_SIZE, total), total)

        logger.info(f"Batch delete complete: {result.successful} deleted, {result.failed} failed")
        return result

    def _create_delete_callback(self, msg_id: str, result: BatchResult) -> Callable:
        """Create callback for delete request."""
        def callback(request_id, response, exception):
            if exception:
                result.failed += 1
                result.errors.append({'id': msg_id, 'error': str(exception)})
            else:
                result.successful += 1
        return callback

    def batch_trash_messages(
        self,
        message_ids: list[str],
        progress_callback: Callable[[int, int], None] | None = None
    ) -> BatchResult:
        """
        Move multiple messages to trash in batched requests.

        Args:
            message_ids: List of message IDs to trash
            progress_callback: Optional progress callback

        Returns:
            BatchResult with operation stats
        """
        if not message_ids:
            return BatchResult()

        result = BatchResult()
        total = len(message_ids)

        logger.info(f"Batch trashing {total} messages")

        for i in range(0, total, self.MAX_BATCH_SIZE):
            batch_ids = message_ids[i:i + self.MAX_BATCH_SIZE]

            if self.rate_limiter:
                self.rate_limiter.wait_if_needed(len(batch_ids))

            batch = self.service.new_batch_http_request()

            for msg_id in batch_ids:
                request = self.service.users().messages().trash(
                    userId='me',
                    id=msg_id
                )
                batch.add(request, callback=self._create_trash_callback(msg_id, result))

            try:
                batch.execute()
            except HttpError as e:
                logger.error(f"Batch trash failed: {e}")
                result.failed += len(batch_ids)
                continue

            if progress_callback:
                progress_callback(min(i + self.MAX_BATCH_SIZE, total), total)

        return result

    def _create_trash_callback(self, msg_id: str, result: BatchResult) -> Callable:
        """Create callback for trash request."""
        def callback(request_id, response, exception):
            if exception:
                result.failed += 1
                result.errors.append({'id': msg_id, 'error': str(exception)})
            else:
                result.successful += 1
        return callback

    def batch_modify_labels(
        self,
        message_ids: list[str],
        add_labels: list[str] | None = None,
        remove_labels: list[str] | None = None,
        progress_callback: Callable[[int, int], None] | None = None
    ) -> BatchResult:
        """
        Modify labels on multiple messages in batch.

        Args:
            message_ids: List of message IDs
            add_labels: Labels to add
            remove_labels: Labels to remove
            progress_callback: Optional progress callback

        Returns:
            BatchResult with operation stats
        """
        if not message_ids:
            return BatchResult()

        result = BatchResult()
        body = {
            'addLabelIds': add_labels or [],
            'removeLabelIds': remove_labels or []
        }

        total = len(message_ids)

        for i in range(0, total, self.MAX_BATCH_SIZE):
            batch_ids = message_ids[i:i + self.MAX_BATCH_SIZE]

            if self.rate_limiter:
                self.rate_limiter.wait_if_needed(len(batch_ids))

            batch = self.service.new_batch_http_request()

            for msg_id in batch_ids:
                request = self.service.users().messages().modify(
                    userId='me',
                    id=msg_id,
                    body=body
                )
                batch.add(request, callback=self._create_modify_callback(msg_id, result))

            try:
                batch.execute()
            except HttpError as e:
                logger.error(f"Batch modify failed: {e}")
                result.failed += len(batch_ids)

            if progress_callback:
                progress_callback(min(i + self.MAX_BATCH_SIZE, total), total)

        return result

    def _create_modify_callback(self, msg_id: str, result: BatchResult) -> Callable:
        """Create callback for modify request."""
        def callback(request_id, response, exception):
            if exception:
                result.failed += 1
            else:
                result.successful += 1
        return callback

    def batch_mark_read(self, message_ids: list[str]) -> BatchResult:
        """Mark multiple messages as read."""
        return self.batch_modify_labels(
            message_ids,
            remove_labels=['UNREAD']
        )

    def batch_mark_unread(self, message_ids: list[str]) -> BatchResult:
        """Mark multiple messages as unread."""
        return self.batch_modify_labels(
            message_ids,
            add_labels=['UNREAD']
        )

    def batch_archive(self, message_ids: list[str]) -> BatchResult:
        """Archive multiple messages (remove from inbox)."""
        return self.batch_modify_labels(
            message_ids,
            remove_labels=['INBOX']
        )
