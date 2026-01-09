"""Unit tests for gmail_assistant.utils.rate_limiter module."""
from __future__ import annotations

import time
import threading
from unittest import mock

import pytest

from gmail_assistant.utils.rate_limiter import (
    RateLimitError,
    GmailRateLimiter,
    QuotaTracker,
    retry_on_rate_limit,
)


@pytest.fixture
def rate_limiter():
    """Create a rate limiter for testing."""
    return GmailRateLimiter(
        requests_per_second=10.0,
        max_retries=3,
        base_delay=0.1,
        max_delay=1.0,
        jitter=False  # Disable jitter for predictable tests
    )


@pytest.fixture
def quota_tracker():
    """Create a quota tracker for testing."""
    return QuotaTracker(daily_quota_limit=1000)


@pytest.mark.unit
class TestRateLimitError:
    """Test RateLimitError exception."""

    def test_rate_limit_error_is_exception(self):
        """RateLimitError should inherit from Exception."""
        assert issubclass(RateLimitError, Exception)

    def test_rate_limit_error_with_message(self):
        """RateLimitError should preserve message."""
        error = RateLimitError("Rate limit exceeded")
        assert str(error) == "Rate limit exceeded"


@pytest.mark.unit
class TestGmailRateLimiterInit:
    """Test GmailRateLimiter initialization."""

    def test_default_initialization(self):
        """GmailRateLimiter should initialize with defaults."""
        limiter = GmailRateLimiter()

        assert limiter.requests_per_second == 10.0
        assert limiter.max_retries == 5
        assert limiter.base_delay == 1.0
        assert limiter.max_delay == 300.0
        assert limiter.jitter is True

    def test_custom_initialization(self):
        """GmailRateLimiter should accept custom parameters."""
        limiter = GmailRateLimiter(
            requests_per_second=5.0,
            max_retries=3,
            base_delay=0.5,
            max_delay=60.0,
            jitter=False
        )

        assert limiter.requests_per_second == 5.0
        assert limiter.max_retries == 3
        assert limiter.base_delay == 0.5
        assert limiter.max_delay == 60.0
        assert limiter.jitter is False

    def test_min_interval_calculated(self):
        """min_interval should be calculated from requests_per_second."""
        limiter = GmailRateLimiter(requests_per_second=10.0)

        assert limiter.min_interval == 0.1

    def test_initial_state(self):
        """Rate limiter should start with zero counters."""
        limiter = GmailRateLimiter()

        assert limiter.request_count == 0
        assert limiter.quota_units_used == 0
        assert limiter.last_request_time == 0.0


@pytest.mark.unit
class TestWaitIfNeeded:
    """Test wait_if_needed method."""

    def test_wait_if_needed_updates_counters(self, rate_limiter: GmailRateLimiter):
        """wait_if_needed should update request count and quota."""
        rate_limiter.wait_if_needed(quota_cost=5)

        assert rate_limiter.request_count == 1
        assert rate_limiter.quota_units_used == 5

    def test_wait_if_needed_accumulates(self, rate_limiter: GmailRateLimiter):
        """wait_if_needed should accumulate counters."""
        rate_limiter.wait_if_needed(quota_cost=5)
        rate_limiter.wait_if_needed(quota_cost=10)

        assert rate_limiter.request_count == 2
        assert rate_limiter.quota_units_used == 15

    def test_wait_if_needed_respects_rate_limit(self):
        """wait_if_needed should delay when rate limit approached."""
        limiter = GmailRateLimiter(requests_per_second=100.0)  # High rate for fast test

        start = time.time()
        limiter.wait_if_needed()
        limiter.wait_if_needed()
        elapsed = time.time() - start

        # Should have some delay due to rate limiting
        assert elapsed >= 0.01  # At least 10ms minimum

    def test_wait_if_needed_thread_safe(self, rate_limiter: GmailRateLimiter):
        """wait_if_needed should be thread-safe."""
        errors = []

        def make_requests():
            try:
                for _ in range(10):
                    rate_limiter.wait_if_needed(quota_cost=1)
            except Exception as e:
                errors.append(e)

        threads = [threading.Thread(target=make_requests) for _ in range(5)]

        for t in threads:
            t.start()
        for t in threads:
            t.join()

        assert len(errors) == 0
        assert rate_limiter.request_count == 50


