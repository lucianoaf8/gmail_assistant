"""Unit tests for gmail_assistant.core.container module."""
from __future__ import annotations

from typing import Protocol
from unittest import mock

import pytest

from gmail_assistant.core.container import (
    ServiceContainer,
    ServiceDescriptor,
    ServiceLifetime,
    ServiceNotFoundError,
    CircularDependencyError,
    create_default_container,
    set_global_container,
    get_global_container,
    resolve,
    inject,
)


# Test fixtures and helper classes
class DummyService:
    """Dummy service for testing."""
    def __init__(self, value: int = 0):
        self.value = value


class AnotherService:
    """Another dummy service for testing."""
    def __init__(self, name: str = "default"):
        self.name = name


class DependentService:
    """Service that depends on another."""
    def __init__(self, dependency: DummyService):
        self.dependency = dependency


@pytest.fixture
def container():
    """Create a fresh ServiceContainer for each test."""
    return ServiceContainer()


@pytest.fixture
def cleanup_global_container():
    """Clean up global container after test."""
    yield
    set_global_container(None)


@pytest.mark.unit
class TestServiceLifetime:
    """Test ServiceLifetime enumeration."""

    def test_singleton_value(self):
        """SINGLETON should have expected value."""
        assert ServiceLifetime.SINGLETON == "singleton"

    def test_transient_value(self):
        """TRANSIENT should have expected value."""
        assert ServiceLifetime.TRANSIENT == "transient"

    def test_scoped_value(self):
        """SCOPED should have expected value."""
        assert ServiceLifetime.SCOPED == "scoped"


@pytest.mark.unit
class TestServiceDescriptor:
    """Test ServiceDescriptor class."""

    def test_create_with_instance(self):
        """ServiceDescriptor should accept an instance."""
        instance = DummyService(42)
        descriptor = ServiceDescriptor(DummyService, instance)

        assert descriptor.service_type == DummyService
        assert descriptor.implementation == instance
        assert descriptor.lifetime == ServiceLifetime.SINGLETON

    def test_create_with_factory(self):
        """ServiceDescriptor should accept a factory function."""
        factory = lambda: DummyService(99)
        descriptor = ServiceDescriptor(DummyService, factory)

        assert descriptor._is_factory is True
        assert descriptor._is_type is False

    def test_create_with_type(self):
        """ServiceDescriptor should accept a type for auto-instantiation."""
        descriptor = ServiceDescriptor(DummyService, DummyService)

        assert descriptor._is_type is True
        assert descriptor._is_factory is False

    def test_get_instance_singleton(self):
        """Singleton descriptor should return same instance."""
        factory = lambda: DummyService(42)
        descriptor = ServiceDescriptor(
            DummyService, factory, ServiceLifetime.SINGLETON
        )
        container = ServiceContainer()

        instance1 = descriptor.get_instance(container)
        instance2 = descriptor.get_instance(container)

        assert instance1 is instance2

    def test_get_instance_transient(self):
        """Transient descriptor should return new instances."""
        factory = lambda: DummyService(42)
        descriptor = ServiceDescriptor(
            DummyService, factory, ServiceLifetime.TRANSIENT
        )
        container = ServiceContainer()

        instance1 = descriptor.get_instance(container)
        instance2 = descriptor.get_instance(container)

        assert instance1 is not instance2
        assert instance1.value == instance2.value


@pytest.mark.unit
class TestServiceContainerRegistration:
    """Test ServiceContainer registration methods."""

    def test_register_instance(self, container: ServiceContainer):
        """register should register an instance."""
        instance = DummyService(42)
        result = container.register(DummyService, instance)

        assert result is container  # Method chaining
        assert container.has_service(DummyService)

    def test_register_factory(self, container: ServiceContainer):
        """register_factory should register a factory function."""
        factory = lambda: DummyService(42)
        result = container.register_factory(DummyService, factory)

        assert result is container  # Method chaining
        assert container.has_service(DummyService)

    def test_register_type(self, container: ServiceContainer):
        """register_type should register a type for auto-instantiation."""
        result = container.register_type(DummyService, DummyService)

        assert result is container  # Method chaining
        assert container.has_service(DummyService)

    def test_register_with_lifetime(self, container: ServiceContainer):
        """register should accept lifetime parameter."""
        instance = DummyService(42)
        container.register(DummyService, instance, ServiceLifetime.TRANSIENT)

        assert container.has_service(DummyService)


