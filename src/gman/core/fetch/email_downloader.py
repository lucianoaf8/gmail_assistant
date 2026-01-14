"""
Email content download functionality.

H-2 refactoring: Extracted from GmailFetcher to follow Single Responsibility Principle.
"""

from __future__ import annotations

import base64
import binascii
import logging
from typing import TYPE_CHECKING, Any

from googleapiclient.errors import HttpError

if TYPE_CHECKING:
    from googleapiclient.discovery import Resource

logger = logging.getLogger(__name__)


class EmailDownloader:
    """
    Downloads email content from Gmail API.

    Handles message fetching, content extraction, and metadata parsing.
    Extracted from GmailFetcher to follow Single Responsibility Principle.
    """

    def __init__(
        self,
        service: Resource,
        rate_limiter: Any | None = None,
    ) -> None:
        """
        Initialize downloader.

        Args:
            service: Authenticated Gmail API service
            rate_limiter: Optional rate limiter for API calls
        """
        self.service = service
        self.rate_limiter = rate_limiter
        self.logger = logger

    def download(self, message_id: str) -> dict[str, Any] | None:
        """
        Download a single email by ID.

        Args:
            message_id: Gmail message ID

        Returns:
            Parsed email data dict or None if download failed
        """
        try:
            if self.rate_limiter:
                self.rate_limiter.wait_if_needed()

            message = self.service.users().messages().get(
                userId='me',
                id=message_id,
                format='full'
            ).execute()

            return self._parse_message(message)

        except HttpError as e:
            self.logger.error(f"HTTP error downloading {message_id}: {e}")
            return None
        except Exception as e:
            self.logger.error(f"Error downloading {message_id}: {e}")
            return None

    def download_batch(
        self,
        message_ids: list[str],
        on_progress: Any | None = None,
    ) -> list[dict[str, Any] | None]:
        """
        Download multiple emails.

        Args:
            message_ids: List of Gmail message IDs
            on_progress: Optional callback(current, total) for progress

        Returns:
            List of parsed email data (None for failed downloads)
        """
        results: list[dict[str, Any] | None] = []

        for i, msg_id in enumerate(message_ids):
            email_data = self.download(msg_id)
            results.append(email_data)

            if on_progress:
                on_progress(i + 1, len(message_ids))

        return results

    def _parse_message(self, message: dict[str, Any]) -> dict[str, Any]:
        """
        Parse Gmail API message into structured format.

        Args:
            message: Raw Gmail API message response

        Returns:
            Structured email data dict
        """
        payload = message.get('payload', {})
        headers = self._extract_headers(payload.get('headers', []))
        plain_text, html_body = self._extract_body(payload)

        return {
            'id': message['id'],
            'threadId': message['threadId'],
            'labelIds': message.get('labelIds', []),
            'snippet': message.get('snippet', ''),
            'internalDate': message.get('internalDate'),
            'historyId': message.get('historyId'),
            'headers': headers,
            'subject': headers.get('subject', ''),
            'sender': headers.get('from', ''),
            'to': headers.get('to', ''),
            'date': headers.get('date', ''),
            'plain_text': plain_text,
            'html_body': html_body,
            'payload': payload,  # Keep raw payload for EML creation
        }

    def _extract_headers(self, headers: list[dict[str, str]]) -> dict[str, str]:
        """
        Extract important headers from email.

        Args:
            headers: List of header dicts from Gmail API

        Returns:
            Dict mapping lowercase header names to values
        """
        header_dict: dict[str, str] = {}
        for header in headers:
            name = header.get('name', '').lower()
            value = header.get('value', '')
            header_dict[name] = value
        return header_dict

    def _extract_body(self, payload: dict[str, Any]) -> tuple[str, str]:
        """
        Extract plain text and HTML body from message payload.

        Args:
            payload: Message payload from Gmail API

        Returns:
            Tuple of (plain_text, html_body)
        """
        plain_text = ''
        html_body = ''

        def extract_parts(part: dict[str, Any]) -> None:
            nonlocal plain_text, html_body

            if 'parts' in part:
                for subpart in part['parts']:
                    extract_parts(subpart)
            else:
                mime_type = part.get('mimeType', '')
                body_data = part.get('body', {}).get('data', '')

                if body_data:
                    decoded = self._decode_base64(body_data)

                    if mime_type == 'text/plain':
                        plain_text += decoded
                    elif mime_type == 'text/html':
                        html_body += decoded

        extract_parts(payload)
        return plain_text, html_body

    def _decode_base64(self, data: str) -> str:
        """
        Decode base64 email data with URL-safe encoding support.

        Args:
            data: Base64 encoded string (possibly URL-safe)

        Returns:
            Decoded UTF-8 string
        """
        try:
            # Handle URL-safe base64
            data = data.replace('-', '+').replace('_', '/')
            # Add padding if needed
            missing_padding = len(data) % 4
            if missing_padding:
                data += '=' * (4 - missing_padding)
            return base64.b64decode(data).decode('utf-8')
        except (ValueError, UnicodeDecodeError, binascii.Error) as e:
            self.logger.warning(f"Base64 decode error: {e}")
            return ''


__all__ = ['EmailDownloader']
