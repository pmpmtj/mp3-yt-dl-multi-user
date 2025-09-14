"""
Session manager factory for dependency injection.

This module provides a factory for creating session managers with
configurable parameters, making it easier to test and configure.
"""

import logging
from typing import Optional, Dict, Any, Union, Callable
from pathlib import Path

from .session_manager import SessionManager
from .user_context import UserContext

# Initialize logger
logger = logging.getLogger("session_manager_factory")


class SessionManagerFactory:
    """
    Factory for creating session managers.
    
    This factory allows for easy configuration and testing of session managers
    with different parameters and dependencies.
    """
    
    def __init__(self, 
                 session_timeout_hours: int = 24,
                 max_concurrent_sessions: int = 100,
                 max_jobs_per_session: int = 10,
                 cleanup_interval_minutes: int = 60,
                 path_generator: Optional[Callable] = None,
                 base_download_dir: Optional[Union[str, Path]] = None):
        """
        Initialize the session manager factory.
        
        Args:
            session_timeout_hours: Hours before inactive session expires
            max_concurrent_sessions: Maximum number of concurrent sessions
            max_jobs_per_session: Maximum jobs per session
            cleanup_interval_minutes: Minutes between cleanup runs
            path_generator: Optional custom path generator function
            base_download_dir: Optional base download directory
        """
        self.session_timeout_hours = session_timeout_hours
        self.max_concurrent_sessions = max_concurrent_sessions
        self.max_jobs_per_session = max_jobs_per_session
        self.cleanup_interval_minutes = cleanup_interval_minutes
        self.path_generator = path_generator
        self.base_download_dir = base_download_dir
        
        logger.debug(f"SessionManagerFactory initialized: "
                    f"timeout={session_timeout_hours}h, "
                    f"max_sessions={max_concurrent_sessions}, "
                    f"max_jobs={max_jobs_per_session}")
    
    def create_session_manager(self) -> SessionManager:
        """
        Create a new session manager instance.
        
        Returns:
            New SessionManager instance with configured parameters
        """
        return SessionManager(
            session_timeout_hours=self.session_timeout_hours,
            max_concurrent_sessions=self.max_concurrent_sessions,
            max_jobs_per_session=self.max_jobs_per_session,
            cleanup_interval_minutes=self.cleanup_interval_minutes
        )
    
    def create_user_context(self, 
                           session_uuid: Optional[str] = None,
                           base_download_dir: Optional[Union[str, Path]] = None) -> UserContext:
        """
        Create a new user context.
        
        Args:
            session_uuid: Optional existing session UUID
            base_download_dir: Optional base download directory
            
        Returns:
            New UserContext instance
        """
        # Use factory's base download dir if not specified
        if base_download_dir is None:
            base_download_dir = self.base_download_dir
        
        return UserContext(
            session_uuid=session_uuid,
            path_generator=self.path_generator,
            base_download_dir=base_download_dir
        )
    
    def get_config(self) -> Dict[str, Any]:
        """
        Get the factory configuration.
        
        Returns:
            Dictionary with factory configuration
        """
        return {
            'session_timeout_hours': self.session_timeout_hours,
            'max_concurrent_sessions': self.max_concurrent_sessions,
            'max_jobs_per_session': self.max_jobs_per_session,
            'cleanup_interval_minutes': self.cleanup_interval_minutes,
            'has_custom_path_generator': self.path_generator is not None,
            'base_download_dir': str(self.base_download_dir) if self.base_download_dir else None
        }


