"""
Tests for the Gmail Fetcher protocol definitions.

Tests the Protocol classes and type system utilities.
"""

import pytest
import sys
from typing import Dict, List, Optional, Any
from pathlib import Path

from gmail_assistant.core.protocols import (
    # Data Transfer Objects
    EmailMetadata,
    FetchResult,
    DeleteResult,
    ParseResult,
    # Protocols
    GmailClientProtocol,
    EmailFetcherProtocol,
    EmailDeleterProtocol,
    EmailParserProtocol,
    CacheProtocol,
    RateLimiterProtocol,
    OutputPluginProtocol,
    OrganizationPluginProtocol,
    # Utilities
    implements_protocol,
    assert_protocol,
)


class TestDataTransferObjects:
    """Tests for DTOs."""

    def test_email_metadata_creation(self):
        """Test EmailMetadata dataclass creation."""
        metadata = EmailMetadata(
            id="abc123",
            thread_id="thread123",
            subject="Test Subject",
            sender="test@example.com",
            recipients=["recipient@example.com"],
            date="2025-01-08",
            labels=["INBOX", "UNREAD"],
            snippet="Email preview...",
            size_estimate=1024
        )

        assert metadata.id == "abc123"
        assert metadata.thread_id == "thread123"
        assert metadata.subject == "Test Subject"
        assert metadata.sender == "test@example.com"
        assert "INBOX" in metadata.labels
        assert metadata.size_estimate == 1024

    def test_email_metadata_defaults(self):
        """Test EmailMetadata default values."""
        metadata = EmailMetadata(
            id="abc123",
            thread_id="thread123",
            subject="Test",
            sender="test@example.com",
            recipients=[],
            date="2025-01-08",
            labels=[]
        )

        assert metadata.snippet == ""
        assert metadata.size_estimate == 0

    def test_fetch_result_creation(self):
        """Test FetchResult dataclass creation."""
        result = FetchResult(
            success=True,
            emails_fetched=100,
            emails_failed=5,
            output_directory="/path/to/output"
        )

        assert result.success is True
        assert result.emails_fetched == 100
        assert result.emails_failed == 5
        assert result.error_message is None

    def test_fetch_result_with_error(self):
        """Test FetchResult with error message."""
        result = FetchResult(
            success=False,
            emails_fetched=0,
            emails_failed=0,
            output_directory="/path",
            error_message="Authentication failed"
        )

        assert result.success is False
        assert result.error_message == "Authentication failed"

    def test_delete_result_creation(self):
        """Test DeleteResult dataclass creation."""
        result = DeleteResult(
            deleted=50,
            failed=2,
            trashed=10
        )

        assert result.deleted == 50
        assert result.failed == 2
        assert result.trashed == 10
        assert result.error_messages == []

    def test_delete_result_post_init(self):
        """Test DeleteResult error_messages initialization."""
        result = DeleteResult(deleted=10, failed=0)
        assert result.error_messages == []

    def test_parse_result_creation(self):
        """Test ParseResult dataclass creation."""
        result = ParseResult(
            success=True,
            markdown="# Test Email\n\nContent here.",
            strategy="smart",
            quality=0.95
        )

        assert result.success is True
        assert "# Test Email" in result.markdown
        assert result.strategy == "smart"
        assert result.quality == 0.95
        assert result.metadata == {}


