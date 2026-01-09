"""
Circuit Breaker pattern implementation for Gmail API calls.
Prevents cascading failures when the Gmail API is experiencing issues.
"""

import time
import logging
import threading
from enum import Enum
from typing import Callable, Any, Optional
from functools import wraps

logger = logging.getLogger(__name__)


class CircuitState(Enum):
    """Circuit breaker states."""
    CLOSED = "closed"      # Normal operation - requests pass through
    OPEN = "open"          # Failing - requests are rejected
    HALF_OPEN = "half_open"  # Testing recovery - limited requests allowed


class CircuitBreakerError(Exception):
    """Exception raised when circuit breaker is open."""
    def __init__(self, message: str = "Circuit breaker is open"):
        self.message = message
        super().__init__(self.message)


class CircuitBreaker:
    """
    Circuit breaker for protecting Gmail API calls.

    Implements the circuit breaker pattern to prevent cascading failures:
    - CLOSED: Normal operation, requests pass through
    - OPEN: Circuit is tripped, requests fail immediately
    - HALF_OPEN: Testing if service recovered, limited requests allowed

    Usage:
        breaker = CircuitBreaker(failure_threshold=5, recovery_timeout=60)

        @breaker
        def call_gmail_api():
            # API call here
            pass

        # Or use with context:
        with breaker.protect():
            # API call here
            pass
    """

    def __init__(self,
                 failure_threshold: int = 5,
                 recovery_timeout: float = 60.0,
                 half_open_max_calls: int = 3,
                 success_threshold: int = 2):
        """
        Initialize circuit breaker.

        Args:
            failure_threshold: Number of failures before opening circuit
            recovery_timeout: Seconds to wait before attempting recovery
            half_open_max_calls: Max concurrent calls in half-open state
            success_threshold: Successes needed in half-open to close circuit
        """
        self.failure_threshold = failure_threshold
        self.recovery_timeout = recovery_timeout
        self.half_open_max_calls = half_open_max_calls
        self.success_threshold = success_threshold

        # State tracking (protected by lock)
        self._lock = threading.Lock()
        self._state = CircuitState.CLOSED
        self._failure_count = 0
        self._success_count = 0
        self._last_failure_time: Optional[float] = None
        self._half_open_calls = 0

        logger.info(f"Circuit breaker initialized: threshold={failure_threshold}, "
                   f"timeout={recovery_timeout}s")

    @property
    def state(self) -> CircuitState:
        """Get current circuit state."""
        with self._lock:
            return self._state

    @property
    def is_closed(self) -> bool:
        """Check if circuit is closed (normal operation)."""
        return self.state == CircuitState.CLOSED

    @property
    def is_open(self) -> bool:
        """Check if circuit is open (failing)."""
        return self.state == CircuitState.OPEN

    def _check_state_transition(self) -> None:
        """Check if state should transition (must hold lock)."""
        if self._state == CircuitState.OPEN:
            # Check if recovery timeout has passed
            if self._last_failure_time is not None:
                elapsed = time.time() - self._last_failure_time
                if elapsed >= self.recovery_timeout:
                    logger.info("Circuit breaker: OPEN -> HALF_OPEN (recovery timeout)")
                    self._state = CircuitState.HALF_OPEN
                    self._half_open_calls = 0
                    self._success_count = 0

    def _can_execute(self) -> bool:
        """Check if request can be executed (must hold lock)."""
        self._check_state_transition()

        if self._state == CircuitState.CLOSED:
            return True
        elif self._state == CircuitState.OPEN:
            return False
        else:  # HALF_OPEN
            if self._half_open_calls < self.half_open_max_calls:
                self._half_open_calls += 1
                return True
            return False

    def _record_success(self) -> None:
        """Record successful call."""
        with self._lock:
            if self._state == CircuitState.HALF_OPEN:
                self._success_count += 1
                if self._success_count >= self.success_threshold:
                    logger.info("Circuit breaker: HALF_OPEN -> CLOSED (recovery successful)")
                    self._state = CircuitState.CLOSED
                    self._failure_count = 0
                    self._success_count = 0
            elif self._state == CircuitState.CLOSED:
                # Reset failure count on success
                self._failure_count = 0

    def _record_failure(self) -> None:
        """Record failed call."""
        with self._lock:
            self._failure_count += 1
            self._last_failure_time = time.time()

            if self._state == CircuitState.HALF_OPEN:
                logger.warning("Circuit breaker: HALF_OPEN -> OPEN (failure during recovery)")
                self._state = CircuitState.OPEN
            elif self._state == CircuitState.CLOSED:
                if self._failure_count >= self.failure_threshold:
                    logger.warning(f"Circuit breaker: CLOSED -> OPEN "
                                 f"({self._failure_count} failures)")
                    self._state = CircuitState.OPEN

    def call(self, func: Callable, *args, **kwargs) -> Any:
        """
        Execute function through circuit breaker.

        Args:
            func: Function to execute
            *args: Positional arguments for function
            **kwargs: Keyword arguments for function

        Returns:
            Function result

        Raises:
            CircuitBreakerError: If circuit is open
        """
        with self._lock:
            if not self._can_execute():
                raise CircuitBreakerError(
                    f"Circuit breaker is {self._state.value}. "
                    f"Retry after {self.recovery_timeout}s"
                )

        try:
            result = func(*args, **kwargs)
            self._record_success()
            return result
        except Exception as e:
            self._record_failure()
            raise

    def __call__(self, func: Callable) -> Callable:
        """Decorator to wrap function with circuit breaker."""
        @wraps(func)
        def wrapper(*args, **kwargs):
            return self.call(func, *args, **kwargs)
        return wrapper

    def get_stats(self) -> dict:
        """Get circuit breaker statistics."""
        with self._lock:
            return {
                'state': self._state.value,
                'failure_count': self._failure_count,
                'success_count': self._success_count,
                'failure_threshold': self.failure_threshold,
                'recovery_timeout': self.recovery_timeout,
                'last_failure_time': self._last_failure_time
            }

    def reset(self) -> None:
        """Reset circuit breaker to initial state."""
        with self._lock:
            logger.info("Circuit breaker reset to CLOSED")
            self._state = CircuitState.CLOSED
            self._failure_count = 0
            self._success_count = 0
            self._last_failure_time = None
            self._half_open_calls = 0


# Pre-configured circuit breaker for Gmail API
gmail_circuit_breaker = CircuitBreaker(
    failure_threshold=5,
    recovery_timeout=60.0,
    half_open_max_calls=3,
    success_threshold=2
)


def with_circuit_breaker(func: Callable) -> Callable:
    """
    Decorator using the default Gmail circuit breaker.

    Usage:
        @with_circuit_breaker
        def call_gmail_api():
            # API call
            pass
    """
    return gmail_circuit_breaker(func)
