"""
Session manager for handling multiple concurrent users.

This module provides centralized session management with thread safety,
session persistence, cleanup, and resource management for multiuser support.
"""

import logging
import threading
import time
from typing import Dict, Optional, List, Any, Union, Callable
from pathlib import Path
from datetime import datetime, timedelta
from dataclasses import dataclass, field

from .uuid_utils import generate_session_uuid, generate_uuid
from .user_context import UserContext, create_user_context

# Initialize logger for this module
logger = logging.getLogger("session_manager")


@dataclass
class SessionInfo:
    """
    Information about a user session.
    
    Tracks session metadata, creation time, last activity, and resource usage.
    """
    session_uuid: str
    user_context: UserContext
    created_at: datetime
    last_activity: datetime
    total_jobs: int = 0
    active_jobs: int = 0
    completed_jobs: int = 0
    failed_jobs: int = 0
    storage_used_bytes: int = 0
    is_active: bool = True
    
    def update_activity(self) -> None:
        """Update the last activity timestamp."""
        self.last_activity = datetime.now()
    
    def add_job(self) -> None:
        """Increment job counters when a new job is started."""
        self.total_jobs += 1
        self.active_jobs += 1
        self.update_activity()
    
    def complete_job(self, storage_bytes: int = 0) -> None:
        """Mark a job as completed."""
        if self.active_jobs > 0:
            self.active_jobs -= 1
        self.completed_jobs += 1
        self.storage_used_bytes += storage_bytes
        self.update_activity()
    
    def fail_job(self) -> None:
        """Mark a job as failed."""
        if self.active_jobs > 0:
            self.active_jobs -= 1
        self.failed_jobs += 1
        self.update_activity()
    
    def deactivate(self) -> None:
        """Mark session as inactive."""
        self.is_active = False
        self.update_activity()


