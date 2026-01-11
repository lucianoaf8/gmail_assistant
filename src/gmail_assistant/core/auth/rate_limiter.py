"""
Authentication rate limiting for Gmail Assistant.
Prevents brute force attacks on authentication.

Security: Rate limits authentication attempts (L-2 fix)
"""

import logging
import threading
import time
from dataclasses import dataclass

logger = logging.getLogger(__name__)


@dataclass
class RateLimitState:
    """Track rate limit state for a single identifier"""
    attempts: int = 0
    first_attempt: float = 0.0
    locked_until: float = 0.0


class AuthRateLimiter:
    """
    Rate limiter for authentication attempts (L-2 security fix).

    Prevents brute force attacks by limiting failed authentication attempts.
    """

    # Configuration
    MAX_ATTEMPTS: int = 5  # Max failed attempts before lockout
    WINDOW_SECONDS: int = 300  # 5 minute window
    LOCKOUT_SECONDS: int = 900  # 15 minute lockout

    def __init__(self):
        """Initialize rate limiter with thread-safe state storage"""
        self._states: dict[str, RateLimitState] = {}
        self._lock = threading.Lock()

    def check_rate_limit(self, identifier: str) -> bool:
        """
        Check if authentication is allowed for identifier.

        Args:
            identifier: Unique identifier (e.g., credentials file path)

        Returns:
            True if authentication allowed, False if rate limited
        """
        with self._lock:
            now = time.time()

            if identifier not in self._states:
                self._states[identifier] = RateLimitState()

            state = self._states[identifier]

            # Check if currently locked out
            if now < state.locked_until:
                remaining = int(state.locked_until - now)
                logger.warning(
                    f"Authentication rate limited for {identifier}. "
                    f"Try again in {remaining} seconds."
                )
                return False

            # Reset window if expired
            if now - state.first_attempt > self.WINDOW_SECONDS:
                state.attempts = 0
                state.first_attempt = now

            # Check if under limit
            if state.attempts >= self.MAX_ATTEMPTS:
                # Apply lockout
                state.locked_until = now + self.LOCKOUT_SECONDS
                logger.warning(
                    f"Too many failed attempts for {identifier}. "
                    f"Locked for {self.LOCKOUT_SECONDS} seconds."
                )
                return False

            return True

    def record_attempt(self, identifier: str, success: bool) -> None:
        """
        Record an authentication attempt.

        Args:
            identifier: Unique identifier (e.g., credentials file path)
            success: Whether the authentication succeeded
        """
        with self._lock:
            now = time.time()

            if identifier not in self._states:
                self._states[identifier] = RateLimitState()

            state = self._states[identifier]

            if success:
                # Reset on success
                state.attempts = 0
                state.locked_until = 0
                logger.debug(f"Successful authentication for {identifier}, resetting rate limit")
            else:
                # Increment failure count
                if state.attempts == 0:
                    state.first_attempt = now
                state.attempts += 1
                logger.debug(
                    f"Failed authentication for {identifier}, "
                    f"attempt {state.attempts}/{self.MAX_ATTEMPTS}"
                )

                # Apply lockout if too many failures
                if state.attempts >= self.MAX_ATTEMPTS:
                    state.locked_until = now + self.LOCKOUT_SECONDS
                    logger.warning(
                        f"Maximum authentication attempts reached for {identifier}. "
                        f"Account locked for {self.LOCKOUT_SECONDS} seconds."
                    )

    def get_remaining_attempts(self, identifier: str) -> int:
        """
        Get remaining authentication attempts before lockout.

        Args:
            identifier: Unique identifier

        Returns:
            Number of remaining attempts
        """
        with self._lock:
            if identifier not in self._states:
                return self.MAX_ATTEMPTS

            state = self._states[identifier]
            now = time.time()

            # Reset if window expired
            if now - state.first_attempt > self.WINDOW_SECONDS:
                return self.MAX_ATTEMPTS

            return max(0, self.MAX_ATTEMPTS - state.attempts)

    def get_lockout_remaining(self, identifier: str) -> int:
        """
        Get seconds remaining in lockout period.

        Args:
            identifier: Unique identifier

        Returns:
            Seconds remaining (0 if not locked)
        """
        with self._lock:
            if identifier not in self._states:
                return 0

            state = self._states[identifier]
            now = time.time()

            if now < state.locked_until:
                return int(state.locked_until - now)

            return 0

    def reset(self, identifier: str) -> None:
        """
        Reset rate limit state for identifier.

        Args:
            identifier: Unique identifier to reset
        """
        with self._lock:
            if identifier in self._states:
                del self._states[identifier]
                logger.debug(f"Reset rate limit state for {identifier}")


# Global rate limiter instance
_auth_rate_limiter = AuthRateLimiter()


def get_auth_rate_limiter() -> AuthRateLimiter:
    """Get the global authentication rate limiter instance"""
    return _auth_rate_limiter
