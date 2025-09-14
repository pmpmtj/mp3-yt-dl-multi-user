"""
Dependency injection container for better testability.

This module provides a dependency injection container that manages
the creation and lifecycle of application dependencies, making the
system more testable and maintainable.
"""

import logging
import threading
from typing import Optional, Dict, Any, Type, TypeVar, Callable
from dataclasses import dataclass
from abc import ABC, abstractmethod

# Initialize logger
logger = logging.getLogger("dependency_container")

T = TypeVar('T')


class ServiceLifetime:
    """Service lifetime enumeration."""
    SINGLETON = "singleton"
    TRANSIENT = "transient"
    SCOPED = "scoped"


@dataclass
class ServiceDescriptor:
    """Descriptor for a registered service."""
    service_type: Type
    implementation_type: Optional[Type] = None
    factory: Optional[Callable] = None
    instance: Optional[Any] = None
    lifetime: str = ServiceLifetime.TRANSIENT
    dependencies: Optional[Dict[str, Type]] = None


class IDependencyContainer(ABC):
    """Interface for dependency injection container."""
    
    @abstractmethod
    def register_singleton(self, service_type: Type[T], implementation_type: Type[T]) -> None:
        """Register a singleton service."""
        pass
    
    @abstractmethod
    def register_transient(self, service_type: Type[T], implementation_type: Type[T]) -> None:
        """Register a transient service."""
        pass
    
    @abstractmethod
    def register_factory(self, service_type: Type[T], factory: Callable[[], T]) -> None:
        """Register a service with a factory function."""
        pass
    
    @abstractmethod
    def get_service(self, service_type: Type[T]) -> T:
        """Get a service instance."""
        pass
    
    @abstractmethod
    def get_optional_service(self, service_type: Type[T]) -> Optional[T]:
        """Get an optional service instance."""
        pass


class DependencyContainer(IDependencyContainer):
    """
    Dependency injection container implementation.
    
    Provides singleton, transient, and factory-based service registration
    and resolution for dependency injection.
    """
    
    def __init__(self):
        """Initialize the dependency container."""
        self._services: Dict[Type, ServiceDescriptor] = {}
        self._lock = threading.RLock()
        logger.debug("DependencyContainer initialized")
    
    def register_singleton(self, service_type: Type[T], implementation_type: Type[T]) -> None:
        """Register a singleton service."""
        with self._lock:
            self._services[service_type] = ServiceDescriptor(
                service_type=service_type,
                implementation_type=implementation_type,
                lifetime=ServiceLifetime.SINGLETON
            )
            logger.debug(f"Registered singleton: {service_type.__name__} -> {implementation_type.__name__}")
    
    def register_transient(self, service_type: Type[T], implementation_type: Type[T]) -> None:
        """Register a transient service."""
        with self._lock:
            self._services[service_type] = ServiceDescriptor(
                service_type=service_type,
                implementation_type=implementation_type,
                lifetime=ServiceLifetime.TRANSIENT
            )
            logger.debug(f"Registered transient: {service_type.__name__} -> {implementation_type.__name__}")
    
    def register_factory(self, service_type: Type[T], factory: Callable[[], T]) -> None:
        """Register a service with a factory function."""
        with self._lock:
            self._services[service_type] = ServiceDescriptor(
                service_type=service_type,
                factory=factory,
                lifetime=ServiceLifetime.TRANSIENT
            )
            logger.debug(f"Registered factory: {service_type.__name__}")
    
    def register_instance(self, service_type: Type[T], instance: T) -> None:
        """Register a service instance."""
        with self._lock:
            self._services[service_type] = ServiceDescriptor(
                service_type=service_type,
                instance=instance,
                lifetime=ServiceLifetime.SINGLETON
            )
            logger.debug(f"Registered instance: {service_type.__name__}")
    
    def get_service(self, service_type: Type[T]) -> T:
        """Get a service instance."""
        with self._lock:
            if service_type not in self._services:
                raise ValueError(f"Service {service_type.__name__} is not registered")
            
            descriptor = self._services[service_type]
            
            if descriptor.lifetime == ServiceLifetime.SINGLETON:
                if descriptor.instance is None:
                    descriptor.instance = self._create_instance(descriptor)
                return descriptor.instance
            
            elif descriptor.lifetime == ServiceLifetime.TRANSIENT:
                return self._create_instance(descriptor)
            
            else:
                raise ValueError(f"Unsupported lifetime: {descriptor.lifetime}")
    
    def get_optional_service(self, service_type: Type[T]) -> Optional[T]:
        """Get an optional service instance."""
        try:
            return self.get_service(service_type)
        except ValueError:
            return None
    
    def _create_instance(self, descriptor: ServiceDescriptor) -> Any:
        """Create an instance of a service."""
        if descriptor.factory:
            return descriptor.factory()
        
        if descriptor.implementation_type:
            return descriptor.implementation_type()
        
        if descriptor.instance:
            return descriptor.instance
        
        raise ValueError(f"Cannot create instance for {descriptor.service_type.__name__}")
    
    def is_registered(self, service_type: Type) -> bool:
        """Check if a service is registered."""
        return service_type in self._services
    
    def clear(self) -> None:
        """Clear all registered services."""
        with self._lock:
            self._services.clear()
            logger.debug("DependencyContainer cleared")


