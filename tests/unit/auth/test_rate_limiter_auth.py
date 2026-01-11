"""Unit tests for gmail_assistant.core.auth.rate_limiter module."""
from __future__ import annotations

import time
from unittest.mock import patch

import pytest

from gmail_assistant.core.auth.rate_limiter import (
    AuthRateLimiter,
    RateLimitState,
    get_auth_rate_limiter,
)


@pytest.fixture
def rate_limiter():
    """Create a fresh AuthRateLimiter instance for testing."""
    return AuthRateLimiter()


@pytest.mark.unit
class TestRateLimitState:
    """Test RateLimitState dataclass."""

    def test_create_default_state(self):
        """Should create state with default values."""
        state = RateLimitState()

        assert state.attempts == 0
        assert state.first_attempt == 0.0
        assert state.locked_until == 0.0

    def test_create_state_with_values(self):
        """Should create state with custom values."""
        now = time.time()
        state = RateLimitState(attempts=3, first_attempt=now, locked_until=now + 100)

        assert state.attempts == 3
        assert state.first_attempt == now
        assert state.locked_until == now + 100


@pytest.mark.unit
class TestAuthRateLimiterInit:
    """Test AuthRateLimiter initialization."""

    def test_init_creates_empty_states(self):
        """Should initialize with empty state storage."""
        limiter = AuthRateLimiter()

        assert limiter._states == {}
        assert limiter._lock is not None

    def test_init_has_correct_constants(self):
        """Should have correct rate limiting constants."""
        limiter = AuthRateLimiter()

        assert limiter.MAX_ATTEMPTS == 5
        assert limiter.WINDOW_SECONDS == 300  # 5 minutes
        assert limiter.LOCKOUT_SECONDS == 900  # 15 minutes


@pytest.mark.unit
class TestCheckRateLimit:
    """Test check_rate_limit method."""

    def test_check_rate_limit_new_identifier(self, rate_limiter):
        """Should allow authentication for new identifier."""
        result = rate_limiter.check_rate_limit("test_user")

        assert result is True

    def test_check_rate_limit_under_limit(self, rate_limiter):
        """Should allow authentication when under attempt limit."""
        identifier = "test_user"

        # Record some failed attempts (but not at limit)
        for i in range(3):
            rate_limiter.record_attempt(identifier, success=False)

        result = rate_limiter.check_rate_limit(identifier)

        assert result is True

    def test_check_rate_limit_at_limit(self, rate_limiter):
        """Should deny authentication when at attempt limit."""
        identifier = "test_user"

        # Record max failed attempts
        for i in range(rate_limiter.MAX_ATTEMPTS):
            rate_limiter.record_attempt(identifier, success=False)

        result = rate_limiter.check_rate_limit(identifier)

        assert result is False

    def test_check_rate_limit_locked_out(self, rate_limiter):
        """Should deny authentication when locked out."""
        identifier = "test_user"

        # Manually set lockout
        with patch("time.time") as mock_time:
            now = 1000.0
            mock_time.return_value = now

            rate_limiter._states[identifier] = RateLimitState(
                attempts=5, first_attempt=now - 100, locked_until=now + 500
            )

            result = rate_limiter.check_rate_limit(identifier)

            assert result is False

    def test_check_rate_limit_window_expired(self, rate_limiter):
        """Should reset attempts when window expires."""
        identifier = "test_user"

        with patch("time.time") as mock_time:
            # Initial attempts at time 0
            mock_time.return_value = 0.0
            for i in range(3):
                rate_limiter.record_attempt(identifier, success=False)

            # Move past window expiration (> 300 seconds)
            mock_time.return_value = 400.0

            result = rate_limiter.check_rate_limit(identifier)

            # Should be allowed since window expired
            assert result is True

            # Attempts should be reset
            state = rate_limiter._states[identifier]
            assert state.attempts == 0


@pytest.mark.unit
class TestRecordAttempt:
    """Test record_attempt method."""

    def test_record_attempt_success_resets_state(self, rate_limiter):
        """Should reset state on successful attempt."""
        identifier = "test_user"

        # Record failed attempts first
        for i in range(3):
            rate_limiter.record_attempt(identifier, success=False)

        # Record successful attempt
        rate_limiter.record_attempt(identifier, success=True)

        state = rate_limiter._states[identifier]
        assert state.attempts == 0
        assert state.locked_until == 0

    def test_record_attempt_failure_increments(self, rate_limiter):
        """Should increment attempt count on failure."""
        identifier = "test_user"

        rate_limiter.record_attempt(identifier, success=False)

        state = rate_limiter._states[identifier]
        assert state.attempts == 1

    def test_record_attempt_multiple_failures(self, rate_limiter):
        """Should track multiple failed attempts."""
        identifier = "test_user"

        for i in range(3):
            rate_limiter.record_attempt(identifier, success=False)

        state = rate_limiter._states[identifier]
        assert state.attempts == 3

    def test_record_attempt_triggers_lockout(self, rate_limiter):
        """Should trigger lockout after max attempts."""
        identifier = "test_user"

        with patch("time.time") as mock_time:
            mock_time.return_value = 1000.0

            for i in range(rate_limiter.MAX_ATTEMPTS):
                rate_limiter.record_attempt(identifier, success=False)

            state = rate_limiter._states[identifier]
            assert state.locked_until > 1000.0

    def test_record_attempt_first_failure_sets_timestamp(self, rate_limiter):
        """Should set first_attempt timestamp on first failure."""
        identifier = "test_user"

        with patch("time.time") as mock_time:
            mock_time.return_value = 1234.5

            rate_limiter.record_attempt(identifier, success=False)

            state = rate_limiter._states[identifier]
            assert state.first_attempt == 1234.5


