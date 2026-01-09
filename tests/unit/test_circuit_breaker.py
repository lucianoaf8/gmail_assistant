"""Unit tests for gmail_assistant.utils.circuit_breaker module."""
from __future__ import annotations

import time
import threading
from unittest import mock

import pytest

from gmail_assistant.utils.circuit_breaker import (
    CircuitState,
    CircuitBreakerError,
    CircuitBreaker,
    gmail_circuit_breaker,
    with_circuit_breaker,
)


@pytest.fixture
def circuit_breaker():
    """Create a circuit breaker for testing."""
    return CircuitBreaker(
        failure_threshold=3,
        recovery_timeout=0.1,  # Fast recovery for testing
        half_open_max_calls=2,
        success_threshold=2
    )


@pytest.mark.unit
class TestCircuitState:
    """Test CircuitState enumeration."""

    def test_closed_value(self):
        """CLOSED should have expected value."""
        assert CircuitState.CLOSED.value == "closed"

    def test_open_value(self):
        """OPEN should have expected value."""
        assert CircuitState.OPEN.value == "open"

    def test_half_open_value(self):
        """HALF_OPEN should have expected value."""
        assert CircuitState.HALF_OPEN.value == "half_open"


@pytest.mark.unit
class TestCircuitBreakerError:
    """Test CircuitBreakerError exception."""

    def test_is_exception(self):
        """CircuitBreakerError should inherit from Exception."""
        assert issubclass(CircuitBreakerError, Exception)

    def test_with_default_message(self):
        """CircuitBreakerError should have default message."""
        error = CircuitBreakerError()
        assert "open" in str(error).lower()

    def test_with_custom_message(self):
        """CircuitBreakerError should preserve custom message."""
        error = CircuitBreakerError("Custom error message")
        assert str(error) == "Custom error message"


@pytest.mark.unit
class TestCircuitBreakerInit:
    """Test CircuitBreaker initialization."""

    def test_default_initialization(self):
        """CircuitBreaker should initialize with defaults."""
        cb = CircuitBreaker()

        assert cb.failure_threshold == 5
        assert cb.recovery_timeout == 60.0
        assert cb.half_open_max_calls == 3
        assert cb.success_threshold == 2

    def test_custom_initialization(self):
        """CircuitBreaker should accept custom parameters."""
        cb = CircuitBreaker(
            failure_threshold=10,
            recovery_timeout=30.0,
            half_open_max_calls=5,
            success_threshold=3
        )

        assert cb.failure_threshold == 10
        assert cb.recovery_timeout == 30.0
        assert cb.half_open_max_calls == 5
        assert cb.success_threshold == 3

    def test_initial_state_is_closed(self):
        """CircuitBreaker should start in CLOSED state."""
        cb = CircuitBreaker()
        assert cb.state == CircuitState.CLOSED


@pytest.mark.unit
class TestCircuitBreakerProperties:
    """Test CircuitBreaker property methods."""

    def test_state_property(self, circuit_breaker: CircuitBreaker):
        """state property should return current state."""
        assert circuit_breaker.state == CircuitState.CLOSED

    def test_is_closed_property(self, circuit_breaker: CircuitBreaker):
        """is_closed property should return True when closed."""
        assert circuit_breaker.is_closed is True

    def test_is_open_property(self, circuit_breaker: CircuitBreaker):
        """is_open property should return False when closed."""
        assert circuit_breaker.is_open is False


@pytest.mark.unit
class TestCircuitBreakerCall:
    """Test CircuitBreaker call method."""

    def test_call_success_when_closed(self, circuit_breaker: CircuitBreaker):
        """call should execute function when circuit is closed."""

        def my_func(x, y):
            return x + y

        result = circuit_breaker.call(my_func, 2, 3)

        assert result == 5

    def test_call_with_kwargs(self, circuit_breaker: CircuitBreaker):
        """call should pass kwargs to function."""

        def my_func(a, b=10):
            return a + b

        result = circuit_breaker.call(my_func, 5, b=20)

        assert result == 25

    def test_call_raises_when_circuit_open(self, circuit_breaker: CircuitBreaker):
        """call should raise CircuitBreakerError when circuit is open."""
        # Force circuit to OPEN state
        circuit_breaker._state = CircuitState.OPEN
        circuit_breaker._last_failure_time = time.time()  # Recent failure

        with pytest.raises(CircuitBreakerError, match="open"):
            circuit_breaker.call(lambda: "test")