@pytest.mark.unit
class TestServiceContainerResolution:
    """Test ServiceContainer resolution methods."""

    def test_resolve_registered_service(self, container: ServiceContainer):
        """resolve should return registered service."""
        instance = DummyService(42)
        container.register(DummyService, instance)

        resolved = container.resolve(DummyService)

        assert resolved is instance
        assert resolved.value == 42

    def test_resolve_factory_service(self, container: ServiceContainer):
        """resolve should create service from factory."""
        container.register_factory(DummyService, lambda: DummyService(99))

        resolved = container.resolve(DummyService)

        assert isinstance(resolved, DummyService)
        assert resolved.value == 99

    def test_resolve_type_service(self, container: ServiceContainer):
        """resolve should create service from type."""
        container.register_type(DummyService, DummyService)

        resolved = container.resolve(DummyService)

        assert isinstance(resolved, DummyService)

    def test_resolve_not_found_raises_error(self, container: ServiceContainer):
        """resolve should raise ServiceNotFoundError for unregistered service."""
        with pytest.raises(ServiceNotFoundError, match="DummyService"):
            container.resolve(DummyService)

    def test_try_resolve_returns_none_when_not_found(
        self, container: ServiceContainer
    ):
        """try_resolve should return None for unregistered service."""
        result = container.try_resolve(DummyService)

        assert result is None

    def test_try_resolve_returns_service_when_found(
        self, container: ServiceContainer
    ):
        """try_resolve should return service when registered."""
        instance = DummyService(42)
        container.register(DummyService, instance)

        result = container.try_resolve(DummyService)

        assert result is instance


@pytest.mark.unit
class TestServiceContainerLifetimes:
    """Test service lifetime behaviors."""

    def test_singleton_returns_same_instance(self, container: ServiceContainer):
        """Singleton services should return same instance."""
        container.register_factory(
            DummyService,
            lambda: DummyService(42),
            ServiceLifetime.SINGLETON
        )

        instance1 = container.resolve(DummyService)
        instance2 = container.resolve(DummyService)

        assert instance1 is instance2

    def test_transient_returns_new_instances(self, container: ServiceContainer):
        """Transient services should return new instances."""
        counter = [0]

        def factory():
            counter[0] += 1
            return DummyService(counter[0])

        container.register_factory(
            DummyService, factory, ServiceLifetime.TRANSIENT
        )

        instance1 = container.resolve(DummyService)
        instance2 = container.resolve(DummyService)

        assert instance1 is not instance2
        assert instance1.value != instance2.value


@pytest.mark.unit
class TestServiceContainerScoping:
    """Test container scoping functionality."""

    def test_create_scope_returns_new_container(
        self, container: ServiceContainer
    ):
        """create_scope should return a new container."""
        scoped = container.create_scope()

        assert scoped is not container
        assert isinstance(scoped, ServiceContainer)

    def test_scoped_container_inherits_from_parent(
        self, container: ServiceContainer
    ):
        """Scoped container should resolve from parent."""
        instance = DummyService(42)
        container.register(DummyService, instance)

        scoped = container.create_scope()
        resolved = scoped.resolve(DummyService)

        assert resolved is instance

    def test_scoped_container_can_override_parent(
        self, container: ServiceContainer
    ):
        """Scoped container should allow overriding parent services."""
        parent_instance = DummyService(1)
        scoped_instance = DummyService(2)

        container.register(DummyService, parent_instance)
        scoped = container.create_scope()
        scoped.register(DummyService, scoped_instance)

        assert container.resolve(DummyService).value == 1
        assert scoped.resolve(DummyService).value == 2

    def test_scope_context_manager(self, container: ServiceContainer):
        """scope context manager should create and cleanup scoped container."""
        instance = DummyService(42)
        container.register(DummyService, instance)

        with container.scope() as scoped:
            resolved = scoped.resolve(DummyService)
            assert resolved is instance


@pytest.mark.unit
class TestServiceContainerUtilities:
    """Test container utility methods."""

    def test_has_service_returns_true_when_registered(
        self, container: ServiceContainer
    ):
        """has_service should return True for registered services."""
        container.register(DummyService, DummyService())

        assert container.has_service(DummyService) is True

    def test_has_service_returns_false_when_not_registered(
        self, container: ServiceContainer
    ):
        """has_service should return False for unregistered services."""
        assert container.has_service(DummyService) is False

    def test_has_service_checks_parent(self, container: ServiceContainer):
        """has_service should check parent container."""
        container.register(DummyService, DummyService())
        scoped = container.create_scope()

        assert scoped.has_service(DummyService) is True

    def test_get_registered_services(self, container: ServiceContainer):
        """get_registered_services should return service info."""
        container.register(DummyService, DummyService())
        container.register(AnotherService, AnotherService())

        services = container.get_registered_services()

        assert "DummyService" in services
        assert "AnotherService" in services

    def test_clear_removes_all_services(self, container: ServiceContainer):
        """clear should remove all registered services."""
        container.register(DummyService, DummyService())
        container.register(AnotherService, AnotherService())

        container.clear()

        assert container.has_service(DummyService) is False
        assert container.has_service(AnotherService) is False


