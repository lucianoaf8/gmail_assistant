"""Unit tests for gmail_assistant.utils.error_handler module."""
from __future__ import annotations

import json
from pathlib import Path
from datetime import datetime
from unittest import mock

import pytest

from gmail_assistant.utils.error_handler import (
    ErrorSeverity,
    ErrorCategory,
    ErrorContext,
    StandardError,
    ErrorClassifier,
    ErrorHandler,
    handle_errors,
    retry_on_error,
    get_error_handler,
    handle_error,
)


@pytest.fixture
def error_handler(temp_dir: Path):
    """Create an error handler for testing."""
    return ErrorHandler(log_dir=temp_dir)


@pytest.fixture
def error_context():
    """Create a sample error context."""
    return ErrorContext(
        operation="test_operation",
        user_id="user123",
        email_id="email456",
        file_path="/test/path.txt",
        query="is:unread"
    )


@pytest.mark.unit
class TestErrorSeverity:
    """Test ErrorSeverity enumeration."""

    def test_low_value(self):
        """LOW should have expected value."""
        assert ErrorSeverity.LOW.value == "low"

    def test_medium_value(self):
        """MEDIUM should have expected value."""
        assert ErrorSeverity.MEDIUM.value == "medium"

    def test_high_value(self):
        """HIGH should have expected value."""
        assert ErrorSeverity.HIGH.value == "high"

    def test_critical_value(self):
        """CRITICAL should have expected value."""
        assert ErrorSeverity.CRITICAL.value == "critical"


@pytest.mark.unit
class TestErrorCategory:
    """Test ErrorCategory enumeration."""

    def test_all_categories_exist(self):
        """All expected error categories should exist."""
        expected_categories = [
            "authentication",
            "authorization",
            "network",
            "api_quota",
            "rate_limit",
            "data_validation",
            "file_system",
            "memory",
            "configuration",
            "parsing",
            "unknown"
        ]

        for category in expected_categories:
            assert hasattr(ErrorCategory, category.upper())


@pytest.mark.unit
class TestErrorContext:
    """Test ErrorContext dataclass."""

    def test_create_with_required_fields(self):
        """ErrorContext should require operation field."""
        ctx = ErrorContext(operation="test")

        assert ctx.operation == "test"

    def test_optional_fields_default_to_none(self):
        """Optional fields should default to None."""
        ctx = ErrorContext(operation="test")

        assert ctx.user_id is None
        assert ctx.email_id is None
        assert ctx.file_path is None
        assert ctx.query is None
        assert ctx.additional_data is None

    def test_create_with_all_fields(self, error_context: ErrorContext):
        """ErrorContext should accept all fields."""
        assert error_context.operation == "test_operation"
        assert error_context.user_id == "user123"
        assert error_context.email_id == "email456"
        assert error_context.file_path == "/test/path.txt"
        assert error_context.query == "is:unread"


@pytest.mark.unit
class TestStandardError:
    """Test StandardError dataclass."""

    def test_create_standard_error(self):
        """StandardError should accept all fields."""
        error = StandardError(
            error_id="ERR_123",
            category=ErrorCategory.NETWORK,
            severity=ErrorSeverity.HIGH,
            message="Network failure",
            original_exception=ValueError("Test"),
            context=ErrorContext(operation="test"),
            timestamp=datetime.now(),
            recoverable=True,
            user_message="Please try again later"
        )

        assert error.error_id == "ERR_123"
        assert error.category == ErrorCategory.NETWORK
        assert error.severity == ErrorSeverity.HIGH
        assert error.recoverable is True

    def test_to_dict_method(self):
        """to_dict should return serializable dictionary."""
        error = StandardError(
            error_id="ERR_123",
            category=ErrorCategory.NETWORK,
            severity=ErrorSeverity.HIGH,
            message="Network failure",
            original_exception=None,
            context=ErrorContext(operation="test"),
            timestamp=datetime.now(),
            recoverable=True,
            user_message="Please try again"
        )

        result = error.to_dict()

        assert result["error_id"] == "ERR_123"
        assert result["category"] == "network"
        assert result["severity"] == "high"
        assert result["recoverable"] is True
        assert "timestamp" in result

    def test_to_dict_handles_none_context(self):
        """to_dict should handle None context."""
        error = StandardError(
            error_id="ERR_123",
            category=ErrorCategory.UNKNOWN,
            severity=ErrorSeverity.LOW,
            message="Test",
            original_exception=None,
            context=None,
            timestamp=datetime.now(),
            recoverable=False,
            user_message="Test"
        )

        result = error.to_dict()

        assert result["context"] is None