@pytest.mark.unit
class TestCircuitBreakerStateTransitions:
    """Test circuit breaker state transitions."""

    def test_closed_to_open_on_failure_threshold(
        self, circuit_breaker: CircuitBreaker
    ):
        """Circuit should open after reaching failure threshold."""

        def failing_func():
            raise ValueError("Error")

        # Fail enough times to trip the breaker
        for _ in range(circuit_breaker.failure_threshold):
            try:
                circuit_breaker.call(failing_func)
            except ValueError:
                pass

        assert circuit_breaker.state == CircuitState.OPEN

    def test_open_to_half_open_after_timeout(
        self, circuit_breaker: CircuitBreaker
    ):
        """Circuit should transition to HALF_OPEN after recovery timeout."""
        # Force circuit to OPEN with old failure time
        circuit_breaker._state = CircuitState.OPEN
        circuit_breaker._last_failure_time = time.time() - 1.0  # Old failure

        # Trigger state check
        def test_func():
            return "success"

        result = circuit_breaker.call(test_func)

        assert circuit_breaker.state in [CircuitState.HALF_OPEN, CircuitState.CLOSED]
        assert result == "success"

    def test_half_open_to_closed_on_success(
        self, circuit_breaker: CircuitBreaker
    ):
        """Circuit should close after successes in HALF_OPEN state."""
        circuit_breaker._state = CircuitState.HALF_OPEN
        circuit_breaker._success_count = 0

        def success_func():
            return "success"

        # Succeed enough times
        for _ in range(circuit_breaker.success_threshold):
            circuit_breaker.call(success_func)

        assert circuit_breaker.state == CircuitState.CLOSED

    def test_half_open_to_open_on_failure(
        self, circuit_breaker: CircuitBreaker
    ):
        """Circuit should re-open on failure during HALF_OPEN."""
        circuit_breaker._state = CircuitState.HALF_OPEN

        def failing_func():
            raise ValueError("Error")

        try:
            circuit_breaker.call(failing_func)
        except ValueError:
            pass

        assert circuit_breaker.state == CircuitState.OPEN

    def test_success_resets_failure_count_when_closed(
        self, circuit_breaker: CircuitBreaker
    ):
        """Success should reset failure count when circuit is closed."""
        # Record some failures
        circuit_breaker._failure_count = 2

        def success_func():
            return "success"

        circuit_breaker.call(success_func)

        assert circuit_breaker._failure_count == 0


@pytest.mark.unit
class TestCircuitBreakerHalfOpenLimits:
    """Test HALF_OPEN state call limits."""

    def test_half_open_limits_concurrent_calls(
        self, circuit_breaker: CircuitBreaker
    ):
        """HALF_OPEN state should limit concurrent calls."""
        circuit_breaker._state = CircuitState.HALF_OPEN
        circuit_breaker._half_open_calls = circuit_breaker.half_open_max_calls

        with pytest.raises(CircuitBreakerError):
            circuit_breaker.call(lambda: "test")


@pytest.mark.unit
class TestCircuitBreakerDecorator:
    """Test CircuitBreaker as decorator."""

    def test_decorator_wraps_function(self, circuit_breaker: CircuitBreaker):
        """CircuitBreaker should work as a decorator."""

        @circuit_breaker
        def my_func(x):
            return x * 2

        result = my_func(5)

        assert result == 10

    def test_decorator_handles_exceptions(
        self, circuit_breaker: CircuitBreaker
    ):
        """Decorator should record failures from exceptions."""

        @circuit_breaker
        def failing_func():
            raise ValueError("Error")

        for _ in range(circuit_breaker.failure_threshold):
            try:
                failing_func()
            except ValueError:
                pass

        assert circuit_breaker.state == CircuitState.OPEN


@pytest.mark.unit
class TestCircuitBreakerGetStats:
    """Test get_stats method."""

    def test_get_stats_initial(self, circuit_breaker: CircuitBreaker):
        """get_stats should return initial statistics."""
        stats = circuit_breaker.get_stats()

        assert stats["state"] == "closed"
        assert stats["failure_count"] == 0
        assert stats["success_count"] == 0
        assert stats["failure_threshold"] == 3
        assert stats["recovery_timeout"] == 0.1

    def test_get_stats_after_failures(self, circuit_breaker: CircuitBreaker):
        """get_stats should reflect failures."""
        circuit_breaker._failure_count = 2
        circuit_breaker._last_failure_time = time.time()

        stats = circuit_breaker.get_stats()

        assert stats["failure_count"] == 2
        assert stats["last_failure_time"] is not None


