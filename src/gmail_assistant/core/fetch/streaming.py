"""
Streaming Gmail fetcher with memory optimization.
Processes emails progressively to handle large datasets efficiently.
"""

import logging
from collections.abc import Iterator
from pathlib import Path
from typing import Any

from gmail_assistant.core.auth.credential_manager import SecureCredentialManager
from gmail_assistant.utils.memory_manager import (
    MemoryTracker,
    ProgressiveLoader,
    StreamingEmailProcessor,
)

logger = logging.getLogger(__name__)


class StreamingGmailFetcher:
    """Gmail fetcher optimized for large-scale operations with memory streaming."""

    def __init__(self, credentials_file: str = 'credentials.json', batch_size: int = 100):
        """
        Initialize streaming Gmail fetcher.

        Args:
            credentials_file: Path to OAuth credentials
            batch_size: Number of emails to process in each batch
        """
        self.credential_manager = SecureCredentialManager(credentials_file)
        self.memory_tracker = MemoryTracker()
        self.streaming_processor = StreamingEmailProcessor(chunk_size=batch_size)
        self.progressive_loader = ProgressiveLoader(batch_size=batch_size)
        self.batch_size = batch_size
        self.logger = logging.getLogger(__name__)

    @property
    def service(self):
        """Get Gmail service with authentication."""
        return self.credential_manager.get_service()

    def fetch_email_ids_streaming(self, query: str, max_results: int = 1000) -> Iterator[str]:
        """
        Fetch email IDs in streaming fashion.

        Args:
            query: Gmail search query
            max_results: Maximum number of emails to fetch

        Yields:
            Email IDs
        """
        service = self.service
        if not service:
            raise RuntimeError("Gmail service not available")

        next_page_token = None
        fetched_count = 0

        while fetched_count < max_results:
            # Calculate remaining emails for this request
            page_size = min(500, max_results - fetched_count)  # Gmail API limit is 500

            try:
                # Build request
                request_params = {
                    'userId': 'me',
                    'q': query,
                    'maxResults': page_size,
                    'fields': 'messages(id),nextPageToken'
                }

                if next_page_token:
                    request_params['pageToken'] = next_page_token

                # Execute request
                result = service.users().messages().list(**request_params).execute()

                # Process messages
                messages = result.get('messages', [])
                for message in messages:
                    yield message['id']
                    fetched_count += 1

                    if fetched_count >= max_results:
                        break

                # Check for next page
                next_page_token = result.get('nextPageToken')
                if not next_page_token:
                    break

                # Memory check after each page
                memory_status = self.memory_tracker.check_memory()
                if memory_status['status'] == 'critical':
                    self.logger.warning(f"High memory usage: {memory_status['current_mb']:.1f} MB")
                    self.memory_tracker.force_gc()

            except Exception as e:
                self.logger.error(f"Error fetching email IDs: {e}")
                break

        self.logger.info(f"Fetched {fetched_count} email IDs for query: {query}")

    def fetch_email_streaming(self, email_id: str) -> dict[str, Any] | None:
        """
        Fetch single email with memory optimization.

        Args:
            email_id: Email ID to fetch

        Returns:
            Email data or None if failed
        """
        service = self.service
        if not service:
            return None

        try:
            message = service.users().messages().get(
                userId='me',
                id=email_id,
                format='full'
            ).execute()

            # Extract essential data only to minimize memory usage
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

    def process_emails_streaming(self, query: str, max_results: int = 1000,
                                output_dir: str = 'gmail_backup',
                                format_type: str = 'eml') -> Iterator[dict[str, Any]]:
        """
        Process emails in streaming fashion.

        Args:
            query: Gmail search query
            max_results: Maximum number of emails to process
            output_dir: Output directory
            format_type: Output format ('eml', 'markdown', or 'both')

        Yields:
            Processing results for each email
        """
        output_path = Path(output_dir)
        output_path.mkdir(exist_ok=True)

        # Get email IDs streaming
        email_ids = list(self.fetch_email_ids_streaming(query, max_results))

        if not email_ids:
            self.logger.info("No emails found for query")
            return

        self.logger.info(f"Processing {len(email_ids)} emails in streaming mode")

        # Process emails progressively
        def fetch_email_func(email_id: str) -> dict[str, Any] | None:
            return self.fetch_email_streaming(email_id)

        # Use progressive loader to manage memory
        email_generator = self.progressive_loader.load_emails_progressive(
            email_ids, fetch_email_func
        )

        # Process each email with streaming processor
        def process_single_email(email_data: dict[str, Any]) -> dict[str, Any]:
            if not email_data:
                return {"error": "No email data", "success": False}

            try:
                result = self._save_email_streaming(email_data, output_path, format_type)
                return {
                    "email_id": email_data['id'],
                    "success": result,
                    "format": format_type
                }
            except Exception as e:
                self.logger.error(f"Error processing email {email_data.get('id')}: {e}")
                return {
                    "email_id": email_data.get('id'),
                    "success": False,
                    "error": str(e)
                }

        # Stream processing with memory management
        yield from self.streaming_processor.process_emails_streaming(
            email_generator, process_single_email
        )

    def _save_email_streaming(self, email_data: dict[str, Any], output_path: Path,
                             format_type: str) -> bool:
        """
        Save email using streaming to minimize memory usage.

        Args:
            email_data: Email data dictionary
            output_path: Output directory path
            format_type: Format to save ('eml', 'markdown', or 'both')

        Returns:
            True if saved successfully, False otherwise
        """
        from .gmail_assistant import GmailFetcher  # Import to reuse methods

        try:
            # Create temporary fetcher instance for utility methods
            temp_fetcher = GmailFetcher()

            # Extract headers and content
            headers = temp_fetcher.extract_headers(email_data['payload'].get('headers', []))
            _plain_text, _html_body = temp_fetcher.get_message_body(email_data['payload'])

            # Generate filename
            date_str = headers.get('date', 'Unknown Date')
            subject = headers.get('subject', 'No Subject')
            filename = temp_fetcher.sanitize_filename(f"{date_str}_{subject}_{email_data['id']}")

            # Save based on format
            success = True

            if format_type in ['eml', 'both']:
                eml_content = temp_fetcher.create_eml_content(email_data)
                eml_path = output_path / f"{filename}.eml"

                # Stream content to file to avoid memory issues
                from ..utils.memory_manager import EmailContentStreamer
                streamer = EmailContentStreamer()
                success &= streamer.stream_to_file(eml_content, eml_path)

            if format_type in ['markdown', 'both']:
                md_content = temp_fetcher.create_markdown_content(email_data)
                md_path = output_path / f"{filename}.md"

                # Stream content to file
                from ..utils.memory_manager import EmailContentStreamer
                streamer = EmailContentStreamer()
                success &= streamer.stream_to_file(md_content, md_path)

            return success

        except Exception as e:
            self.logger.error(f"Error saving email {email_data.get('id')}: {e}")
            return False

    def get_memory_stats(self) -> dict[str, Any]:
        """Get current memory usage statistics."""
        return self.memory_tracker.check_memory()

    def cleanup_memory(self) -> int:
        """Force memory cleanup and return freed bytes."""
        return self.memory_tracker.force_gc()
