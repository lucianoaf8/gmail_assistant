"""
Comprehensive tests for streaming.py module.
Tests StreamingGmailFetcher class for memory-optimized operations.
"""

import tempfile
from pathlib import Path
from unittest import mock

import pytest


class TestStreamingGmailFetcherInit:
    """Tests for StreamingGmailFetcher initialization."""

    def test_init_default_values(self):
        """Test initialization with default values."""
        with mock.patch('gmail_assistant.core.fetch.streaming.SecureCredentialManager'):
            with mock.patch('gmail_assistant.core.fetch.streaming.MemoryTracker'):
                with mock.patch('gmail_assistant.core.fetch.streaming.StreamingEmailProcessor'):
                    with mock.patch('gmail_assistant.core.fetch.streaming.ProgressiveLoader'):
                        from gmail_assistant.core.fetch.streaming import StreamingGmailFetcher

                        fetcher = StreamingGmailFetcher()
                        assert fetcher.batch_size == 100

    def test_init_custom_batch_size(self):
        """Test initialization with custom batch size."""
        with mock.patch('gmail_assistant.core.fetch.streaming.SecureCredentialManager'):
            with mock.patch('gmail_assistant.core.fetch.streaming.MemoryTracker'):
                with mock.patch('gmail_assistant.core.fetch.streaming.StreamingEmailProcessor'):
                    with mock.patch('gmail_assistant.core.fetch.streaming.ProgressiveLoader'):
                        from gmail_assistant.core.fetch.streaming import StreamingGmailFetcher

                        fetcher = StreamingGmailFetcher(batch_size=50)
                        assert fetcher.batch_size == 50


class TestServiceProperty:
    """Tests for service property."""

    def test_service_property_delegates_to_credential_manager(self):
        """Test service property gets service from credential manager."""
        with mock.patch('gmail_assistant.core.fetch.streaming.SecureCredentialManager') as MockCM:
            with mock.patch('gmail_assistant.core.fetch.streaming.MemoryTracker'):
                with mock.patch('gmail_assistant.core.fetch.streaming.StreamingEmailProcessor'):
                    with mock.patch('gmail_assistant.core.fetch.streaming.ProgressiveLoader'):
                        mock_cm = mock.MagicMock()
                        mock_cm.get_service.return_value = "mock_service"
                        MockCM.return_value = mock_cm

                        from gmail_assistant.core.fetch.streaming import StreamingGmailFetcher

                        fetcher = StreamingGmailFetcher()
                        service = fetcher.service
                        assert service == "mock_service"


class TestFetchEmailIdsStreaming:
    """Tests for fetch_email_ids_streaming method."""

    def test_fetch_email_ids_no_service_raises(self):
        """Test fetch raises when service not available."""
        with mock.patch('gmail_assistant.core.fetch.streaming.SecureCredentialManager') as MockCM:
            with mock.patch('gmail_assistant.core.fetch.streaming.MemoryTracker'):
                with mock.patch('gmail_assistant.core.fetch.streaming.StreamingEmailProcessor'):
                    with mock.patch('gmail_assistant.core.fetch.streaming.ProgressiveLoader'):
                        mock_cm = mock.MagicMock()
                        mock_cm.get_service.return_value = None
                        MockCM.return_value = mock_cm

                        from gmail_assistant.core.fetch.streaming import StreamingGmailFetcher

                        fetcher = StreamingGmailFetcher()

                        with pytest.raises(RuntimeError, match="Gmail service not available"):
                            list(fetcher.fetch_email_ids_streaming("is:unread"))

    def test_fetch_email_ids_yields_ids(self):
        """Test fetch yields message IDs."""
        with mock.patch('gmail_assistant.core.fetch.streaming.SecureCredentialManager') as MockCM:
            with mock.patch('gmail_assistant.core.fetch.streaming.MemoryTracker') as MockMT:
                with mock.patch('gmail_assistant.core.fetch.streaming.StreamingEmailProcessor'):
                    with mock.patch('gmail_assistant.core.fetch.streaming.ProgressiveLoader'):
                        mock_cm = mock.MagicMock()
                        mock_service = mock.MagicMock()

                        # Mock API response
                        mock_service.users().messages().list().execute.return_value = {
                            'messages': [{'id': 'msg1'}, {'id': 'msg2'}],
                            'nextPageToken': None
                        }
                        mock_cm.get_service.return_value = mock_service
                        MockCM.return_value = mock_cm

                        mock_mt_instance = mock.MagicMock()
                        mock_mt_instance.check_memory.return_value = {'status': 'ok'}
                        MockMT.return_value = mock_mt_instance

                        from gmail_assistant.core.fetch.streaming import StreamingGmailFetcher

                        fetcher = StreamingGmailFetcher()
                        ids = list(fetcher.fetch_email_ids_streaming("is:unread", max_results=10))

                        assert 'msg1' in ids
                        assert 'msg2' in ids


