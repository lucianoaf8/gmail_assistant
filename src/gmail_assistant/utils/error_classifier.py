"""
Error classification logic (H-9 refactoring).

Classifies exceptions into categories for appropriate handling.
Split from error_handler.py for single responsibility.
"""

import traceback
from dataclasses import dataclass
from datetime import datetime
from enum import Enum
from typing import Any

from googleapiclient.errors import HttpError


class ErrorSeverity(Enum):
    """Error severity levels."""
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    CRITICAL = "critical"


class ErrorCategory(Enum):
    """Error categories for classification."""
    AUTHENTICATION = "authentication"
    AUTHORIZATION = "authorization"
    NETWORK = "network"
    API_QUOTA = "api_quota"
    RATE_LIMIT = "rate_limit"
    DATA_VALIDATION = "data_validation"
    FILE_SYSTEM = "file_system"
    MEMORY = "memory"
    CONFIGURATION = "configuration"
    PARSING = "parsing"
    UNKNOWN = "unknown"


@dataclass
class ErrorContext:
    """Context information for errors."""
    operation: str
    user_id: str | None = None
    email_id: str | None = None
    file_path: str | None = None
    query: str | None = None
    additional_data: dict[str, Any] | None = None


@dataclass
class StandardError:
    """Standardized error structure."""
    error_id: str
    category: ErrorCategory
    severity: ErrorSeverity
    message: str
    original_exception: Exception | None
    context: ErrorContext | None
    timestamp: datetime
    recoverable: bool
    user_message: str
    technical_details: str | None = None
    suggested_actions: list[str] | None = None

    def to_dict(self) -> dict[str, Any]:
        """Convert error to dictionary."""
        return {
            'error_id': self.error_id,
            'category': self.category.value,
            'severity': self.severity.value,
            'message': self.message,
            'user_message': self.user_message,
            'timestamp': self.timestamp.isoformat(),
            'recoverable': self.recoverable,
            'technical_details': self.technical_details,
            'suggested_actions': self.suggested_actions,
            'context': {
                'operation': self.context.operation if self.context else None,
                'user_id': self.context.user_id if self.context else None,
                'email_id': self.context.email_id if self.context else None,
                'file_path': self.context.file_path if self.context else None,
                'query': self.context.query if self.context else None,
                'additional_data': self.context.additional_data if self.context else None
            } if self.context else None
        }


