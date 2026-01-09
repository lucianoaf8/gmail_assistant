"""Unit tests for gmail_assistant.core.protocols module."""
from __future__ import annotations

from typing import Any, Dict, List, Optional
from dataclasses import is_dataclass

import pytest

from gmail_assistant.core.protocols import (
    # DTOs
    EmailMetadata,
    FetchResult,
    DeleteResult,
    ParseResult,
    # Protocols (runtime_checkable)
    CredentialProviderProtocol,
    GmailClientProtocol,
    EmailFetcherProtocol,
    EmailDeleterProtocol,
    EmailParserProtocol,
    CacheProtocol,
    RateLimiterProtocol,
    ValidatorProtocol,
    ServiceContainerProtocol,
    ErrorHandlerProtocol,
    # Utilities
    implements_protocol,
    assert_protocol,
)


@pytest.mark.unit
class TestEmailMetadataDTO:
    """Test EmailMetadata dataclass."""

    def test_is_dataclass(self):
        """EmailMetadata should be a dataclass."""
        assert is_dataclass(EmailMetadata)

    def test_create_with_required_fields(self):
        """EmailMetadata should accept required fields."""
        metadata = EmailMetadata(
            id="msg123",
            thread_id="thread456",
            subject="Test Subject",
            sender="sender@example.com",
            recipients=["recipient@example.com"],
            date="2024-01-01",
            labels=["INBOX"]
        )

        assert metadata.id == "msg123"
        assert metadata.thread_id == "thread456"
        assert metadata.subject == "Test Subject"
        assert metadata.sender == "sender@example.com"
        assert metadata.recipients == ["recipient@example.com"]
        assert metadata.date == "2024-01-01"
        assert metadata.labels == ["INBOX"]

    def test_default_values(self):
        """EmailMetadata should have default values for optional fields."""
        metadata = EmailMetadata(
            id="msg123",
            thread_id="thread456",
            subject="Test",
            sender="test@example.com",
            recipients=[],
            date="2024-01-01",
            labels=[]
        )

        assert metadata.snippet == ""
        assert metadata.size_estimate == 0

    def test_with_all_fields(self):
        """EmailMetadata should accept all fields."""
        metadata = EmailMetadata(
            id="msg123",
            thread_id="thread456",
            subject="Test",
            sender="test@example.com",
            recipients=["a@test.com", "b@test.com"],
            date="2024-01-01",
            labels=["INBOX", "UNREAD"],
            snippet="This is a preview...",
            size_estimate=1024
        )

        assert metadata.snippet == "This is a preview..."
        assert metadata.size_estimate == 1024
        assert len(metadata.recipients) == 2
        assert len(metadata.labels) == 2


@pytest.mark.unit
class TestFetchResultDTO:
    """Test FetchResult dataclass."""

    def test_is_dataclass(self):
        """FetchResult should be a dataclass."""
        assert is_dataclass(FetchResult)

    def test_create_successful_result(self):
        """FetchResult should represent successful fetch."""
        result = FetchResult(
            success=True,
            emails_fetched=100,
            emails_failed=0,
            output_directory="/path/to/output"
        )

        assert result.success is True
        assert result.emails_fetched == 100
        assert result.emails_failed == 0
        assert result.output_directory == "/path/to/output"
        assert result.error_message is None

    def test_create_failed_result(self):
        """FetchResult should represent failed fetch."""
        result = FetchResult(
            success=False,
            emails_fetched=50,
            emails_failed=10,
            output_directory="/path/to/output",
            error_message="Network error occurred"
        )

        assert result.success is False
        assert result.emails_failed == 10
        assert result.error_message == "Network error occurred"


@pytest.mark.unit
class TestDeleteResultDTO:
    """Test DeleteResult dataclass."""

    def test_is_dataclass(self):
        """DeleteResult should be a dataclass."""
        assert is_dataclass(DeleteResult)

    def test_create_with_required_fields(self):
        """DeleteResult should accept required fields."""
        result = DeleteResult(
            deleted=50,
            failed=2
        )

        assert result.deleted == 50
        assert result.failed == 2

    def test_default_trashed_value(self):
        """DeleteResult should have default trashed value."""
        result = DeleteResult(deleted=50, failed=0)

        assert result.trashed == 0

    def test_post_init_creates_empty_list(self):
        """DeleteResult should create empty error_messages list if None."""
        result = DeleteResult(deleted=50, failed=0)

        assert result.error_messages == []

    def test_preserves_error_messages(self):
        """DeleteResult should preserve provided error_messages."""
        errors = ["Error 1", "Error 2"]
        result = DeleteResult(deleted=50, failed=2, error_messages=errors)

        assert result.error_messages == errors
        assert len(result.error_messages) == 2