class SessionManager:
    """
    Manages multiple concurrent user sessions with thread safety.
    
    Provides session creation, retrieval, cleanup, and resource management
    for anonymous multiuser support without database dependency.
    """
    
    def __init__(self, 
                 session_timeout_hours: int = 24,
                 max_concurrent_sessions: int = 100,
                 max_jobs_per_session: int = 10,
                 cleanup_interval_minutes: int = 60):
        """
        Initialize the session manager.
        
        Args:
            session_timeout_hours: Hours before inactive session expires
            max_concurrent_sessions: Maximum number of concurrent sessions
            max_jobs_per_session: Maximum jobs per session
            cleanup_interval_minutes: Minutes between cleanup runs
        """
        self._sessions: Dict[str, SessionInfo] = {}
        self._lock = threading.RLock()  # Reentrant lock for nested access
        self._session_timeout = timedelta(hours=session_timeout_hours)
        self._max_concurrent_sessions = max_concurrent_sessions
        self._max_jobs_per_session = max_jobs_per_session
        self._cleanup_interval = timedelta(minutes=cleanup_interval_minutes)
        self._last_cleanup = datetime.now()
        
        logger.info(f"SessionManager initialized: timeout={session_timeout_hours}h, "
                   f"max_sessions={max_concurrent_sessions}, max_jobs={max_jobs_per_session}")
    
    def create_session(self, 
                      session_uuid: Optional[str] = None,
                      path_generator: Optional[Callable] = None,
                      base_download_dir: Optional[Union[str, Path]] = None) -> str:
        """
        Create a new user session.
        
        Args:
            session_uuid: Optional existing session UUID
            path_generator: Optional path generation function
            base_download_dir: Optional base download directory
            
        Returns:
            Session UUID string
            
        Raises:
            RuntimeError: If maximum concurrent sessions exceeded
        """
        with self._lock:
            # Check session limits
            if len(self._sessions) >= self._max_concurrent_sessions:
                # Try to clean up expired sessions first
                self._cleanup_expired_sessions()
                if len(self._sessions) >= self._max_concurrent_sessions:
                    raise RuntimeError(f"Maximum concurrent sessions ({self._max_concurrent_sessions}) exceeded")
            
            # Generate session UUID if not provided
            if not session_uuid:
                session_uuid = generate_session_uuid()
            elif session_uuid in self._sessions:
                # Reactivate existing session
                self._sessions[session_uuid].is_active = True
                self._sessions[session_uuid].update_activity()
                logger.info(f"Reactivated existing session: {session_uuid}")
                return session_uuid
            
            # Create user context and session info
            user_context = create_user_context(
                session_uuid=session_uuid,
                path_generator=path_generator,
                base_download_dir=base_download_dir
            )
            
            now = datetime.now()
            session_info = SessionInfo(
                session_uuid=session_uuid,
                user_context=user_context,
                created_at=now,
                last_activity=now
            )
            
            self._sessions[session_uuid] = session_info
            logger.info(f"Created new session: {session_uuid}")
            
            return session_uuid
    
    def get_session(self, session_uuid: str) -> Optional[UserContext]:
        """
        Get a user context by session UUID.
        
        Args:
            session_uuid: Session identifier
            
        Returns:
            UserContext if session exists and is active, None otherwise
        """
        with self._lock:
            if session_uuid in self._sessions:
                session_info = self._sessions[session_uuid]
                if session_info.is_active:
                    session_info.update_activity()
                    return session_info.user_context
                else:
                    logger.debug(f"Session {session_uuid} is inactive")
            else:
                logger.debug(f"Session {session_uuid} not found")
            return None
    
    def get_session_info(self, session_uuid: str) -> Optional[Dict[str, Any]]:
        """
        Get detailed session information.
        
        Args:
            session_uuid: Session identifier
            
        Returns:
            Dictionary with session info or None if not found
        """
        with self._lock:
            if session_uuid not in self._sessions:
                return None
            
            session_info = self._sessions[session_uuid]
            return {
                'session_uuid': session_info.session_uuid,
                'created_at': session_info.created_at.isoformat(),
                'last_activity': session_info.last_activity.isoformat(),
                'is_active': session_info.is_active,
                'total_jobs': session_info.total_jobs,
                'active_jobs': session_info.active_jobs,
                'completed_jobs': session_info.completed_jobs,
                'failed_jobs': session_info.failed_jobs,
                'storage_used_bytes': session_info.storage_used_bytes,
                'age_hours': (datetime.now() - session_info.created_at).total_seconds() / 3600
            }
    
    def start_job(self, session_uuid: str) -> bool:
        """
        Start a new job for a session.
        
        Args:
            session_uuid: Session identifier
            
        Returns:
            True if job started successfully, False if limits exceeded
        """
        with self._lock:
            if session_uuid not in self._sessions:
                logger.warning(f"Cannot start job: session {session_uuid} not found")
                return False
            
            session_info = self._sessions[session_uuid]
            if not session_info.is_active:
                logger.warning(f"Cannot start job: session {session_uuid} is inactive")
                return False
            
            if session_info.active_jobs >= self._max_jobs_per_session:
                logger.warning(f"Cannot start job: session {session_uuid} has max jobs ({self._max_jobs_per_session})")
                return False
            
            session_info.add_job()
            logger.debug(f"Started job for session {session_uuid} (active: {session_info.active_jobs})")
            return True
    
    def complete_job(self, session_uuid: str, storage_bytes: int = 0) -> None:
        """
        Mark a job as completed for a session.
        
        Args:
            session_uuid: Session identifier
            storage_bytes: Storage used by the completed job
        """
        with self._lock:
            if session_uuid in self._sessions:
                self._sessions[session_uuid].complete_job(storage_bytes)
                logger.debug(f"Completed job for session {session_uuid} (storage: {storage_bytes} bytes)")
    
    def fail_job(self, session_uuid: str) -> None:
        """
        Mark a job as failed for a session.
        
        Args:
            session_uuid: Session identifier
        """
        with self._lock:
            if session_uuid in self._sessions:
                self._sessions[session_uuid].fail_job()
                logger.debug(f"Failed job for session {session_uuid}")
    
    def deactivate_session(self, session_uuid: str) -> None:
        """
        Deactivate a session.
        
        Args:
            session_uuid: Session identifier
        """
        with self._lock:
            if session_uuid in self._sessions:
                self._sessions[session_uuid].deactivate()
                logger.info(f"Deactivated session: {session_uuid}")
    
    def get_active_sessions(self) -> List[str]:
        """
        Get list of active session UUIDs.
        
        Returns:
            List of active session UUIDs
        """
        with self._lock:
            return [uuid for uuid, info in self._sessions.items() if info.is_active]
    
    def get_session_stats(self) -> Dict[str, Any]:
        """
        Get overall session statistics.
        
        Returns:
            Dictionary with session statistics
        """
        with self._lock:
            active_sessions = sum(1 for info in self._sessions.values() if info.is_active)
            total_jobs = sum(info.total_jobs for info in self._sessions.values())
            active_jobs = sum(info.active_jobs for info in self._sessions.values())
            total_storage = sum(info.storage_used_bytes for info in self._sessions.values())
            
            return {
                'total_sessions': len(self._sessions),
                'active_sessions': active_sessions,
                'total_jobs': total_jobs,
                'active_jobs': active_jobs,
                'total_storage_bytes': total_storage,
                'max_concurrent_sessions': self._max_concurrent_sessions,
                'max_jobs_per_session': self._max_jobs_per_session
            }
    
    def cleanup_expired_sessions(self) -> int:
        """
        Remove expired sessions.
        
        Returns:
            Number of sessions cleaned up
        """
        return self._cleanup_expired_sessions()
    
    def _cleanup_expired_sessions(self) -> int:
        """
        Internal method to clean up expired sessions.
        
        Returns:
            Number of sessions cleaned up
        """
        with self._lock:
            now = datetime.now()
            expired_sessions = []
            
            for session_uuid, session_info in self._sessions.items():
                # Check if session is expired (inactive for too long)
                if (now - session_info.last_activity) > self._session_timeout:
                    expired_sessions.append(session_uuid)
            
            # Remove expired sessions
            for session_uuid in expired_sessions:
                del self._sessions[session_uuid]
                logger.info(f"Cleaned up expired session: {session_uuid}")
            
            self._last_cleanup = now
            
            if expired_sessions:
                logger.info(f"Cleaned up {len(expired_sessions)} expired sessions")
            
            return len(expired_sessions)
    
    def periodic_cleanup(self) -> None:
        """
        Perform periodic cleanup if enough time has passed.
        
        This should be called periodically (e.g., from a background thread).
        """
        now = datetime.now()
        if (now - self._last_cleanup) >= self._cleanup_interval:
            self._cleanup_expired_sessions()


# Global session manager instance
_session_manager: Optional[SessionManager] = None
_manager_lock = threading.Lock()


def get_session_manager() -> SessionManager:
    """
    Get the global session manager instance.
    
    Returns:
        SessionManager instance (creates one if none exists)
    """
    global _session_manager
    
    if _session_manager is None:
        with _manager_lock:
            if _session_manager is None:
                _session_manager = SessionManager()
                logger.info("Created global SessionManager instance")
    
    return _session_manager


def create_session(session_uuid: Optional[str] = None,
                  path_generator: Optional[Callable] = None,
                  base_download_dir: Optional[Union[str, Path]] = None) -> str:
    """
    Create a new session using the global session manager.
    
    Args:
        session_uuid: Optional existing session UUID
        path_generator: Optional path generation function
        base_download_dir: Optional base download directory
        
    Returns:
        Session UUID string
    """
    return get_session_manager().create_session(session_uuid, path_generator, base_download_dir)


def get_session(session_uuid: str) -> Optional[UserContext]:
    """
    Get a session using the global session manager.
    
    Args:
        session_uuid: Session identifier
        
    Returns:
        UserContext if session exists and is active, None otherwise
    """
    return get_session_manager().get_session(session_uuid)
