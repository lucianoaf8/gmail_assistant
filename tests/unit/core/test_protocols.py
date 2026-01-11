"""
Comprehensive tests for protocols.py module.
Tests protocol definitions, DTOs, and utility functions.
"""

import warnings
from dataclasses import FrozenInstanceError
from pathlib import Path
from unittest import mock

import pytest


class TestEmailMetadata:
    """Tests for EmailMetadata dataclass."""

    def test_email_metadata_creation(self):
        """Test creating EmailMetadata."""
        from gmail_assistant.core.protocols import EmailMetadata

        with warnings.catch_warnings(record=True) as w:
            warnings.simplefilter("always")
            metadata = EmailMetadata(
                id="msg123",
                thread_id="thread123",
                subject="Test Subject",
                sender="sender@example.com",
                recipients=["recipient@example.com"],
                date="2024-01-15",
                labels=["INBOX"]
            )

            assert metadata.id == "msg123"
            assert metadata.subject == "Test Subject"
            # Should emit deprecation warning
            assert len(w) >= 1

    def test_email_metadata_default_values(self):
        """Test EmailMetadata default values."""
        from gmail_assistant.core.protocols import EmailMetadata

        with warnings.catch_warnings():
            warnings.simplefilter("ignore")
            metadata = EmailMetadata(
                id="msg123",
                thread_id="thread123",
                subject="Test",
                sender="test@example.com",
                recipients=[],
                date="2024-01-15",
                labels=[]
            )

            assert metadata.snippet == ""
            assert metadata.size_estimate == 0


class TestFetchResult:
    """Tests for FetchResult dataclass."""

    def test_fetch_result_success(self):
        """Test creating successful FetchResult."""
        from gmail_assistant.core.protocols import FetchResult

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

    def test_fetch_result_failure(self):
        """Test creating failed FetchResult."""
        from gmail_assistant.core.protocols import FetchResult

        result = FetchResult(
            success=False,
            emails_fetched=0,
            emails_failed=0,
            output_directory="",
            error_message="Authentication failed"
        )

        assert result.success is False
        assert result.error_message == "Authentication failed"


class TestDeleteResult:
    """Tests for DeleteResult dataclass."""

    def test_delete_result_creation(self):
        """Test creating DeleteResult."""
        from gmail_assistant.core.protocols import DeleteResult

        result = DeleteResult(
            deleted=50,
            failed=2,
            trashed=10
        )

        assert result.deleted == 50
        assert result.failed == 2
        assert result.trashed == 10

    def test_delete_result_error_messages_default(self):
        """Test DeleteResult error_messages default to empty list."""
        from gmail_assistant.core.protocols import DeleteResult

        result = DeleteResult(
            deleted=0,
            failed=0
        )

        assert result.error_messages == []


class TestParseResult:
    """Tests for ParseResult dataclass."""

    def test_parse_result_success(self):
        """Test creating successful ParseResult."""
        from gmail_assistant.core.protocols import ParseResult

        result = ParseResult(
            success=True,
            markdown="# Email Content",
            strategy="html2text",
            quality=0.95
        )

        assert result.success is True
        assert result.markdown == "# Email Content"
        assert result.quality == 0.95

    def test_parse_result_metadata_default(self):
        """Test ParseResult metadata defaults to empty dict."""
        from gmail_assistant.core.protocols import ParseResult

        result = ParseResult(
            success=True,
            markdown="",
            strategy="basic",
            quality=0.5
        )

        assert result.metadata == {}


class TestCredentialProviderProtocol:
    """Tests for CredentialProviderProtocol."""

    def test_protocol_is_runtime_checkable(self):
        """Test protocol is runtime checkable."""
        from gmail_assistant.core.protocols import CredentialProviderProtocol

        class MockProvider:
            @property
            def is_authenticated(self) -> bool:
                return True

            def get_credentials(self):
                return None

            def refresh_credentials(self) -> bool:
                return True

            def revoke_credentials(self) -> bool:
                return True

        provider = MockProvider()
        assert isinstance(provider, CredentialProviderProtocol)


class TestGmailClientProtocol:
    """Tests for GmailClientProtocol."""

    def test_protocol_is_runtime_checkable(self):
        """Test protocol is runtime checkable."""
        from gmail_assistant.core.protocols import GmailClientProtocol

        class MockClient:
            def authenticate(self) -> bool:
                return True

            def get_service(self):
                return None

            @property
            def is_authenticated(self) -> bool:
                return True

            def get_user_info(self):
                return None

        client = MockClient()
        assert isinstance(client, GmailClientProtocol)


