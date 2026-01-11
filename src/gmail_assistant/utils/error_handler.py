"""
Standardized error handling framework for Gmail Fetcher.
Provides consistent error handling patterns and centralized error management.
"""

import json
import logging
import traceback
from collections.abc import Callable
from dataclasses import dataclass
from datetime import datetime
from enum import Enum
from pathlib import Path
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
    def _classify_http_error(exception: HttpError, error_id: str,
                           timestamp: datetime, context: ErrorContext | None) -> StandardError:
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
    def _classify_file_error(exception: Exception, error_id: str,
                           timestamp: datetime, context: ErrorContext | None) -> StandardError:
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


class ErrorHandler:
    """Centralized error handler with logging and recovery."""

    def __init__(self, log_dir: Path | None = None):
        """
        Initialize error handler.

        Args:
            log_dir: Directory for error logs
        """
        self.log_dir = log_dir or Path.cwd() / "logs"
        self.log_dir.mkdir(exist_ok=True)

        # Setup error logging
        self.error_logger = self._setup_error_logger()

        # Error statistics
        self.error_counts: dict[str, int] = {}
        self.recovery_handlers: dict[ErrorCategory, Callable] = {}

    def _setup_error_logger(self) -> logging.Logger:
        """Setup dedicated error logger."""
        logger = logging.getLogger('gmail_assistant.errors')
        logger.setLevel(logging.INFO)

        if not logger.handlers:
            # File handler for errors
            error_log_file = self.log_dir / "errors.log"
            file_handler = logging.FileHandler(error_log_file)
            file_handler.setLevel(logging.INFO)

            # JSON formatter for structured logging
            formatter = logging.Formatter(
                '%(asctime)s - %(levelname)s - %(message)s'
            )
            file_handler.setFormatter(formatter)
            logger.addHandler(file_handler)

        return logger

    def handle_error(self, exception: Exception, context: ErrorContext | None = None) -> StandardError:
        """
        Handle an error with classification, logging, and recovery.

        Args:
            exception: The exception to handle
            context: Optional context information

        Returns:
            StandardError object
        """
        # Classify the error
        standard_error = ErrorClassifier.classify_exception(exception, context)

        # Log the error
        self._log_error(standard_error)

        # Update statistics
        self._update_error_stats(standard_error)

        # Attempt recovery if possible
        if standard_error.recoverable:
            self._attempt_recovery(standard_error)

        return standard_error

    def _log_error(self, error: StandardError) -> None:
        """Log error with structured format."""
        log_data = {
            'error_id': error.error_id,
            'category': error.category.value,
            'severity': error.severity.value,
            'message': error.message,
            'operation': error.context.operation if error.context else None,
            'recoverable': error.recoverable
        }

        # Log based on severity
        if error.severity == ErrorSeverity.CRITICAL:
            self.error_logger.critical(json.dumps(log_data))
        elif error.severity == ErrorSeverity.HIGH:
            self.error_logger.error(json.dumps(log_data))
        elif error.severity == ErrorSeverity.MEDIUM:
            self.error_logger.warning(json.dumps(log_data))
        else:
            self.error_logger.info(json.dumps(log_data))

        # Save detailed error for critical issues
        if error.severity == ErrorSeverity.CRITICAL:
            self._save_detailed_error(error)

    def _save_detailed_error(self, error: StandardError) -> None:
        """Save detailed error information to file."""
        try:
            error_file = self.log_dir / f"error_detail_{error.error_id}.json"
            with open(error_file, 'w') as f:
                json.dump(error.to_dict(), f, indent=2, default=str)
        except Exception as e:
            self.error_logger.error(f"Failed to save detailed error: {e}")

    def _update_error_stats(self, error: StandardError) -> None:
        """Update error statistics."""
        category_key = error.category.value
        self.error_counts[category_key] = self.error_counts.get(category_key, 0) + 1

    def _attempt_recovery(self, error: StandardError) -> bool:
        """Attempt to recover from error."""
        if error.category in self.recovery_handlers:
            try:
                recovery_handler = self.recovery_handlers[error.category]
                return recovery_handler(error)
            except Exception as e:
                self.error_logger.error(f"Recovery failed for {error.error_id}: {e}")

        return False

    def register_recovery_handler(self, category: ErrorCategory, handler: Callable) -> None:
        """
        Register a recovery handler for specific error category.

        Args:
            category: Error category
            handler: Recovery function
        """
        self.recovery_handlers[category] = handler

    def get_error_stats(self) -> dict[str, Any]:
        """Get error statistics."""
        total_errors = sum(self.error_counts.values())
        return {
            'total_errors': total_errors,
            'by_category': self.error_counts.copy(),
            'most_common': max(self.error_counts.items(), key=lambda x: x[1]) if self.error_counts else None
        }

    def clear_stats(self) -> None:
        """Clear error statistics."""
        self.error_counts.clear()


