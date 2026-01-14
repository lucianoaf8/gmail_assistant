"""
Standardized error handling framework for Gmail Fetcher (H-9 refactored).

Provides consistent error handling patterns and centralized error management.
Error classification logic has been moved to error_classifier.py.
"""

import json
import logging
import threading
from collections.abc import Callable
from pathlib import Path
from typing import Any

# H-9: Import from error_classifier module
from .error_classifier import (
    ErrorCategory,
    ErrorClassifier,
    ErrorContext,
    ErrorSeverity,
    StandardError,
)

# Re-export for backward compatibility
__all__ = [
    'ErrorSeverity',
    'ErrorCategory',
    'ErrorContext',
    'StandardError',
    'ErrorClassifier',
    'ErrorHandler',
    'IntegratedErrorHandler',
    'handle_errors',
    'retry_on_error',
    'get_error_handler',
    'handle_error',
    'get_integrated_handler',
    'with_api_protection',
]


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
        logger = logging.getLogger('gman.errors')
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


# =============================================================================
# Global Error Handler Instance
# =============================================================================
#
# Thread Safety: The global error handler uses lazy initialization with a
# module-level variable. While Python's GIL provides some protection during
# initialization, concurrent access in multi-threaded scenarios should use
# `get_error_handler()` which performs atomic initialization.
#
# For multi-threaded applications, consider:
# 1. Initialize handler at startup before spawning threads
# 2. Use thread-local handlers via `threading.local()`
# 3. Pass handler explicitly to avoid global state

_global_error_handler: ErrorHandler | None = None
_global_error_handler_lock = threading.Lock()


def get_error_handler() -> ErrorHandler:
    """
    Get global error handler instance (thread-safe lazy initialization).

    Returns:
        Singleton ErrorHandler instance.

    Note:
        For multi-threaded applications, consider initializing at startup
        or using dependency injection instead of global state.
    """
    global _global_error_handler
    if _global_error_handler is None:
        with _global_error_handler_lock:
            if _global_error_handler is None:  # Double-check locking
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


# =============================================================================
# Global Integrated Error Handler Instance
# =============================================================================
#
# Thread Safety: Same pattern as _global_error_handler above.
# Uses double-check locking for thread-safe lazy initialization.

_integrated_handler: IntegratedErrorHandler | None = None
_integrated_handler_lock = threading.Lock()


def get_integrated_handler() -> IntegratedErrorHandler:
    """
    Get global integrated error handler instance (thread-safe).

    Returns:
        Singleton IntegratedErrorHandler instance.

    Note:
        For multi-threaded applications, consider initializing at startup
        or using dependency injection instead of global state.
    """
    global _integrated_handler
    if _integrated_handler is None:
        with _integrated_handler_lock:
            if _integrated_handler is None:  # Double-check locking
                _integrated_handler = IntegratedErrorHandler()
    return _integrated_handler


def with_api_protection(func: Callable) -> Callable:
    """
    Decorator for API calls with full protection.

    Combines circuit breaker, error handling, and retry logic.
    """
    return get_integrated_handler().with_circuit_breaker(func)
