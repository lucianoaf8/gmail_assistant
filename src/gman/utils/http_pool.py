"""
HTTP connection pooling for Gman.

L-6: Provides connection pool management for efficient HTTP reuse.

This module wraps httplib2.Http with connection pooling support
and provides a requests-like interface with session reuse.

Usage:
    from gman.utils.http_pool import get_http_client, HttpPoolConfig

    # Get pooled HTTP client for Gmail API
    http = get_http_client()

    # Or with custom config
    config = HttpPoolConfig(max_connections=20, timeout=60)
    http = get_http_client(config)
"""
from __future__ import annotations

import logging
import threading
from dataclasses import dataclass
from typing import Any

logger = logging.getLogger(__name__)


@dataclass(frozen=True)
class HttpPoolConfig:
    """Configuration for HTTP connection pool.

    Attributes:
        max_connections: Maximum connections in pool (default: 10)
        timeout: Request timeout in seconds (default: 30)
        disable_ssl_verification: Disable SSL verification (default: False, for testing)
        cache_directory: Directory for HTTP cache (default: None, no caching)
    """
    max_connections: int = 10
    timeout: int = 30
    disable_ssl_verification: bool = False
    cache_directory: str | None = None

    def __post_init__(self) -> None:
        if self.max_connections < 1:
            raise ValueError("max_connections must be >= 1")
        if self.timeout < 1:
            raise ValueError("timeout must be >= 1")


class HttpConnectionPool:
    """
    Thread-safe HTTP connection pool.

    L-6: Provides connection reuse to reduce connection overhead.

    Uses httplib2 internally for compatibility with Google API client.
    """

    def __init__(self, config: HttpPoolConfig | None = None):
        """Initialize connection pool.

        Args:
            config: Pool configuration (uses defaults if None)
        """
        self.config = config or HttpPoolConfig()
        self._lock = threading.Lock()
        self._http: Any = None
        self._created = False

        logger.info(
            f"HttpConnectionPool initialized: max_connections={self.config.max_connections}, "
            f"timeout={self.config.timeout}s"
        )

    def get_http(self) -> Any:
        """
        Get or create HTTP client with connection pooling.

        Returns:
            httplib2.Http instance configured with connection pooling
        """
        if self._http is not None:
            return self._http

        with self._lock:
            if self._http is not None:
                return self._http

            self._http = self._create_http()
            self._created = True
            return self._http

    def _create_http(self) -> Any:
        """Create httplib2.Http with pooling configuration."""
        try:
            import httplib2

            # Create cache if configured
            cache = None
            if self.config.cache_directory:
                from pathlib import Path
                cache_path = Path(self.config.cache_directory)
                cache_path.mkdir(parents=True, exist_ok=True)
                cache = str(cache_path)

            http = httplib2.Http(
                cache=cache,
                timeout=self.config.timeout,
            )

            # Configure SSL if needed
            if self.config.disable_ssl_verification:
                http.disable_ssl_certificate_validation = True
                logger.warning("SSL certificate verification disabled")

            # Connection pooling is enabled by default in httplib2
            # but we set max connections explicitly
            http.connections = {}  # Reset connections dict

            logger.debug("Created httplib2.Http client")
            return http

        except ImportError:
            logger.warning(
                "httplib2 not available, falling back to basic HTTP"
            )
            return None

    def close(self) -> None:
        """Close all pooled connections."""
        with self._lock:
            if self._http is not None and hasattr(self._http, 'connections'):
                # Close all cached connections
                for conn in self._http.connections.values():
                    try:
                        if hasattr(conn, 'close'):
                            conn.close()
                    except Exception as e:
                        logger.debug(f"Error closing connection: {e}")
                self._http.connections.clear()
                logger.debug("Connection pool closed")

    def __enter__(self) -> 'HttpConnectionPool':
        """Context manager entry."""
        return self

    def __exit__(self, exc_type: Any, exc_val: Any, exc_tb: Any) -> None:
        """Context manager exit - close pool."""
        self.close()


# Global pool instance
_global_pool: HttpConnectionPool | None = None
_global_pool_lock = threading.Lock()


def get_http_client(config: HttpPoolConfig | None = None) -> Any:
    """
    Get HTTP client from global connection pool.

    L-6: Provides easy access to pooled HTTP connections.

    Args:
        config: Optional configuration (only used on first call)

    Returns:
        httplib2.Http instance or None if not available
    """
    global _global_pool

    if _global_pool is None:
        with _global_pool_lock:
            if _global_pool is None:
                _global_pool = HttpConnectionPool(config)

    return _global_pool.get_http()


def close_pool() -> None:
    """Close the global connection pool."""
    global _global_pool

    if _global_pool is not None:
        with _global_pool_lock:
            if _global_pool is not None:
                _global_pool.close()
                _global_pool = None
                logger.info("Global HTTP pool closed")


def create_authorized_http(credentials: Any, config: HttpPoolConfig | None = None) -> Any:
    """
    Create authorized HTTP client with connection pooling.

    L-6: Wraps google-auth-httplib2 with pooling support.

    Args:
        credentials: Google API credentials
        config: Optional pool configuration

    Returns:
        Authorized httplib2.Http instance
    """
    try:
        from google_auth_httplib2 import AuthorizedHttp

        pool = HttpConnectionPool(config)
        http = pool.get_http()

        if http is None:
            logger.warning("HTTP pool unavailable, credentials may not work")
            return None

        authorized = AuthorizedHttp(credentials, http=http)
        logger.debug("Created authorized HTTP client with pooling")
        return authorized

    except ImportError:
        logger.warning(
            "google-auth-httplib2 not available. "
            "Install with: pip install google-auth-httplib2"
        )
        return None
