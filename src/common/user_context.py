"""
User context management for multiuser support.

This module provides session-based user management without requiring a database.
Each user session gets isolated download directories and unique identifiers.
"""

import logging
from typing import Optional, Dict, Any, Union, Callable
from pathlib import Path

# Import UUID functions from uuid_utils
from .uuid_utils import generate_session_uuid, generate_job_uuid

# Initialize logger for this module
logger = logging.getLogger("user_context")


class UserContext:
    """
    Manages user session context for multiuser support.
    
    Each UserContext represents a user session with:
    - Unique session UUID
    - Isolated download directories
    - Session-specific configuration
    - Video-specific download tracking
    """
    
    def __init__(self, session_uuid: Optional[str] = None, 
                 path_generator: Optional[Callable] = None,
                 base_download_dir: Optional[Union[str, Path]] = None):
        """
        Initialize a user context.
        
        Args:
            session_uuid: Existing session UUID, or None to create new session
            path_generator: Function to generate download paths (dependency injection)
            base_download_dir: Base directory for downloads (uses config default if None)
        """
        self.session_uuid = session_uuid or generate_session_uuid()
        self._job_sessions: Dict[str, str] = {}  # job_url -> job_uuid mapping
        self._path_generator = path_generator or self._default_path_generator
        self._base_download_dir = base_download_dir
        logger.info(f"Initialized user context with session: {self.session_uuid}")
    
    def _default_path_generator(self, session_uuid: str, job_uuid: str, 
                               media_type: str, base_dir: Optional[Union[str, Path]] = None) -> Path:
        """
        Default path generator using simple directory structure.
        
        Args:
            session_uuid: Session identifier
            job_uuid: Job identifier
            media_type: Media type (audio, video, transcripts)
            base_dir: Base directory for downloads
            
        Returns:
            Path to the download directory
        """
        if base_dir is None:
            base_dir = self._base_download_dir or "./downloads"
        
        return Path(base_dir) / session_uuid / job_uuid / media_type
    
    def get_session_id(self) -> str:
        """
        Get the session UUID for this user context.
        
        Returns:
            Session UUID string
        """
        return self.session_uuid
    
    def get_url_uuid(self, job_url: str) -> str:
        """
        Get or create a job UUID for a given job URL.
        
        This ensures the same job URL always gets the same job UUID
        within a session, enabling proper file organization.
        
        Args:
            job_url: Job URL (e.g., YouTube video URL)
            
        Returns:
            Job UUID string
        """
        if job_url not in self._job_sessions:
            self._job_sessions[job_url] = generate_job_uuid()
            logger.debug(f"Created job UUID for URL: {job_url} -> {self._job_sessions[job_url]}")
        
        return self._job_sessions[job_url]
    
    def get_audio_download_path(self, job_url: str, base_dir: Optional[Union[str, Path]] = None) -> Path:
        """
        Get the audio download path for a job in this user's session.
        
        Args:
            job_url: Job URL (e.g., YouTube video URL)
            base_dir: Base downloads directory (uses instance default if None)
            
        Returns:
            Path to the audio download directory
        """
        job_uuid = self.get_url_uuid(job_url)
        return self._path_generator(self.session_uuid, job_uuid, "audio", base_dir)
    
    def get_video_download_path(self, job_url: str, base_dir: Optional[Union[str, Path]] = None) -> Path:
        """
        Get the video download path for a job in this user's session.
        
        Args:
            job_url: Job URL (e.g., YouTube video URL)
            base_dir: Base downloads directory (uses instance default if None)
            
        Returns:
            Path to the video download directory
        """
        job_uuid = self.get_url_uuid(job_url)
        return self._path_generator(self.session_uuid, job_uuid, "video", base_dir)
    
    def get_transcript_download_path(self, job_url: str, base_dir: Optional[Union[str, Path]] = None) -> Path:
        """
        Get the transcript download path for a job in this user's session.
        
        Args:
            job_url: Job URL (e.g., YouTube video URL)
            base_dir: Base downloads directory (uses instance default if None)
            
        Returns:
            Path to the transcript download directory
        """
        job_uuid = self.get_url_uuid(job_url)
        return self._path_generator(self.session_uuid, job_uuid, "transcripts", base_dir)
    
    def get_session_info(self) -> Dict[str, Any]:
        """
        Get information about this user session.
        
        Returns:
            Dictionary with session information
        """
        return {
            'session_uuid': self.session_uuid,
            'total_jobs': len(self._job_sessions),
            'job_urls': list(self._job_sessions.keys()),
            'job_uuids': list(self._job_sessions.values())
        }
    
    def get_job_info(self, job_url: str) -> Dict[str, str]:
        """
        Get information about a specific job in this session.
        
        Args:
            job_url: Job URL (e.g., YouTube video URL)
            
        Returns:
            Dictionary with job information
        """
        job_uuid = self.get_url_uuid(job_url)
        return {
            'job_url': job_url,
            'job_uuid': job_uuid,
            'session_uuid': self.session_uuid
        }


def create_user_context(session_uuid: Optional[str] = None, 
                       path_generator: Optional[Callable] = None,
                       base_download_dir: Optional[Union[str, Path]] = None) -> UserContext:
    """
    Create a new user context for multiuser support.
    
    Args:
        session_uuid: Existing session UUID, or None to create new session
        path_generator: Function to generate download paths (dependency injection)
        base_download_dir: Base directory for downloads
        
    Returns:
        New UserContext instance
    """
    return UserContext(session_uuid, path_generator, base_download_dir)


def get_default_user_context() -> UserContext:
    """
    Get a default user context (creates new session if none exists).
    
    This is useful for backward compatibility with existing single-user code.
    
    Returns:
        UserContext instance
    """
    return UserContext()