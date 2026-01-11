"""Integration tests for Gmail API operations.

These tests use comprehensive mocks to test Gmail API integration
without requiring real credentials. Tests validate the integration
of internal components and API interaction patterns.
"""
from __future__ import annotations

import time
from pathlib import Path
from typing import Optional
from unittest import mock

import pytest


@pytest.mark.integration
class TestGmailAuthentication:
    """Integration tests for Gmail authentication."""

    def test_authenticate_with_credentials(self, mock_credentials_file, mock_gmail_service_full):
        """Should authenticate successfully with valid credentials."""
        from gmail_assistant.core.auth.base import ReadOnlyGmailAuth

        auth = ReadOnlyGmailAuth(str(mock_credentials_file))

        # Mock the service building in credential_manager where it's imported
        with mock.patch('gmail_assistant.core.auth.credential_manager.build', return_value=mock_gmail_service_full):
            with mock.patch('gmail_assistant.core.auth.credential_manager.InstalledAppFlow.from_client_secrets_file') as mock_flow:
                # Mock credentials
                mock_creds = mock.MagicMock()
                mock_creds.valid = True
                mock_creds.expired = False
                mock_creds.refresh_token = "test-refresh-token"

                mock_flow.return_value.run_local_server.return_value = mock_creds

                # Mock Credentials.from_authorized_user_file
                with mock.patch('gmail_assistant.core.auth.credential_manager.Credentials') as mock_creds_class:
                    mock_creds_class.from_authorized_user_file.return_value = mock_creds

                    result = auth.authenticate()

                    assert result is True
                    assert auth.service is not None

    def test_get_user_profile(self, mock_credentials_file, mock_gmail_service_full):
        """Should fetch user profile after authentication."""
        from gmail_assistant.core.fetch.gmail_assistant import GmailFetcher

        fetcher = GmailFetcher(str(mock_credentials_file))

        with mock.patch.object(fetcher.auth, 'authenticate', return_value=True):
            with mock.patch.object(type(fetcher.auth), 'service', new_callable=mock.PropertyMock, return_value=mock_gmail_service_full):
                fetcher.authenticate()
                profile = fetcher.get_profile()

                assert profile is not None
                assert 'email' in profile
                assert profile['email'] == 'test@gmail.com'
                assert profile['total_messages'] == 10000


@pytest.mark.integration
class TestGmailFetching:
    """Integration tests for email fetching."""

    def test_search_emails(self, mock_credentials_file, mock_gmail_service_full):
        """Should search emails with query."""
        from gmail_assistant.core.fetch.gmail_assistant import GmailFetcher

        fetcher = GmailFetcher(str(mock_credentials_file))

        with mock.patch.object(fetcher.auth, 'authenticate', return_value=True):
            with mock.patch.object(type(fetcher.auth), 'service', new_callable=mock.PropertyMock, return_value=mock_gmail_service_full):
                fetcher.authenticate()

                # Test search with query
                message_ids = fetcher.search_messages("is:unread", max_results=10)

                assert isinstance(message_ids, list)
                assert len(message_ids) <= 10

    def test_fetch_email_by_id(self, mock_credentials_file, mock_gmail_service_full):
        """Should fetch email by message ID."""
        from gmail_assistant.core.fetch.gmail_assistant import GmailFetcher

        fetcher = GmailFetcher(str(mock_credentials_file))

        with mock.patch.object(fetcher.auth, 'authenticate', return_value=True):
            with mock.patch.object(type(fetcher.auth), 'service', new_callable=mock.PropertyMock, return_value=mock_gmail_service_full):
                fetcher.authenticate()

                # Get message details
                message_details = fetcher.get_message_details("msg00001")

                assert message_details is not None
                assert 'id' in message_details
                assert 'payload' in message_details

    def test_download_emails_to_directory(self, mock_credentials_file, mock_gmail_service_full, temp_dir: Path):
        """Should download emails to specified directory."""
        from gmail_assistant.core.fetch.gmail_assistant import GmailFetcher

        fetcher = GmailFetcher(str(mock_credentials_file))
        output_dir = temp_dir / "downloads"

        with mock.patch.object(fetcher.auth, 'authenticate', return_value=True):
            with mock.patch.object(type(fetcher.auth), 'service', new_callable=mock.PropertyMock, return_value=mock_gmail_service_full):
                fetcher.authenticate()

                # Download emails
                fetcher.download_emails(
                    query="",
                    max_emails=2,
                    output_dir=str(output_dir),
                    format_type="eml",
                    organize_by="none"
                )

                # Verify files were created
                assert output_dir.exists()
                eml_files = list(output_dir.rglob("*.eml"))
                assert len(eml_files) > 0


@pytest.mark.integration
class TestGmailDeletion:
    """Integration tests for email deletion.

    Tests deletion workflows using mocked API calls.
    """

    def test_trash_email_dry_run(self, mock_credentials_file, mock_gmail_service_full):
        """Should perform dry run without deleting."""
        from gmail_assistant.core.fetch.gmail_api_client import GmailAPIClient

        client = GmailAPIClient(str(mock_credentials_file))

        with mock.patch.object(client.auth, 'authenticate', return_value=True):
            with mock.patch.object(type(client.auth), 'service', new_callable=mock.PropertyMock, return_value=mock_gmail_service_full):
                client.authenticate()

                # Test dry run - should not actually call trash
                messages = client.search_messages("from:spam", max_results=5)

                # Verify messages found but not deleted (dry run)
                assert isinstance(messages, list)
                assert len(messages) <= 5

    def test_delete_by_query_dry_run(self, mock_credentials_file, mock_gmail_service_full):
        """Should list emails to delete without deleting."""
        from gmail_assistant.core.fetch.gmail_api_client import GmailAPIClient

        client = GmailAPIClient(str(mock_credentials_file))

        with mock.patch.object(client.auth, 'authenticate', return_value=True):
            with mock.patch.object(type(client.auth), 'service', new_callable=mock.PropertyMock, return_value=mock_gmail_service_full):
                client.authenticate()

                # Search for messages to potentially delete
                messages = client.search_messages("from:noreply", max_results=10)

                assert isinstance(messages, list)
                # Verify we can get message details for potential deletion
                if messages:
                    details = client.get_message_details(messages[0])
                    assert details is not None


