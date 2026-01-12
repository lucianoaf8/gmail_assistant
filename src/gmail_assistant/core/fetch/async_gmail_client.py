"""
True async Gmail API client using httpx.

H-4 refactoring: Replaces sync-over-async pattern with native async HTTP calls.

This module provides a native async implementation of Gmail API operations
that avoids the thread pool overhead of running synchronous calls in an executor.

Note: Requires the 'httpx' package. Falls back to sync-over-async if unavailable.
Install with: pip install gmail-assistant[async]
"""

from __future__ import annotations

import logging
from typing import TYPE_CHECKING, Any

logger = logging.getLogger(__name__)

# Check if httpx is available
_HTTPX_AVAILABLE = False
try:
    import httpx
    _HTTPX_AVAILABLE = True
except ImportError:
    httpx = None  # type: ignore[assignment]

if TYPE_CHECKING:
    from google.oauth2.credentials import Credentials


class AsyncGmailClient:
    """
    Native async Gmail API client using httpx.

    H-4 fix: Uses httpx for true async HTTP operations instead of
    wrapping synchronous calls in an executor.

    This client requires the httpx package. If not available, the
    AsyncGmailFetcher will fall back to using run_in_executor.

    Example:
        async with AsyncGmailClient(credentials) as client:
            messages = await client.list_messages('is:unread')
            for msg_id in messages.get('messages', []):
                details = await client.get_message(msg_id['id'])
    """

    BASE_URL = "https://gmail.googleapis.com/gmail/v1"

    def __init__(
        self,
        credentials: Credentials,
        timeout: float = 30.0,
        use_http2: bool = True,
    ) -> None:
        """
        Initialize async client.

        Args:
            credentials: Google OAuth credentials
            timeout: HTTP request timeout in seconds
            use_http2: Whether to use HTTP/2 (recommended for performance)
        """
        if not _HTTPX_AVAILABLE:
            raise ImportError(
                "httpx is required for AsyncGmailClient. "
                "Install with: pip install gmail-assistant[async]"
            )

        self.credentials = credentials
        self.timeout = timeout
        self.use_http2 = use_http2
        self._client: httpx.AsyncClient | None = None
        self.logger = logger

    async def __aenter__(self) -> AsyncGmailClient:
        """Async context manager entry."""
        self._client = httpx.AsyncClient(
            timeout=self.timeout,
            http2=self.use_http2,
        )
        return self

    async def __aexit__(self, exc_type, exc_val, exc_tb) -> None:
        """Async context manager exit."""
        if self._client:
            await self._client.aclose()
            self._client = None

    async def _ensure_client(self) -> None:
        """Ensure client is initialized."""
        if self._client is None:
            self._client = httpx.AsyncClient(
                timeout=self.timeout,
                http2=self.use_http2,
            )

    async def _get_auth_headers(self) -> dict[str, str]:
        """
        Get authorization headers with fresh token.

        Refreshes the token if expired.
        """
        # Note: Token refresh is synchronous in the google-auth library.
        # This is acceptable as it only happens periodically.
        if self.credentials.expired and self.credentials.refresh_token:
            from google.auth.transport.requests import Request
            self.credentials.refresh(Request())

        return {
            'Authorization': f'Bearer {self.credentials.token}',
            'Accept': 'application/json',
        }

    async def close(self) -> None:
        """Close the HTTP client."""
        if self._client:
            await self._client.aclose()
            self._client = None

    async def list_messages(
        self,
        query: str = '',
        max_results: int = 100,
        page_token: str | None = None,
        label_ids: list[str] | None = None,
    ) -> dict[str, Any]:
        """
        List messages matching query.

        Args:
            query: Gmail search query
            max_results: Maximum results to return (max 500 per call)
            page_token: Token for pagination
            label_ids: Optional label IDs to filter by

        Returns:
            API response with 'messages' and optionally 'nextPageToken'
        """
        await self._ensure_client()
        headers = await self._get_auth_headers()

        params: dict[str, Any] = {
            'maxResults': min(max_results, 500),
        }
        if query:
            params['q'] = query
        if page_token:
            params['pageToken'] = page_token
        if label_ids:
            params['labelIds'] = label_ids

        response = await self._client.get(
            f"{self.BASE_URL}/users/me/messages",
            headers=headers,
            params=params,
        )
        response.raise_for_status()
        return response.json()

    async def get_message(
        self,
        message_id: str,
        format: str = 'full',
        metadata_headers: list[str] | None = None,
    ) -> dict[str, Any]:
        """
        Get a single message by ID.

        Args:
            message_id: Gmail message ID
            format: Response format ('full', 'minimal', 'metadata', 'raw')
            metadata_headers: Headers to include when format='metadata'

        Returns:
            Message data
        """
        await self._ensure_client()
        headers = await self._get_auth_headers()

        params: dict[str, Any] = {'format': format}
        if metadata_headers and format == 'metadata':
            params['metadataHeaders'] = metadata_headers

        response = await self._client.get(
            f"{self.BASE_URL}/users/me/messages/{message_id}",
            headers=headers,
            params=params,
        )
        response.raise_for_status()
        return response.json()

    async def get_profile(self) -> dict[str, Any]:
        """
        Get the user's Gmail profile.

        Returns:
            Profile data including email address and message counts
        """
        await self._ensure_client()
        headers = await self._get_auth_headers()

        response = await self._client.get(
            f"{self.BASE_URL}/users/me/profile",
            headers=headers,
        )
        response.raise_for_status()
        return response.json()

    async def batch_get_messages(
        self,
        message_ids: list[str],
        format: str = 'full',
    ) -> list[dict[str, Any] | None]:
        """
        Get multiple messages concurrently.

        Args:
            message_ids: List of Gmail message IDs
            format: Response format

        Returns:
            List of message data (None for failed fetches)
        """
        import asyncio

        async def fetch_one(msg_id: str) -> dict[str, Any] | None:
            try:
                return await self.get_message(msg_id, format)
            except Exception as e:
                self.logger.warning(f"Failed to fetch {msg_id}: {e}")
                return None

        tasks = [fetch_one(mid) for mid in message_ids]
        return await asyncio.gather(*tasks)


def is_async_client_available() -> bool:
    """
    Check if the native async client is available.

    Returns:
        True if httpx is installed and AsyncGmailClient can be used
    """
    return _HTTPX_AVAILABLE


__all__ = ['AsyncGmailClient', 'is_async_client_available']
