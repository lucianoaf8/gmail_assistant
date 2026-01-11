"""
Comprehensive tests for container.py module.
Tests dependency injection container, service descriptors, and factory functions.
"""

import threading
import time
from typing import Protocol
from unittest import mock

import pytest

from gmail_assistant.core.container import (
    CircularDependencyError,
    ServiceContainer,
    ServiceDescriptor,
    ServiceLifetime,
    ServiceNotFoundError,
    create_default_container,
    create_full_container,
    create_modify_container,
    create_readonly_container,
    get_global_container,
    inject,
    resolve,
    set_global_container,
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


class CounterService:
    """Service with instance counter for testing transient behavior."""
    _counter = 0

    def __init__(self):
        CounterService._counter += 1
        self.instance_number = CounterService._counter

    @classmethod
    def reset_counter(cls):
        cls._counter = 0


@pytest.fixture
def container():
    """Create a fresh ServiceContainer for each test."""
    return ServiceContainer()


@pytest.fixture
def cleanup_global_container():
    """Clean up global container after test."""
    original = get_global_container()
    yield
    set_global_container(original)


@pytest.fixture
def reset_counter():
    """Reset CounterService counter after test."""
    CounterService.reset_counter()
    yield
    CounterService.reset_counter()


class TestServiceLifetime:
    """Tests for ServiceLifetime enumeration."""

    def test_singleton_value(self):
        """SINGLETON should have expected value."""
        assert ServiceLifetime.SINGLETON == "singleton"

    def test_transient_value(self):
        """TRANSIENT should have expected value."""
        assert ServiceLifetime.TRANSIENT == "transient"

    def test_scoped_value(self):
        """SCOPED should have expected value."""
        assert ServiceLifetime.SCOPED == "scoped"


class TestServiceDescriptor:
    """Tests for ServiceDescriptor class."""

    def test_create_with_instance(self):
        """ServiceDescriptor should accept an instance."""
        instance = DummyService(42)
        descriptor = ServiceDescriptor(DummyService, instance)

        assert descriptor.service_type == DummyService
        assert descriptor.implementation == instance
        assert descriptor.lifetime == ServiceLifetime.SINGLETON
        assert descriptor._is_factory is False
        assert descriptor._is_type is False

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
        assert instance1.value == 42

    def test_get_instance_transient(self, reset_counter):
        """Transient descriptor should return new instances."""
        factory = lambda: CounterService()
        descriptor = ServiceDescriptor(
            CounterService, factory, ServiceLifetime.TRANSIENT
        )
        container = ServiceContainer()

        instance1 = descriptor.get_instance(container)
        instance2 = descriptor.get_instance(container)

        assert instance1 is not instance2
        assert instance1.instance_number != instance2.instance_number

    def test_get_instance_scoped(self):
        """Scoped descriptor should cache instance."""
        factory = lambda: DummyService(42)
        descriptor = ServiceDescriptor(
            DummyService, factory, ServiceLifetime.SCOPED
        )
        container = ServiceContainer()

        instance1 = descriptor.get_instance(container)
        instance2 = descriptor.get_instance(container)

        # Scoped should cache like singleton within the scope
        assert instance1 is instance2

    def test_get_instance_from_type(self):
        """Descriptor should create instance from type."""
        descriptor = ServiceDescriptor(
            DummyService, DummyService, ServiceLifetime.TRANSIENT
        )
        container = ServiceContainer()

        instance = descriptor.get_instance(container)

        assert isinstance(instance, DummyService)
        assert instance.value == 0

    def test_get_instance_from_direct_instance(self):
        """Descriptor should return direct instance."""
        instance = DummyService(99)
        descriptor = ServiceDescriptor(DummyService, instance)
        container = ServiceContainer()

        result = descriptor.get_instance(container)

        assert result is instance
        assert result.value == 99


class TestServiceContainerInit:
    """Tests for ServiceContainer initialization."""

    def test_container_init(self):
        """Container should initialize with empty services."""
        container = ServiceContainer()

        assert isinstance(container._services, dict)
        assert len(container._services) == 0
        assert container._parent is None

    def test_container_init_with_parent(self):
        """Container should accept parent container."""
        parent = ServiceContainer()
        child = ServiceContainer(parent=parent)

        assert child._parent is parent


class TestServiceContainerRegistration:
    """Tests for ServiceContainer registration methods."""

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

    def test_register_with_singleton_lifetime(self, container: ServiceContainer):
        """register should accept singleton lifetime parameter."""
        instance = DummyService(42)
        container.register(DummyService, instance, ServiceLifetime.SINGLETON)

        assert container.has_service(DummyService)
        # Verify singleton behavior
        resolved1 = container.resolve(DummyService)
        resolved2 = container.resolve(DummyService)
        assert resolved1 is resolved2

    def test_register_with_transient_lifetime(self, container: ServiceContainer, reset_counter):
        """register should accept transient lifetime parameter."""
        container.register_factory(
            CounterService,
            lambda: CounterService(),
            ServiceLifetime.TRANSIENT
        )

        assert container.has_service(CounterService)
        # Verify transient behavior
        resolved1 = container.resolve(CounterService)
        resolved2 = container.resolve(CounterService)
        assert resolved1 is not resolved2

    def test_register_override_existing_service(self, container: ServiceContainer):
        """Registering same service type should override previous registration."""
        container.register(DummyService, DummyService(1))
        container.register(DummyService, DummyService(2))

        resolved = container.resolve(DummyService)
        assert resolved.value == 2


class TestServiceContainerResolution:
    """Tests for ServiceContainer resolution methods."""

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

    def test_resolve_from_parent_container(self, container: ServiceContainer):
        """resolve should check parent container."""
        instance = DummyService(42)
        container.register(DummyService, instance)

        child = ServiceContainer(parent=container)
        resolved = child.resolve(DummyService)

        assert resolved is instance

    def test_resolve_child_overrides_parent(self, container: ServiceContainer):
        """Child container should override parent service."""
        parent_instance = DummyService(1)
        child_instance = DummyService(2)

        container.register(DummyService, parent_instance)
        child = ServiceContainer(parent=container)
        child.register(DummyService, child_instance)

        assert container.resolve(DummyService).value == 1
        assert child.resolve(DummyService).value == 2

    def test_try_resolve_returns_none_when_not_found(self, container: ServiceContainer):
        """try_resolve should return None for unregistered service."""
        result = container.try_resolve(DummyService)

        assert result is None

    def test_try_resolve_returns_service_when_found(self, container: ServiceContainer):
        """try_resolve should return service when registered."""
        instance = DummyService(42)
        container.register(DummyService, instance)

        result = container.try_resolve(DummyService)

        assert result is instance


class TestServiceContainerLifetimes:
    """Tests for service lifetime behaviors."""

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

    def test_transient_returns_new_instances(self, container: ServiceContainer, reset_counter):
        """Transient services should return new instances."""
        container.register_factory(
            CounterService,
            lambda: CounterService(),
            ServiceLifetime.TRANSIENT
        )

        instance1 = container.resolve(CounterService)
        instance2 = container.resolve(CounterService)

        assert instance1 is not instance2
        assert instance1.instance_number != instance2.instance_number

    def test_scoped_lifetime_behavior(self, container: ServiceContainer, reset_counter):
        """Scoped services should cache within scope."""
        container.register_factory(
            CounterService,
            lambda: CounterService(),
            ServiceLifetime.SCOPED
        )

        instance1 = container.resolve(CounterService)
        instance2 = container.resolve(CounterService)

        # Scoped should cache like singleton within the container
        assert instance1 is instance2


class TestServiceContainerScoping:
    """Tests for container scoping functionality."""

    def test_create_scope_returns_new_container(self, container: ServiceContainer):
        """create_scope should return a new container."""
        scoped = container.create_scope()

        assert scoped is not container
        assert isinstance(scoped, ServiceContainer)

    def test_scoped_container_inherits_from_parent(self, container: ServiceContainer):
        """Scoped container should resolve from parent."""
        instance = DummyService(42)
        container.register(DummyService, instance)

        scoped = container.create_scope()
        resolved = scoped.resolve(DummyService)

        assert resolved is instance

    def test_scoped_container_can_override_parent(self, container: ServiceContainer):
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
            # Add a scoped service
            scoped.register(AnotherService, AnotherService("scoped"))
            assert scoped.has_service(AnotherService)

        # After context, parent container shouldn't have the scoped service
        assert not container.has_service(AnotherService)

    def test_scope_context_manager_clears_services(self, container: ServiceContainer):
        """scope context manager should clear scoped services on exit."""
        scoped_service = None

        with container.scope() as scoped:
            scoped.register(DummyService, DummyService(99))
            scoped_service = scoped

        # Services should be cleared after exiting context
        assert len(scoped_service._services) == 0


class TestServiceContainerUtilities:
    """Tests for container utility methods."""

    def test_has_service_returns_true_when_registered(self, container: ServiceContainer):
        """has_service should return True for registered services."""
        container.register(DummyService, DummyService())

        assert container.has_service(DummyService) is True

    def test_has_service_returns_false_when_not_registered(self, container: ServiceContainer):
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
        assert services["DummyService"] == ServiceLifetime.SINGLETON

    def test_get_registered_services_empty(self, container: ServiceContainer):
        """get_registered_services should return empty dict for empty container."""
        services = container.get_registered_services()

        assert services == {}

    def test_clear_removes_all_services(self, container: ServiceContainer):
        """clear should remove all registered services."""
        container.register(DummyService, DummyService())
        container.register(AnotherService, AnotherService())

        container.clear()

        assert container.has_service(DummyService) is False
        assert container.has_service(AnotherService) is False
        assert len(container._services) == 0


class TestCircularDependencyDetection:
    """Tests for circular dependency detection."""

    def test_circular_dependency_detection(self, container: ServiceContainer):
        """Container should detect circular dependencies."""
        def factory_a():
            # Try to resolve the same service during its creation
            container.resolve(DummyService)
            return DummyService()

        container.register_factory(DummyService, factory_a)

        with pytest.raises(CircularDependencyError, match="Circular dependency detected"):
            container.resolve(DummyService)

    def test_circular_dependency_cleanup(self, container: ServiceContainer):
        """Circular dependency detection should cleanup resolving set."""
        def factory_a():
            container.resolve(DummyService)
            return DummyService()

        container.register_factory(DummyService, factory_a)

        try:
            container.resolve(DummyService)
        except CircularDependencyError:
            pass

        # Resolving set should be cleaned up after error
        assert DummyService not in container._resolving


class TestGlobalContainerFunctions:
    """Tests for global container functions."""

    def test_set_and_get_global_container(self, cleanup_global_container):
        """set_global_container and get_global_container should work together."""
        container = ServiceContainer()

        set_global_container(container)
        result = get_global_container()

        assert result is container

    def test_get_global_container_returns_none_when_not_set(self, cleanup_global_container):
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

    def test_resolve_raises_when_no_global_container(self, cleanup_global_container):
        """resolve should raise RuntimeError when no global container."""
        set_global_container(None)

        with pytest.raises(RuntimeError, match="No global container"):
            resolve(DummyService)


class TestInjectDecorator:
    """Tests for inject decorator."""

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

    def test_inject_decorator_with_additional_args(self, cleanup_global_container):
        """inject decorator should work with additional function arguments."""
        container = ServiceContainer()
        instance = DummyService(10)
        container.register(DummyService, instance)
        set_global_container(container)

        @inject(DummyService)
        def my_function(service: DummyService, multiplier: int):
            return service.value * multiplier

        result = my_function(5)

        assert result == 50

    def test_inject_decorator_raises_without_global_container(self, cleanup_global_container):
        """inject decorator should raise when no global container."""
        set_global_container(None)

        @inject(DummyService)
        def my_function(service: DummyService):
            return service.value

        with pytest.raises(RuntimeError, match="No global container"):
            my_function()


class TestCreateDefaultContainer:
    """Tests for create_default_container factory function."""

    def test_create_default_container_returns_container(self):
        """create_default_container should return a ServiceContainer."""
        container = create_default_container()

        assert isinstance(container, ServiceContainer)

    def test_default_container_has_cache_manager(self):
        """Default container should have CacheManager registered."""
        from gmail_assistant.utils.cache_manager import CacheManager

        container = create_default_container()

        assert container.has_service(CacheManager)

    def test_default_container_has_rate_limiter(self):
        """Default container should have GmailRateLimiter registered."""
        from gmail_assistant.utils.rate_limiter import GmailRateLimiter

        container = create_default_container()

        assert container.has_service(GmailRateLimiter)

    def test_default_container_has_input_validator(self):
        """Default container should have InputValidator registered."""
        from gmail_assistant.utils.input_validator import InputValidator

        container = create_default_container()

        assert container.has_service(InputValidator)

    def test_default_container_has_error_handler(self):
        """Default container should have ErrorHandler registered."""
        from gmail_assistant.utils.error_handler import ErrorHandler

        container = create_default_container()

        assert container.has_service(ErrorHandler)

    def test_default_container_has_email_repository(self):
        """Default container should have EmailRepositoryProtocol registered."""
        from gmail_assistant.core.protocols import EmailRepositoryProtocol

        container = create_default_container()

        assert container.has_service(EmailRepositoryProtocol)


# Note: Factory function tests are covered in integration tests since they require
# actual imports and instantiations. The core container functionality is thoroughly
# tested above.


class TestThreadSafety:
    """Tests for thread safety of ServiceContainer."""

    def test_container_operations_are_thread_safe(self, container: ServiceContainer, reset_counter):
        """Container operations should be thread-safe."""
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

    def test_concurrent_resolve_singleton(self, container: ServiceContainer, reset_counter):
        """Concurrent singleton resolution should be thread-safe."""
        container.register_factory(
            CounterService,
            lambda: CounterService(),
            ServiceLifetime.SINGLETON
        )

        instances = []

        def resolve_service():
            instance = container.resolve(CounterService)
            instances.append(instance)

        threads = [threading.Thread(target=resolve_service) for _ in range(10)]

        for t in threads:
            t.start()

        for t in threads:
            t.join()

        # All should be the same instance
        assert len(instances) == 10
        assert all(inst is instances[0] for inst in instances)


class TestErrorConditions:
    """Tests for error conditions and edge cases."""

    def test_service_not_found_error_message(self, container: ServiceContainer):
        """ServiceNotFoundError should have descriptive message."""
        with pytest.raises(ServiceNotFoundError) as exc_info:
            container.resolve(DummyService)

        assert "DummyService" in str(exc_info.value)

    def test_circular_dependency_error_message(self, container: ServiceContainer):
        """CircularDependencyError should have descriptive message."""
        def factory():
            container.resolve(DummyService)
            return DummyService()

        container.register_factory(DummyService, factory)

        with pytest.raises(CircularDependencyError) as exc_info:
            container.resolve(DummyService)

        assert "Circular dependency" in str(exc_info.value)
        assert "DummyService" in str(exc_info.value)

    def test_parent_service_not_found_propagates(self, container: ServiceContainer):
        """ServiceNotFoundError should propagate from parent."""
        child = ServiceContainer(parent=container)

        with pytest.raises(ServiceNotFoundError):
            child.resolve(DummyService)