@pytest.mark.unit
class TestCircularDependencyDetection:
    """Test circular dependency detection."""

    def test_circular_dependency_detection(self, container: ServiceContainer):
        """Container should detect circular dependencies."""
        # Create a scenario that would cause circular resolution
        # This is a bit contrived but tests the detection mechanism

        def factory_a():
            container.resolve(DummyService)  # Try to resolve during resolution
            return AnotherService()

        container.register_factory(DummyService, factory_a)

        with pytest.raises(CircularDependencyError):
            container.resolve(DummyService)


@pytest.mark.unit
class TestGlobalContainerFunctions:
    """Test global container functions."""

    def test_set_and_get_global_container(self, cleanup_global_container):
        """set_global_container and get_global_container should work together."""
        container = ServiceContainer()

        set_global_container(container)
        result = get_global_container()

        assert result is container

    def test_get_global_container_returns_none_when_not_set(
        self, cleanup_global_container
    ):
        """get_global_container should return None when not set."""
        set_global_container(None)
        result = get_global_container()

        assert result is None

    def test_resolve_uses_global_container(self, cleanup_global_container):
        """resolve should use global container."""
        container = ServiceContainer()
        instance = DummyService(42)
        container.register(DummyService, instance)
        set_global_container(container)

        resolved = resolve(DummyService)

        assert resolved is instance

    def test_resolve_raises_when_no_global_container(
        self, cleanup_global_container
    ):
        """resolve should raise RuntimeError when no global container."""
        set_global_container(None)

        with pytest.raises(RuntimeError, match="No global container"):
            resolve(DummyService)


@pytest.mark.unit
class TestInjectDecorator:
    """Test inject decorator."""

    def test_inject_decorator_injects_service(self, cleanup_global_container):
        """inject decorator should inject service into function."""
        container = ServiceContainer()
        instance = DummyService(42)
        container.register(DummyService, instance)
        set_global_container(container)

        @inject(DummyService)
        def my_function(service: DummyService):
            return service.value

        result = my_function()

        assert result == 42

    def test_inject_decorator_raises_without_global_container(
        self, cleanup_global_container
    ):
        """inject decorator should raise when no global container."""
        set_global_container(None)

        @inject(DummyService)
        def my_function(service: DummyService):
            return service.value

        with pytest.raises(RuntimeError, match="No global container"):
            my_function()


@pytest.mark.unit
class TestCreateDefaultContainer:
    """Test create_default_container factory function."""

    def test_create_default_container_returns_container(self):
        """create_default_container should return a ServiceContainer."""
        container = create_default_container()

        assert isinstance(container, ServiceContainer)

    def test_default_container_has_cache_manager(self):
        """Default container should have CacheManager registered."""
        container = create_default_container()

        from gmail_assistant.utils.cache_manager import CacheManager
        assert container.has_service(CacheManager)

    def test_default_container_has_rate_limiter(self):
        """Default container should have GmailRateLimiter registered."""
        container = create_default_container()

        from gmail_assistant.utils.rate_limiter import GmailRateLimiter
        assert container.has_service(GmailRateLimiter)

    def test_default_container_has_input_validator(self):
        """Default container should have InputValidator registered."""
        container = create_default_container()

        from gmail_assistant.utils.input_validator import InputValidator
        assert container.has_service(InputValidator)

    def test_default_container_has_error_handler(self):
        """Default container should have ErrorHandler registered."""
        container = create_default_container()

        from gmail_assistant.utils.error_handler import ErrorHandler
        assert container.has_service(ErrorHandler)


@pytest.mark.unit
class TestThreadSafety:
    """Test thread safety of ServiceContainer."""

    def test_container_operations_are_thread_safe(
        self, container: ServiceContainer
    ):
        """Container operations should be thread-safe."""
        import threading
        import time

        results = []
        errors = []

        def register_and_resolve():
            try:
                for i in range(10):
                    container.register(
                        DummyService,
                        DummyService(i),
                        ServiceLifetime.TRANSIENT
                    )
                    resolved = container.resolve(DummyService)
                    results.append(resolved.value)
            except Exception as e:
                errors.append(e)

        threads = [threading.Thread(target=register_and_resolve) for _ in range(5)]

        for t in threads:
            t.start()

        for t in threads:
            t.join()

        assert len(errors) == 0
        assert len(results) == 50
