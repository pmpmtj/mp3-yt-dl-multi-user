"""
Health monitoring and system status API endpoints.

This module provides endpoints for monitoring system health,
performance metrics, and overall application status.
"""

import logging
import psutil
import platform
from typing import Dict, Any
from fastapi import APIRouter, HTTPException, Depends, Request
from fastapi.responses import JSONResponse
import time

from .models import HealthResponse, SessionStatsResponse
from ..common import get_session_manager

# Initialize logger
logger = logging.getLogger("api.health")

# Create router
router = APIRouter()


def get_session_manager_dependency():
    """Dependency to get the session manager instance."""
    return get_session_manager()


@router.get("/health", response_model=HealthResponse)
async def health_check(
    request: Request,
    session_manager=Depends(get_session_manager_dependency)
):
    """
    Comprehensive health check endpoint.
    
    Returns detailed system health information including:
    - Application status
    - Session statistics
    - System resource usage
    - Uptime information
    """
    try:
        # Get application start time (assuming it's available from main.py)
        from .main import get_app_start_time
        app_start_time = get_app_start_time()
        uptime_seconds = time.time() - app_start_time
        
        # Get session statistics
        session_stats = session_manager.get_session_stats()
        
        # Get system information
        system_info = get_system_info()
        
        # Determine overall health status
        health_status = determine_health_status(session_stats, system_info)
        
        health_data = {
            "status": health_status,
            "timestamp": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
            "version": "1.0.0",
            "uptime_seconds": uptime_seconds,
            "active_sessions": session_stats["active_sessions"],
            "total_sessions": session_stats["total_sessions"],
            "active_jobs": session_stats["active_jobs"],
            "total_jobs": session_stats["total_jobs"],
            "system_info": system_info
        }
        
        return HealthResponse(**health_data)
        
    except Exception as e:
        logger.error(f"Error in health check: {e}")
        raise HTTPException(status_code=500, detail="Health check failed")


@router.get("/health/simple")
async def simple_health_check():
    """
    Simple health check endpoint for load balancers.
    
    Returns a minimal response indicating if the service is running.
    """
    return {
        "status": "healthy",
        "timestamp": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
        "service": "youtube-downloader-api"
    }


@router.get("/metrics", response_model=SessionStatsResponse)
async def get_metrics(
    session_manager=Depends(get_session_manager_dependency)
):
    """
    Get detailed system metrics.
    
    Returns comprehensive metrics about sessions, jobs, and system performance.
    """
    try:
        logger.debug("Getting system metrics")
        
        # Get session statistics
        stats = session_manager.get_session_stats()
        
        # Add additional metrics
        metrics = {
            **stats,
            "timestamp": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
            "system_metrics": get_system_metrics()
        }
        
        return SessionStatsResponse(**stats)
        
    except Exception as e:
        logger.error(f"Error getting metrics: {e}")
        raise HTTPException(status_code=500, detail="Failed to get metrics")


@router.get("/status")
async def get_detailed_status(
    session_manager=Depends(get_session_manager_dependency)
):
    """
    Get detailed system status information.
    
    Returns comprehensive status including system resources, sessions, and configuration.
    """
    try:
        logger.debug("Getting detailed system status")
        
        # Get session statistics
        session_stats = session_manager.get_session_stats()
        
        # Get system information
        system_info = get_system_info()
        system_metrics = get_system_metrics()
        
        # Get configuration information
        config_info = get_configuration_info()
        
        status = {
            "timestamp": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
            "application": {
                "version": "1.0.0",
                "status": "running",
                "uptime_seconds": time.time() - (getattr(get_app_start_time, 'start_time', time.time())),
            },
            "sessions": session_stats,
            "system": {
                "info": system_info,
                "metrics": system_metrics
            },
            "configuration": config_info
        }
        
        return status
        
    except Exception as e:
        logger.error(f"Error getting detailed status: {e}")
        raise HTTPException(status_code=500, detail="Failed to get status")


def get_system_info() -> Dict[str, Any]:
    """Get basic system information."""
    try:
        return {
            "platform": platform.platform(),
            "python_version": platform.python_version(),
            "cpu_count": psutil.cpu_count(),
            "memory_total_gb": round(psutil.virtual_memory().total / (1024**3), 2),
            "disk_total_gb": round(psutil.disk_usage('/').total / (1024**3), 2),
            "hostname": platform.node()
        }
    except Exception as e:
        logger.warning(f"Could not get system info: {e}")
        return {"error": "System info unavailable"}


def get_system_metrics() -> Dict[str, Any]:
    """Get current system performance metrics."""
    try:
        return {
            "cpu_percent": psutil.cpu_percent(interval=1),
            "memory_percent": psutil.virtual_memory().percent,
            "memory_available_gb": round(psutil.virtual_memory().available / (1024**3), 2),
            "disk_percent": psutil.disk_usage('/').percent,
            "disk_free_gb": round(psutil.disk_usage('/').free / (1024**3), 2),
            "load_average": psutil.getloadavg() if hasattr(psutil, 'getloadavg') else None
        }
    except Exception as e:
        logger.warning(f"Could not get system metrics: {e}")
        return {"error": "System metrics unavailable"}


def get_configuration_info() -> Dict[str, Any]:
    """Get application configuration information."""
    try:
        from ..common.app_config import get_config
        config = get_config()
        
        return {
            "download_path": config.get("download", {}).get("download_path", "default"),
            "max_concurrent_sessions": 100,  # From session manager
            "max_jobs_per_session": 10,      # From session manager
            "session_timeout_hours": 24,     # From session manager
            "features": config.get("features", {})
        }
    except Exception as e:
        logger.warning(f"Could not get configuration info: {e}")
        return {"error": "Configuration info unavailable"}


def determine_health_status(session_stats: Dict[str, Any], system_info: Dict[str, Any]) -> str:
    """
    Determine overall system health status.
    
    Args:
        session_stats: Session statistics
        system_info: System information
        
    Returns:
        Health status: 'healthy', 'degraded', or 'unhealthy'
    """
    try:
        # Check session limits
        if session_stats["active_sessions"] >= session_stats["max_concurrent_sessions"] * 0.9:
            return "degraded"
        
        # Check system resources
        if "system_metrics" in system_info:
            metrics = system_info["system_metrics"]
            if metrics.get("cpu_percent", 0) > 90:
                return "degraded"
            if metrics.get("memory_percent", 0) > 90:
                return "degraded"
            if metrics.get("disk_percent", 0) > 90:
                return "degraded"
        
        return "healthy"
        
    except Exception as e:
        logger.warning(f"Could not determine health status: {e}")
        return "unhealthy"


def get_app_start_time() -> float:
    """Get application start time."""
    try:
        from .main import get_app_start_time as _get_app_start_time
        return _get_app_start_time()
    except:
        return time.time()