@pytest.mark.unit
class TestCircuitBreakerReset:
    """Test reset method."""

    def test_reset_returns_to_closed_state(
        self, circuit_breaker: CircuitBreaker
    ):
        """reset should return circuit to CLOSED state."""
        circuit_breaker._state = CircuitState.OPEN
        circuit_breaker._failure_count = 5
        circuit_breaker._success_count = 1
        circuit_breaker._last_failure_time = time.time()

        circuit_breaker.reset()

        assert circuit_breaker.state == CircuitState.CLOSED
        assert circuit_breaker._failure_count == 0
        assert circuit_breaker._success_count == 0
        assert circuit_breaker._last_failure_time is None


@pytest.mark.unit
class TestGmailCircuitBreaker:
    """Test pre-configured Gmail circuit breaker."""

    def test_gmail_circuit_breaker_exists(self):
        """gmail_circuit_breaker should be a CircuitBreaker instance."""
        assert isinstance(gmail_circuit_breaker, CircuitBreaker)

    def test_gmail_circuit_breaker_configuration(self):
        """gmail_circuit_breaker should have expected configuration."""
        assert gmail_circuit_breaker.failure_threshold == 5
        assert gmail_circuit_breaker.recovery_timeout == 60.0
        assert gmail_circuit_breaker.half_open_max_calls == 3
        assert gmail_circuit_breaker.success_threshold == 2


@pytest.mark.unit
class TestWithCircuitBreakerDecorator:
    """Test with_circuit_breaker decorator function."""

    def test_with_circuit_breaker_uses_gmail_breaker(self):
        """with_circuit_breaker should use global gmail_circuit_breaker."""
        # Reset the global breaker first
        gmail_circuit_breaker.reset()

        @with_circuit_breaker
        def my_func():
            return "success"

        result = my_func()

        assert result == "success"

    def test_with_circuit_breaker_decorator(self):
        """with_circuit_breaker should work as a decorator."""
        gmail_circuit_breaker.reset()

        @with_circuit_breaker
        def failing_func():
            raise ValueError("Error")

        for _ in range(gmail_circuit_breaker.failure_threshold):
            try:
                failing_func()
            except ValueError:
                pass

        assert gmail_circuit_breaker.state == CircuitState.OPEN

        # Reset after test
        gmail_circuit_breaker.reset()


@pytest.mark.unit
class TestCircuitBreakerThreadSafety:
    """Test circuit breaker thread safety."""

    def test_concurrent_calls_are_thread_safe(
        self, circuit_breaker: CircuitBreaker
    ):
        """Circuit breaker should handle concurrent calls safely."""
        results = []
        errors = []

        def make_call():
            try:
                for _ in range(10):
                    result = circuit_breaker.call(lambda: "success")
                    results.append(result)
            except Exception as e:
                errors.append(e)

        threads = [threading.Thread(target=make_call) for _ in range(5)]

        for t in threads:
            t.start()
        for t in threads:
            t.join()

        assert len(errors) == 0
        assert len(results) == 50

    def test_concurrent_failures_handled(self, circuit_breaker: CircuitBreaker):
        """Circuit breaker should handle concurrent failures safely."""
        errors_caught = []

        def make_failing_call():
            try:
                circuit_breaker.call(lambda: (_ for _ in ()).throw(ValueError("Error")))
            except (ValueError, CircuitBreakerError) as e:
                errors_caught.append(e)

        threads = [threading.Thread(target=make_failing_call) for _ in range(10)]

        for t in threads:
            t.start()
        for t in threads:
            t.join()

        # Should have caught some errors
        assert len(errors_caught) > 0


@pytest.mark.unit
class TestCircuitBreakerRecoveryFlow:
    """Test complete recovery flow scenarios."""

    def test_complete_failure_and_recovery_cycle(self):
        """Test full cycle: closed -> open -> half-open -> closed."""
        cb = CircuitBreaker(
            failure_threshold=2,
            recovery_timeout=0.1,
            half_open_max_calls=1,
            success_threshold=1
        )

        # Start closed
        assert cb.state == CircuitState.CLOSED

        # Fail to open
        for _ in range(2):
            try:
                cb.call(lambda: (_ for _ in ()).throw(ValueError("Error")))
            except ValueError:
                pass

        assert cb.state == CircuitState.OPEN

        # Wait for recovery timeout
        time.sleep(0.15)

        # Should transition to half-open and then closed on success
        result = cb.call(lambda: "recovered")

        assert result == "recovered"
        assert cb.state == CircuitState.CLOSED
