"""
Audio download module for YouTube downloader.

This module provides audio download functionality using yt-dlp,
integrated with the multiuser session management system.
"""

from .audio_core import AudioDownloader, AudioDownloadResult, AudioDownloadError
from .audio_core_cli import AudioDownloadCLI

__all__ = [
    'AudioDownloader',
    'AudioDownloadResult', 
    'AudioDownloadError',
    'AudioDownloadCLI'
]