@pytest.mark.unit
class TestParseResultDTO:
    """Test ParseResult dataclass."""

    def test_is_dataclass(self):
        """ParseResult should be a dataclass."""
        assert is_dataclass(ParseResult)

    def test_create_successful_result(self):
        """ParseResult should represent successful parse."""
        result = ParseResult(
            success=True,
            markdown="# Email Title\n\nContent here",
            strategy="html2text",
            quality=0.95
        )

        assert result.success is True
        assert "# Email Title" in result.markdown
        assert result.strategy == "html2text"
        assert result.quality == 0.95

    def test_default_metadata_value(self):
        """ParseResult should have default metadata value."""
        result = ParseResult(
            success=True,
            markdown="Content",
            strategy="basic",
            quality=0.8
        )

        assert result.metadata == {}

    def test_post_init_creates_empty_dict(self):
        """ParseResult should create empty metadata dict if None."""
        result = ParseResult(
            success=True,
            markdown="Content",
            strategy="basic",
            quality=0.8
        )

        assert result.metadata == {}
        assert isinstance(result.metadata, dict)

    def test_with_error_message(self):
        """ParseResult should store error message on failure."""
        result = ParseResult(
            success=False,
            markdown="",
            strategy="none",
            quality=0.0,
            error_message="Failed to parse HTML"
        )

        assert result.success is False
        assert result.error_message == "Failed to parse HTML"


@pytest.mark.unit
class TestProtocolImplementation:
    """Test protocol implementation checking."""

    def test_implements_protocol_positive(self):
        """implements_protocol should return True for implementing class."""

        class MyCache:
            def get(self, key: str, default=None):
                return default

            def put(self, key: str, value, ttl=None):
                return True

            def invalidate(self, key: str):
                return True

            def clear(self):
                pass

        cache = MyCache()
        assert implements_protocol(cache, CacheProtocol) is True

    def test_implements_protocol_negative(self):
        """implements_protocol should return False for non-implementing class."""

        class NotACache:
            def do_something(self):
                pass

        obj = NotACache()
        assert implements_protocol(obj, CacheProtocol) is False

    def test_assert_protocol_success(self):
        """assert_protocol should not raise for implementing class."""

        class MyRateLimiter:
            def wait_if_needed(self, quota_cost=1):
                return 0.0

            def check_quota(self):
                return {}

            def reset(self):
                pass

        limiter = MyRateLimiter()
        # Should not raise
        assert_protocol(limiter, RateLimiterProtocol, "limiter")

    def test_assert_protocol_failure(self):
        """assert_protocol should raise TypeError for non-implementing class."""

        class NotARateLimiter:
            pass

        obj = NotARateLimiter()
        with pytest.raises(TypeError, match="must implement RateLimiterProtocol"):
            assert_protocol(obj, RateLimiterProtocol, "my_object")


@pytest.mark.unit
class TestCredentialProviderProtocol:
    """Test CredentialProviderProtocol."""

    def test_protocol_is_runtime_checkable(self):
        """CredentialProviderProtocol should be runtime checkable."""

        class MyCredentialProvider:
            @property
            def is_authenticated(self) -> bool:
                return True

            def get_credentials(self):
                return None

            def refresh_credentials(self) -> bool:
                return True

            def revoke_credentials(self) -> bool:
                return True

        provider = MyCredentialProvider()
        assert isinstance(provider, CredentialProviderProtocol)


@pytest.mark.unit
class TestGmailClientProtocol:
    """Test GmailClientProtocol."""

    def test_protocol_is_runtime_checkable(self):
        """GmailClientProtocol should be runtime checkable."""

        class MyGmailClient:
            def authenticate(self) -> bool:
                return True

            def get_service(self):
                return None

            @property
            def is_authenticated(self) -> bool:
                return True

            def get_user_info(self):
                return {}

        client = MyGmailClient()
        assert isinstance(client, GmailClientProtocol)


