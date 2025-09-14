"""
Main FastAPI application module.

This module sets up the FastAPI application with all routes,
middleware, and configuration for the YouTube downloader API.
"""

import logging
from fastapi import FastAPI, Request, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.middleware.trustedhost import TrustedHostMiddleware
from fastapi.responses import JSONResponse
from contextlib import asynccontextmanager
import time
import uuid

from .sessions import router as sessions_router
from .jobs import router as jobs_router
from .health import router as health_router
from ..common import setup_logging, get_session_manager

# Initialize logging
setup_logging()
logger = logging.getLogger("api.main")

# Global variables for app state
app_start_time = None
session_manager = None


@asynccontextmanager
async def lifespan(app: FastAPI):
    """
    Application lifespan manager.
    
    Handles startup and shutdown events for the FastAPI application.
    """
    global app_start_time, session_manager
    
    # Startup
    logger.info("Starting YouTube Downloader API...")
    app_start_time = time.time()
    session_manager = get_session_manager()
    logger.info("API startup complete")
    
    yield
    
    # Shutdown
    logger.info("Shutting down YouTube Downloader API...")
    # Cleanup any resources here if needed
    logger.info("API shutdown complete")


# Create FastAPI application
app = FastAPI(
    title="YouTube Downloader API",
    description="Multiuser YouTube downloader with session management",
    version="1.0.0",
    lifespan=lifespan,
    docs_url="/docs",
    redoc_url="/redoc"
)

# Add middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Configure this properly for production
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.add_middleware(
    TrustedHostMiddleware,
    allowed_hosts=["*"]  # Configure this properly for production
)


# Request ID middleware
@app.middleware("http")
async def add_request_id(request: Request, call_next):
    """Add request ID to all requests for tracing."""
    request_id = str(uuid.uuid4())
    request.state.request_id = request_id
    
    response = await call_next(request)
    response.headers["X-Request-ID"] = request_id
    return response


# Global exception handler
@app.exception_handler(Exception)
async def global_exception_handler(request: Request, exc: Exception):
    """Global exception handler for unhandled errors."""
    request_id = getattr(request.state, 'request_id', 'unknown')
    
    logger.error(f"Unhandled exception in request {request_id}: {exc}", exc_info=True)
    
    return JSONResponse(
        status_code=500,
        content={
            "error": "Internal server error",
            "detail": "An unexpected error occurred",
            "timestamp": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
            "request_id": request_id
        }
    )


# Include routers
app.include_router(sessions_router, prefix="/sessions", tags=["sessions"])
app.include_router(jobs_router, prefix="/jobs", tags=["jobs"])
app.include_router(health_router, prefix="/api", tags=["health"])


# Root endpoint
@app.get("/")
async def root():
    """Root endpoint with basic API information."""
    return {
        "message": "YouTube Downloader API",
        "version": "1.0.0",
        "status": "running",
        "docs_url": "/docs",
        "health_url": "/api/health"
    }


# Get app start time for uptime calculation
def get_app_start_time() -> float:
    """Get the application start time."""
    global app_start_time
    return app_start_time or time.time()


# Get session manager instance
def get_session_manager_instance():
    """Get the global session manager instance."""
    global session_manager
    return session_manager or get_session_manager()


# Export for use in other modules
__all__ = ['app', 'get_app_start_time', 'get_session_manager_instance']