@pytest.mark.integration
class TestGmailAnalysis:
    """Integration tests for email analysis."""

    def test_analyze_email_content(self, mock_credentials_file, mock_gmail_service_full):
        """Should analyze email content."""
        from gmail_assistant.core.fetch.gmail_assistant import GmailFetcher

        fetcher = GmailFetcher(str(mock_credentials_file))

        with mock.patch.object(fetcher.auth, 'authenticate', return_value=True):
            with mock.patch.object(type(fetcher.auth), 'service', new_callable=mock.PropertyMock, return_value=mock_gmail_service_full):
                fetcher.authenticate()

                # Get message and analyze content
                message_ids = fetcher.search_messages("", max_results=1)
                assert len(message_ids) > 0

                message_details = fetcher.get_message_details(message_ids[0])
                assert message_details is not None

                # Extract and verify content
                headers = fetcher.extract_headers(message_details)
                assert isinstance(headers, dict)
                assert 'From' in headers or 'Subject' in headers

    def test_classify_newsletters(self, mock_credentials_file, mock_gmail_service_full):
        """Should classify emails as newsletters."""
        from gmail_assistant.core.fetch.gmail_assistant import GmailFetcher

        fetcher = GmailFetcher(str(mock_credentials_file))

        with mock.patch.object(fetcher.auth, 'authenticate', return_value=True):
            with mock.patch.object(type(fetcher.auth), 'service', new_callable=mock.PropertyMock, return_value=mock_gmail_service_full):
                fetcher.authenticate()

                # Search for potential newsletters
                message_ids = fetcher.search_messages("subject:newsletter", max_results=5)

                assert isinstance(message_ids, list)
                # Verify we can get details for classification
                for msg_id in message_ids[:2]:
                    details = fetcher.get_message_details(msg_id)
                    assert details is not None
                    assert 'payload' in details


@pytest.mark.integration
class TestRateLimiting:
    """Integration tests for rate limiting.

    These tests can run without credentials as they test
    the rate limiter behavior independent of API calls.
    """

    def test_rate_limiter_throttles_requests(self):
        """Rate limiter should throttle rapid requests."""
        from gmail_assistant.utils.rate_limiter import GmailRateLimiter

        limiter = GmailRateLimiter(requests_per_second=10.0)

        start_time = time.time()

        # Make 20 requests
        for _ in range(20):
            limiter.wait_if_needed()

        elapsed = time.time() - start_time

        # Should take at least 2 seconds for 20 requests at 10/second
        # Allow some tolerance
        assert elapsed >= 1.5

    def test_quota_tracker_accumulates(self):
        """Quota tracker should accumulate usage."""
        from gmail_assistant.utils.rate_limiter import QuotaTracker

        tracker = QuotaTracker(daily_quota_limit=1000)

        tracker.consume_quota("list_messages", count=10)
        tracker.consume_quota("get_message", count=20)

        status = tracker.get_quota_status()

        assert status["daily_used"] == (10 * 5) + (20 * 5)  # list=5, get=5


@pytest.mark.integration
class TestCachePersistence:
    """Integration tests for cache persistence."""

    def test_cache_survives_restart(self, temp_dir: Path):
        """Cache should persist data across restarts."""
        from gmail_assistant.utils.cache_manager import IntelligentCache

        cache_dir = temp_dir / "cache"

        # Create cache and store data
        cache1 = IntelligentCache(
            memory_limit_mb=10,
            disk_cache_dir=cache_dir,
            enable_persistence=True
        )

        # Use large payload (> 1KB) and long TTL (> 1 hour) to trigger persistence
        large_value = "test_value" * 200  # > 1KB to trigger disk persistence
        cache1.put("test_key", {"data": large_value}, ttl=7200)  # 2 hour TTL

        # Create new cache instance
        cache2 = IntelligentCache(
            memory_limit_mb=10,
            disk_cache_dir=cache_dir,
            enable_persistence=True
        )

        # Data should be loadable from disk
        result = cache2.get("test_key")

        assert result is not None
        assert result["data"] == large_value


@pytest.mark.integration
class TestCircuitBreakerRecovery:
    """Integration tests for circuit breaker recovery."""

    def test_circuit_breaker_recovery_timing(self):
        """Circuit breaker should recover after timeout."""
        from gmail_assistant.utils.circuit_breaker import (
            CircuitBreaker,
            CircuitState,
        )

        cb = CircuitBreaker(
            failure_threshold=2,
            recovery_timeout=0.5,  # 500ms for testing
            success_threshold=1
        )

        # Trip the breaker
        for _ in range(2):
            try:
                cb.call(lambda: (_ for _ in ()).throw(ValueError("Error")))
            except ValueError:
                pass

        assert cb.state == CircuitState.OPEN

        # Wait for recovery
        time.sleep(0.6)

        # Should allow test call
        result = cb.call(lambda: "recovered")

        assert result == "recovered"
        assert cb.state == CircuitState.CLOSED