class SessionManagerProvider:
    """
    Provider for session managers with dependency injection support.
    
    This class manages the creation and configuration of session managers
    and can be easily mocked for testing.
    """
    
    def __init__(self, factory: Optional[SessionManagerFactory] = None):
        """
        Initialize the session manager provider.
        
        Args:
            factory: Optional custom factory instance
        """
        self._factory = factory or SessionManagerFactory()
        self._session_manager: Optional[SessionManager] = None
        self._lock = None  # Will be set when session manager is created
        
        logger.debug("SessionManagerProvider initialized")
    
    def get_session_manager(self) -> SessionManager:
        """
        Get the session manager instance (singleton pattern).
        
        Returns:
            SessionManager instance
        """
        if self._session_manager is None:
            # Import here to avoid circular imports
            import threading
            if self._lock is None:
                self._lock = threading.Lock()
            
            with self._lock:
                if self._session_manager is None:
                    self._session_manager = self._factory.create_session_manager()
                    logger.info("Created SessionManager instance via provider")
        
        return self._session_manager
    
    def create_user_context(self, 
                           session_uuid: Optional[str] = None,
                           base_download_dir: Optional[Union[str, Path]] = None) -> UserContext:
        """
        Create a new user context.
        
        Args:
            session_uuid: Optional existing session UUID
            base_download_dir: Optional base download directory
            
        Returns:
            New UserContext instance
        """
        return self._factory.create_user_context(session_uuid, base_download_dir)
    
    def reset_session_manager(self) -> None:
        """Reset the session manager instance (useful for testing)."""
        self._session_manager = None
        logger.debug("SessionManager instance reset")
    
    def configure_factory(self, 
                         session_timeout_hours: Optional[int] = None,
                         max_concurrent_sessions: Optional[int] = None,
                         max_jobs_per_session: Optional[int] = None,
                         cleanup_interval_minutes: Optional[int] = None,
                         path_generator: Optional[Callable] = None,
                         base_download_dir: Optional[Union[str, Path]] = None) -> None:
        """
        Reconfigure the factory with new parameters.
        
        Args:
            session_timeout_hours: New session timeout in hours
            max_concurrent_sessions: New max concurrent sessions
            max_jobs_per_session: New max jobs per session
            cleanup_interval_minutes: New cleanup interval in minutes
            path_generator: New path generator function
            base_download_dir: New base download directory
        """
        # Create new factory with updated parameters
        new_factory = SessionManagerFactory(
            session_timeout_hours=session_timeout_hours or self._factory.session_timeout_hours,
            max_concurrent_sessions=max_concurrent_sessions or self._factory.max_concurrent_sessions,
            max_jobs_per_session=max_jobs_per_session or self._factory.max_jobs_per_session,
            cleanup_interval_minutes=cleanup_interval_minutes or self._factory.cleanup_interval_minutes,
            path_generator=path_generator or self._factory.path_generator,
            base_download_dir=base_download_dir or self._factory.base_download_dir
        )
        
        self._factory = new_factory
        self.reset_session_manager()  # Reset to use new configuration
        
        logger.info("SessionManagerProvider reconfigured")
    
    def get_config(self) -> Dict[str, Any]:
        """
        Get the current configuration.
        
        Returns:
            Dictionary with current configuration
        """
        config = self._factory.get_config()
        config['has_session_manager'] = self._session_manager is not None
        return config


# Global session manager provider
_session_manager_provider: Optional[SessionManagerProvider] = None
_provider_lock = None


def get_session_manager_provider() -> SessionManagerProvider:
    """Get the global session manager provider."""
    global _session_manager_provider, _provider_lock
    
    if _session_manager_provider is None:
        import threading
        if _provider_lock is None:
            _provider_lock = threading.Lock()
        
        with _provider_lock:
            if _session_manager_provider is None:
                _session_manager_provider = SessionManagerProvider()
                logger.info("Created global SessionManagerProvider instance")
    
    return _session_manager_provider


def get_session_manager() -> SessionManager:
    """Get the session manager from the global provider."""
    return get_session_manager_provider().get_session_manager()


def create_session(session_uuid: Optional[str] = None,
                  path_generator: Optional[Callable] = None,
                  base_download_dir: Optional[Union[str, Path]] = None) -> str:
    """Create a new session using the global provider."""
    provider = get_session_manager_provider()
    session_manager = provider.get_session_manager()
    
    # Create user context with custom parameters if provided
    if path_generator is not None or base_download_dir is not None:
        user_context = provider.create_user_context(
            session_uuid=session_uuid,
            base_download_dir=base_download_dir
        )
        # Override path generator if provided
        if path_generator is not None:
            user_context._path_generator = path_generator
        session_uuid = user_context.get_session_id()
    else:
        session_uuid = session_manager.create_session(session_uuid, path_generator, base_download_dir)
    
    return session_uuid


def get_session(session_uuid: str) -> Optional[UserContext]:
    """Get a session using the global provider."""
    provider = get_session_manager_provider()
    session_manager = provider.get_session_manager()
    return session_manager.get_session(session_uuid)


def configure_session_manager_for_testing(**kwargs) -> None:
    """
    Configure the session manager for testing.
    
    Args:
        **kwargs: Configuration parameters for testing
    """
    provider = get_session_manager_provider()
    provider.configure_factory(**kwargs)
    logger.info("SessionManager configured for testing")


def reset_session_manager() -> None:
    """Reset the global session manager (useful for testing)."""
    provider = get_session_manager_provider()
    provider.reset_session_manager()
    logger.info("SessionManager reset")