class TestEmailFetcherProtocol:
    """Tests for EmailFetcherProtocol."""

    def test_protocol_is_runtime_checkable(self):
        """Test protocol is runtime checkable."""
        from gmail_assistant.core.protocols import EmailFetcherProtocol, FetchResult

        class MockFetcher:
            def search_messages(self, query: str, max_results: int = 100):
                return []

            def get_message(self, message_id: str, format: str = "full"):
                return None

            def get_message_metadata(self, message_id: str):
                return None

            def download_emails(self, query, max_emails=100, output_dir="", format_type="both", organize_by="date"):
                return FetchResult(True, 0, 0, output_dir)

            def get_profile(self):
                return None

        fetcher = MockFetcher()
        assert isinstance(fetcher, EmailFetcherProtocol)


class TestStreamingFetcherProtocol:
    """Tests for StreamingFetcherProtocol."""

    def test_protocol_is_runtime_checkable(self):
        """Test protocol is runtime checkable."""
        from gmail_assistant.core.protocols import StreamingFetcherProtocol

        class MockStreamingFetcher:
            def stream_messages(self, query: str, batch_size: int = 100):
                yield from []

            def stream_message_ids(self, query: str, batch_size: int = 500):
                yield from []

        fetcher = MockStreamingFetcher()
        assert isinstance(fetcher, StreamingFetcherProtocol)


class TestEmailDeleterProtocol:
    """Tests for EmailDeleterProtocol."""

    def test_protocol_is_runtime_checkable(self):
        """Test protocol is runtime checkable."""
        from gmail_assistant.core.protocols import EmailDeleterProtocol, DeleteResult

        class MockDeleter:
            def delete_emails(self, email_ids, batch_size=100):
                return DeleteResult(0, 0)

            def trash_emails(self, email_ids):
                return DeleteResult(0, 0)

            def get_email_count(self, query: str):
                return 0

            def delete_by_query(self, query, dry_run=True, max_delete=None):
                return DeleteResult(0, 0)

        deleter = MockDeleter()
        assert isinstance(deleter, EmailDeleterProtocol)


class TestEmailParserProtocol:
    """Tests for EmailParserProtocol."""

    def test_protocol_is_runtime_checkable(self):
        """Test protocol is runtime checkable."""
        from gmail_assistant.core.protocols import EmailParserProtocol, ParseResult

        class MockParser:
            def parse_eml(self, file_path):
                return {}

            def parse_html(self, html_content, sender=""):
                return ParseResult(True, "", "basic", 0.5)

            def extract_headers(self, headers):
                return {}

        parser = MockParser()
        assert isinstance(parser, EmailParserProtocol)


class TestMarkdownConverterProtocol:
    """Tests for MarkdownConverterProtocol."""

    def test_protocol_is_runtime_checkable(self):
        """Test protocol is runtime checkable."""
        from gmail_assistant.core.protocols import MarkdownConverterProtocol

        class MockConverter:
            def to_markdown(self, email_data):
                return ""

            def clean_html(self, html_content):
                return ""

            def html_to_markdown(self, html_content):
                return ""

        converter = MockConverter()
        assert isinstance(converter, MarkdownConverterProtocol)


class TestOutputPluginProtocol:
    """Tests for OutputPluginProtocol."""

    def test_protocol_is_runtime_checkable(self):
        """Test protocol is runtime checkable."""
        from gmail_assistant.core.protocols import OutputPluginProtocol

        class MockPlugin:
            @property
            def name(self):
                return "test"

            @property
            def extension(self):
                return ".txt"

            def generate(self, email_data):
                return ""

            def save(self, content, path):
                return True

        plugin = MockPlugin()
        assert isinstance(plugin, OutputPluginProtocol)


class TestOrganizationPluginProtocol:
    """Tests for OrganizationPluginProtocol."""

    def test_protocol_is_runtime_checkable(self):
        """Test protocol is runtime checkable."""
        from gmail_assistant.core.protocols import OrganizationPluginProtocol

        class MockPlugin:
            @property
            def name(self):
                return "test"

            def get_path(self, email_data, base_dir):
                return Path(base_dir) / "email.txt"

        plugin = MockPlugin()
        assert isinstance(plugin, OrganizationPluginProtocol)


class TestCacheProtocol:
    """Tests for CacheProtocol."""

    def test_protocol_is_runtime_checkable(self):
        """Test protocol is runtime checkable."""
        from gmail_assistant.core.protocols import CacheProtocol

        class MockCache:
            def get(self, key, default=None):
                return default

            def put(self, key, value, ttl=None):
                return True

            def invalidate(self, key):
                return True

            def clear(self):
                pass

        cache = MockCache()
        assert isinstance(cache, CacheProtocol)