class ServiceProvider:
    """
    Service provider that manages dependency injection.
    
    This class provides a global service provider that can be configured
    for different environments (production, testing, etc.).
    """
    
    def __init__(self, container: Optional[IDependencyContainer] = None):
        """Initialize the service provider."""
        self._container = container or DependencyContainer()
        self._default_container = DependencyContainer()
        self._is_test_mode = False
    
    def configure_for_testing(self, test_container: Optional[IDependencyContainer] = None) -> None:
        """Configure the service provider for testing."""
        self._container = test_container or DependencyContainer()
        self._is_test_mode = True
        logger.debug("ServiceProvider configured for testing")
    
    def configure_for_production(self) -> None:
        """Configure the service provider for production."""
        self._container = self._default_container
        self._is_test_mode = False
        logger.debug("ServiceProvider configured for production")
    
    def register_singleton(self, service_type: Type[T], implementation_type: Type[T]) -> None:
        """Register a singleton service."""
        self._container.register_singleton(service_type, implementation_type)
    
    def register_transient(self, service_type: Type[T], implementation_type: Type[T]) -> None:
        """Register a transient service."""
        self._container.register_transient(service_type, implementation_type)
    
    def register_factory(self, service_type: Type[T], factory: Callable[[], T]) -> None:
        """Register a service with a factory function."""
        self._container.register_factory(service_type, factory)
    
    def register_instance(self, service_type: Type[T], instance: T) -> None:
        """Register a service instance."""
        self._container.register_instance(service_type, instance)
    
    def get_service(self, service_type: Type[T]) -> T:
        """Get a service instance."""
        return self._container.get_service(service_type)
    
    def get_optional_service(self, service_type: Type[T]) -> Optional[T]:
        """Get an optional service instance."""
        return self._container.get_optional_service(service_type)
    
    def is_test_mode(self) -> bool:
        """Check if in test mode."""
        return self._is_test_mode


# Global service provider instance
_service_provider: Optional[ServiceProvider] = None
_provider_lock = threading.Lock()


def get_service_provider() -> ServiceProvider:
    """Get the global service provider instance."""
    global _service_provider
    
    if _service_provider is None:
        with _provider_lock:
            if _service_provider is None:
                _service_provider = ServiceProvider()
                logger.info("Created global ServiceProvider instance")
    
    return _service_provider


def configure_for_testing(test_container: Optional[IDependencyContainer] = None) -> None:
    """Configure the global service provider for testing."""
    get_service_provider().configure_for_testing(test_container)


def configure_for_production() -> None:
    """Configure the global service provider for production."""
    get_service_provider().configure_for_production()


def get_service(service_type: Type[T]) -> T:
    """Get a service from the global service provider."""
    return get_service_provider().get_service(service_type)


def get_optional_service(service_type: Type[T]) -> Optional[T]:
    """Get an optional service from the global service provider."""
    return get_service_provider().get_optional_service(service_type)