@pytest.mark.unit
class TestGetRemainingAttempts:
    """Test get_remaining_attempts method."""

    def test_get_remaining_attempts_new_identifier(self, rate_limiter):
        """Should return max attempts for new identifier."""
        result = rate_limiter.get_remaining_attempts("new_user")

        assert result == rate_limiter.MAX_ATTEMPTS

    def test_get_remaining_attempts_after_failures(self, rate_limiter):
        """Should return correct remaining attempts."""
        identifier = "test_user"

        # Record 2 failed attempts
        for i in range(2):
            rate_limiter.record_attempt(identifier, success=False)

        result = rate_limiter.get_remaining_attempts(identifier)

        assert result == rate_limiter.MAX_ATTEMPTS - 2

    def test_get_remaining_attempts_at_limit(self, rate_limiter):
        """Should return 0 when at limit."""
        identifier = "test_user"

        for i in range(rate_limiter.MAX_ATTEMPTS):
            rate_limiter.record_attempt(identifier, success=False)

        result = rate_limiter.get_remaining_attempts(identifier)

        assert result == 0

    def test_get_remaining_attempts_window_expired(self, rate_limiter):
        """Should return max attempts when window expired."""
        identifier = "test_user"

        with patch("time.time") as mock_time:
            # Initial attempts at time 0
            mock_time.return_value = 0.0
            for i in range(3):
                rate_limiter.record_attempt(identifier, success=False)

            # Move past window expiration
            mock_time.return_value = 400.0

            result = rate_limiter.get_remaining_attempts(identifier)

            assert result == rate_limiter.MAX_ATTEMPTS


@pytest.mark.unit
class TestGetLockoutRemaining:
    """Test get_lockout_remaining method."""

    def test_get_lockout_remaining_not_locked(self, rate_limiter):
        """Should return 0 when not locked out."""
        result = rate_limiter.get_lockout_remaining("test_user")

        assert result == 0

    def test_get_lockout_remaining_locked(self, rate_limiter):
        """Should return seconds remaining when locked out."""
        identifier = "test_user"

        with patch("time.time") as mock_time:
            now = 1000.0
            mock_time.return_value = now

            # Manually set lockout
            rate_limiter._states[identifier] = RateLimitState(
                attempts=5, first_attempt=now - 100, locked_until=now + 500
            )

            result = rate_limiter.get_lockout_remaining(identifier)

            assert result == 500

    def test_get_lockout_remaining_expired(self, rate_limiter):
        """Should return 0 when lockout has expired."""
        identifier = "test_user"

        with patch("time.time") as mock_time:
            now = 1000.0
            mock_time.return_value = now

            # Set expired lockout
            rate_limiter._states[identifier] = RateLimitState(
                attempts=5, first_attempt=now - 1000, locked_until=now - 100
            )

            result = rate_limiter.get_lockout_remaining(identifier)

            assert result == 0


@pytest.mark.unit
class TestReset:
    """Test reset method."""

    def test_reset_existing_identifier(self, rate_limiter):
        """Should reset state for existing identifier."""
        identifier = "test_user"

        # Record some attempts
        for i in range(3):
            rate_limiter.record_attempt(identifier, success=False)

        rate_limiter.reset(identifier)

        assert identifier not in rate_limiter._states

    def test_reset_nonexistent_identifier(self, rate_limiter):
        """Should handle reset of nonexistent identifier gracefully."""
        rate_limiter.reset("nonexistent_user")

        # Should not raise exception
        assert "nonexistent_user" not in rate_limiter._states


@pytest.mark.unit
class TestThreadSafety:
    """Test thread safety of rate limiter."""

    def test_concurrent_access_thread_safe(self, rate_limiter):
        """Should handle concurrent access safely."""
        import threading

        identifier = "test_user"
        results = []

        def check_and_record():
            for i in range(10):
                rate_limiter.check_rate_limit(identifier)
                rate_limiter.record_attempt(identifier, success=False)

        threads = [threading.Thread(target=check_and_record) for _ in range(5)]

        for thread in threads:
            thread.start()

        for thread in threads:
            thread.join()

        # Verify state is consistent
        state = rate_limiter._states.get(identifier)
        assert state is not None


@pytest.mark.unit
class TestGetAuthRateLimiter:
    """Test get_auth_rate_limiter function."""

    def test_get_auth_rate_limiter_returns_instance(self):
        """Should return AuthRateLimiter instance."""
        limiter = get_auth_rate_limiter()

        assert isinstance(limiter, AuthRateLimiter)

    def test_get_auth_rate_limiter_singleton(self):
        """Should return same instance on multiple calls."""
        limiter1 = get_auth_rate_limiter()
        limiter2 = get_auth_rate_limiter()

        assert limiter1 is limiter2


