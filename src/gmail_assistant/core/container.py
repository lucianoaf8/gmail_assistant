"""
Dependency Injection Container for Gmail Fetcher.

This module provides a lightweight dependency injection container
that enables loose coupling between components and easier testing.

Usage:
    # Create container and register services
    container = ServiceContainer()
    container.register(CacheManager, cache_instance)
    container.register_factory(GmailFetcher, lambda: GmailFetcher())

    # Resolve services
    cache = container.resolve(CacheManager)
    fetcher = container.resolve(GmailFetcher)

    # Use factory functions for common setups
    container = create_default_container()
    container = create_readonly_container()
"""

import logging
import threading
from collections.abc import Callable
from contextlib import contextmanager
from typing import (
    Any,
    Optional,
    TypeVar,
)

from .protocols import (
    EmailRepositoryProtocol,  # M-9: Repository pattern
)

logger = logging.getLogger(__name__)

T = TypeVar('T')


class ServiceNotFoundError(Exception):
    """Raised when a service cannot be resolved."""
    pass


class CircularDependencyError(Exception):
    """Raised when a circular dependency is detected."""
    pass


class ServiceLifetime:
    """Enumeration of service lifetimes."""
    SINGLETON = "singleton"  # One instance for entire container
    TRANSIENT = "transient"  # New instance each time
    SCOPED = "scoped"        # One instance per scope


class ServiceDescriptor:
    """Describes a registered service."""

    def __init__(
        self,
        service_type: type[T],
        implementation: T | Callable[[], T] | type[T],
        lifetime: str = ServiceLifetime.SINGLETON
    ):
        self.service_type = service_type
        self.implementation = implementation
        self.lifetime = lifetime
        self.instance: T | None = None
        self._is_factory = callable(implementation) and not isinstance(implementation, type)
        self._is_type = isinstance(implementation, type)

    def get_instance(self, container: 'ServiceContainer') -> T:
        """Get or create the service instance."""
        if self.lifetime == ServiceLifetime.SINGLETON:
            if self.instance is None:
                self.instance = self._create_instance(container)
            return self.instance
        elif self.lifetime == ServiceLifetime.TRANSIENT:
            return self._create_instance(container)
        else:
            # Scoped lifetime handled by ScopedContainer
            if self.instance is None:
                self.instance = self._create_instance(container)
            return self.instance

    def _create_instance(self, container: 'ServiceContainer') -> T:
        """Create a new instance of the service."""
        if self._is_factory:
            return self.implementation()
        elif self._is_type:
            return self._create_from_type(container)
        else:
            # Already an instance
            return self.implementation

    def _create_from_type(self, container: 'ServiceContainer') -> T:
        """Create instance from type with dependency injection."""
        # Simple instantiation for now
        # Could be extended to support constructor injection
        return self.implementation()