class TestFetchEmailStreaming:
    """Tests for fetch_email_streaming method."""

    def test_fetch_email_no_service_returns_none(self):
        """Test fetch returns None when service not available."""
        with mock.patch('gmail_assistant.core.fetch.streaming.SecureCredentialManager') as MockCM:
            with mock.patch('gmail_assistant.core.fetch.streaming.MemoryTracker'):
                with mock.patch('gmail_assistant.core.fetch.streaming.StreamingEmailProcessor'):
                    with mock.patch('gmail_assistant.core.fetch.streaming.ProgressiveLoader'):
                        mock_cm = mock.MagicMock()
                        mock_cm.get_service.return_value = None
                        MockCM.return_value = mock_cm

                        from gmail_assistant.core.fetch.streaming import StreamingGmailFetcher

                        fetcher = StreamingGmailFetcher()
                        result = fetcher.fetch_email_streaming("msg123")
                        assert result is None

    def test_fetch_email_returns_essential_data(self):
        """Test fetch returns essential email data."""
        with mock.patch('gmail_assistant.core.fetch.streaming.SecureCredentialManager') as MockCM:
            with mock.patch('gmail_assistant.core.fetch.streaming.MemoryTracker'):
                with mock.patch('gmail_assistant.core.fetch.streaming.StreamingEmailProcessor'):
                    with mock.patch('gmail_assistant.core.fetch.streaming.ProgressiveLoader'):
                        mock_cm = mock.MagicMock()
                        mock_service = mock.MagicMock()

                        mock_message = {
                            'id': 'msg123',
                            'threadId': 'thread123',
                            'labelIds': ['INBOX'],
                            'snippet': 'Test snippet',
                            'payload': {'headers': []},
                            'internalDate': '1234567890',
                            'historyId': '12345'
                        }
                        mock_service.users().messages().get().execute.return_value = mock_message
                        mock_cm.get_service.return_value = mock_service
                        MockCM.return_value = mock_cm

                        from gmail_assistant.core.fetch.streaming import StreamingGmailFetcher

                        fetcher = StreamingGmailFetcher()
                        result = fetcher.fetch_email_streaming("msg123")

                        assert result['id'] == 'msg123'
                        assert result['threadId'] == 'thread123'
                        assert 'INBOX' in result['labelIds']

    def test_fetch_email_handles_exception(self):
        """Test fetch handles exceptions gracefully."""
        with mock.patch('gmail_assistant.core.fetch.streaming.SecureCredentialManager') as MockCM:
            with mock.patch('gmail_assistant.core.fetch.streaming.MemoryTracker'):
                with mock.patch('gmail_assistant.core.fetch.streaming.StreamingEmailProcessor'):
                    with mock.patch('gmail_assistant.core.fetch.streaming.ProgressiveLoader'):
                        mock_cm = mock.MagicMock()
                        mock_service = mock.MagicMock()

                        mock_service.users().messages().get().execute.side_effect = Exception("API Error")
                        mock_cm.get_service.return_value = mock_service
                        MockCM.return_value = mock_cm

                        from gmail_assistant.core.fetch.streaming import StreamingGmailFetcher

                        fetcher = StreamingGmailFetcher()
                        result = fetcher.fetch_email_streaming("msg123")
                        assert result is None