class ErrorClassifier:
    """Classify and categorize errors."""

    @staticmethod
    def classify_exception(exception: Exception, context: ErrorContext | None = None) -> StandardError:
        """
        Classify an exception into a standardized error.

        Args:
            exception: The exception to classify
            context: Optional context information

        Returns:
            StandardError object
        """
        error_id = f"ERR_{int(datetime.now().timestamp())}"
        timestamp = datetime.now()

        # HTTP/API errors
        if isinstance(exception, HttpError):
            return ErrorClassifier._classify_http_error(
                exception, error_id, timestamp, context
            )

        # File system errors
        elif isinstance(exception, (FileNotFoundError, PermissionError, OSError)):
            return ErrorClassifier._classify_file_error(
                exception, error_id, timestamp, context
            )

        # Memory errors
        elif isinstance(exception, MemoryError):
            return StandardError(
                error_id=error_id,
                category=ErrorCategory.MEMORY,
                severity=ErrorSeverity.CRITICAL,
                message=str(exception),
                original_exception=exception,
                context=context,
                timestamp=timestamp,
                recoverable=True,
                user_message="System is running low on memory. Try reducing batch size or enabling streaming mode.",
                suggested_actions=[
                    "Reduce the number of emails processed at once",
                    "Enable streaming mode for large operations",
                    "Close other applications to free memory",
                    "Restart the application"
                ]
            )

        # Validation errors
        elif hasattr(exception, '__name__') and 'validation' in exception.__class__.__name__.lower():
            return StandardError(
                error_id=error_id,
                category=ErrorCategory.DATA_VALIDATION,
                severity=ErrorSeverity.MEDIUM,
                message=str(exception),
                original_exception=exception,
                context=context,
                timestamp=timestamp,
                recoverable=True,
                user_message="Invalid input data provided.",
                suggested_actions=[
                    "Check input format and values",
                    "Refer to documentation for valid input examples"
                ]
            )

        # Generic errors
        else:
            return StandardError(
                error_id=error_id,
                category=ErrorCategory.UNKNOWN,
                severity=ErrorSeverity.MEDIUM,
                message=str(exception),
                original_exception=exception,
                context=context,
                timestamp=timestamp,
                recoverable=False,
                user_message="An unexpected error occurred.",
                technical_details=traceback.format_exc(),
                suggested_actions=[
                    "Check application logs for details",
                    "Retry the operation",
                    "Contact support if the issue persists"
                ]
            )

    @staticmethod
    def _classify_http_error(
        exception: HttpError,
        error_id: str,
        timestamp: datetime,
        context: ErrorContext | None
    ) -> StandardError:
        """Classify HTTP/API errors."""
        status_code = exception.resp.status
        error_content = exception.content.decode() if exception.content else ""

        # Authentication errors
        if status_code == 401:
            return StandardError(
                error_id=error_id,
                category=ErrorCategory.AUTHENTICATION,
                severity=ErrorSeverity.HIGH,
                message=f"Authentication failed: {error_content}",
                original_exception=exception,
                context=context,
                timestamp=timestamp,
                recoverable=True,
                user_message="Authentication failed. Please re-authenticate with Gmail.",
                suggested_actions=[
                    "Run authentication setup",
                    "Check credentials.json file",
                    "Verify Gmail API permissions"
                ]
            )

        # Authorization errors
        elif status_code == 403:
            if "quota" in error_content.lower():
                return StandardError(
                    error_id=error_id,
                    category=ErrorCategory.API_QUOTA,
                    severity=ErrorSeverity.HIGH,
                    message=f"API quota exceeded: {error_content}",
                    original_exception=exception,
                    context=context,
                    timestamp=timestamp,
                    recoverable=True,
                    user_message="Gmail API quota exceeded. Please wait or reduce request frequency.",
                    suggested_actions=[
                        "Wait 24 hours for quota reset",
                        "Reduce batch size",
                        "Enable rate limiting"
                    ]
                )
            else:
                return StandardError(
                    error_id=error_id,
                    category=ErrorCategory.AUTHORIZATION,
                    severity=ErrorSeverity.HIGH,
                    message=f"Authorization failed: {error_content}",
                    original_exception=exception,
                    context=context,
                    timestamp=timestamp,
                    recoverable=True,
                    user_message="Insufficient permissions for this operation.",
                    suggested_actions=[
                        "Check Gmail API scopes",
                        "Re-authenticate with required permissions"
                    ]
                )

        # Rate limiting
        elif status_code == 429:
            return StandardError(
                error_id=error_id,
                category=ErrorCategory.RATE_LIMIT,
                severity=ErrorSeverity.MEDIUM,
                message=f"Rate limit exceeded: {error_content}",
                original_exception=exception,
                context=context,
                timestamp=timestamp,
                recoverable=True,
                user_message="Request rate limit exceeded. The operation will be retried automatically.",
                suggested_actions=[
                    "Reduce request frequency",
                    "Enable exponential backoff",
                    "Wait before retrying"
                ]
            )

        # Server errors
        elif 500 <= status_code < 600:
            return StandardError(
                error_id=error_id,
                category=ErrorCategory.NETWORK,
                severity=ErrorSeverity.MEDIUM,
                message=f"Server error {status_code}: {error_content}",
                original_exception=exception,
                context=context,
                timestamp=timestamp,
                recoverable=True,
                user_message="Gmail server is experiencing issues. Please try again later.",
                suggested_actions=[
                    "Wait and retry",
                    "Check Gmail service status",
                    "Try again in a few minutes"
                ]
            )

        # Other HTTP errors
        else:
            return StandardError(
                error_id=error_id,
                category=ErrorCategory.NETWORK,
                severity=ErrorSeverity.MEDIUM,
                message=f"HTTP error {status_code}: {error_content}",
                original_exception=exception,
                context=context,
                timestamp=timestamp,
                recoverable=False,
                user_message=f"Network error occurred (status {status_code}).",
                technical_details=str(exception)
            )

    @staticmethod
    def _classify_file_error(
        exception: Exception,
        error_id: str,
        timestamp: datetime,
        context: ErrorContext | None
    ) -> StandardError:
        """Classify file system errors."""
        if isinstance(exception, FileNotFoundError):
            return StandardError(
                error_id=error_id,
                category=ErrorCategory.FILE_SYSTEM,
                severity=ErrorSeverity.MEDIUM,
                message=str(exception),
                original_exception=exception,
                context=context,
                timestamp=timestamp,
                recoverable=True,
                user_message="Required file not found.",
                suggested_actions=[
                    "Check file path",
                    "Ensure file exists",
                    "Check file permissions"
                ]
            )

        elif isinstance(exception, PermissionError):
            return StandardError(
                error_id=error_id,
                category=ErrorCategory.FILE_SYSTEM,
                severity=ErrorSeverity.HIGH,
                message=str(exception),
                original_exception=exception,
                context=context,
                timestamp=timestamp,
                recoverable=True,
                user_message="Permission denied. Cannot access file or directory.",
                suggested_actions=[
                    "Check file permissions",
                    "Run with appropriate privileges",
                    "Ensure directory is writable"
                ]
            )

        else:
            return StandardError(
                error_id=error_id,
                category=ErrorCategory.FILE_SYSTEM,
                severity=ErrorSeverity.MEDIUM,
                message=str(exception),
                original_exception=exception,
                context=context,
                timestamp=timestamp,
                recoverable=False,
                user_message="File system error occurred.",
                technical_details=str(exception)
            )
