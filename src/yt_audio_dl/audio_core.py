"""
Core audio download functionality using yt-dlp.

This module provides the main audio download engine with progress tracking,
error handling, and integration with the session management system.
"""

import logging
import time
from src.common.download_monitor import get_global_monitor
from src.common.url_utils import sanitize_youtube_url, YouTubeURLError
from typing import Optional, Dict, Any, Callable, Union
from pathlib import Path
from dataclasses import dataclass
from enum import Enum

import yt_dlp

# Initialize logger
logger = logging.getLogger("audio_core")

# Constants for audio download configuration
DEFAULT_QUALITY = "best"
DEFAULT_FORMAT = "mp3"
DEFAULT_BITRATE = "192"  # kbps


class DownloadStatus(Enum):
    """Download status enumeration."""
    PENDING = "pending"
    DOWNLOADING = "downloading"
    PROCESSING = "processing"
    COMPLETED = "completed"
    FAILED = "failed"
    CANCELLED = "cancelled"


@dataclass
class AudioDownloadResult:
    """Result of an audio download operation."""
    success: bool
    status: DownloadStatus
    output_path: Optional[Path] = None
    file_size_bytes: Optional[int] = None
    duration_seconds: Optional[float] = None
    title: Optional[str] = None
    artist: Optional[str] = None
    format: Optional[str] = None
    error_message: Optional[str] = None
    download_time_seconds: Optional[float] = None
    metadata: Optional[Dict[str, Any]] = None


class AudioDownloadError(Exception):
    """Custom exception for audio download errors."""
    pass


class ProgressHook:
    """Progress hook for yt-dlp to track download progress."""
    
    def __init__(self, progress_callback: Optional[Callable] = None):
        self.progress_callback = progress_callback
        self.start_time = None
        self.total_bytes = None
        self.downloaded_bytes = 0
        self.eta = None
        self.speed = None
    
    def __call__(self, d):
        """Progress hook callback."""
        if d['status'] == 'downloading':
            if self.start_time is None:
                self.start_time = time.time()
            
            # Extract progress information
            if 'total_bytes' in d and d['total_bytes']:
                self.total_bytes = d['total_bytes']
                self.downloaded_bytes = d.get('downloaded_bytes', 0)
                progress_percent = (self.downloaded_bytes / self.total_bytes) * 100
            elif 'total_bytes_estimate' in d and d['total_bytes_estimate']:
                self.total_bytes = d['total_bytes_estimate']
                self.downloaded_bytes = d.get('downloaded_bytes', 0)
                progress_percent = (self.downloaded_bytes / self.total_bytes) * 100
            else:
                # Still update downloaded_bytes even without total bytes
                self.downloaded_bytes = d.get('downloaded_bytes', 0)
                progress_percent = None
            
            # Extract speed and ETA
            self.speed = d.get('speed')
            self.eta = d.get('eta')
            
            # Call progress callback if provided
            if self.progress_callback:
                self.progress_callback({
                    'status': 'downloading',
                    'progress_percent': progress_percent,
                    'downloaded_bytes': self.downloaded_bytes,
                    'total_bytes': self.total_bytes,
                    'speed': self.speed,
                    'eta': self.eta
                })
            
            if progress_percent is not None:
                logger.debug(f"Download progress: {progress_percent:.1f}% "
                            f"({self.downloaded_bytes}/{self.total_bytes} bytes)")
            else:
                logger.debug(f"Download progress: {self.downloaded_bytes} bytes downloaded")
        
        elif d['status'] == 'finished':
            logger.info(f"Download finished: {d['filename']}")
            if self.progress_callback:
                self.progress_callback({
                    'status': 'finished',
                    'filename': d['filename']
                })


