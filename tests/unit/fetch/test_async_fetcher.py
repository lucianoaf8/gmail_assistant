"""
Comprehensive tests for async_fetcher.py module.
Tests AsyncGmailFetcher class for asynchronous operations.
"""

import asyncio
from unittest import mock

import pytest


class TestAsyncGmailFetcherInit:
    """Tests for AsyncGmailFetcher initialization."""

    def test_init_default_values(self):
        """Test initialization with default values."""
        with mock.patch('gmail_assistant.core.fetch.async_fetcher.SecureCredentialManager'):
            with mock.patch('gmail_assistant.core.fetch.async_fetcher.GmailRateLimiter'):
                with mock.patch('gmail_assistant.core.fetch.async_fetcher.MemoryTracker'):
                    from gmail_assistant.core.fetch.async_fetcher import AsyncGmailFetcher

                    fetcher = AsyncGmailFetcher()
                    assert fetcher.max_concurrent == 10
                    assert fetcher.max_workers == 4

    def test_init_custom_values(self):
        """Test initialization with custom values."""
        with mock.patch('gmail_assistant.core.fetch.async_fetcher.SecureCredentialManager'):
            with mock.patch('gmail_assistant.core.fetch.async_fetcher.GmailRateLimiter'):
                with mock.patch('gmail_assistant.core.fetch.async_fetcher.MemoryTracker'):
                    from gmail_assistant.core.fetch.async_fetcher import AsyncGmailFetcher

                    fetcher = AsyncGmailFetcher(
                        credentials_file='custom_creds.json',
                        max_concurrent=20,
                        max_workers=8
                    )
                    assert fetcher.max_concurrent == 20
                    assert fetcher.max_workers == 8


class TestAsyncContextManager:
    """Tests for async context manager."""

    @pytest.mark.asyncio
    async def test_async_context_manager_enter(self):
        """Test async context manager enter."""
        with mock.patch('gmail_assistant.core.fetch.async_fetcher.SecureCredentialManager'):
            with mock.patch('gmail_assistant.core.fetch.async_fetcher.GmailRateLimiter'):
                with mock.patch('gmail_assistant.core.fetch.async_fetcher.MemoryTracker'):
                    from gmail_assistant.core.fetch.async_fetcher import AsyncGmailFetcher

                    fetcher = AsyncGmailFetcher()
                    result = await fetcher.__aenter__()
                    assert result == fetcher

    @pytest.mark.asyncio
    async def test_async_context_manager_exit(self):
        """Test async context manager exit shuts down executor."""
        with mock.patch('gmail_assistant.core.fetch.async_fetcher.SecureCredentialManager'):
            with mock.patch('gmail_assistant.core.fetch.async_fetcher.GmailRateLimiter'):
                with mock.patch('gmail_assistant.core.fetch.async_fetcher.MemoryTracker'):
                    from gmail_assistant.core.fetch.async_fetcher import AsyncGmailFetcher

                    fetcher = AsyncGmailFetcher()
                    await fetcher.__aenter__()

                    # Mock the executor
                    mock_executor = mock.MagicMock()
                    fetcher.executor = mock_executor

                    await fetcher.__aexit__(None, None, None)
                    mock_executor.shutdown.assert_called_once_with(wait=True)


class TestServiceProperty:
    """Tests for service property."""

    def test_service_property_delegates_to_credential_manager(self):
        """Test service property gets service from credential manager."""
        with mock.patch('gmail_assistant.core.fetch.async_fetcher.SecureCredentialManager') as MockCM:
            with mock.patch('gmail_assistant.core.fetch.async_fetcher.GmailRateLimiter'):
                with mock.patch('gmail_assistant.core.fetch.async_fetcher.MemoryTracker'):
                    mock_cm = mock.MagicMock()
                    mock_cm.get_service.return_value = "mock_service"
                    MockCM.return_value = mock_cm

                    from gmail_assistant.core.fetch.async_fetcher import AsyncGmailFetcher

                    fetcher = AsyncGmailFetcher()
                    service = fetcher.service
                    assert service == "mock_service"
                    mock_cm.get_service.assert_called_once()


class TestSyncApiCall:
    """Tests for _sync_api_call method."""

    def test_sync_api_call_uses_rate_limiter(self):
        """Test sync API call uses rate limiter."""
        with mock.patch('gmail_assistant.core.fetch.async_fetcher.SecureCredentialManager'):
            with mock.patch('gmail_assistant.core.fetch.async_fetcher.GmailRateLimiter') as MockRL:
                with mock.patch('gmail_assistant.core.fetch.async_fetcher.MemoryTracker'):
                    mock_rl = mock.MagicMock()
                    mock_rl.rate_limited_call.return_value = "result"
                    MockRL.return_value = mock_rl

                    from gmail_assistant.core.fetch.async_fetcher import AsyncGmailFetcher

                    fetcher = AsyncGmailFetcher()

                    def test_func(a, b):
                        return a + b

                    result = fetcher._sync_api_call(test_func, 1, b=2)
                    mock_rl.rate_limited_call.assert_called_once()


class TestFetchEmailIdsAsync:
    """Tests for fetch_email_ids_async method."""

    @pytest.mark.asyncio
    async def test_fetch_email_ids_no_service_raises(self):
        """Test fetch raises when service not available."""
        with mock.patch('gmail_assistant.core.fetch.async_fetcher.SecureCredentialManager') as MockCM:
            with mock.patch('gmail_assistant.core.fetch.async_fetcher.GmailRateLimiter'):
                with mock.patch('gmail_assistant.core.fetch.async_fetcher.MemoryTracker'):
                    mock_cm = mock.MagicMock()
                    mock_cm.get_service.return_value = None
                    MockCM.return_value = mock_cm

                    from gmail_assistant.core.fetch.async_fetcher import AsyncGmailFetcher

                    fetcher = AsyncGmailFetcher()

                    with pytest.raises(RuntimeError, match="Gmail service not available"):
                        await fetcher.fetch_email_ids_async("is:unread")