@pytest.mark.unit
class TestErrorClassifierHttpErrors:
    """Test ErrorClassifier with HTTP errors."""

    def test_classify_401_authentication_error(self):
        """Should classify 401 as authentication error."""
        from googleapiclient.errors import HttpError
        from unittest.mock import Mock

        resp = Mock()
        resp.status = 401
        exception = HttpError(resp, b"Unauthorized")

        result = ErrorClassifier.classify_exception(exception)

        assert result.category == ErrorCategory.AUTHENTICATION
        assert result.severity == ErrorSeverity.HIGH
        assert result.recoverable is True

    def test_classify_403_quota_exceeded(self):
        """Should classify 403 with quota message as API_QUOTA."""
        from googleapiclient.errors import HttpError
        from unittest.mock import Mock

        resp = Mock()
        resp.status = 403
        exception = HttpError(resp, b"Quota exceeded for this project")

        result = ErrorClassifier.classify_exception(exception)

        assert result.category == ErrorCategory.API_QUOTA
        assert result.severity == ErrorSeverity.HIGH

    def test_classify_403_authorization(self):
        """Should classify generic 403 as authorization error."""
        from googleapiclient.errors import HttpError
        from unittest.mock import Mock

        resp = Mock()
        resp.status = 403
        exception = HttpError(resp, b"Access denied")

        result = ErrorClassifier.classify_exception(exception)

        assert result.category == ErrorCategory.AUTHORIZATION

    def test_classify_429_rate_limit(self):
        """Should classify 429 as rate limit error."""
        from googleapiclient.errors import HttpError
        from unittest.mock import Mock

        resp = Mock()
        resp.status = 429
        exception = HttpError(resp, b"Too many requests")

        result = ErrorClassifier.classify_exception(exception)

        assert result.category == ErrorCategory.RATE_LIMIT
        assert result.severity == ErrorSeverity.MEDIUM
        assert result.recoverable is True

    def test_classify_500_server_error(self):
        """Should classify 500 as network error."""
        from googleapiclient.errors import HttpError
        from unittest.mock import Mock

        resp = Mock()
        resp.status = 500
        exception = HttpError(resp, b"Internal server error")

        result = ErrorClassifier.classify_exception(exception)

        assert result.category == ErrorCategory.NETWORK
        assert result.recoverable is True

    def test_classify_503_server_error(self):
        """Should classify 503 as network error."""
        from googleapiclient.errors import HttpError
        from unittest.mock import Mock

        resp = Mock()
        resp.status = 503
        exception = HttpError(resp, b"Service unavailable")

        result = ErrorClassifier.classify_exception(exception)

        assert result.category == ErrorCategory.NETWORK


@pytest.mark.unit
class TestErrorClassifierFileErrors:
    """Test ErrorClassifier with file system errors."""

    def test_classify_file_not_found(self):
        """Should classify FileNotFoundError correctly."""
        exception = FileNotFoundError("File not found: test.txt")

        result = ErrorClassifier.classify_exception(exception)

        assert result.category == ErrorCategory.FILE_SYSTEM
        assert result.severity == ErrorSeverity.MEDIUM
        assert result.recoverable is True

    def test_classify_permission_error(self):
        """Should classify PermissionError correctly."""
        exception = PermissionError("Permission denied")

        result = ErrorClassifier.classify_exception(exception)

        assert result.category == ErrorCategory.FILE_SYSTEM
        assert result.severity == ErrorSeverity.HIGH
        assert result.recoverable is True

    def test_classify_os_error(self):
        """Should classify generic OSError correctly."""
        exception = OSError("Disk full")

        result = ErrorClassifier.classify_exception(exception)

        assert result.category == ErrorCategory.FILE_SYSTEM