class AudioDownloader:
    """
    Audio downloader using yt-dlp.
    
    Provides audio download functionality with progress tracking,
    error handling, and session integration.
    
    All downloads are performed with best quality and MP3 format.
    """
    
    def __init__(self, 
                 output_dir: Union[str, Path],
                 progress_callback: Optional[Callable] = None):
        """
        Initialize the audio downloader.
        
        Args:
            output_dir: Directory to save downloaded files
            progress_callback: Optional callback for progress updates
        """
        self.output_dir = Path(output_dir)
        self.quality = DEFAULT_QUALITY
        self.format = DEFAULT_FORMAT
        self.progress_callback = progress_callback
        
        # Initialize download monitor
        self.monitor = get_global_monitor()

        # Ensure output directory exists
        self.output_dir.mkdir(parents=True, exist_ok=True)
        
        logger.info(f"AudioDownloader initialized: output_dir={self.output_dir}, "
                   f"quality={DEFAULT_QUALITY}, format={DEFAULT_FORMAT}")
    
    def _get_ydl_opts(self, output_template: str) -> Dict[str, Any]:
        """
        Get yt-dlp options for audio download.
        
        Args:
            output_template: Template for output filename
            
        Returns:
            Dictionary of yt-dlp options configured for best quality MP3 download
        """
        return {
            'format': self.quality,
            'outtmpl': str(self.output_dir / output_template),
            'postprocessors': [{
                'key': 'FFmpegExtractAudio',
                'preferredcodec': self.format,
                'preferredquality': DEFAULT_BITRATE,
            }],
            'extractaudio': True,
            'audioformat': self.format,
            'noplaylist': True,  # Download single video, not playlist
            'ignoreerrors': False,
            'no_warnings': False,
            'extract_flat': False,
            'writethumbnail': False,
            'writeinfojson': False,
            'writesubtitles': False,
            'writeautomaticsub': False,
        }
    
    def get_video_info(self, url: str) -> Dict[str, Any]:
        """
        Get video information without downloading.
        
        Args:
            url: YouTube video URL
            
        Returns:
            Dictionary with video information
            
        Raises:
            AudioDownloadError: If unable to extract video info
        """
        try:
            logger.debug(f"Getting video info for: {url}")
            
            ydl_opts = {
                'quiet': True,
                'no_warnings': True,
                'extract_flat': False,
                'noplaylist': True,
            }
            
            with yt_dlp.YoutubeDL(ydl_opts) as ydl:
                info = ydl.extract_info(url, download=False)
                
                if not info:
                    raise AudioDownloadError("Unable to extract video information")
                
                # Extract relevant information
                video_info = {
                    'id': info.get('id'),
                    'title': info.get('title'),
                    'uploader': info.get('uploader'),
                    'duration': info.get('duration'),
                    'upload_date': info.get('upload_date'),
                    'view_count': info.get('view_count'),
                    'description': info.get('description'),
                    'thumbnail': info.get('thumbnail'),
                    'webpage_url': info.get('webpage_url'),
                    'formats': info.get('formats', [])
                }
                
                logger.debug(f"Video info extracted: {video_info['title']}")
                return video_info
                
        except Exception as e:
            logger.error(f"Error getting video info for {url}: {e}")
            raise AudioDownloadError(f"Failed to get video info: {e}")
    
    def download_audio(self, 
                      url: str, 
                      output_filename: Optional[str] = None,
                      metadata: Optional[Dict[str, Any]] = None) -> AudioDownloadResult:
        """
        Download audio from a YouTube URL.
        
        Args:
            url: YouTube video URL
            output_filename: Optional custom output filename
            metadata: Optional metadata to embed in the file
            
        Returns:
            AudioDownloadResult with download information
            
        Raises:
            AudioDownloadError: If download fails
        """
        start_time = time.time()
        download_id = f"download_{int(start_time)}_{hash(url) % 10000}"
        
        try:
            logger.info(f"Starting audio download: {url}")
            
            # Sanitize URL first
            try:
                url_info = sanitize_youtube_url(url, preserve_metadata=True)
                clean_url = url_info.clean_url
                logger.debug(f"URL sanitized: {url} -> {clean_url}")
                if url_info.timestamp:
                    logger.debug(f"Timestamp detected: {url_info.timestamp}s (note: timestamp will be ignored for full download)")
            except YouTubeURLError as e:
                logger.error(f"Invalid YouTube URL: {e}")
                return AudioDownloadResult(
                    success=False,
                    status=DownloadStatus.FAILED,
                    error_message=f"Invalid YouTube URL: {e}",
                    download_time_seconds=0
                )
            
            # Start monitoring
            if not self.monitor.start_download_monitoring(download_id, clean_url):
                logger.error("Failed to start download monitoring - network issues detected")
                return AudioDownloadResult(
                    success=False,
                    status=DownloadStatus.FAILED,
                    error_message="Network connectivity issues detected. Please check your internet connection.",
                    download_time_seconds=0
                )
            
            # Get video info first
            try:
                video_info = self.get_video_info(clean_url)
                title = video_info.get('title', 'Unknown')
                duration = video_info.get('duration', 0)
            except AudioDownloadError as e:
                # Handle network errors gracefully
                if "Failed to resolve" in str(e) or "getaddrinfo failed" in str(e):
                    logger.error(f"Network error detected: {e}")
                    self.monitor.complete_download(download_id, False, f"Network error: {e}")
                    return AudioDownloadResult(
                        success=False,
                        status=DownloadStatus.FAILED,
                        error_message="Network error: Unable to connect to YouTube. Please check your internet connection.",
                        download_time_seconds=time.time() - start_time
                    )
                else:
                    # Other errors, proceed with download anyway
                    title = "Unknown"
                    duration = 0
                    video_info = {}
            
            # Generate output filename if not provided
            if not output_filename:
                # Sanitize title for filename
                safe_title = "".join(c for c in title if c.isalnum() or c in (' ', '-', '_')).strip()
                safe_title = safe_title[:50]  # Limit length
                output_filename = f"{safe_title}.%(ext)s"
            
            # Set up yt-dlp options
            ydl_opts = self._get_ydl_opts(output_filename)
            
            # Add metadata if provided
            if metadata:
                ydl_opts['postprocessors'].append({
                    'key': 'FFmpegMetadata',
                    'add_metadata': True,
                    'add_chapters': False,
                })
            
            # Download the audio
            with yt_dlp.YoutubeDL(ydl_opts) as ydl:
                logger.debug(f"Downloading with yt-dlp options: {ydl_opts}")
                
                # Add progress hook for monitoring
                def progress_hook(d):
                    if d['status'] == 'downloading':
                        self.monitor.update_download_progress(download_id, d)
                    elif d['status'] == 'finished':
                        logger.info(f"Download finished: {d['filename']}")
                
                ydl.add_progress_hook(progress_hook)
                
                # Extract info and download using clean URL
                info = ydl.extract_info(clean_url, download=True)
                
                if not info:
                    self.monitor.complete_download(download_id, False, "Download failed - no info extracted")
                    raise AudioDownloadError("Download failed - no info extracted")
                
                # Find the downloaded file
                downloaded_files = []
                for file_path in self.output_dir.glob("*"):
                    if file_path.is_file() and file_path.suffix.lstrip('.') == self.format:
                        downloaded_files.append(file_path)
                
                if not downloaded_files:
                    self.monitor.complete_download(download_id, False, "Download completed but no output file found")
                    raise AudioDownloadError("Download completed but no output file found")
                
                # Use the most recently modified file (should be our download)
                output_file = max(downloaded_files, key=lambda f: f.stat().st_mtime)
                
                # Get file size
                file_size = output_file.stat().st_size
                download_time = time.time() - start_time
                
                # Complete monitoring
                self.monitor.complete_download(download_id, True)
                
                logger.info(f"Audio download completed: {output_file} ({file_size} bytes, "
                           f"{download_time:.1f}s)")
                
                return AudioDownloadResult(
                    success=True,
                    status=DownloadStatus.COMPLETED,
                    output_path=output_file,
                    file_size_bytes=file_size,
                    duration_seconds=duration,
                    title=title,
                    artist=video_info.get('uploader'),
                    format=self.format,
                    download_time_seconds=download_time,
                    metadata=video_info
                )
                
        except yt_dlp.DownloadError as e:
            error_str = str(e).lower()
            logger.error(f"yt-dlp download error for {url}: {e}")
            
            # Check for network-related errors and provide user-friendly messages
            if any(network_error in error_str for network_error in [
                'failed to resolve', 'getaddrinfo failed', 'network is unreachable',
                'connection timed out', 'connection refused', 'connection reset',
                'unable to download webpage', 'http error 5', 'bytes read', 'more expected',
                'connection broken', 'incomplete read', 'partial download', 'download interrupted'
            ]):
                # Try to handle network error with retry logic
                retry_should_happen = self.monitor.handle_network_error(download_id, e)
                logger.info(f"Monitor retry decision for {download_id}: {retry_should_happen}")
                
                if retry_should_happen:
                    logger.info(f"Retrying download {download_id} after network error")
                    # Return a special status to indicate retry should be attempted
                    return AudioDownloadResult(
                        success=False,
                        status=DownloadStatus.PENDING,
                        error_message=f"Network connectivity issue detected (attempt {self.monitor.active_downloads.get(download_id, type('', (), {'retry_count': 0})).retry_count}). Retrying...",
                        download_time_seconds=time.time() - start_time
                    )
                else:
                    # Max retries exceeded
                    user_friendly_message = (
                        "Network connectivity issues prevented the download. "
                        "This could be due to:\n"
                        "• Temporary internet connection problems\n"
                        "• DNS resolution failures\n"
                        "• YouTube server access issues\n"
                        "Please check your internet connection and try again later."
                    )
                    return AudioDownloadResult(
                        success=False,
                        status=DownloadStatus.FAILED,
                        error_message=user_friendly_message,
                        download_time_seconds=time.time() - start_time
                    )
            else:
                # Non-network related yt-dlp error
                self.monitor.complete_download(download_id, False, f"Download error: {e}")
                return AudioDownloadResult(
                    success=False,
                    status=DownloadStatus.FAILED,
                    error_message=f"Download error: {e}",
                    download_time_seconds=time.time() - start_time
                )
        except Exception as e:
            error_str = str(e).lower()
            logger.error(f"Unexpected error during audio download for {url}: {e}")
            
            # Check for network-related exceptions
            if any(network_error in error_str for network_error in [
                'gaierror', 'socket.gaierror', 'connectionerror', 'timeout',
                'failed to resolve', 'network', 'connection'
            ]):
                user_friendly_message = (
                    "A network error occurred during download. This is usually temporary. "
                    "Please check your internet connection and try again."
                )
                self.monitor.complete_download(download_id, False, user_friendly_message)
                return AudioDownloadResult(
                    success=False,
                    status=DownloadStatus.FAILED,
                    error_message=user_friendly_message,
                    download_time_seconds=time.time() - start_time
                )
            else:
                self.monitor.complete_download(download_id, False, f"Unexpected error: {e}")
                return AudioDownloadResult(
                    success=False,
                    status=DownloadStatus.FAILED,
                    error_message=f"Unexpected error: {e}",
                    download_time_seconds=time.time() - start_time
                )
        
    def download_audio_with_session(self, 
                                   url: str,
                                   session_uuid: str,
                                   job_uuid: str,
                                   progress_callback: Optional[Callable] = None) -> AudioDownloadResult:
        """
        Download audio with session integration.
        
        Args:
            url: YouTube video URL
            session_uuid: Session identifier
            job_uuid: Job identifier
            progress_callback: Optional progress callback
            
        Returns:
            AudioDownloadResult with download information
        """
        try:
            logger.info(f"Starting session-based audio download: session={session_uuid}, job={job_uuid}")
            
            # Create session-specific output directory
            session_output_dir = self.output_dir / session_uuid / job_uuid
            session_output_dir.mkdir(parents=True, exist_ok=True)
            
            # Create a temporary downloader with session-specific output
            session_downloader = AudioDownloader(
                output_dir=session_output_dir,
                progress_callback=progress_callback
            )
            
            # Download the audio
            result = session_downloader.download_audio(url)
            
            if result.success:
                logger.info(f"Session download completed: {result.output_path}")
            else:
                logger.error(f"Session download failed: {result.error_message}")
            
            return result
            
        except Exception as e:
            logger.error(f"Error in session-based download: {e}")
            return AudioDownloadResult(
                success=False,
                status=DownloadStatus.FAILED,
                error_message=f"Session download error: {e}"
            )
    
    def cancel_download(self):
        """Cancel ongoing download (placeholder for future implementation)."""
        # This would require more complex implementation with threading
        logger.warning("Download cancellation not yet implemented")
    
    
    def validate_url(self, url: str) -> bool:
        """
        Validate if URL is a supported YouTube URL.
        
        Args:
            url: URL to validate
            
        Returns:
            True if URL is valid and supported
        """
        try:
            # Use URL sanitizer for comprehensive validation
            url_info = sanitize_youtube_url(url, preserve_metadata=False)
            
            # Try to extract info to validate with yt-dlp
            self.get_video_info(url_info.clean_url)
            return True
            
        except (YouTubeURLError, AudioDownloadError):
            return False
        except Exception:
            return False