@pytest.mark.unit
class TestExponentialBackoff:
    """Test exponential_backoff method."""

    def test_exponential_backoff_zero_attempt(self, rate_limiter: GmailRateLimiter):
        """exponential_backoff should return 0 for attempt 0."""
        delay = rate_limiter.exponential_backoff(0)
        assert delay == 0.0

    def test_exponential_backoff_first_attempt(self, rate_limiter: GmailRateLimiter):
        """exponential_backoff should return base_delay for attempt 1."""
        delay = rate_limiter.exponential_backoff(1)
        assert delay == rate_limiter.base_delay

    def test_exponential_backoff_increases(self, rate_limiter: GmailRateLimiter):
        """exponential_backoff should increase exponentially."""
        delay1 = rate_limiter.exponential_backoff(1)
        delay2 = rate_limiter.exponential_backoff(2)
        delay3 = rate_limiter.exponential_backoff(3)

        assert delay2 == delay1 * 2
        assert delay3 == delay1 * 4

    def test_exponential_backoff_capped_at_max(self, rate_limiter: GmailRateLimiter):
        """exponential_backoff should not exceed max_delay."""
        delay = rate_limiter.exponential_backoff(100)

        assert delay <= rate_limiter.max_delay

    def test_exponential_backoff_with_jitter(self):
        """exponential_backoff should add jitter when enabled."""
        limiter = GmailRateLimiter(
            base_delay=1.0,
            max_delay=300.0,
            jitter=True
        )

        # With jitter, delays should vary
        delays = [limiter.exponential_backoff(2) for _ in range(10)]

        # All delays should be roughly around 2.0 (2^1 * 1.0) with +/- 10% jitter
        for delay in delays:
            assert 1.8 <= delay <= 2.2

        # There should be some variation (not all identical)
        assert len(set(delays)) > 1


@pytest.mark.unit
class TestShouldRetry:
    """Test should_retry method."""

    def test_should_retry_rate_limit_429(self, rate_limiter: GmailRateLimiter):
        """should_retry should return True for 429 status."""
        from googleapiclient.errors import HttpError
        from unittest.mock import Mock

        resp = Mock()
        resp.status = 429
        error = HttpError(resp, b"Rate limited")

        assert rate_limiter.should_retry(error) is True

    def test_should_retry_server_error_500(self, rate_limiter: GmailRateLimiter):
        """should_retry should return True for 500 status."""
        from googleapiclient.errors import HttpError
        from unittest.mock import Mock

        resp = Mock()
        resp.status = 500
        error = HttpError(resp, b"Server error")

        assert rate_limiter.should_retry(error) is True

    def test_should_retry_server_error_503(self, rate_limiter: GmailRateLimiter):
        """should_retry should return True for 503 status."""
        from googleapiclient.errors import HttpError
        from unittest.mock import Mock

        resp = Mock()
        resp.status = 503
        error = HttpError(resp, b"Service unavailable")

        assert rate_limiter.should_retry(error) is True

    def test_should_retry_quota_exceeded_403(self, rate_limiter: GmailRateLimiter):
        """should_retry should return True for quota exceeded 403."""
        from googleapiclient.errors import HttpError
        from unittest.mock import Mock

        resp = Mock()
        resp.status = 403
        error = HttpError(resp, b"Quota exceeded for this project")

        assert rate_limiter.should_retry(error) is True

    def test_should_retry_generic_403(self, rate_limiter: GmailRateLimiter):
        """should_retry should return False for generic 403."""
        from googleapiclient.errors import HttpError
        from unittest.mock import Mock

        resp = Mock()
        resp.status = 403
        error = HttpError(resp, b"Access denied")

        assert rate_limiter.should_retry(error) is False

    def test_should_retry_404(self, rate_limiter: GmailRateLimiter):
        """should_retry should return False for 404."""
        from googleapiclient.errors import HttpError
        from unittest.mock import Mock

        resp = Mock()
        resp.status = 404
        error = HttpError(resp, b"Not found")

        assert rate_limiter.should_retry(error) is False

    def test_should_retry_non_http_error(self, rate_limiter: GmailRateLimiter):
        """should_retry should return False for non-HTTP errors."""
        error = ValueError("Some other error")

        assert rate_limiter.should_retry(error) is False


