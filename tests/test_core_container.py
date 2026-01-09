"""
Tests for the Gmail Fetcher dependency injection container.

Tests service registration, resolution, and factory functions.
"""

import pytest
import sys
from pathlib import Path
from typing import Protocol

from gmail_assistant.core.container import (
    ServiceContainer,
    ServiceLifetime,
    ServiceDescriptor,
    ServiceNotFoundError,
    CircularDependencyError,
)


class TestServiceContainer:
    """Tests for ServiceContainer."""

    def test_container_creation(self):
        """Test basic container creation."""
        container = ServiceContainer()
        assert container is not None
        assert container.get_registered_services() == {}

    def test_register_instance(self):
        """Test registering a service instance."""

        class MyService:
            def __init__(self, value: int):
                self.value = value

        container = ServiceContainer()
        service = MyService(42)
        container.register(MyService, service)

        assert container.has_service(MyService)
        resolved = container.resolve(MyService)
        assert resolved is service
        assert resolved.value == 42

    def test_register_factory(self):
        """Test registering a factory function."""

        class MyService:
            counter = 0

            def __init__(self):
                MyService.counter += 1
                self.id = MyService.counter

        MyService.counter = 0  # Reset
        container = ServiceContainer()
        container.register_factory(MyService, lambda: MyService())

        # First resolution creates instance
        service1 = container.resolve(MyService)
        assert service1.id == 1

        # Second resolution returns same instance (singleton)
        service2 = container.resolve(MyService)
        assert service2.id == 1
        assert service2 is service1

    def test_register_factory_transient(self):
        """Test registering a factory with transient lifetime."""

        class MyService:
            counter = 0

            def __init__(self):
                MyService.counter += 1
                self.id = MyService.counter

        MyService.counter = 0  # Reset
        container = ServiceContainer()
        container.register_factory(
            MyService,
            lambda: MyService(),
            lifetime=ServiceLifetime.TRANSIENT
        )

        # Each resolution creates new instance
        service1 = container.resolve(MyService)
        service2 = container.resolve(MyService)
        assert service1.id != service2.id

    def test_register_type(self):
        """Test registering a type for auto-instantiation."""

        class SimpleService:
            def __init__(self):
                self.initialized = True

        container = ServiceContainer()
        container.register_type(SimpleService, SimpleService)

        service = container.resolve(SimpleService)
        assert service.initialized is True

    def test_resolve_not_found(self):
        """Test resolving unregistered service raises error."""

        class UnknownService:
            pass

        container = ServiceContainer()

        with pytest.raises(ServiceNotFoundError) as exc_info:
            container.resolve(UnknownService)

        assert "UnknownService" in str(exc_info.value)

    def test_try_resolve_not_found(self):
        """Test try_resolve returns None for unregistered service."""

        class UnknownService:
            pass

        container = ServiceContainer()
        result = container.try_resolve(UnknownService)
        assert result is None

    def test_has_service(self):
        """Test has_service method."""

        class MyService:
            pass

        container = ServiceContainer()
        assert not container.has_service(MyService)

        container.register(MyService, MyService())
        assert container.has_service(MyService)

    def test_method_chaining(self):
        """Test that register methods return self for chaining."""

        class ServiceA:
            pass

        class ServiceB:
            pass

        container = ServiceContainer()
        result = container.register(ServiceA, ServiceA()).register(ServiceB, ServiceB())

        assert result is container
        assert container.has_service(ServiceA)
        assert container.has_service(ServiceB)

    def test_clear(self):
        """Test clearing the container."""

        class MyService:
            pass

        container = ServiceContainer()
        container.register(MyService, MyService())
        assert container.has_service(MyService)

        container.clear()
        assert not container.has_service(MyService)

    def test_get_registered_services(self):
        """Test getting registered service info."""

        class ServiceA:
            pass

        class ServiceB:
            pass

        container = ServiceContainer()
        container.register(ServiceA, ServiceA())
        container.register_factory(ServiceB, lambda: ServiceB(), ServiceLifetime.TRANSIENT)

        services = container.get_registered_services()
        assert "ServiceA" in services
        assert "ServiceB" in services
        assert services["ServiceA"] == ServiceLifetime.SINGLETON
        assert services["ServiceB"] == ServiceLifetime.TRANSIENT


class TestScopedContainer:
    """Tests for scoped container functionality."""

    def test_create_scope(self):
        """Test creating a scoped container."""

        class ParentService:
            pass

        class ScopedService:
            pass

        parent = ServiceContainer()
        parent.register(ParentService, ParentService())

        scoped = parent.create_scope()

        # Scoped can access parent services
        assert scoped.has_service(ParentService)

        # Scoped can have its own services
        scoped.register(ScopedService, ScopedService())
        assert scoped.has_service(ScopedService)

        # Parent doesn't have scoped services
        assert not parent.has_service(ScopedService)

    def test_scope_context_manager(self):
        """Test scope context manager."""

        class MyService:
            pass

        container = ServiceContainer()

        with container.scope() as scoped:
            scoped.register(MyService, MyService())
            assert scoped.has_service(MyService)

        # After context, scoped is cleared
        # (but this is a new container, so we can't check it)


class TestServiceDescriptor:
    """Tests for ServiceDescriptor."""

    def test_descriptor_with_instance(self):
        """Test descriptor with direct instance."""

        class MyService:
            pass

        instance = MyService()
        descriptor = ServiceDescriptor(MyService, instance)

        assert descriptor.service_type is MyService
        assert descriptor.implementation is instance
        assert descriptor.lifetime == ServiceLifetime.SINGLETON

    def test_descriptor_with_factory(self):
        """Test descriptor with factory function."""

        class MyService:
            pass

        descriptor = ServiceDescriptor(
            MyService,
            lambda: MyService(),
            ServiceLifetime.TRANSIENT
        )

        assert descriptor.lifetime == ServiceLifetime.TRANSIENT
        assert descriptor._is_factory is True


class TestCircularDependencyDetection:
    """Tests for circular dependency detection."""

    def test_no_circular_dependency(self):
        """Test that normal resolution works."""

        class ServiceA:
            pass

        class ServiceB:
            pass

        container = ServiceContainer()
        container.register(ServiceA, ServiceA())
        container.register(ServiceB, ServiceB())

        # Should not raise
        a = container.resolve(ServiceA)
        b = container.resolve(ServiceB)
        assert a is not None
        assert b is not None


class TestIntegration:
    """Integration tests for the container."""

    def test_multiple_services_integration(self):
        """Test container with multiple interacting services."""

        class Logger:
            def __init__(self):
                self.logs = []

            def log(self, message: str):
                self.logs.append(message)

        class Repository:
            def __init__(self):
                self.data = {}

            def save(self, key: str, value: str):
                self.data[key] = value

        class Service:
            def __init__(self, logger: Logger, repo: Repository):
                self.logger = logger
                self.repo = repo

            def process(self, key: str, value: str):
                self.logger.log(f"Processing {key}")
                self.repo.save(key, value)

        container = ServiceContainer()
        logger = Logger()
        repo = Repository()

        container.register(Logger, logger)
        container.register(Repository, repo)
        container.register_factory(
            Service,
            lambda: Service(container.resolve(Logger), container.resolve(Repository))
        )

        service = container.resolve(Service)
        service.process("test", "value")

        assert "Processing test" in logger.logs
        assert repo.data.get("test") == "value"


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
