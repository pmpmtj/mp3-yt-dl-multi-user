"""
UUID generation utilities for multiuser support.

This module provides UUID generation functions for session and video management
without dependencies on path utilities or configuration.
"""

import logging
import uuid
from typing import Optional

# Initialize logger for this module
logger = logging.getLogger("uuid_utils")


def generate_session_uuid() -> str:
    """
    Generate a unique session identifier for multiuser support.
    
    Returns:
        String representation of a UUID4
    """
    session_id = str(uuid.uuid4())
    logger.debug(f"Generated session UUID: {session_id}")
    return session_id


def generate_video_uuid() -> str:
    """
    Generate a unique video identifier for multiuser support.
    
    Returns:
        String representation of a UUID4
    """
    video_id = str(uuid.uuid4())
    logger.debug(f"Generated video UUID: {video_id}")
    return video_id


def generate_uuid(prefix: Optional[str] = None) -> str:
    """
    Generate a UUID with optional prefix.
    
    Args:
        prefix: Optional prefix to add to the UUID
        
    Returns:
        String representation of a UUID4 with optional prefix
    """
    uuid_str = str(uuid.uuid4())
    if prefix:
        return f"{prefix}-{uuid_str}"
    return uuid_str