@pytest.mark.unit
class TestGetRetryDelayFromError:
    """Test get_retry_delay_from_error method."""

    def test_get_retry_delay_with_header(self, rate_limiter: GmailRateLimiter):
        """get_retry_delay_from_error should extract Retry-After header."""
        from googleapiclient.errors import HttpError
        from unittest.mock import Mock

        resp = Mock()
        resp.status = 429
        resp.headers = {"Retry-After": "30"}
        error = HttpError(resp, b"Rate limited")

        delay = rate_limiter.get_retry_delay_from_error(error)

        assert delay == 30.0

    def test_get_retry_delay_without_header(self, rate_limiter: GmailRateLimiter):
        """get_retry_delay_from_error should return None without header."""
        from googleapiclient.errors import HttpError
        from unittest.mock import Mock

        resp = Mock()
        resp.status = 429
        resp.headers = {}
        error = HttpError(resp, b"Rate limited")

        delay = rate_limiter.get_retry_delay_from_error(error)

        assert delay is None

    def test_get_retry_delay_non_http_error(self, rate_limiter: GmailRateLimiter):
        """get_retry_delay_from_error should return None for non-HTTP errors."""
        error = ValueError("Some error")

        delay = rate_limiter.get_retry_delay_from_error(error)

        assert delay is None


@pytest.mark.unit
class TestRateLimitedCall:
    """Test rate_limited_call method."""

    def test_rate_limited_call_success(self, rate_limiter: GmailRateLimiter):
        """rate_limited_call should execute function successfully."""

        def my_func(x, y):
            return x + y

        result = rate_limiter.rate_limited_call(my_func, 2, 3)

        assert result == 5

    def test_rate_limited_call_tracks_quota(self, rate_limiter: GmailRateLimiter):
        """rate_limited_call should track quota usage."""

        def my_func():
            return "done"

        rate_limiter.rate_limited_call(my_func, quota_cost=10)

        assert rate_limiter.quota_units_used == 10

    def test_rate_limited_call_retries_on_retryable_error(
        self, rate_limiter: GmailRateLimiter
    ):
        """rate_limited_call should retry on retryable errors."""
        from googleapiclient.errors import HttpError
        from unittest.mock import Mock

        call_count = [0]

        def failing_func():
            call_count[0] += 1
            if call_count[0] < 3:
                resp = Mock()
                resp.status = 503
                # Properly mock the headers attribute to avoid Mock object issues
                resp.headers = {}
                raise HttpError(resp, b"Service unavailable")
            return "success"

        result = rate_limiter.rate_limited_call(failing_func)

        assert result == "success"
        assert call_count[0] == 3

    def test_rate_limited_call_raises_after_max_retries(
        self, rate_limiter: GmailRateLimiter
    ):
        """rate_limited_call should raise RateLimitError after max retries."""
        from googleapiclient.errors import HttpError
        from unittest.mock import Mock

        def always_failing_func():
            resp = Mock()
            resp.status = 503
            resp.headers = {}
            raise HttpError(resp, b"Service unavailable")

        with pytest.raises(RateLimitError, match="Rate limit exceeded"):
            rate_limiter.rate_limited_call(always_failing_func)

    def test_rate_limited_call_raises_non_retryable_immediately(
        self, rate_limiter: GmailRateLimiter
    ):
        """rate_limited_call should raise non-retryable errors immediately."""
        from googleapiclient.errors import HttpError
        from unittest.mock import Mock

        call_count = [0]

        def failing_func():
            call_count[0] += 1
            resp = Mock()
            resp.status = 404
            raise HttpError(resp, b"Not found")

        with pytest.raises(HttpError):
            rate_limiter.rate_limited_call(failing_func)

        assert call_count[0] == 1  # Only one attempt


@pytest.mark.unit
class TestGetStats:
    """Test get_stats method."""

    def test_get_stats_initial(self, rate_limiter: GmailRateLimiter):
        """get_stats should return initial statistics."""
        stats = rate_limiter.get_stats()

        assert stats["requests_made"] == 0
        assert stats["quota_units_used"] == 0
        assert stats["requests_per_second_limit"] == 10.0

    def test_get_stats_after_requests(self, rate_limiter: GmailRateLimiter):
        """get_stats should reflect requests made."""
        rate_limiter.wait_if_needed(quota_cost=5)
        rate_limiter.wait_if_needed(quota_cost=10)

        stats = rate_limiter.get_stats()

        assert stats["requests_made"] == 2
        assert stats["quota_units_used"] == 15


@pytest.mark.unit
class TestQuotaTrackerInit:
    """Test QuotaTracker initialization."""

    def test_default_initialization(self):
        """QuotaTracker should initialize with default quota."""
        tracker = QuotaTracker()

        assert tracker.daily_quota_limit == 1000000000
        assert tracker.daily_quota_used == 0

    def test_custom_quota_limit(self):
        """QuotaTracker should accept custom quota limit."""
        tracker = QuotaTracker(daily_quota_limit=5000)

        assert tracker.daily_quota_limit == 5000

    def test_quota_costs_defined(self):
        """QuotaTracker should have predefined quota costs."""
        assert QuotaTracker.QUOTA_COSTS["list_messages"] == 5
        assert QuotaTracker.QUOTA_COSTS["get_message"] == 5
        assert QuotaTracker.QUOTA_COSTS["delete_message"] == 10
        assert QuotaTracker.QUOTA_COSTS["batch_delete"] == 50


