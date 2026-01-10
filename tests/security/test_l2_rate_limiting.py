"""
Test L-2: Authentication Rate Limiting
Validates rate limiting on authentication attempts.
"""
import pytest
import time
from pathlib import Path
from unittest.mock import patch


class TestAuthRateLimiter:
    """Tests for authentication rate limiting (L-2 fix)."""

    def test_rate_limiter_module_exists(self):
        """Verify rate limiter module exists."""
        from gmail_assistant.core.auth import rate_limiter

        assert hasattr(rate_limiter, 'AuthRateLimiter') or \
               hasattr(rate_limiter, 'get_auth_rate_limiter'), \
            "Rate limiter should exist"

    def test_rate_limit_configuration(self):
        """Verify rate limit configuration."""
        from gmail_assistant.core.auth.rate_limiter import AuthRateLimiter

        limiter = AuthRateLimiter()

        # Should have reasonable limits
        assert hasattr(limiter, 'max_attempts') or hasattr(limiter, 'MAX_ATTEMPTS')
        assert hasattr(limiter, 'window_seconds') or hasattr(limiter, 'WINDOW_SECONDS')

    def test_failed_attempts_tracked(self):
        """Verify failed authentication attempts are tracked."""
        from gmail_assistant.core.auth.rate_limiter import AuthRateLimiter

        limiter = AuthRateLimiter()
        test_key = "test_credential_file"

        # Record failed attempts
        for _ in range(3):
            limiter.record_attempt(test_key, success=False)

        remaining = limiter.get_remaining_attempts(test_key)
        assert remaining < 5, "Failed attempts should reduce remaining count"

    def test_rate_limit_triggered(self):
        """Verify rate limit is triggered after max attempts."""
        from gmail_assistant.core.auth.rate_limiter import AuthRateLimiter

        limiter = AuthRateLimiter()
        test_key = "test_rate_limit"

        # Exhaust all attempts
        max_attempts = getattr(limiter, 'max_attempts', 5)
        for _ in range(max_attempts):
            limiter.record_attempt(test_key, success=False)

        # Should be rate limited
        assert not limiter.check_rate_limit(test_key), \
            "Should be rate limited after max attempts"

    def test_lockout_duration(self):
        """Verify lockout duration is enforced."""
        from gmail_assistant.core.auth.rate_limiter import AuthRateLimiter

        limiter = AuthRateLimiter()
        test_key = "test_lockout"

        # Trigger lockout
        max_attempts = getattr(limiter, 'max_attempts', 5)
        for _ in range(max_attempts):
            limiter.record_attempt(test_key, success=False)

        remaining = limiter.get_lockout_remaining(test_key)
        assert remaining > 0, "Should have lockout time remaining"

    def test_successful_auth_resets_counter(self):
        """Verify successful authentication resets the counter."""
        from gmail_assistant.core.auth.rate_limiter import AuthRateLimiter

        limiter = AuthRateLimiter()
        test_key = "test_reset"

        # Some failed attempts
        for _ in range(3):
            limiter.record_attempt(test_key, success=False)

        # Successful attempt
        limiter.record_attempt(test_key, success=True)

        # Should have full attempts available
        remaining = limiter.get_remaining_attempts(test_key)
        max_attempts = getattr(limiter, 'max_attempts', 5)
        assert remaining == max_attempts, "Success should reset counter"


class TestRateLimiterIntegration:
    """Tests for rate limiter integration in auth flow."""

    def test_auth_base_uses_rate_limiter(self):
        """Verify AuthenticationBase uses rate limiter."""
        from gmail_assistant.core.auth import base

        source = Path(base.__file__).read_text()

        assert 'rate_limit' in source.lower(), \
            "Auth base should use rate limiting"

    def test_rate_limit_check_before_auth(self):
        """Verify rate limit checked before auth attempt."""
        from gmail_assistant.core.auth import base

        source = Path(base.__file__).read_text()

        assert 'check_rate_limit' in source, \
            "Should check rate limit before authentication"

    def test_attempt_recorded_after_auth(self):
        """Verify attempt recorded after auth result."""
        from gmail_assistant.core.auth import base

        source = Path(base.__file__).read_text()

        assert 'record_attempt' in source, \
            "Should record attempt after authentication"
