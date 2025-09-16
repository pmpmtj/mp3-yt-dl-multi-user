"""
YouTube Downloader Application

A comprehensive multiuser YouTube downloader with session management,
progress tracking, and both CLI and API interfaces.
"""

__version__ = "1.0.0"
__author__ = "YouTube Downloader Team"
__description__ = "Multiuser YouTube Downloader with Session Management"

# Main modules
from . import common
from . import yt_audio_dl

# Conditionally import API module to avoid FastAPI dependency in Django
try:
    from . import api
    __all__ = [
        'common',
        'yt_audio_dl', 
        'api'
    ]
except ImportError:
    # API module not available (e.g., in Django context)
    __all__ = [
        'common',
        'yt_audio_dl'
    ]
