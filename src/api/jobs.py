"""
Job management API endpoints.

This module provides RESTful endpoints for creating, monitoring,
and managing download jobs in the multiuser YouTube downloader.
"""

import logging
import asyncio
from typing import List, Optional
from fastapi import APIRouter, HTTPException, Depends, Request, BackgroundTasks
from fastapi.responses import JSONResponse
import time
from pathlib import Path

from .models import (
    JobRequest, JobResponse, JobStatusRequest, DownloadPathResponse,
    ErrorResponse
)
from ..common import get_session_manager, get_session

# Initialize logger
logger = logging.getLogger("api.jobs")

# Create router
router = APIRouter()

# In-memory job storage (will be replaced with database later)
job_storage = {}
job_counter = 0


def get_session_manager_dependency():
    """Dependency to get the session manager instance."""
    return get_session_manager()


def generate_job_id() -> str:
    """Generate a unique job ID."""
    global job_counter
    job_counter += 1
    return f"job-{job_counter}-{int(time.time())}"


@router.post("/", response_model=JobResponse)
async def create_download_job(
    job_request: JobRequest,
    background_tasks: BackgroundTasks,
    request: Request,
    session_manager=Depends(get_session_manager_dependency)
):
    """
    Create a new download job.
    
    Args:
        job_request: Job details including URL and media type
        background_tasks: FastAPI background tasks for async processing
        session_manager: Session manager instance
    """
    try:
        # Extract session ID from request headers or query params
        session_uuid = request.headers.get("X-Session-ID")
        if not session_uuid:
            raise HTTPException(status_code=400, detail="Session ID required in X-Session-ID header")
        
        logger.info(f"Creating download job for session {session_uuid}: {job_request.url}")
        
        # Validate session exists and is active
        user_context = session_manager.get_session(session_uuid)
        if not user_context:
            raise HTTPException(status_code=404, detail="Session not found or inactive")
        
        # Check if session can start a new job
        if not session_manager.start_job(session_uuid):
            raise HTTPException(status_code=429, detail="Maximum jobs per session exceeded")
        
        # Generate job ID and get job UUID from user context
        job_id = generate_job_id()
        job_uuid = user_context.get_url_uuid(str(job_request.url))
        
        # Create job record
        job_data = {
            "job_uuid": job_uuid,
            "job_id": job_id,
            "session_uuid": session_uuid,
            "job_url": str(job_request.url),
            "media_type": job_request.media_type,
            "quality": job_request.quality,
            "output_format": job_request.output_format,
            "status": "pending",
            "created_at": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
            "started_at": None,
            "completed_at": None,
            "progress_percent": None,
            "error_message": None,
            "output_path": None,
            "file_size_bytes": None
        }
        
        # Store job data
        job_storage[job_id] = job_data
        
        # Get download paths
        download_paths = get_download_paths(user_context, job_request)
        
        logger.info(f"Created job {job_id} for session {session_uuid}")
        
        # Schedule background processing (placeholder for now)
        background_tasks.add_task(process_download_job, job_id, job_request)
        
        return JobResponse(**job_data)
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error creating download job: {e}")
        raise HTTPException(status_code=500, detail="Failed to create download job")


@router.get("/{job_id}", response_model=JobResponse)
async def get_job_status(
    job_id: str,
    request: Request,
    session_manager=Depends(get_session_manager_dependency)
):
    """
    Get the status of a specific job.
    
    Args:
        job_id: The job ID to get status for
    """
    try:
        # Extract session ID from request headers
        session_uuid = request.headers.get("X-Session-ID")
        if not session_uuid:
            raise HTTPException(status_code=400, detail="Session ID required in X-Session-ID header")
        
        logger.debug(f"Getting job status for job {job_id}")
        
        # Check if job exists
        if job_id not in job_storage:
            raise HTTPException(status_code=404, detail="Job not found")
        
        job_data = job_storage[job_id]
        
        # Verify job belongs to the session
        if job_data["session_uuid"] != session_uuid:
            raise HTTPException(status_code=403, detail="Job does not belong to this session")
        
        return JobResponse(**job_data)
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error getting job status for {job_id}: {e}")
        raise HTTPException(status_code=500, detail="Internal server error")


@router.get("/", response_model=List[JobResponse])
async def list_session_jobs(
    request: Request,
    session_manager=Depends(get_session_manager_dependency)
):
    """
    Get all jobs for the current session.
    
    Returns a list of all jobs associated with the session.
    """
    try:
        # Extract session ID from request headers
        session_uuid = request.headers.get("X-Session-ID")
        if not session_uuid:
            raise HTTPException(status_code=400, detail="Session ID required in X-Session-ID header")
        
        logger.debug(f"Listing jobs for session {session_uuid}")
        
        # Filter jobs by session
        session_jobs = [
            JobResponse(**job_data) for job_data in job_storage.values()
            if job_data["session_uuid"] == session_uuid
        ]
        
        logger.debug(f"Found {len(session_jobs)} jobs for session {session_uuid}")
        return session_jobs
        
    except Exception as e:
        logger.error(f"Error listing jobs for session: {e}")
        raise HTTPException(status_code=500, detail="Internal server error")