@pytest.mark.unit
class TestErrorClassifierMemoryErrors:
    """Test ErrorClassifier with memory errors."""

    def test_classify_memory_error(self):
        """Should classify MemoryError correctly."""
        exception = MemoryError("Out of memory")

        result = ErrorClassifier.classify_exception(exception)

        assert result.category == ErrorCategory.MEMORY
        assert result.severity == ErrorSeverity.CRITICAL
        assert result.recoverable is True
        assert "memory" in result.user_message.lower()


@pytest.mark.unit
class TestErrorClassifierGenericErrors:
    """Test ErrorClassifier with generic errors."""

    def test_classify_unknown_exception(self):
        """Should classify unknown exceptions as UNKNOWN."""
        exception = RuntimeError("Something went wrong")

        result = ErrorClassifier.classify_exception(exception)

        assert result.category == ErrorCategory.UNKNOWN
        assert result.severity == ErrorSeverity.MEDIUM
        assert result.recoverable is False

    def test_classify_preserves_context(self, error_context: ErrorContext):
        """Should preserve context in classified error."""
        exception = ValueError("Test error")

        result = ErrorClassifier.classify_exception(exception, error_context)

        assert result.context == error_context
        assert result.context.operation == "test_operation"


@pytest.mark.unit
class TestErrorHandlerInit:
    """Test ErrorHandler initialization."""

    def test_creates_log_directory(self, temp_dir: Path):
        """ErrorHandler should create log directory."""
        log_dir = temp_dir / "new_logs"

        handler = ErrorHandler(log_dir=log_dir)

        assert log_dir.exists()

    def test_initializes_error_counts(self, error_handler: ErrorHandler):
        """ErrorHandler should initialize empty error counts."""
        assert error_handler.error_counts == {}


@pytest.mark.unit
class TestErrorHandlerHandleError:
    """Test ErrorHandler.handle_error method."""

    def test_handle_error_returns_standard_error(
        self, error_handler: ErrorHandler
    ):
        """handle_error should return StandardError."""
        exception = ValueError("Test error")

        result = error_handler.handle_error(exception)

        assert isinstance(result, StandardError)

    def test_handle_error_with_context(
        self, error_handler: ErrorHandler, error_context: ErrorContext
    ):
        """handle_error should preserve context."""
        exception = ValueError("Test error")

        result = error_handler.handle_error(exception, error_context)

        assert result.context == error_context

    def test_handle_error_updates_stats(self, error_handler: ErrorHandler):
        """handle_error should update error statistics."""
        exception = ValueError("Test error")

        error_handler.handle_error(exception)

        assert "unknown" in error_handler.error_counts
        assert error_handler.error_counts["unknown"] == 1

    def test_handle_error_accumulates_stats(self, error_handler: ErrorHandler):
        """handle_error should accumulate statistics."""
        for _ in range(3):
            error_handler.handle_error(ValueError("Test"))

        assert error_handler.error_counts["unknown"] == 3


@pytest.mark.unit
class TestErrorHandlerRecovery:
    """Test ErrorHandler recovery functionality."""

    def test_register_recovery_handler(self, error_handler: ErrorHandler):
        """Should register recovery handler."""

        def recovery_func(error):
            return True

        error_handler.register_recovery_handler(
            ErrorCategory.NETWORK,
            recovery_func
        )

        assert ErrorCategory.NETWORK in error_handler.recovery_handlers

    def test_recovery_handler_called(self, error_handler: ErrorHandler):
        """Should call recovery handler for recoverable errors."""
        called = [False]

        def recovery_func(error):
            called[0] = True
            return True

        error_handler.register_recovery_handler(
            ErrorCategory.NETWORK,
            recovery_func
        )

        # Create a network error
        from googleapiclient.errors import HttpError
        from unittest.mock import Mock

        resp = Mock()
        resp.status = 503
        exception = HttpError(resp, b"Service unavailable")

        error_handler.handle_error(exception)

        assert called[0] is True