class TestEmailRepositoryProtocol:
    """Tests for EmailRepositoryProtocol."""

    def test_protocol_is_runtime_checkable(self):
        """Test protocol is runtime checkable."""
        from gmail_assistant.core.protocols import EmailRepositoryProtocol

        class MockRepository:
            def save(self, email):
                return True

            def get(self, email_id):
                return None

            def find(self, query, limit=100):
                return []

            def delete(self, email_id):
                return True

            def count(self, query=None):
                return 0

            def exists(self, email_id):
                return False

        repo = MockRepository()
        assert isinstance(repo, EmailRepositoryProtocol)


class TestRateLimiterProtocol:
    """Tests for RateLimiterProtocol."""

    def test_protocol_is_runtime_checkable(self):
        """Test protocol is runtime checkable."""
        from gmail_assistant.core.protocols import RateLimiterProtocol

        class MockRateLimiter:
            def wait_if_needed(self, quota_cost=1):
                return 0.0

            def check_quota(self):
                return {}

            def reset(self):
                pass

        limiter = MockRateLimiter()
        assert isinstance(limiter, RateLimiterProtocol)


class TestServiceContainerProtocol:
    """Tests for ServiceContainerProtocol."""

    def test_protocol_is_runtime_checkable(self):
        """Test protocol is runtime checkable."""
        from gmail_assistant.core.protocols import ServiceContainerProtocol

        class MockContainer:
            def register(self, service_type, instance):
                pass

            def register_factory(self, service_type, factory):
                pass

            def resolve(self, service_type):
                return None

            def has_service(self, service_type):
                return False

        container = MockContainer()
        assert isinstance(container, ServiceContainerProtocol)


class TestValidatorProtocol:
    """Tests for ValidatorProtocol."""

    def test_protocol_is_runtime_checkable(self):
        """Test protocol is runtime checkable."""
        from gmail_assistant.core.protocols import ValidatorProtocol

        class MockValidator:
            def validate_email(self, email):
                return email

            def validate_gmail_query(self, query):
                return query

            def validate_file_path(self, path, must_exist=False):
                return Path(path)

            def validate_batch_size(self, size, max_allowed=1000):
                return size

        validator = MockValidator()
        assert isinstance(validator, ValidatorProtocol)


class TestErrorHandlerProtocol:
    """Tests for ErrorHandlerProtocol."""

    def test_protocol_is_runtime_checkable(self):
        """Test protocol is runtime checkable."""
        from gmail_assistant.core.protocols import ErrorHandlerProtocol

        class MockErrorHandler:
            def handle_error(self, error, context=None):
                pass

            def is_recoverable(self, error):
                return True

            def get_recovery_action(self, error):
                return None

        handler = MockErrorHandler()
        assert isinstance(handler, ErrorHandlerProtocol)


class TestImplementsProtocol:
    """Tests for implements_protocol utility function."""

    def test_implements_protocol_true(self):
        """Test implements_protocol returns True for valid implementation."""
        from gmail_assistant.core.protocols import implements_protocol, CacheProtocol

        class ValidCache:
            def get(self, key, default=None):
                return default

            def put(self, key, value, ttl=None):
                return True

            def invalidate(self, key):
                return True

            def clear(self):
                pass

        cache = ValidCache()
        assert implements_protocol(cache, CacheProtocol) is True

    def test_implements_protocol_false(self):
        """Test implements_protocol returns False for invalid implementation."""
        from gmail_assistant.core.protocols import implements_protocol, CacheProtocol

        class InvalidCache:
            def get(self, key):
                return None
            # Missing other required methods

        cache = InvalidCache()
        assert implements_protocol(cache, CacheProtocol) is False


class TestAssertProtocol:
    """Tests for assert_protocol utility function."""

    def test_assert_protocol_passes(self):
        """Test assert_protocol passes for valid implementation."""
        from gmail_assistant.core.protocols import assert_protocol, CacheProtocol

        class ValidCache:
            def get(self, key, default=None):
                return default

            def put(self, key, value, ttl=None):
                return True

            def invalidate(self, key):
                return True

            def clear(self):
                pass

        cache = ValidCache()
        # Should not raise
        assert_protocol(cache, CacheProtocol, "cache")

    def test_assert_protocol_raises_type_error(self):
        """Test assert_protocol raises TypeError for invalid implementation."""
        from gmail_assistant.core.protocols import assert_protocol, CacheProtocol

        class InvalidCache:
            pass

        cache = InvalidCache()
        with pytest.raises(TypeError, match="must implement CacheProtocol"):
            assert_protocol(cache, CacheProtocol, "cache")