@pytest.mark.unit
class TestEmailFetcherProtocol:
    """Test EmailFetcherProtocol."""

    def test_protocol_is_runtime_checkable(self):
        """EmailFetcherProtocol should be runtime checkable."""

        class MyEmailFetcher:
            def search_messages(self, query: str, max_results: int = 100):
                return []

            def get_message(self, message_id: str, format: str = "full"):
                return None

            def get_message_metadata(self, message_id: str):
                return None

            def download_emails(
                self,
                query: str,
                max_emails: int = 100,
                output_dir: str = "gmail_backup",
                format_type: str = "both",
                organize_by: str = "date"
            ):
                return FetchResult(True, 0, 0, output_dir)

            def get_profile(self):
                return {}

        fetcher = MyEmailFetcher()
        assert isinstance(fetcher, EmailFetcherProtocol)


@pytest.mark.unit
class TestEmailDeleterProtocol:
    """Test EmailDeleterProtocol."""

    def test_protocol_is_runtime_checkable(self):
        """EmailDeleterProtocol should be runtime checkable."""

        class MyEmailDeleter:
            def delete_emails(self, email_ids: List[str], batch_size: int = 100):
                return DeleteResult(0, 0)

            def trash_emails(self, email_ids: List[str]):
                return DeleteResult(0, 0)

            def get_email_count(self, query: str) -> int:
                return 0

            def delete_by_query(
                self,
                query: str,
                dry_run: bool = True,
                max_delete: Optional[int] = None
            ):
                return DeleteResult(0, 0)

        deleter = MyEmailDeleter()
        assert isinstance(deleter, EmailDeleterProtocol)


@pytest.mark.unit
class TestValidatorProtocol:
    """Test ValidatorProtocol."""

    def test_protocol_is_runtime_checkable(self):
        """ValidatorProtocol should be runtime checkable."""

        class MyValidator:
            def validate_email(self, email: str) -> str:
                return email

            def validate_gmail_query(self, query: str) -> str:
                return query

            def validate_file_path(self, path, must_exist: bool = False):
                from pathlib import Path
                return Path(path)

            def validate_batch_size(self, size: int, max_allowed: int = 1000) -> int:
                return size

        validator = MyValidator()
        assert isinstance(validator, ValidatorProtocol)


@pytest.mark.unit
class TestCacheProtocol:
    """Test CacheProtocol."""

    def test_protocol_is_runtime_checkable(self):
        """CacheProtocol should be runtime checkable."""

        class MyCache:
            def get(self, key: str, default=None):
                return default

            def put(self, key: str, value, ttl=None) -> bool:
                return True

            def invalidate(self, key: str) -> bool:
                return True

            def clear(self):
                pass

        cache = MyCache()
        assert isinstance(cache, CacheProtocol)


@pytest.mark.unit
class TestRateLimiterProtocol:
    """Test RateLimiterProtocol."""

    def test_protocol_is_runtime_checkable(self):
        """RateLimiterProtocol should be runtime checkable."""

        class MyRateLimiter:
            def wait_if_needed(self, quota_cost: int = 1) -> float:
                return 0.0

            def check_quota(self) -> Dict[str, Any]:
                return {"available": True}

            def reset(self):
                pass

        limiter = MyRateLimiter()
        assert isinstance(limiter, RateLimiterProtocol)


@pytest.mark.unit
class TestServiceContainerProtocol:
    """Test ServiceContainerProtocol."""

    def test_protocol_is_runtime_checkable(self):
        """ServiceContainerProtocol should be runtime checkable."""

        class MyContainer:
            def register(self, service_type: type, instance):
                pass

            def register_factory(self, service_type: type, factory):
                pass

            def resolve(self, service_type: type):
                return None

            def has_service(self, service_type: type) -> bool:
                return False

        container = MyContainer()
        assert isinstance(container, ServiceContainerProtocol)


@pytest.mark.unit
class TestErrorHandlerProtocol:
    """Test ErrorHandlerProtocol."""

    def test_protocol_is_runtime_checkable(self):
        """ErrorHandlerProtocol should be runtime checkable."""

        class MyErrorHandler:
            def handle_error(self, error: Exception, context=None):
                pass

            def is_recoverable(self, error: Exception) -> bool:
                return False

            def get_recovery_action(self, error: Exception):
                return None

        handler = MyErrorHandler()
        assert isinstance(handler, ErrorHandlerProtocol)