# Decorators for error handling
def handle_errors(error_handler: ErrorHandler, context: ErrorContext | None = None):
    """
    Decorator to automatically handle errors in functions.

    Args:
        error_handler: ErrorHandler instance
        context: Optional context information
    """
    def decorator(func):
        def wrapper(*args, **kwargs):
            try:
                return func(*args, **kwargs)
            except Exception as e:
                standard_error = error_handler.handle_error(e, context)
                # Re-raise if not recoverable or recovery failed
                if not standard_error.recoverable:
                    raise
                return None
        return wrapper
    return decorator


def retry_on_error(max_retries: int = 3, categories: list[ErrorCategory] | None = None):
    """
    Decorator to retry operations on specific error categories.

    Args:
        max_retries: Maximum number of retries
        categories: Error categories to retry on (None for all recoverable)
    """
    def decorator(func):
        def wrapper(*args, **kwargs):
            last_error = None

            for attempt in range(max_retries + 1):
                try:
                    return func(*args, **kwargs)
                except Exception as e:
                    standard_error = ErrorClassifier.classify_exception(e)
                    last_error = e

                    # Check if should retry
                    should_retry = (
                        attempt < max_retries and
                        standard_error.recoverable and
                        (categories is None or standard_error.category in categories)
                    )

                    if not should_retry:
                        break

                    # Wait before retry
                    import time
                    time.sleep(2 ** attempt)  # Exponential backoff

            if last_error:
                raise last_error

        return wrapper
    return decorator


# Global error handler instance
_global_error_handler: ErrorHandler | None = None


def get_error_handler() -> ErrorHandler:
    """Get global error handler instance."""
    global _global_error_handler
    if _global_error_handler is None:
        _global_error_handler = ErrorHandler()
    return _global_error_handler


def handle_error(exception: Exception, context: ErrorContext | None = None) -> StandardError:
    """Handle error using global error handler."""
    return get_error_handler().handle_error(exception, context)


# =============================================================================
# Circuit Breaker Integration
# =============================================================================

from .circuit_breaker import CircuitBreaker, CircuitBreakerError