class ServiceContainer:
    """
    Lightweight dependency injection container.

    Supports singleton, transient, and scoped lifetimes.
    Thread-safe for concurrent access.

    Example:
        container = ServiceContainer()

        # Register singleton
        container.register(CacheManager, cache_instance)

        # Register factory
        container.register_factory(GmailFetcher, lambda: GmailFetcher())

        # Register type for auto-instantiation
        container.register_type(InputValidator, InputValidator)

        # Resolve
        cache = container.resolve(CacheManager)
    """

    def __init__(self, parent: Optional['ServiceContainer'] = None):
        self._services: dict[type, ServiceDescriptor] = {}
        self._parent = parent
        self._lock = threading.RLock()
        self._resolving: set = set()  # Track currently resolving services

    def register(
        self,
        service_type: type[T],
        instance: T,
        lifetime: str = ServiceLifetime.SINGLETON
    ) -> 'ServiceContainer':
        """
        Register a service instance.

        Args:
            service_type: The type/interface to register
            instance: The service instance
            lifetime: Service lifetime (default: singleton)

        Returns:
            Self for method chaining.
        """
        with self._lock:
            self._services[service_type] = ServiceDescriptor(
                service_type, instance, lifetime
            )
            logger.debug(f"Registered service: {service_type.__name__}")
        return self

    def register_factory(
        self,
        service_type: type[T],
        factory: Callable[[], T],
        lifetime: str = ServiceLifetime.SINGLETON
    ) -> 'ServiceContainer':
        """
        Register a factory function for a service.

        Args:
            service_type: The type/interface to register
            factory: Factory function that creates instances
            lifetime: Service lifetime (default: singleton)

        Returns:
            Self for method chaining.
        """
        with self._lock:
            self._services[service_type] = ServiceDescriptor(
                service_type, factory, lifetime
            )
            logger.debug(f"Registered factory for: {service_type.__name__}")
        return self

    def register_type(
        self,
        service_type: type[T],
        implementation_type: type[T],
        lifetime: str = ServiceLifetime.TRANSIENT
    ) -> 'ServiceContainer':
        """
        Register a type for auto-instantiation.

        Args:
            service_type: The type/interface to register
            implementation_type: The implementation type to instantiate
            lifetime: Service lifetime (default: transient)

        Returns:
            Self for method chaining.
        """
        with self._lock:
            self._services[service_type] = ServiceDescriptor(
                service_type, implementation_type, lifetime
            )
            logger.debug(f"Registered type: {service_type.__name__} -> {implementation_type.__name__}")
        return self

    def resolve(self, service_type: type[T]) -> T:
        """
        Resolve a service by type.

        Args:
            service_type: The type/interface to resolve

        Returns:
            The service instance.

        Raises:
            ServiceNotFoundError: If service is not registered.
            CircularDependencyError: If circular dependency detected.
        """
        with self._lock:
            # Check for circular dependencies
            if service_type in self._resolving:
                raise CircularDependencyError(
                    f"Circular dependency detected for {service_type.__name__}"
                )

            self._resolving.add(service_type)
            try:
                # Check local services
                if service_type in self._services:
                    return self._services[service_type].get_instance(self)

                # Check parent container
                if self._parent is not None:
                    try:
                        return self._parent.resolve(service_type)
                    except ServiceNotFoundError:
                        pass

                raise ServiceNotFoundError(
                    f"Service not found: {service_type.__name__}"
                )
            finally:
                self._resolving.discard(service_type)

    def try_resolve(self, service_type: type[T]) -> T | None:
        """
        Try to resolve a service, returning None if not found.

        Args:
            service_type: The type/interface to resolve

        Returns:
            The service instance or None.
        """
        try:
            return self.resolve(service_type)
        except ServiceNotFoundError:
            return None

    def has_service(self, service_type: type) -> bool:
        """
        Check if a service is registered.

        Args:
            service_type: The type/interface to check

        Returns:
            True if service is registered.
        """
        if service_type in self._services:
            return True
        if self._parent is not None:
            return self._parent.has_service(service_type)
        return False

    def create_scope(self) -> 'ServiceContainer':
        """
        Create a new scoped container.

        Scoped containers inherit from the parent but can have
        their own scoped services.

        Returns:
            New ServiceContainer with this container as parent.
        """
        return ServiceContainer(parent=self)

    def get_registered_services(self) -> dict[str, str]:
        """
        Get information about registered services.

        Returns:
            Dictionary mapping service names to their lifetimes.
        """
        services = {}
        for service_type, descriptor in self._services.items():
            services[service_type.__name__] = descriptor.lifetime
        return services

    def clear(self) -> None:
        """Clear all registered services."""
        with self._lock:
            self._services.clear()
            logger.debug("Container cleared")

    @contextmanager
    def scope(self):
        """
        Context manager for scoped service resolution.

        Example:
            with container.scope() as scoped:
                service = scoped.resolve(MyScopedService)
        """
        scoped_container = self.create_scope()
        try:
            yield scoped_container
        finally:
            scoped_container.clear()


# =============================================================================
# Factory Functions
# =============================================================================

def create_default_container() -> ServiceContainer:
    """
    Create a container with default service configuration.

    Includes:
    - CacheManager (singleton)
    - RateLimiter (singleton)
    - InputValidator (transient)
    - ErrorHandler (singleton)
    - EmailRepository (singleton) - M-9: Repository pattern

    Returns:
        Configured ServiceContainer.
    """
    from ..utils.cache_manager import CacheManager
    from ..utils.error_handler import ErrorHandler
    from ..utils.input_validator import InputValidator
    from ..utils.rate_limiter import GmailRateLimiter
    from .constants import (
        CONSERVATIVE_REQUESTS_PER_SECOND,
    )
    from .processing.database import EmailDatabaseImporter

    container = ServiceContainer()

    # Register core utilities
    container.register(CacheManager, CacheManager())
    container.register_factory(
        GmailRateLimiter,
        lambda: GmailRateLimiter(requests_per_second=CONSERVATIVE_REQUESTS_PER_SECOND)
    )
    container.register_type(InputValidator, InputValidator, ServiceLifetime.TRANSIENT)
    container.register(ErrorHandler, ErrorHandler())

    # M-9: Register email repository for persistence operations
    container.register_factory(
        EmailRepositoryProtocol,
        lambda: EmailDatabaseImporter()
    )

    logger.info("Created default container with core utilities")
    return container


