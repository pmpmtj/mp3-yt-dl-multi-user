"""
Session management API endpoints.

This module provides RESTful endpoints for creating, managing,
and monitoring user sessions in the multiuser YouTube downloader.
"""

import logging
from typing import List, Optional
from fastapi import APIRouter, HTTPException, Depends, Request
from fastapi.responses import JSONResponse
import time

from .models import SessionResponse, SessionStatsResponse, ErrorResponse
from ..common import get_session_manager, create_session, get_session

# Initialize logger
logger = logging.getLogger("api.sessions")

# Create router
router = APIRouter()


def get_session_manager_dependency():
    """Dependency to get the session manager instance."""
    return get_session_manager()


@router.post("/", response_model=SessionResponse, status_code=201)
async def create_new_session(
    request: Request,
    session_manager=Depends(get_session_manager_dependency)
):
    """
    Create a new anonymous user session.
    
    Returns a new session with unique UUID and isolated download directories.
    """
    try:
        logger.info("Creating new session")
        
        # Create new session
        session_uuid = session_manager.create_session()
        
        # Get session info
        session_info = session_manager.get_session_info(session_uuid)
        
        if not session_info:
            raise HTTPException(status_code=500, detail="Failed to create session")
        
        logger.info(f"Created session: {session_uuid}")
        
        return SessionResponse(**session_info)
        
    except Exception as e:
        logger.error(f"Error creating session: {e}")
        raise HTTPException(status_code=500, detail="Failed to create session")


@router.get("/{session_uuid}", response_model=SessionResponse)
async def get_session_info_endpoint(
    session_uuid: str,
    session_manager=Depends(get_session_manager_dependency)
):
    """
    Get information about a specific session.
    
    Args:
        session_uuid: The session UUID to retrieve information for
    """
    try:
        logger.debug(f"Getting session info for: {session_uuid}")
        
        session_info = session_manager.get_session_info(session_uuid)
        
        if not session_info:
            raise HTTPException(status_code=404, detail="Session not found")
        
        return SessionResponse(**session_info)
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error getting session info for {session_uuid}: {e}")
        raise HTTPException(status_code=500, detail="Internal server error")


@router.get("/", response_model=List[SessionResponse])
async def list_active_sessions(
    session_manager=Depends(get_session_manager_dependency)
):
    """
    Get list of all active sessions.
    
    Returns information about all currently active user sessions.
    """
    try:
        logger.debug("Listing active sessions")
        
        active_session_uuids = session_manager.get_active_sessions()
        sessions = []
        
        for session_uuid in active_session_uuids:
            session_info = session_manager.get_session_info(session_uuid)
            if session_info:
                sessions.append(SessionResponse(**session_info))
        
        logger.debug(f"Found {len(sessions)} active sessions")
        return sessions
        
    except Exception as e:
        logger.error(f"Error listing sessions: {e}")
        raise HTTPException(status_code=500, detail="Internal server error")


@router.delete("/{session_uuid}")
async def deactivate_session(
    session_uuid: str,
    session_manager=Depends(get_session_manager_dependency)
):
    """
    Deactivate a session.
    
    Args:
        session_uuid: The session UUID to deactivate
    """
    try:
        logger.info(f"Deactivating session: {session_uuid}")
        
        # Check if session exists
        session_info = session_manager.get_session_info(session_uuid)
        if not session_info:
            raise HTTPException(status_code=404, detail="Session not found")
        
        # Deactivate session
        session_manager.deactivate_session(session_uuid)
        
        logger.info(f"Deactivated session: {session_uuid}")
        
        return {"message": "Session deactivated successfully", "session_uuid": session_uuid}
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error deactivating session {session_uuid}: {e}")
        raise HTTPException(status_code=500, detail="Internal server error")


@router.get("/stats/overview", response_model=SessionStatsResponse)
async def get_session_statistics(
    session_manager=Depends(get_session_manager_dependency)
):
    """
    Get overall session statistics.
    
    Returns aggregated statistics about all sessions and jobs.
    """
    try:
        logger.debug("Getting session statistics")
        
        stats = session_manager.get_session_stats()
        
        return SessionStatsResponse(**stats)
        
    except Exception as e:
        logger.error(f"Error getting session statistics: {e}")
        raise HTTPException(status_code=500, detail="Internal server error")


@router.post("/cleanup/expired")
async def cleanup_expired_sessions(
    session_manager=Depends(get_session_manager_dependency)
):
    """
    Manually trigger cleanup of expired sessions.
    
    This endpoint allows manual cleanup of sessions that have exceeded
    their timeout period.
    """
    try:
        logger.info("Manual cleanup of expired sessions triggered")
        
        cleaned_count = session_manager.cleanup_expired_sessions()
        
        logger.info(f"Cleaned up {cleaned_count} expired sessions")
        
        return {
            "message": f"Cleaned up {cleaned_count} expired sessions",
            "cleaned_count": cleaned_count,
            "timestamp": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime())
        }
        
    except Exception as e:
        logger.error(f"Error during session cleanup: {e}")
        raise HTTPException(status_code=500, detail="Cleanup failed")


@router.get("/{session_uuid}/context")
async def get_session_context(
    session_uuid: str,
    session_manager=Depends(get_session_manager_dependency)
):
    """
    Get the user context for a session.
    
    Args:
        session_uuid: The session UUID to get context for
        
    Returns session context information including job mappings.
    """
    try:
        logger.debug(f"Getting session context for: {session_uuid}")
        
        user_context = session_manager.get_session(session_uuid)
        
        if not user_context:
            raise HTTPException(status_code=404, detail="Session not found or inactive")
        
        # Get session info from user context
        session_info = user_context.get_session_info()
        
        return {
            "session_uuid": session_uuid,
            "context_info": session_info,
            "download_base_dir": str(user_context._base_download_dir or "./downloads")
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error getting session context for {session_uuid}: {e}")
        raise HTTPException(status_code=500, detail="Internal server error")