class TestTypeAliases:
    """Tests for type aliases."""

    def test_message_id_is_str(self):
        """Test MessageId is str type."""
        from gmail_assistant.core.protocols import MessageId

        assert MessageId == str

    def test_thread_id_is_str(self):
        """Test ThreadId is str type."""
        from gmail_assistant.core.protocols import ThreadId

        assert ThreadId == str

    def test_email_headers_is_dict(self):
        """Test EmailHeaders type."""
        from gmail_assistant.core.protocols import EmailHeaders

        assert EmailHeaders == dict[str, str]


class TestDataclassImmutability:
    """Tests for dataclass immutability and edge cases."""

    def test_fetch_result_immutable_after_creation(self):
        """FetchResult fields should be assignable but validated."""
        from gmail_assistant.core.protocols import FetchResult

        result = FetchResult(
            success=True,
            emails_fetched=10,
            emails_failed=0,
            output_directory="/path"
        )

        # Should be able to modify fields (not frozen)
        result.emails_fetched = 20
        assert result.emails_fetched == 20

    def test_delete_result_error_messages_initialization(self):
        """DeleteResult should properly initialize error_messages list."""
        from gmail_assistant.core.protocols import DeleteResult

        # Test with None
        result1 = DeleteResult(deleted=5, failed=0, error_messages=None)
        assert result1.error_messages == []

        # Test with provided list
        errors = ["error1", "error2"]
        result2 = DeleteResult(deleted=5, failed=2, error_messages=errors)
        assert result2.error_messages == errors

    def test_parse_result_metadata_initialization(self):
        """ParseResult should properly initialize metadata dict."""
        from gmail_assistant.core.protocols import ParseResult

        # Test with None
        result1 = ParseResult(
            success=True,
            markdown="content",
            strategy="html2text",
            quality=0.9,
            metadata=None
        )
        assert result1.metadata == {}

        # Test with provided dict
        meta = {"key": "value"}
        result2 = ParseResult(
            success=True,
            markdown="content",
            strategy="html2text",
            quality=0.9,
            metadata=meta
        )
        assert result2.metadata == meta

    def test_email_metadata_all_fields(self):
        """EmailMetadata should accept all field values."""
        from gmail_assistant.core.protocols import EmailMetadata

        with warnings.catch_warnings():
            warnings.simplefilter("ignore")
            metadata = EmailMetadata(
                id="msg123",
                thread_id="thread456",
                subject="Test Email",
                sender="sender@example.com",
                recipients=["recipient1@example.com", "recipient2@example.com"],
                date="2025-01-10",
                labels=["INBOX", "IMPORTANT"],
                snippet="This is a preview",
                size_estimate=12345
            )

            assert metadata.id == "msg123"
            assert metadata.thread_id == "thread456"
            assert metadata.subject == "Test Email"
            assert metadata.sender == "sender@example.com"
            assert len(metadata.recipients) == 2
            assert metadata.date == "2025-01-10"
            assert len(metadata.labels) == 2
            assert metadata.snippet == "This is a preview"
            assert metadata.size_estimate == 12345


