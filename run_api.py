#!/usr/bin/env python3
"""
Startup script for the YouTube Downloader API.

This script starts the FastAPI application using uvicorn.
"""

import sys
import uvicorn
from pathlib import Path

# Add src directory to Python path
SCRIPT_DIR = Path(__file__).resolve().parent
SRC_DIR = SCRIPT_DIR / "src"
sys.path.insert(0, str(SRC_DIR))

def main():
    """Start the API server."""
    print("Starting YouTube Downloader API...")
    print("API Documentation will be available at: http://localhost:8000/docs")
    print("Health check endpoint: http://localhost:8000/api/health")
    print("Press Ctrl+C to stop the server")
    print("-" * 50)
    
    # Start the server
    uvicorn.run(
        "src.api.main:app",
        host="0.0.0.0",
        port=8000,
        reload=True,  # Enable auto-reload for development
        log_level="info",
        access_log=True
    )

if __name__ == "__main__":
    main()
