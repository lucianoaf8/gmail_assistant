"""
Advanced rate limiting with exponential backoff for Gmail API.
Implements proper quota management and request throttling.

H-2 fix: Uses centralized RateLimitError from exceptions.py
"""

import time
import logging
import random
import threading
from typing import Optional, Callable, Any
from functools import wraps
from tenacity import retry, stop_after_attempt, wait_exponential, retry_if_exception
from googleapiclient.errors import HttpError

from gmail_assistant.core.exceptions import RateLimitError

logger = logging.getLogger(__name__)


class GmailRateLimiter:
    """
    Gmail API rate limiter with exponential backoff and quota management.

    Gmail API Quotas:
    - 1,000,000,000 quota units per day
    - 250 quota units per user per second
    - Most operations cost 5-10 quota units
    """

    def __init__(self,
                 requests_per_second: float = 10.0,
                 max_retries: int = 5,
                 base_delay: float = 1.0,
                 max_delay: float = 300.0,
                 jitter: bool = True):
        """
        Initialize rate limiter.

        Args:
            requests_per_second: Maximum requests per second
            max_retries: Maximum retry attempts
            base_delay: Base delay for exponential backoff
            max_delay: Maximum delay between retries
            jitter: Whether to add random jitter to delays
        """
        self.requests_per_second = requests_per_second
        self.max_retries = max_retries
        self.base_delay = base_delay
        self.max_delay = max_delay
        self.jitter = jitter

        # Thread safety lock for concurrent access
        self._lock = threading.Lock()

        # Request tracking (protected by _lock)
        self.last_request_time = 0.0
        self.request_count = 0
        self.quota_units_used = 0

        # Rate limiting state
        self.min_interval = 1.0 / requests_per_second

        logger.info(f"Initialized rate limiter: {requests_per_second} req/s, "
                   f"max_retries={max_retries}, base_delay={base_delay}s")

    def wait_if_needed(self, quota_cost: int = 5):
        """
        Wait if necessary to respect rate limits.
        Thread-safe implementation using lock.

        Args:
            quota_cost: Quota units this request will consume
        """
        with self._lock:
            current_time = time.time()

            # Calculate time since last request
            time_since_last = current_time - self.last_request_time

            # Wait if we need to respect rate limit
            if time_since_last < self.min_interval:
                wait_time = self.min_interval - time_since_last
                logger.debug(f"Rate limiting: waiting {wait_time:.2f}s")
                time.sleep(wait_time)
                current_time = time.time()

            # Update tracking (protected by lock)
            self.last_request_time = current_time
            self.request_count += 1
            self.quota_units_used += quota_cost

            logger.debug(f"Request #{self.request_count}, quota used: {self.quota_units_used}")

    def exponential_backoff(self, attempt: int) -> float:
        """
        Calculate exponential backoff delay.

        Args:
            attempt: Current attempt number (0-based)

        Returns:
            Delay in seconds
        """
        if attempt <= 0:
            return 0.0

        # Exponential backoff: base_delay * 2^(attempt-1)
        delay = self.base_delay * (2 ** (attempt - 1))

        # Cap at max_delay
        delay = min(delay, self.max_delay)

        # Add jitter to prevent thundering herd
        if self.jitter:
            jitter_amount = delay * 0.1  # 10% jitter
            delay += random.uniform(-jitter_amount, jitter_amount)

        return max(0.0, delay)

    def should_retry(self, exception: Exception) -> bool:
        """
        Determine if an exception should trigger a retry.

        Args:
            exception: The exception that occurred

        Returns:
            True if should retry, False otherwise
        """
        if isinstance(exception, HttpError):
            status_code = exception.resp.status

            # Retry on rate limit and server errors
            if status_code in [429, 500, 502, 503, 504]:
                return True

            # Check for quota exceeded
            if status_code == 403:
                error_details = str(exception)
                if any(phrase in error_details.lower() for phrase in
                      ['quota exceeded', 'rate limit', 'too many requests']):
                    return True

        return False

    def get_retry_delay_from_error(self, exception: Exception) -> Optional[float]:
        """
        Extract retry delay from error response.

        Args:
            exception: The exception that occurred

        Returns:
            Delay in seconds if specified in error, None otherwise
        """
        if isinstance(exception, HttpError):
            # Check for Retry-After header
            if hasattr(exception, 'resp') and hasattr(exception.resp, 'headers'):
                retry_after = exception.resp.headers.get('Retry-After')
                if retry_after:
                    try:
                        return float(retry_after)
                    except ValueError:
                        pass

        return None

    def rate_limited_call(self, func: Callable, *args, quota_cost: int = 5, **kwargs) -> Any:
        """
        Execute a function with rate limiting and retry logic.

        Args:
            func: Function to execute
            args: Positional arguments for function
            quota_cost: Quota units this call will consume
            kwargs: Keyword arguments for function

        Returns:
            Function result

        Raises:
            RateLimitError: If all retries exhausted
        """
        last_exception = None

        for attempt in range(self.max_retries + 1):
            try:
                # Wait for rate limiting
                self.wait_if_needed(quota_cost)

                # Execute the function
                result = func(*args, **kwargs)

                # Success - reset any backoff state
                if attempt > 0:
                    logger.info(f"Function succeeded after {attempt} retries")

                return result

            except Exception as e:
                last_exception = e

                if not self.should_retry(e):
                    logger.error(f"Non-retryable error: {e}")
                    raise

                if attempt >= self.max_retries:
                    logger.error(f"Max retries ({self.max_retries}) exhausted")
                    break

                # Calculate backoff delay
                delay = self.exponential_backoff(attempt + 1)

                # Check if error specifies a retry delay
                error_delay = self.get_retry_delay_from_error(e)
                if error_delay:
                    delay = max(delay, error_delay)

                logger.warning(f"Attempt {attempt + 1} failed: {e}. "
                              f"Retrying in {delay:.2f}s")

                time.sleep(delay)

        # All retries exhausted
        raise RateLimitError(f"Rate limit exceeded after {self.max_retries} retries. "
                            f"Last error: {last_exception}")

    def get_stats(self) -> dict:
        """
        Get rate limiter statistics.

        Returns:
            Dictionary with rate limiting stats
        """
        return {
            'requests_made': self.request_count,
            'quota_units_used': self.quota_units_used,
            'requests_per_second_limit': self.requests_per_second,
            'last_request_time': self.last_request_time
        }