class TestProtocolEdgeCases:
    """Tests for edge cases in protocol implementations."""

    def test_cache_protocol_with_none_default(self):
        """CacheProtocol get should support None as default."""
        from gmail_assistant.core.protocols import CacheProtocol

        class TestCache:
            def get(self, key, default=None):
                return default

            def put(self, key, value, ttl=None):
                return True

            def invalidate(self, key):
                return True

            def clear(self):
                pass

        cache = TestCache()
        assert isinstance(cache, CacheProtocol)
        assert cache.get("missing_key") is None

    def test_email_repository_protocol_complex_queries(self):
        """EmailRepositoryProtocol should handle various query types."""
        from gmail_assistant.core.protocols import EmailRepositoryProtocol

        class TestRepository:
            def save(self, email):
                return True

            def get(self, email_id):
                return {"id": email_id}

            def find(self, query, limit=100):
                return []

            def delete(self, email_id):
                return True

            def count(self, query=None):
                if query:
                    return 50
                return 100

            def exists(self, email_id):
                return email_id == "existing_id"

        repo = TestRepository()
        assert isinstance(repo, EmailRepositoryProtocol)
        assert repo.count() == 100
        assert repo.count({"subject": "test"}) == 50
        assert repo.exists("existing_id") is True
        assert repo.exists("missing_id") is False

    def test_rate_limiter_protocol_quota_check(self):
        """RateLimiterProtocol quota check should return dict."""
        from gmail_assistant.core.protocols import RateLimiterProtocol

        class TestRateLimiter:
            def wait_if_needed(self, quota_cost=1):
                return 0.5

            def check_quota(self):
                return {
                    "remaining": 100,
                    "limit": 1000,
                    "reset_time": 3600
                }

            def reset(self):
                pass

        limiter = TestRateLimiter()
        assert isinstance(limiter, RateLimiterProtocol)
        quota = limiter.check_quota()
        assert "remaining" in quota
        assert quota["remaining"] == 100

    def test_validator_protocol_path_validation(self):
        """ValidatorProtocol should handle path validation with must_exist flag."""
        from gmail_assistant.core.protocols import ValidatorProtocol

        class TestValidator:
            def validate_email(self, email):
                return email.lower()

            def validate_gmail_query(self, query):
                return query.strip()

            def validate_file_path(self, path, must_exist=False):
                p = Path(path)
                if must_exist and not p.exists():
                    raise FileNotFoundError(f"Path not found: {path}")
                return p

            def validate_batch_size(self, size, max_allowed=1000):
                if size > max_allowed:
                    raise ValueError(f"Batch size {size} exceeds max {max_allowed}")
                return size

        validator = TestValidator()
        assert isinstance(validator, ValidatorProtocol)

        # Test path validation
        assert validator.validate_file_path("/some/path") == Path("/some/path")

        # Test batch size validation
        assert validator.validate_batch_size(100) == 100
        with pytest.raises(ValueError):
            validator.validate_batch_size(2000, max_allowed=1000)


class TestProtocolReturnTypes:
    """Tests for protocol method return types."""

    def test_credential_provider_refresh_returns_bool(self):
        """CredentialProviderProtocol refresh should return bool."""
        from gmail_assistant.core.protocols import CredentialProviderProtocol

        class SuccessProvider:
            @property
            def is_authenticated(self) -> bool:
                return True

            def get_credentials(self):
                return {"token": "abc123"}

            def refresh_credentials(self) -> bool:
                return True

            def revoke_credentials(self) -> bool:
                return True

        class FailureProvider:
            @property
            def is_authenticated(self) -> bool:
                return False

            def get_credentials(self):
                return None

            def refresh_credentials(self) -> bool:
                return False

            def revoke_credentials(self) -> bool:
                return False

        success = SuccessProvider()
        failure = FailureProvider()

        assert isinstance(success, CredentialProviderProtocol)
        assert isinstance(failure, CredentialProviderProtocol)
        assert success.refresh_credentials() is True
        assert failure.refresh_credentials() is False

    def test_error_handler_recovery_action(self):
        """ErrorHandlerProtocol should return recovery actions."""
        from gmail_assistant.core.protocols import ErrorHandlerProtocol

        class TestErrorHandler:
            def handle_error(self, error, context=None):
                print(f"Error: {error}")

            def is_recoverable(self, error):
                return not isinstance(error, KeyboardInterrupt)

            def get_recovery_action(self, error):
                if isinstance(error, ValueError):
                    return "retry"
                elif isinstance(error, FileNotFoundError):
                    return "create_file"
                return None

        handler = TestErrorHandler()
        assert isinstance(handler, ErrorHandlerProtocol)
        assert handler.get_recovery_action(ValueError()) == "retry"
        assert handler.get_recovery_action(FileNotFoundError()) == "create_file"
        assert handler.get_recovery_action(Exception()) is None


class TestStreamingProtocolBehavior:
    """Tests for streaming protocol behavior."""

    def test_streaming_fetcher_yields_messages(self):
        """StreamingFetcherProtocol should yield message data."""
        from gmail_assistant.core.protocols import StreamingFetcherProtocol

        class TestStreamingFetcher:
            def stream_messages(self, query: str, batch_size: int = 100):
                for i in range(5):
                    yield {"id": f"msg{i}", "subject": f"Message {i}"}

            def stream_message_ids(self, query: str, batch_size: int = 500):
                for i in range(10):
                    yield f"id_{i}"

        fetcher = TestStreamingFetcher()
        assert isinstance(fetcher, StreamingFetcherProtocol)

        messages = list(fetcher.stream_messages("is:unread"))
        assert len(messages) == 5
        assert messages[0]["id"] == "msg0"

        ids = list(fetcher.stream_message_ids("is:important"))
        assert len(ids) == 10
        assert ids[0] == "id_0"
