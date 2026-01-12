"""
Email search and pagination functionality.

H-2 refactoring: Extracted from GmailFetcher to follow Single Responsibility Principle.
"""

from __future__ import annotations

import logging
from typing import TYPE_CHECKING, Any

from googleapiclient.errors import HttpError

if TYPE_CHECKING:
    from googleapiclient.discovery import Resource

logger = logging.getLogger(__name__)


class EmailSearcher:
    """
    Handles Gmail search queries and pagination.

    Extracted from GmailFetcher to follow Single Responsibility Principle.
    This class is responsible solely for executing search queries against
    the Gmail API and handling pagination to retrieve message IDs.
    """

    def __init__(
        self,
        service: Resource,
        rate_limiter: Any | None = None,
    ) -> None:
        """
        Initialize searcher.

        Args:
            service: Authenticated Gmail API service
            rate_limiter: Optional rate limiter for API calls
        """
        self.service = service
        self.rate_limiter = rate_limiter
        self.logger = logger

    def search(self, query: str = '', max_results: int = 500) -> list[str]:
        """
        Search for emails matching query.

        Args:
            query: Gmail search query (supports all Gmail operators)
            max_results: Maximum results to return (default 500)

        Returns:
            List of message IDs matching the query
        """
        message_ids: list[str] = []
        page_token: str | None = None

        self.logger.info(f"Searching for emails with query: '{query}'")

        while len(message_ids) < max_results:
            try:
                # Apply rate limiting if configured
                if self.rate_limiter:
                    self.rate_limiter.wait_if_needed()

                batch_size = min(500, max_results - len(message_ids))

                # Build request parameters
                params: dict[str, Any] = {
                    'userId': 'me',
                    'q': query,
                    'maxResults': batch_size,
                }
                if page_token:
                    params['pageToken'] = page_token

                # Execute search
                results = self.service.users().messages().list(**params).execute()

                # Extract message IDs
                messages = results.get('messages', [])
                for msg in messages:
                    message_ids.append(msg['id'])

                # Check for next page
                page_token = results.get('nextPageToken')
                if not page_token:
                    break

            except HttpError as e:
                self.logger.error(f"HTTP error during search: {e}")
                break
            except Exception as e:
                self.logger.error(f"Unexpected error during search: {e}")
                break

        self.logger.info(f"Found {len(message_ids)} messages")
        return message_ids[:max_results]

    def count(self, query: str = '') -> int:
        """
        Get estimated count of emails matching query.

        Args:
            query: Gmail search query

        Returns:
            Estimated count of matching emails
        """
        try:
            results = self.service.users().messages().list(
                userId='me',
                q=query,
                maxResults=1
            ).execute()
            return results.get('resultSizeEstimate', 0)
        except HttpError as e:
            self.logger.error(f"Error getting count: {e}")
            return 0

    def search_with_metadata(
        self,
        query: str = '',
        max_results: int = 100,
        metadata_headers: list[str] | None = None,
    ) -> list[dict[str, Any]]:
        """
        Search for emails and return basic metadata.

        More efficient than downloading full messages when only
        metadata is needed.

        Args:
            query: Gmail search query
            max_results: Maximum results
            metadata_headers: Headers to include (default: From, Subject, Date)

        Returns:
            List of dicts with message ID and metadata
        """
        if metadata_headers is None:
            metadata_headers = ['From', 'Subject', 'Date']

        message_ids = self.search(query, max_results)
        results: list[dict[str, Any]] = []

        for msg_id in message_ids:
            try:
                if self.rate_limiter:
                    self.rate_limiter.wait_if_needed()

                msg = self.service.users().messages().get(
                    userId='me',
                    id=msg_id,
                    format='metadata',
                    metadataHeaders=metadata_headers
                ).execute()

                headers = {
                    h['name']: h['value']
                    for h in msg['payload'].get('headers', [])
                }
                results.append({
                    'id': msg_id,
                    'threadId': msg.get('threadId'),
                    'snippet': msg.get('snippet', ''),
                    **headers
                })

            except HttpError as e:
                self.logger.warning(f"Error getting metadata for {msg_id}: {e}")
                continue

        return results


__all__ = ['EmailSearcher']