def create_readonly_container(
    credentials_file: str = "credentials.json"
) -> ServiceContainer:
    """
    Create a container for read-only Gmail operations.

    Includes all default services plus:
    - ReadOnlyGmailAuth (singleton)
    - GmailFetcher (singleton)

    Args:
        credentials_file: Path to OAuth credentials file

    Returns:
        Configured ServiceContainer.
    """
    from .auth_base import ReadOnlyGmailAuth
    from .gmail_assistant import GmailFetcher

    container = create_default_container()

    # Register authentication
    container.register_factory(
        ReadOnlyGmailAuth,
        lambda: ReadOnlyGmailAuth(credentials_file)
    )

    # Register fetcher
    container.register_factory(
        GmailFetcher,
        lambda: GmailFetcher(credentials_file)
    )

    logger.info("Created read-only container")
    return container


def create_modify_container(
    credentials_file: str = "credentials.json"
) -> ServiceContainer:
    """
    Create a container for Gmail operations that modify data.

    Includes all default services plus:
    - GmailModifyAuth (singleton)
    - GmailDeleter (singleton)

    Args:
        credentials_file: Path to OAuth credentials file

    Returns:
        Configured ServiceContainer.
    """
    from .auth_base import GmailModifyAuth

    container = create_default_container()

    # Register authentication with modify scope
    container.register_factory(
        GmailModifyAuth,
        lambda: GmailModifyAuth(credentials_file)
    )

    logger.info("Created modify container")
    return container


def create_full_container(
    credentials_file: str = "credentials.json"
) -> ServiceContainer:
    """
    Create a container with all Gmail capabilities.

    Includes:
    - All default services
    - Read-only services
    - Modification services
    - Parser services

    Args:
        credentials_file: Path to OAuth credentials file

    Returns:
        Configured ServiceContainer.
    """
    from ..parsers.advanced_email_parser import EmailContentParser
    from .auth_base import FullGmailAuth
    from .gmail_assistant import GmailFetcher

    container = create_default_container()

    # Register authentication with full access
    container.register_factory(
        FullGmailAuth,
        lambda: FullGmailAuth(credentials_file)
    )

    # Register fetcher
    container.register_factory(
        GmailFetcher,
        lambda: GmailFetcher(credentials_file)
    )

    # Register parser
    container.register(EmailContentParser, EmailContentParser())

    logger.info("Created full container with all services")
    return container


# =============================================================================
# Convenience Functions
# =============================================================================

def inject(service_type: type[T]) -> Callable[[Callable[..., Any]], Callable[..., Any]]:
    """
    Decorator for injecting services into functions.

    Note: Requires a global container to be set.

    Example:
        @inject(CacheManager)
        def my_function(cache: CacheManager):
            cache.get("key")
    """
    def decorator(func: Callable[..., Any]) -> Callable[..., Any]:
        def wrapper(*args, **kwargs):
            if _global_container is not None:
                service = _global_container.resolve(service_type)
                return func(service, *args, **kwargs)
            raise RuntimeError("No global container configured")
        return wrapper
    return decorator


# Global container for convenience (optional usage)
_global_container: ServiceContainer | None = None


def set_global_container(container: ServiceContainer) -> None:
    """Set the global container for convenience methods."""
    global _global_container
    _global_container = container


def get_global_container() -> ServiceContainer | None:
    """Get the global container."""
    return _global_container


def resolve(service_type: type[T]) -> T:
    """
    Resolve a service from the global container.

    Args:
        service_type: The type to resolve

    Returns:
        The service instance.

    Raises:
        RuntimeError: If no global container is set.
    """
    if _global_container is None:
        raise RuntimeError("No global container configured. Call set_global_container first.")
    return _global_container.resolve(service_type)
