"""
Pydantic models for API requests and responses.

This module defines the data structures used for API communication,
including request validation and response serialization.
"""

from typing import Optional, Dict, Any, List
from datetime import datetime
from pydantic import BaseModel, HttpUrl, Field


class SessionResponse(BaseModel):
    """Response model for session information."""
    session_uuid: str
    created_at: str
    last_activity: str
    is_active: bool
    total_jobs: int
    active_jobs: int
    completed_jobs: int
    failed_jobs: int
    storage_used_bytes: int
    age_hours: float


class JobRequest(BaseModel):
    """Request model for creating a new job."""
    url: HttpUrl = Field(..., description="URL to download (YouTube video URL)")
    media_type: str = Field(default="video", regex="^(video|audio|transcript)$", 
                           description="Type of media to download")
    quality: Optional[str] = Field(default=None, description="Video/audio quality preference")
    output_format: Optional[str] = Field(default=None, description="Output format (mp4, mp3, etc.)")


class JobResponse(BaseModel):
    """Response model for job information."""
    job_uuid: str
    session_uuid: str
    job_url: str
    media_type: str
    status: str = Field(..., regex="^(pending|processing|completed|failed|cancelled)$")
    created_at: str
    started_at: Optional[str] = None
    completed_at: Optional[str] = None
    progress_percent: Optional[float] = Field(default=None, ge=0, le=100)
    error_message: Optional[str] = None
    output_path: Optional[str] = None
    file_size_bytes: Optional[int] = None


class JobStatusRequest(BaseModel):
    """Request model for updating job status."""
    status: str = Field(..., regex="^(processing|completed|failed|cancelled)$")
    progress_percent: Optional[float] = Field(default=None, ge=0, le=100)
    error_message: Optional[str] = None
    output_path: Optional[str] = None
    file_size_bytes: Optional[int] = None


class HealthResponse(BaseModel):
    """Response model for system health status."""
    status: str = Field(..., regex="^(healthy|degraded|unhealthy)$")
    timestamp: str
    version: str
    uptime_seconds: float
    active_sessions: int
    total_sessions: int
    active_jobs: int
    total_jobs: int
    system_info: Dict[str, Any]


class SessionStatsResponse(BaseModel):
    """Response model for session statistics."""
    total_sessions: int
    active_sessions: int
    total_jobs: int
    active_jobs: int
    total_storage_bytes: int
    max_concurrent_sessions: int
    max_jobs_per_session: int


class ErrorResponse(BaseModel):
    """Response model for API errors."""
    error: str
    detail: Optional[str] = None
    timestamp: str
    request_id: Optional[str] = None


class DownloadPathResponse(BaseModel):
    """Response model for download path information."""
    job_uuid: str
    session_uuid: str
    job_url: str
    media_type: str
    download_path: str
    audio_path: Optional[str] = None
    video_path: Optional[str] = None
    transcript_path: Optional[str] = None