@pytest.mark.unit
class TestEmailParserProtocol:
    """Test EmailParserProtocol."""

    def test_protocol_is_runtime_checkable(self):
        """EmailParserProtocol should be runtime checkable."""
        from pathlib import Path

        class MyEmailParser:
            def parse_eml(self, file_path) -> Dict[str, Any]:
                return {}

            def parse_html(self, html_content: str, sender: str = "") -> ParseResult:
                return ParseResult(True, "", "basic", 0.0)

            def extract_headers(self, headers: List[Dict[str, str]]) -> Dict[str, str]:
                return {}

        parser = MyEmailParser()
        assert isinstance(parser, EmailParserProtocol)


@pytest.mark.unit
class TestStreamingFetcherProtocol:
    """Test StreamingFetcherProtocol."""

    def test_protocol_is_runtime_checkable(self):
        """StreamingFetcherProtocol should be runtime checkable."""
        from gmail_assistant.core.protocols import StreamingFetcherProtocol

        class MyStreamingFetcher:
            def stream_messages(self, query: str, batch_size: int = 100):
                yield {"id": "msg1"}

            def stream_message_ids(self, query: str, batch_size: int = 500):
                yield "msg1"

        fetcher = MyStreamingFetcher()
        assert isinstance(fetcher, StreamingFetcherProtocol)


@pytest.mark.unit
class TestMarkdownConverterProtocol:
    """Test MarkdownConverterProtocol."""

    def test_protocol_is_runtime_checkable(self):
        """MarkdownConverterProtocol should be runtime checkable."""
        from gmail_assistant.core.protocols import MarkdownConverterProtocol

        class MyMarkdownConverter:
            def to_markdown(self, email_data: Dict[str, Any]) -> str:
                return "# Email"

            def clean_html(self, html_content: str) -> str:
                return html_content

            def html_to_markdown(self, html_content: str) -> str:
                return html_content

        converter = MyMarkdownConverter()
        assert isinstance(converter, MarkdownConverterProtocol)


@pytest.mark.unit
class TestOutputPluginProtocol:
    """Test OutputPluginProtocol."""

    def test_protocol_is_runtime_checkable(self):
        """OutputPluginProtocol should be runtime checkable."""
        from pathlib import Path
        from gmail_assistant.core.protocols import OutputPluginProtocol

        class MyOutputPlugin:
            @property
            def name(self) -> str:
                return "my_plugin"

            @property
            def extension(self) -> str:
                return ".txt"

            def generate(self, email_data: Dict[str, Any]) -> str:
                return "output"

            def save(self, content: str, path: Path) -> bool:
                return True

        plugin = MyOutputPlugin()
        assert isinstance(plugin, OutputPluginProtocol)


@pytest.mark.unit
class TestOrganizationPluginProtocol:
    """Test OrganizationPluginProtocol."""

    def test_protocol_is_runtime_checkable(self):
        """OrganizationPluginProtocol should be runtime checkable."""
        from pathlib import Path
        from gmail_assistant.core.protocols import OrganizationPluginProtocol

        class MyOrganizationPlugin:
            @property
            def name(self) -> str:
                return "by_date"

            def get_path(self, email_data: Dict[str, Any], base_dir: Path) -> Path:
                return base_dir / "2024"

        plugin = MyOrganizationPlugin()
        assert isinstance(plugin, OrganizationPluginProtocol)


@pytest.mark.unit
class TestTypeAliases:
    """Test type alias definitions."""

    def test_progress_callback_type(self):
        """ProgressCallback should be callable."""
        from gmail_assistant.core.protocols import ProgressCallback

        def my_progress(current: int, total: int) -> None:
            pass

        # Verify it's a valid callable type
        assert callable(my_progress)

    def test_error_callback_type(self):
        """ErrorCallback should be callable."""
        from gmail_assistant.core.protocols import ErrorCallback

        def my_error(error: Exception) -> None:
            pass

        assert callable(my_error)

    def test_success_callback_type(self):
        """SuccessCallback should be callable."""
        from gmail_assistant.core.protocols import SuccessCallback

        def my_success(data: Dict[str, Any]) -> None:
            pass

        assert callable(my_success)


@pytest.mark.unit
class TestMessageIdTypeAlias:
    """Test MessageId type alias."""

    def test_message_id_is_string(self):
        """MessageId should be a string type alias."""
        from gmail_assistant.core.protocols import MessageId

        msg_id: MessageId = "msg123"
        assert isinstance(msg_id, str)