def retry_on_rate_limit(max_attempts: int = 5,
                       base_delay: float = 1.0,
                       max_delay: float = 300.0,
                       jitter: bool = True):
    """
    Decorator for automatic retry with exponential backoff on rate limit errors.

    Args:
        max_attempts: Maximum number of attempts
        base_delay: Base delay for exponential backoff
        max_delay: Maximum delay between retries
        jitter: Whether to add random jitter

    Returns:
        Decorated function
    """
    def should_retry_exception(exception):
        """Check if exception should trigger retry."""
        if isinstance(exception, HttpError):
            status_code = exception.resp.status
            return status_code in [429, 500, 502, 503, 504]
        return False

    # Tenacity uses seconds directly, with optional jitter
    jitter_range = (0.9, 1.1) if jitter else (1, 1)

    return retry(
        retry=retry_if_exception(should_retry_exception),
        wait=wait_exponential(multiplier=base_delay, max=max_delay, exp_base=2),
        stop=stop_after_attempt(max_attempts),
        reraise=True
    )


class QuotaTracker:
    """Track Gmail API quota usage."""

    # Gmail API quota costs (approximate)
    QUOTA_COSTS = {
        'list_messages': 5,
        'get_message': 5,
        'delete_message': 10,
        'batch_delete': 50,
        'get_profile': 1,
        'get_labels': 1,
        'search': 5,
    }

    def __init__(self, daily_quota_limit: int = 1000000000):
        """
        Initialize quota tracker.

        Args:
            daily_quota_limit: Daily quota limit in units
        """
        self.daily_quota_limit = daily_quota_limit
        self.daily_quota_used = 0
        self.quota_reset_time = self._get_next_reset_time()

    def _get_next_reset_time(self) -> float:
        """Get timestamp for next quota reset (midnight UTC)."""
        import datetime
        now = datetime.datetime.utcnow()
        tomorrow = now.replace(hour=0, minute=0, second=0, microsecond=0) + datetime.timedelta(days=1)
        return tomorrow.timestamp()

    def check_quota_available(self, operation: str, count: int = 1) -> bool:
        """
        Check if quota is available for operation.

        Args:
            operation: Operation name
            count: Number of operations

        Returns:
            True if quota available, False otherwise
        """
        current_time = time.time()

        # Reset quota if new day
        if current_time >= self.quota_reset_time:
            self.daily_quota_used = 0
            self.quota_reset_time = self._get_next_reset_time()
            logger.info("Daily quota reset")

        cost = self.QUOTA_COSTS.get(operation, 5) * count

        if self.daily_quota_used + cost > self.daily_quota_limit:
            logger.warning(f"Quota limit would be exceeded. Used: {self.daily_quota_used}, "
                          f"Requested: {cost}, Limit: {self.daily_quota_limit}")
            return False

        return True

    def consume_quota(self, operation: str, count: int = 1):
        """
        Consume quota for operation.

        Args:
            operation: Operation name
            count: Number of operations
        """
        cost = self.QUOTA_COSTS.get(operation, 5) * count
        self.daily_quota_used += cost
        logger.debug(f"Consumed {cost} quota units for {operation}. "
                    f"Total used: {self.daily_quota_used}")

    def get_quota_status(self) -> dict:
        """
        Get current quota status.

        Returns:
            Dictionary with quota information
        """
        return {
            'daily_limit': self.daily_quota_limit,
            'daily_used': self.daily_quota_used,
            'daily_remaining': self.daily_quota_limit - self.daily_quota_used,
            'usage_percentage': (self.daily_quota_used / self.daily_quota_limit) * 100,
            'reset_time': self.quota_reset_time
        }