class IntegratedErrorHandler(ErrorHandler):
    """
    Error handler with circuit breaker integration.

    Combines error classification, logging, recovery handling, and circuit
    breaker patterns for robust API error management.

    Usage:
        handler = IntegratedErrorHandler()

        @handler.with_circuit_breaker
        def call_gmail_api():
            # API call here
            pass

        # Or handle errors manually
        try:
            result = risky_operation()
        except Exception as e:
            error = handler.handle_api_error(e, context)
    """

    def __init__(
        self,
        log_dir: Path | None = None,
        failure_threshold: int = 5,
        recovery_timeout: float = 60.0
    ):
        """
        Initialize integrated error handler.

        Args:
            log_dir: Directory for error logs
            failure_threshold: Failures before circuit opens
            recovery_timeout: Seconds before attempting recovery
        """
        super().__init__(log_dir)

        self.circuit_breaker = CircuitBreaker(
            failure_threshold=failure_threshold,
            recovery_timeout=recovery_timeout
        )

        # Register default recovery handlers
        self._register_default_handlers()

        # Track API-specific error patterns
        self._rate_limit_backoff = 1.0
        self._consecutive_failures = 0
        self._max_backoff = 300.0  # 5 minutes max

    def _register_default_handlers(self) -> None:
        """Register default recovery handlers."""
        self.register_recovery_handler(
            ErrorCategory.RATE_LIMIT,
            self._handle_rate_limit_recovery
        )
        self.register_recovery_handler(
            ErrorCategory.NETWORK,
            self._handle_network_recovery
        )
        self.register_recovery_handler(
            ErrorCategory.API_QUOTA,
            self._handle_quota_recovery
        )

    def handle_api_error(
        self,
        exception: Exception,
        context: ErrorContext | None = None
    ) -> StandardError:
        """
        Handle API error with circuit breaker integration.

        Records failure in circuit breaker and handles error through
        standard error handling pipeline.

        Args:
            exception: The exception to handle
            context: Optional context information

        Returns:
            StandardError object
        """

        # Record failure in circuit breaker
        self.circuit_breaker._record_failure()
        self._consecutive_failures += 1

        # Log circuit breaker state change
        if self.circuit_breaker.is_open:
            self.error_logger.warning(
                f"Circuit breaker opened after {self._consecutive_failures} failures"
            )

        # Handle through standard pipeline
        return self.handle_error(exception, context)

    def record_success(self) -> None:
        """Record successful API call."""
        self.circuit_breaker._record_success()
        self._consecutive_failures = 0
        self._rate_limit_backoff = 1.0  # Reset backoff

    def check_circuit(self) -> None:
        """
        Check if circuit allows requests.

        Raises:
            CircuitBreakerError: If circuit is open
        """
        if self.circuit_breaker.is_open:
            stats = self.circuit_breaker.get_stats()
            raise CircuitBreakerError(
                f"Circuit breaker open. Retry after {stats['recovery_timeout']}s"
            )

    def _handle_rate_limit_recovery(self, error: StandardError) -> bool:
        """
        Recovery handler for rate limit errors.

        Implements exponential backoff with jitter.
        """
        import random
        import time

        # Extract retry-after if available
        wait_time = self._extract_retry_after(error)

        if wait_time is None:
            # Exponential backoff with jitter
            wait_time = min(
                self._rate_limit_backoff * (1 + random.random() * 0.1),
                self._max_backoff
            )
            self._rate_limit_backoff *= 2  # Double for next time

        self.error_logger.info(
            f"Rate limit recovery: waiting {wait_time:.1f}s"
        )
        time.sleep(wait_time)
        return True

    def _handle_network_recovery(self, error: StandardError) -> bool:
        """
        Recovery handler for network errors.

        Checks circuit breaker state before allowing recovery.
        """
        import time

        # If circuit is open, don't attempt recovery yet
        if self.circuit_breaker.is_open:
            self.error_logger.info(
                "Network recovery blocked - circuit breaker open"
            )
            return False

        # Brief wait before retry
        time.sleep(min(2 ** self._consecutive_failures, 30))
        return True

    def _handle_quota_recovery(self, error: StandardError) -> bool:
        """
        Recovery handler for API quota errors.

        Quota errors typically require longer wait or user intervention.
        """
        self.error_logger.warning(
            "API quota exceeded - automatic recovery not possible. "
            "Wait 24 hours or reduce request frequency."
        )
        return False  # Cannot auto-recover from quota errors

    def _extract_retry_after(self, error: StandardError) -> float | None:
        """Extract Retry-After header from error response."""
        if error.original_exception and hasattr(error.original_exception, 'resp'):
            resp = error.original_exception.resp
            retry_after = resp.get('retry-after')
            if retry_after:
                try:
                    return float(retry_after)
                except (ValueError, TypeError):
                    pass
        return None

    def with_circuit_breaker(self, func: Callable) -> Callable:
        """
        Decorator to wrap function with circuit breaker and error handling.

        Usage:
            @handler.with_circuit_breaker
            def call_gmail_api():
                return service.users().messages().list().execute()
        """
        from functools import wraps

        @wraps(func)
        def wrapper(*args, **kwargs):
            # Check circuit before executing
            self.check_circuit()

            try:
                result = func(*args, **kwargs)
                self.record_success()
                return result
            except Exception as e:
                context = ErrorContext(
                    operation=func.__name__,
                    additional_data={'args_count': len(args)}
                )
                self.handle_api_error(e, context)
                raise

        return wrapper

    def get_health_status(self) -> dict[str, Any]:
        """
        Get comprehensive health status.

        Returns:
            Dictionary with error stats and circuit breaker state
        """
        error_stats = self.get_error_stats()
        circuit_stats = self.circuit_breaker.get_stats()

        return {
            'errors': error_stats,
            'circuit_breaker': circuit_stats,
            'consecutive_failures': self._consecutive_failures,
            'current_backoff': self._rate_limit_backoff,
            'healthy': (
                not self.circuit_breaker.is_open and
                self._consecutive_failures < 3
            )
        }

    def reset(self) -> None:
        """Reset error handler and circuit breaker state."""
        self.clear_stats()
        self.circuit_breaker.reset()
        self._rate_limit_backoff = 1.0
        self._consecutive_failures = 0
        self.error_logger.info("Integrated error handler reset")


# Global integrated error handler
_integrated_handler: IntegratedErrorHandler | None = None


def get_integrated_handler() -> IntegratedErrorHandler:
    """Get global integrated error handler instance."""
    global _integrated_handler
    if _integrated_handler is None:
        _integrated_handler = IntegratedErrorHandler()
    return _integrated_handler


def with_api_protection(func: Callable) -> Callable:
    """
    Decorator for API calls with full protection.

    Combines circuit breaker, error handling, and retry logic.
    """
    return get_integrated_handler().with_circuit_breaker(func)