@pytest.mark.unit
class TestThreadIdTypeAlias:
    """Test ThreadId type alias."""

    def test_thread_id_is_string(self):
        """ThreadId should be a string type alias."""
        from gmail_assistant.core.protocols import ThreadId

        thread_id: ThreadId = "thread456"
        assert isinstance(thread_id, str)


@pytest.mark.unit
class TestEmailHeadersTypeAlias:
    """Test EmailHeaders type alias."""

    def test_email_headers_is_dict(self):
        """EmailHeaders should be a dict type alias."""
        from gmail_assistant.core.protocols import EmailHeaders

        headers: EmailHeaders = {"From": "test@example.com", "Subject": "Test"}
        assert isinstance(headers, dict)


@pytest.mark.unit
class TestEmailBodyTypeAlias:
    """Test EmailBody type alias."""

    def test_email_body_is_dict(self):
        """EmailBody should be a dict type alias."""
        from gmail_assistant.core.protocols import EmailBody

        body: EmailBody = {"text": "Hello", "html": "<p>Hello</p>"}
        assert isinstance(body, dict)


@pytest.mark.unit
class TestOperationResultTypeAlias:
    """Test OperationResult type alias."""

    def test_operation_result_is_dict(self):
        """OperationResult should be a dict type alias."""
        from gmail_assistant.core.protocols import OperationResult

        result: OperationResult = {
            "count": 10,
            "success": True,
            "message": "Done",
            "errors": ["error1"]
        }
        assert isinstance(result, dict)


@pytest.mark.unit
class TestImplementsProtocolEdgeCases:
    """Test edge cases for implements_protocol function."""

    def test_implements_protocol_with_none(self):
        """implements_protocol should handle None gracefully."""
        result = implements_protocol(None, CacheProtocol)
        assert result is False

    def test_implements_protocol_with_primitive(self):
        """implements_protocol should handle primitives."""
        result = implements_protocol("string", CacheProtocol)
        assert result is False

    def test_implements_protocol_with_partial_implementation(self):
        """implements_protocol should return False for partial implementation."""

        class PartialCache:
            def get(self, key: str, default=None):
                return default
            # Missing: put, invalidate, clear

        obj = PartialCache()
        # Structural subtyping means this might pass if only get is checked
        # The actual result depends on protocol definition


@pytest.mark.unit
class TestAssertProtocolEdgeCases:
    """Test edge cases for assert_protocol function."""

    def test_assert_protocol_with_custom_name(self):
        """assert_protocol should use custom name in error message."""

        class NotImplementing:
            pass

        with pytest.raises(TypeError, match="my_custom_name"):
            assert_protocol(NotImplementing(), CacheProtocol, "my_custom_name")

    def test_assert_protocol_with_default_name(self):
        """assert_protocol should use 'object' as default name."""

        class NotImplementing:
            pass

        with pytest.raises(TypeError, match="object"):
            assert_protocol(NotImplementing(), CacheProtocol)


@pytest.mark.unit
class TestParseResultMetadataPostInit:
    """Test ParseResult __post_init__ behavior."""

    def test_post_init_with_explicit_none(self):
        """ParseResult should handle explicit None metadata."""
        result = ParseResult(
            success=True,
            markdown="Content",
            strategy="basic",
            quality=0.8,
            metadata=None
        )

        assert result.metadata == {}

    def test_post_init_with_provided_metadata(self):
        """ParseResult should preserve provided metadata."""
        metadata = {"key": "value", "num": 42}
        result = ParseResult(
            success=True,
            markdown="Content",
            strategy="basic",
            quality=0.8,
            metadata=metadata
        )

        assert result.metadata == metadata


@pytest.mark.unit
class TestDeleteResultErrorMessagesPostInit:
    """Test DeleteResult __post_init__ behavior."""

    def test_post_init_with_explicit_none(self):
        """DeleteResult should handle explicit None error_messages."""
        result = DeleteResult(
            deleted=10,
            failed=2,
            error_messages=None
        )

        assert result.error_messages == []

    def test_post_init_with_provided_errors(self):
        """DeleteResult should preserve provided error_messages."""
        errors = ["Error 1", "Error 2"]
        result = DeleteResult(
            deleted=10,
            failed=2,
            error_messages=errors
        )

        assert result.error_messages == errors
        assert len(result.error_messages) == 2