class TestFetchEmailAsync:
    """Tests for fetch_email_async method."""

    @pytest.mark.asyncio
    async def test_fetch_email_no_service_returns_none(self):
        """Test fetch returns None when service not available."""
        with mock.patch('gmail_assistant.core.fetch.async_fetcher.SecureCredentialManager') as MockCM:
            with mock.patch('gmail_assistant.core.fetch.async_fetcher.GmailRateLimiter'):
                with mock.patch('gmail_assistant.core.fetch.async_fetcher.MemoryTracker'):
                    mock_cm = mock.MagicMock()
                    mock_cm.get_service.return_value = None
                    MockCM.return_value = mock_cm

                    from gmail_assistant.core.fetch.async_fetcher import AsyncGmailFetcher

                    fetcher = AsyncGmailFetcher()
                    result = await fetcher.fetch_email_async("msg123")
                    assert result is None


class TestGetProfileAsync:
    """Tests for get_profile_async method."""

    @pytest.mark.asyncio
    async def test_get_profile_no_service_returns_none(self):
        """Test get profile returns None when service not available."""
        with mock.patch('gmail_assistant.core.fetch.async_fetcher.SecureCredentialManager') as MockCM:
            with mock.patch('gmail_assistant.core.fetch.async_fetcher.GmailRateLimiter'):
                with mock.patch('gmail_assistant.core.fetch.async_fetcher.MemoryTracker'):
                    mock_cm = mock.MagicMock()
                    mock_cm.get_service.return_value = None
                    MockCM.return_value = mock_cm

                    from gmail_assistant.core.fetch.async_fetcher import AsyncGmailFetcher

                    fetcher = AsyncGmailFetcher()
                    result = await fetcher.get_profile_async()
                    assert result is None


class TestPerformanceStats:
    """Tests for get_performance_stats method."""

    def test_get_performance_stats_returns_dict(self):
        """Test get_performance_stats returns dict with expected keys."""
        with mock.patch('gmail_assistant.core.fetch.async_fetcher.SecureCredentialManager'):
            with mock.patch('gmail_assistant.core.fetch.async_fetcher.GmailRateLimiter') as MockRL:
                with mock.patch('gmail_assistant.core.fetch.async_fetcher.MemoryTracker') as MockMT:
                    mock_rl = mock.MagicMock()
                    mock_rl.get_stats.return_value = {'calls': 100}
                    MockRL.return_value = mock_rl

                    mock_mt = mock.MagicMock()
                    mock_mt.check_memory.return_value = {'current_mb': 150}
                    MockMT.return_value = mock_mt

                    from gmail_assistant.core.fetch.async_fetcher import AsyncGmailFetcher

                    fetcher = AsyncGmailFetcher()
                    stats = fetcher.get_performance_stats()

                    assert 'memory' in stats
                    assert 'rate_limiting' in stats
                    assert 'concurrent_limit' in stats
                    assert 'thread_pool_workers' in stats


class TestFetchEmailsBatchAsync:
    """Tests for fetch_emails_batch_async method."""

    @pytest.mark.asyncio
    async def test_fetch_emails_batch_logs_info(self):
        """Test batch fetch logs info message."""
        with mock.patch('gmail_assistant.core.fetch.async_fetcher.SecureCredentialManager') as MockCM:
            with mock.patch('gmail_assistant.core.fetch.async_fetcher.GmailRateLimiter'):
                with mock.patch('gmail_assistant.core.fetch.async_fetcher.MemoryTracker') as MockMT:
                    mock_cm = mock.MagicMock()
                    mock_cm.get_service.return_value = None
                    MockCM.return_value = mock_cm

                    mock_mt = mock.MagicMock()
                    mock_mt.check_memory.return_value = {'status': 'ok', 'current_mb': 100}
                    MockMT.return_value = mock_mt

                    from gmail_assistant.core.fetch.async_fetcher import AsyncGmailFetcher

                    fetcher = AsyncGmailFetcher()

                    # Should return None for each ID since service is None
                    results = await fetcher.fetch_emails_batch_async(['id1', 'id2'])
                    assert len(results) == 2
                    assert all(r is None for r in results)


class TestSearchEmailsAsync:
    """Tests for search_emails_async method."""

    @pytest.mark.asyncio
    async def test_search_emails_returns_empty_when_no_ids(self):
        """Test search returns empty list when no IDs found."""
        with mock.patch('gmail_assistant.core.fetch.async_fetcher.SecureCredentialManager') as MockCM:
            with mock.patch('gmail_assistant.core.fetch.async_fetcher.GmailRateLimiter'):
                with mock.patch('gmail_assistant.core.fetch.async_fetcher.MemoryTracker'):
                    mock_cm = mock.MagicMock()
                    mock_cm.get_service.return_value = mock.MagicMock()
                    MockCM.return_value = mock_cm

                    from gmail_assistant.core.fetch.async_fetcher import AsyncGmailFetcher

                    fetcher = AsyncGmailFetcher()

                    # Mock fetch_email_ids_async to return empty
                    with mock.patch.object(fetcher, 'fetch_email_ids_async', return_value=[]):
                        results = await fetcher.search_emails_async("is:unread")
                        assert results == []
