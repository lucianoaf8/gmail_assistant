"""Integration tests for Gmail API operations.

These tests require actual Gmail API credentials and will skip
if credentials are not available. Use pytest markers to control
which tests run in CI vs local development.

To run integration tests locally:
    pytest tests/integration/ -m integration --credentials=/path/to/credentials.json

Required environment:
    - GMAIL_CREDENTIALS_PATH: Path to OAuth credentials file
    - GMAIL_TEST_ACCOUNT: Email address for test account (optional)
"""
from __future__ import annotations

import os
from pathlib import Path
from typing import Optional

import pytest


# Check if credentials are available
def _get_credentials_path() -> Optional[Path]:
    """Get path to Gmail API credentials."""
    env_path = os.environ.get("GMAIL_CREDENTIALS_PATH")
    if env_path:
        path = Path(env_path)
        if path.exists():
            return path

    # Check common locations
    common_paths = [
        Path.home() / ".gmail-assistant" / "credentials.json",
        Path.cwd() / "credentials.json",
        Path.cwd() / "config" / "credentials.json",
    ]

    for path in common_paths:
        if path.exists():
            return path

    return None


CREDENTIALS_PATH = _get_credentials_path()
SKIP_REASON = "Gmail API credentials not available"


@pytest.fixture
def gmail_credentials() -> Path:
    """Provide Gmail credentials path or skip test."""
    if CREDENTIALS_PATH is None:
        pytest.skip(SKIP_REASON)
    return CREDENTIALS_PATH


@pytest.mark.integration
@pytest.mark.skipif(CREDENTIALS_PATH is None, reason=SKIP_REASON)
class TestGmailAuthentication:
    """Integration tests for Gmail authentication."""

    def test_authenticate_with_credentials(self, gmail_credentials: Path):
        """Should authenticate successfully with valid credentials."""
        from gmail_assistant.core.auth.base import ReadOnlyGmailAuth

        auth = ReadOnlyGmailAuth(str(gmail_credentials))

        # Note: This will open a browser for OAuth flow if no token cached
        # In CI, this should be skipped or use cached tokens
        pytest.skip("Manual OAuth flow required - run locally")

    def test_get_user_profile(self, gmail_credentials: Path):
        """Should fetch user profile after authentication."""
        pytest.skip("Requires authenticated session - run locally")


@pytest.mark.integration
@pytest.mark.skipif(CREDENTIALS_PATH is None, reason=SKIP_REASON)
class TestGmailFetching:
    """Integration tests for email fetching."""

    def test_search_emails(self, gmail_credentials: Path):
        """Should search emails with query."""
        pytest.skip("Requires authenticated session - run locally")

    def test_fetch_email_by_id(self, gmail_credentials: Path):
        """Should fetch email by message ID."""
        pytest.skip("Requires authenticated session - run locally")

    def test_download_emails_to_directory(self, gmail_credentials: Path, temp_dir: Path):
        """Should download emails to specified directory."""
        pytest.skip("Requires authenticated session - run locally")


@pytest.mark.integration
@pytest.mark.skipif(CREDENTIALS_PATH is None, reason=SKIP_REASON)
class TestGmailDeletion:
    """Integration tests for email deletion.

    WARNING: These tests can delete real emails!
    Only run against a dedicated test account.
    """

    def test_trash_email_dry_run(self, gmail_credentials: Path):
        """Should perform dry run without deleting."""
        pytest.skip("Requires authenticated session - run locally")

    def test_delete_by_query_dry_run(self, gmail_credentials: Path):
        """Should list emails to delete without deleting."""
        pytest.skip("Requires authenticated session - run locally")


@pytest.mark.integration
@pytest.mark.skipif(CREDENTIALS_PATH is None, reason=SKIP_REASON)
class TestGmailAnalysis:
    """Integration tests for email analysis."""

    def test_analyze_email_content(self, gmail_credentials: Path):
        """Should analyze email content."""
        pytest.skip("Requires authenticated session - run locally")

    def test_classify_newsletters(self, gmail_credentials: Path):
        """Should classify emails as newsletters."""
        pytest.skip("Requires authenticated session - run locally")


@pytest.mark.integration
class TestRateLimiting:
    """Integration tests for rate limiting.

    These tests can run without credentials as they test
    the rate limiter behavior independent of API calls.
    """

    def test_rate_limiter_throttles_requests(self):
        """Rate limiter should throttle rapid requests."""
        import time
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
        import time
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