@pytest.mark.unit
class TestErrorHandlerStats:
    """Test ErrorHandler statistics methods."""

    def test_get_error_stats_empty(self, error_handler: ErrorHandler):
        """get_error_stats should return empty stats initially."""
        stats = error_handler.get_error_stats()

        assert stats["total_errors"] == 0
        assert stats["by_category"] == {}
        assert stats["most_common"] is None

    def test_get_error_stats_with_errors(self, error_handler: ErrorHandler):
        """get_error_stats should reflect errors handled."""
        error_handler.handle_error(ValueError("Error 1"))
        error_handler.handle_error(ValueError("Error 2"))

        stats = error_handler.get_error_stats()

        assert stats["total_errors"] == 2
        assert "unknown" in stats["by_category"]
        assert stats["most_common"] is not None

    def test_clear_stats(self, error_handler: ErrorHandler):
        """clear_stats should reset error counts."""
        error_handler.handle_error(ValueError("Error"))
        error_handler.clear_stats()

        stats = error_handler.get_error_stats()

        assert stats["total_errors"] == 0


@pytest.mark.unit
class TestHandleErrorsDecorator:
    """Test handle_errors decorator."""

    def test_decorator_re_raises_non_recoverable(
        self, error_handler: ErrorHandler, error_context: ErrorContext
    ):
        """handle_errors decorator should re-raise non-recoverable errors."""

        @handle_errors(error_handler, error_context)
        def failing_func():
            raise ValueError("Test error")

        # Non-recoverable errors are re-raised per the decorator implementation
        with pytest.raises(ValueError, match="Test error"):
            failing_func()

    def test_decorator_passes_through_success(
        self, error_handler: ErrorHandler, error_context: ErrorContext
    ):
        """handle_errors decorator should pass through successful calls."""

        @handle_errors(error_handler, error_context)
        def success_func():
            return "success"

        result = success_func()

        assert result == "success"


@pytest.mark.unit
class TestRetryOnErrorDecorator:
    """Test retry_on_error decorator."""

    def test_retries_on_recoverable_error(self):
        """retry_on_error should retry on recoverable errors."""
        call_count = [0]

        @retry_on_error(max_retries=3)
        def sometimes_fails():
            call_count[0] += 1
            if call_count[0] < 3:
                raise MemoryError("Low memory")  # Recoverable
            return "success"

        result = sometimes_fails()

        assert result == "success"
        assert call_count[0] == 3

    def test_respects_max_retries(self):
        """retry_on_error should respect max_retries limit."""
        call_count = [0]

        @retry_on_error(max_retries=2)
        def always_fails():
            call_count[0] += 1
            raise MemoryError("Low memory")

        with pytest.raises(MemoryError):
            always_fails()

        # Initial call + 2 retries = 3 total
        assert call_count[0] == 3

    def test_success_on_first_try(self):
        """retry_on_error should work on first successful try."""
        call_count = [0]

        @retry_on_error(max_retries=3)
        def success_func():
            call_count[0] += 1
            return "done"

        result = success_func()

        assert result == "done"
        assert call_count[0] == 1


@pytest.mark.unit
class TestGetErrorHandler:
    """Test get_error_handler function."""

    def test_returns_error_handler(self):
        """get_error_handler should return ErrorHandler instance."""
        handler = get_error_handler()

        assert isinstance(handler, ErrorHandler)

    def test_returns_same_instance(self):
        """get_error_handler should return singleton instance."""
        handler1 = get_error_handler()
        handler2 = get_error_handler()

        assert handler1 is handler2


@pytest.mark.unit
class TestHandleErrorFunction:
    """Test handle_error convenience function."""

    def test_handle_error_returns_standard_error(self):
        """handle_error function should return StandardError."""
        exception = ValueError("Test error")

        result = handle_error(exception)

        assert isinstance(result, StandardError)

    def test_handle_error_with_context(self, error_context: ErrorContext):
        """handle_error function should accept context."""
        exception = ValueError("Test error")

        result = handle_error(exception, error_context)

        assert result.context == error_context