class TestProtocolImplementation:
    """Tests for protocol implementations."""

    def test_gmail_client_protocol_implementation(self):
        """Test that a class can implement GmailClientProtocol."""

        class MockGmailClient:
            def __init__(self):
                self._authenticated = False
                self._service = None

            def authenticate(self) -> bool:
                self._authenticated = True
                return True

            def get_service(self) -> Any:
                return self._service

            @property
            def is_authenticated(self) -> bool:
                return self._authenticated

            def get_user_info(self) -> Optional[Dict[str, Any]]:
                return {"email": "test@example.com"}

        client = MockGmailClient()
        assert implements_protocol(client, GmailClientProtocol)

    def test_email_fetcher_protocol_implementation(self):
        """Test that a class can implement EmailFetcherProtocol."""

        class MockFetcher:
            def search_messages(self, query: str, max_results: int = 100) -> List[str]:
                return ["msg1", "msg2"]

            def get_message(self, message_id: str, format: str = "full") -> Optional[Dict[str, Any]]:
                return {"id": message_id}

            def get_message_metadata(self, message_id: str) -> Optional[EmailMetadata]:
                return None

            def download_emails(
                self, query: str, max_emails: int = 100,
                output_dir: str = "backup", format_type: str = "both",
                organize_by: str = "date"
            ) -> FetchResult:
                return FetchResult(True, 10, 0, output_dir)

            def get_profile(self) -> Optional[Dict[str, Any]]:
                return {"email": "test@example.com"}

        fetcher = MockFetcher()
        assert implements_protocol(fetcher, EmailFetcherProtocol)

    def test_cache_protocol_implementation(self):
        """Test that a class can implement CacheProtocol."""

        class MockCache:
            def __init__(self):
                self._data: Dict[str, Any] = {}

            def get(self, key: str, default: Any = None) -> Any:
                return self._data.get(key, default)

            def put(self, key: str, value: Any, ttl: Optional[int] = None) -> bool:
                self._data[key] = value
                return True

            def invalidate(self, key: str) -> bool:
                if key in self._data:
                    del self._data[key]
                    return True
                return False

            def clear(self) -> None:
                self._data.clear()

        cache = MockCache()
        assert implements_protocol(cache, CacheProtocol)

        # Test functionality
        cache.put("test_key", "test_value")
        assert cache.get("test_key") == "test_value"
        cache.invalidate("test_key")
        assert cache.get("test_key") is None

    def test_output_plugin_protocol_implementation(self):
        """Test that a class can implement OutputPluginProtocol."""

        class MockOutputPlugin:
            @property
            def name(self) -> str:
                return "mock"

            @property
            def extension(self) -> str:
                return ".mock"

            def generate(self, email_data: Dict[str, Any]) -> str:
                return f"Mock output for {email_data.get('id', 'unknown')}"

            def save(self, content: str, path: Path) -> bool:
                return True

        plugin = MockOutputPlugin()
        assert implements_protocol(plugin, OutputPluginProtocol)


class TestProtocolUtilities:
    """Tests for protocol utility functions."""

    def test_implements_protocol_positive(self):
        """Test implements_protocol returns True for valid implementation."""

        class ValidClient:
            def authenticate(self) -> bool:
                return True

            def get_service(self) -> Any:
                return None

            @property
            def is_authenticated(self) -> bool:
                return True

            def get_user_info(self) -> Optional[Dict[str, Any]]:
                return None

        assert implements_protocol(ValidClient(), GmailClientProtocol)

    def test_implements_protocol_negative(self):
        """Test implements_protocol returns False for invalid implementation."""

        class InvalidClient:
            def some_method(self):
                pass

        # Should return False because missing required methods
        # Note: runtime_checkable protocols check method presence
        assert not implements_protocol(InvalidClient(), GmailClientProtocol)

    def test_assert_protocol_success(self):
        """Test assert_protocol does not raise for valid implementation."""

        class ValidClient:
            def authenticate(self) -> bool:
                return True

            def get_service(self) -> Any:
                return None

            @property
            def is_authenticated(self) -> bool:
                return True

            def get_user_info(self) -> Optional[Dict[str, Any]]:
                return None

        # Should not raise
        assert_protocol(ValidClient(), GmailClientProtocol)

    def test_assert_protocol_failure(self):
        """Test assert_protocol raises TypeError for invalid implementation."""

        class InvalidClient:
            pass

        with pytest.raises(TypeError) as exc_info:
            assert_protocol(InvalidClient(), GmailClientProtocol, "test_client")

        assert "must implement" in str(exc_info.value)
        assert "GmailClientProtocol" in str(exc_info.value)


class TestRateLimiterProtocol:
    """Tests for RateLimiterProtocol."""

    def test_rate_limiter_implementation(self):
        """Test RateLimiterProtocol implementation."""

        class MockRateLimiter:
            def __init__(self):
                self._calls = 0

            def wait_if_needed(self, quota_cost: int = 1) -> float:
                self._calls += 1
                return 0.0

            def check_quota(self) -> Dict[str, Any]:
                return {"remaining": 100, "limit": 1000}

            def reset(self) -> None:
                self._calls = 0

        limiter = MockRateLimiter()
        assert implements_protocol(limiter, RateLimiterProtocol)

        # Test functionality
        wait_time = limiter.wait_if_needed(1)
        assert wait_time == 0.0
        assert limiter._calls == 1

        quota = limiter.check_quota()
        assert "remaining" in quota


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