@pytest.mark.unit
class TestRateLimiterScenarios:
    """Test real-world rate limiting scenarios."""

    def test_scenario_brute_force_attack(self, rate_limiter):
        """Should lock out after repeated failed attempts."""
        identifier = "attacker"

        # Simulate brute force attack
        for i in range(10):
            if rate_limiter.check_rate_limit(identifier):
                rate_limiter.record_attempt(identifier, success=False)

        # Should be locked out
        assert rate_limiter.check_rate_limit(identifier) is False
        assert rate_limiter.get_lockout_remaining(identifier) > 0

    def test_scenario_successful_auth_after_failures(self, rate_limiter):
        """Should reset on successful authentication."""
        identifier = "legitimate_user"

        # Some failed attempts
        for i in range(3):
            rate_limiter.record_attempt(identifier, success=False)

        # Successful authentication
        rate_limiter.record_attempt(identifier, success=True)

        # Should be able to authenticate again
        assert rate_limiter.check_rate_limit(identifier) is True
        assert rate_limiter.get_remaining_attempts(identifier) == rate_limiter.MAX_ATTEMPTS

    def test_scenario_window_expiration_recovery(self, rate_limiter):
        """Should recover after window expiration."""
        identifier = "test_user"

        with patch("time.time") as mock_time:
            # Initial failed attempts
            mock_time.return_value = 0.0
            for i in range(4):
                rate_limiter.record_attempt(identifier, success=False)

            # User locked out
            assert rate_limiter.get_remaining_attempts(identifier) == 1

            # Wait for window to expire
            mock_time.return_value = 500.0  # > WINDOW_SECONDS

            # Should be able to try again
            assert rate_limiter.check_rate_limit(identifier) is True
            assert rate_limiter.get_remaining_attempts(identifier) == rate_limiter.MAX_ATTEMPTS

    def test_scenario_lockout_expiration(self, rate_limiter):
        """Should allow attempts after lockout expires."""
        identifier = "test_user"

        with patch("time.time") as mock_time:
            # Trigger lockout
            mock_time.return_value = 0.0
            for i in range(rate_limiter.MAX_ATTEMPTS):
                rate_limiter.record_attempt(identifier, success=False)

            # Verify locked
            assert rate_limiter.check_rate_limit(identifier) is False

            # Wait for lockout to expire
            mock_time.return_value = 1000.0  # > LOCKOUT_SECONDS

            # Should be allowed again
            assert rate_limiter.check_rate_limit(identifier) is True


@pytest.mark.unit
class TestRateLimiterConfiguration:
    """Test rate limiter configuration."""

    def test_max_attempts_configuration(self):
        """MAX_ATTEMPTS should be 5."""
        assert AuthRateLimiter.MAX_ATTEMPTS == 5

    def test_window_seconds_configuration(self):
        """WINDOW_SECONDS should be 300 (5 minutes)."""
        assert AuthRateLimiter.WINDOW_SECONDS == 300

    def test_lockout_seconds_configuration(self):
        """LOCKOUT_SECONDS should be 900 (15 minutes)."""
        assert AuthRateLimiter.LOCKOUT_SECONDS == 900


@pytest.mark.unit
class TestRateLimiterEdgeCases:
    """Test edge cases in rate limiting."""

    def test_exact_window_boundary(self, rate_limiter):
        """Should handle exact window boundary correctly."""
        identifier = "test_user"

        with patch("time.time") as mock_time:
            mock_time.return_value = 0.0
            rate_limiter.record_attempt(identifier, success=False)

            # Exactly at window boundary
            mock_time.return_value = float(AuthRateLimiter.WINDOW_SECONDS)

            # Should still be in window
            result = rate_limiter.get_remaining_attempts(identifier)
            assert result == AuthRateLimiter.MAX_ATTEMPTS - 1

    def test_exact_lockout_boundary(self, rate_limiter):
        """Should handle exact lockout boundary correctly."""
        identifier = "test_user"

        with patch("time.time") as mock_time:
            now = 1000.0
            mock_time.return_value = now

            # Set lockout
            rate_limiter._states[identifier] = RateLimitState(
                attempts=5, first_attempt=now - 100, locked_until=now + 100
            )

            # Exactly at lockout expiry
            mock_time.return_value = now + 100

            # Should not be locked anymore
            result = rate_limiter.get_lockout_remaining(identifier)
            assert result == 0

    def test_multiple_identifiers_isolation(self, rate_limiter):
        """Should isolate rate limits between different identifiers."""
        user1 = "user1"
        user2 = "user2"

        # Lock out user1
        for i in range(rate_limiter.MAX_ATTEMPTS):
            rate_limiter.record_attempt(user1, success=False)

        # user2 should not be affected
        assert rate_limiter.check_rate_limit(user1) is False
        assert rate_limiter.check_rate_limit(user2) is True