@pytest.mark.unit
class TestQuotaTrackerCheckQuota:
    """Test QuotaTracker.check_quota_available method."""

    def test_check_quota_available_true(self, quota_tracker: QuotaTracker):
        """check_quota_available should return True when quota available."""
        available = quota_tracker.check_quota_available("list_messages", count=10)

        assert available is True

    def test_check_quota_available_false_when_exceeded(
        self, quota_tracker: QuotaTracker
    ):
        """check_quota_available should return False when quota exceeded."""
        # Use up quota
        quota_tracker.daily_quota_used = 999

        available = quota_tracker.check_quota_available("list_messages", count=10)

        assert available is False

    def test_check_quota_uses_default_cost(self, quota_tracker: QuotaTracker):
        """check_quota_available should use default cost for unknown operation."""
        # Should use default cost of 5
        quota_tracker.daily_quota_used = 996

        # 996 + 5*1 = 1001 > 1000, should be False
        available = quota_tracker.check_quota_available("unknown_operation", count=1)

        assert available is False


@pytest.mark.unit
class TestQuotaTrackerConsumeQuota:
    """Test QuotaTracker.consume_quota method."""

    def test_consume_quota_updates_used(self, quota_tracker: QuotaTracker):
        """consume_quota should update daily_quota_used."""
        quota_tracker.consume_quota("list_messages", count=10)

        # 5 * 10 = 50
        assert quota_tracker.daily_quota_used == 50

    def test_consume_quota_accumulates(self, quota_tracker: QuotaTracker):
        """consume_quota should accumulate usage."""
        quota_tracker.consume_quota("list_messages", count=5)  # 25
        quota_tracker.consume_quota("get_message", count=10)  # 50

        assert quota_tracker.daily_quota_used == 75


@pytest.mark.unit
class TestQuotaTrackerGetStatus:
    """Test QuotaTracker.get_quota_status method."""

    def test_get_quota_status_initial(self, quota_tracker: QuotaTracker):
        """get_quota_status should return initial status."""
        status = quota_tracker.get_quota_status()

        assert status["daily_limit"] == 1000
        assert status["daily_used"] == 0
        assert status["daily_remaining"] == 1000
        assert status["usage_percentage"] == 0.0

    def test_get_quota_status_after_usage(self, quota_tracker: QuotaTracker):
        """get_quota_status should reflect quota usage."""
        quota_tracker.consume_quota("list_messages", count=40)  # 200

        status = quota_tracker.get_quota_status()

        assert status["daily_used"] == 200
        assert status["daily_remaining"] == 800
        assert status["usage_percentage"] == 20.0


@pytest.mark.unit
class TestRetryOnRateLimitDecorator:
    """Test retry_on_rate_limit decorator."""

    def test_decorator_retries_on_rate_limit(self):
        """retry_on_rate_limit should retry on 429 errors."""
        from googleapiclient.errors import HttpError
        from unittest.mock import Mock

        call_count = [0]

        @retry_on_rate_limit(max_attempts=5, base_delay=0.01, jitter=False)
        def failing_func():
            call_count[0] += 1
            if call_count[0] < 3:
                resp = Mock()
                resp.status = 429
                raise HttpError(resp, b"Rate limited")
            return "success"

        result = failing_func()

        assert result == "success"
        assert call_count[0] == 3

    def test_decorator_does_not_retry_non_rate_limit(self):
        """retry_on_rate_limit should not retry on non-rate-limit errors."""
        from googleapiclient.errors import HttpError
        from unittest.mock import Mock

        call_count = [0]

        @retry_on_rate_limit(max_attempts=5, base_delay=0.01)
        def failing_func():
            call_count[0] += 1
            resp = Mock()
            resp.status = 404
            raise HttpError(resp, b"Not found")

        with pytest.raises(HttpError):
            failing_func()

        assert call_count[0] == 1

    def test_decorator_success_first_try(self):
        """retry_on_rate_limit should work on first successful try."""
        call_count = [0]

        @retry_on_rate_limit(max_attempts=3)
        def successful_func():
            call_count[0] += 1
            return "done"

        result = successful_func()

        assert result == "done"
        assert call_count[0] == 1