class TestMemoryStats:
    """Tests for memory stats methods."""

    def test_get_memory_stats(self):
        """Test get_memory_stats returns memory info."""
        with mock.patch('gmail_assistant.core.fetch.streaming.SecureCredentialManager'):
            with mock.patch('gmail_assistant.core.fetch.streaming.MemoryTracker') as MockMT:
                with mock.patch('gmail_assistant.core.fetch.streaming.StreamingEmailProcessor'):
                    with mock.patch('gmail_assistant.core.fetch.streaming.ProgressiveLoader'):
                        mock_mt = mock.MagicMock()
                        mock_mt.check_memory.return_value = {'current_mb': 150, 'status': 'ok'}
                        MockMT.return_value = mock_mt

                        from gmail_assistant.core.fetch.streaming import StreamingGmailFetcher

                        fetcher = StreamingGmailFetcher()
                        stats = fetcher.get_memory_stats()

                        assert stats['current_mb'] == 150
                        assert stats['status'] == 'ok'

    def test_cleanup_memory(self):
        """Test cleanup_memory calls force_gc."""
        with mock.patch('gmail_assistant.core.fetch.streaming.SecureCredentialManager'):
            with mock.patch('gmail_assistant.core.fetch.streaming.MemoryTracker') as MockMT:
                with mock.patch('gmail_assistant.core.fetch.streaming.StreamingEmailProcessor'):
                    with mock.patch('gmail_assistant.core.fetch.streaming.ProgressiveLoader'):
                        mock_mt = mock.MagicMock()
                        mock_mt.force_gc.return_value = 1024
                        MockMT.return_value = mock_mt

                        from gmail_assistant.core.fetch.streaming import StreamingGmailFetcher

                        fetcher = StreamingGmailFetcher()
                        freed = fetcher.cleanup_memory()

                        mock_mt.force_gc.assert_called_once()
                        assert freed == 1024


class TestProcessEmailsStreaming:
    """Tests for process_emails_streaming method."""

    def test_process_emails_creates_output_dir(self):
        """Test process_emails creates output directory."""
        with mock.patch('gmail_assistant.core.fetch.streaming.SecureCredentialManager') as MockCM:
            with mock.patch('gmail_assistant.core.fetch.streaming.MemoryTracker'):
                with mock.patch('gmail_assistant.core.fetch.streaming.StreamingEmailProcessor'):
                    with mock.patch('gmail_assistant.core.fetch.streaming.ProgressiveLoader'):
                        mock_cm = mock.MagicMock()
                        mock_service = mock.MagicMock()
                        mock_service.users().messages().list().execute.return_value = {
                            'messages': [],
                            'nextPageToken': None
                        }
                        mock_cm.get_service.return_value = mock_service
                        MockCM.return_value = mock_cm

                        from gmail_assistant.core.fetch.streaming import StreamingGmailFetcher

                        fetcher = StreamingGmailFetcher()

                        with tempfile.TemporaryDirectory() as tmpdir:
                            output_dir = Path(tmpdir) / "test_output"
                            list(fetcher.process_emails_streaming("is:unread", output_dir=str(output_dir)))
                            assert output_dir.exists()

    def test_process_emails_returns_empty_when_no_emails(self):
        """Test process_emails returns empty when no emails found."""
        with mock.patch('gmail_assistant.core.fetch.streaming.SecureCredentialManager') as MockCM:
            with mock.patch('gmail_assistant.core.fetch.streaming.MemoryTracker'):
                with mock.patch('gmail_assistant.core.fetch.streaming.StreamingEmailProcessor'):
                    with mock.patch('gmail_assistant.core.fetch.streaming.ProgressiveLoader'):
                        mock_cm = mock.MagicMock()
                        mock_service = mock.MagicMock()
                        mock_service.users().messages().list().execute.return_value = {
                            'messages': [],
                            'nextPageToken': None
                        }
                        mock_cm.get_service.return_value = mock_service
                        MockCM.return_value = mock_cm

                        from gmail_assistant.core.fetch.streaming import StreamingGmailFetcher

                        fetcher = StreamingGmailFetcher()

                        with tempfile.TemporaryDirectory() as tmpdir:
                            results = list(fetcher.process_emails_streaming("is:unread", output_dir=tmpdir))
                            assert results == []


class TestSaveEmailStreaming:
    """Tests for _save_email_streaming method."""

    def test_save_email_handles_exception(self):
        """Test save handles exception gracefully."""
        with mock.patch('gmail_assistant.core.fetch.streaming.SecureCredentialManager'):
            with mock.patch('gmail_assistant.core.fetch.streaming.MemoryTracker'):
                with mock.patch('gmail_assistant.core.fetch.streaming.StreamingEmailProcessor'):
                    with mock.patch('gmail_assistant.core.fetch.streaming.ProgressiveLoader'):
                        from gmail_assistant.core.fetch.streaming import StreamingGmailFetcher

                        fetcher = StreamingGmailFetcher()

                        with tempfile.TemporaryDirectory() as tmpdir:
                            # Test with minimal valid data structure
                            email_data = {
                                'id': 'test',
                                'payload': {'headers': []}
                            }
                            # The _save_email_streaming method catches exceptions and returns False
                            result = fetcher._save_email_streaming(
                                email_data, Path(tmpdir), 'eml'
                            )
                            # Should return False since data is incomplete/invalid
                            assert result is False