@router.get("/{job_id}/paths", response_model=DownloadPathResponse)
async def get_job_download_paths(
    job_id: str,
    request: Request,
    session_manager=Depends(get_session_manager_dependency)
):
    """
    Get download paths for a specific job.
    
    Args:
        job_id: The job ID to get download paths for
    """
    try:
        # Extract session ID from request headers
        session_uuid = request.headers.get("X-Session-ID")
        if not session_uuid:
            raise HTTPException(status_code=400, detail="Session ID required in X-Session-ID header")
        
        logger.debug(f"Getting download paths for job {job_id}")
        
        # Check if job exists
        if job_id not in job_storage:
            raise HTTPException(status_code=404, detail="Job not found")
        
        job_data = job_storage[job_id]
        
        # Verify job belongs to the session
        if job_data["session_uuid"] != session_uuid:
            raise HTTPException(status_code=403, detail="Job does not belong to this session")
        
        # Get user context
        user_context = session_manager.get_session(session_uuid)
        if not user_context:
            raise HTTPException(status_code=404, detail="Session not found")
        
        # Get download paths
        download_paths = get_download_paths(user_context, job_data)
        
        return DownloadPathResponse(
            job_uuid=job_data["job_uuid"],
            session_uuid=session_uuid,
            job_url=job_data["job_url"],
            media_type=job_data["media_type"],
            download_path=str(download_paths["base"]),
            audio_path=str(download_paths["audio"]),
            video_path=str(download_paths["video"]),
            transcript_path=str(download_paths["transcript"])
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error getting download paths for job {job_id}: {e}")
        raise HTTPException(status_code=500, detail="Internal server error")


@router.put("/{job_id}/status")
async def update_job_status(
    job_id: str,
    status_update: JobStatusRequest,
    request: Request,
    session_manager=Depends(get_session_manager_dependency)
):
    """
    Update the status of a specific job.
    
    Args:
        job_id: The job ID to update
        status_update: New status information
    """
    try:
        # Extract session ID from request headers
        session_uuid = request.headers.get("X-Session-ID")
        if not session_uuid:
            raise HTTPException(status_code=400, detail="Session ID required in X-Session-ID header")
        
        logger.debug(f"Updating job status for job {job_id}")
        
        # Check if job exists
        if job_id not in job_storage:
            raise HTTPException(status_code=404, detail="Job not found")
        
        job_data = job_storage[job_id]
        
        # Verify job belongs to the session
        if job_data["session_uuid"] != session_uuid:
            raise HTTPException(status_code=403, detail="Job does not belong to this session")
        
        # Update job data
        job_data["status"] = status_update.status
        if status_update.progress_percent is not None:
            job_data["progress_percent"] = status_update.progress_percent
        if status_update.error_message is not None:
            job_data["error_message"] = status_update.error_message
        if status_update.output_path is not None:
            job_data["output_path"] = status_update.output_path
        if status_update.file_size_bytes is not None:
            job_data["file_size_bytes"] = status_update.file_size_bytes
        
        # Update timestamps
        if status_update.status == "processing" and job_data["started_at"] is None:
            job_data["started_at"] = time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime())
        elif status_update.status in ["completed", "failed", "cancelled"]:
            job_data["completed_at"] = time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime())
        
        # Update session manager
        if status_update.status == "completed":
            session_manager.complete_job(session_uuid, status_update.file_size_bytes or 0)
        elif status_update.status == "failed":
            session_manager.fail_job(session_uuid)
        
        logger.info(f"Updated job {job_id} status to {status_update.status}")
        
        return {"message": "Job status updated successfully", "job_id": job_id}
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error updating job status for {job_id}: {e}")
        raise HTTPException(status_code=500, detail="Internal server error")


def get_download_paths(user_context, job_data) -> dict:
    """
    Get download paths for a job.
    
    Args:
        user_context: User context instance
        job_data: Job data dictionary
        
    Returns:
        Dictionary with download paths
    """
    job_url = job_data["job_url"]
    
    return {
        "base": user_context.get_audio_download_path(job_url).parent,
        "audio": user_context.get_audio_download_path(job_url),
        "video": user_context.get_video_download_path(job_url),
        "transcript": user_context.get_transcript_download_path(job_url)
    }


async def process_download_job(job_id: str, job_request: JobRequest):
    """
    Background task to process a download job.
    
    This is a placeholder for the actual download processing logic.
    In a real implementation, this would use yt-dlp to download the content.
    
    Args:
        job_id: The job ID to process
        job_request: The job request data
    """
    try:
        logger.info(f"Starting background processing for job {job_id}")
        
        # Update job status to processing
        if job_id in job_storage:
            job_storage[job_id]["status"] = "processing"
            job_storage[job_id]["started_at"] = time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime())
            job_storage[job_id]["progress_percent"] = 0
        
        # Simulate download processing
        for progress in range(0, 101, 10):
            await asyncio.sleep(0.5)  # Simulate processing time
            if job_id in job_storage:
                job_storage[job_id]["progress_percent"] = progress
        
        # Simulate completion
        if job_id in job_storage:
            job_storage[job_id]["status"] = "completed"
            job_storage[job_id]["completed_at"] = time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime())
            job_storage[job_id]["progress_percent"] = 100
            job_storage[job_id]["file_size_bytes"] = 1024 * 1024  # 1MB placeholder
        
        logger.info(f"Completed background processing for job {job_id}")
        
    except Exception as e:
        logger.error(f"Error in background processing for job {job_id}: {e}")
        if job_id in job_storage:
            job_storage[job_id]["status"] = "failed"
            job_storage[job_id]["error_message"] = str(e)
            job_storage[job_id]["completed_at"] = time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime())
