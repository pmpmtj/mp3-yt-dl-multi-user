"""
Download Monitoring Module

This module provides comprehensive monitoring for YouTube audio downloads,
including network connectivity checks, progress tracking, error handling,
and graceful failure management.
"""

import logging
import time
import socket
import urllib.parse
from typing import Dict, Any, Optional, Callable, List
from dataclasses import dataclass, field
from enum import Enum
from pathlib import Path
import json
from datetime import datetime

# Initialize logger
logger = logging.getLogger("download_monitor")


class NetworkStatus(Enum):
    """Network connectivity status."""
    ONLINE = "online"
    OFFLINE = "offline"
    UNKNOWN = "unknown"


class DownloadEvent(Enum):
    """Download event types."""
    STARTED = "started"
    PROGRESS = "progress"
    COMPLETED = "completed"
    FAILED = "failed"
    CANCELLED = "cancelled"
    NETWORK_ERROR = "network_error"
    RETRY_ATTEMPT = "retry_attempt"


@dataclass
class DownloadMetrics:
    """Download performance metrics."""
    start_time: float
    end_time: Optional[float] = None
    total_bytes: Optional[int] = None
    downloaded_bytes: int = 0
    current_speed: Optional[float] = None
    average_speed: Optional[float] = None
    eta_seconds: Optional[float] = None
    progress_percent: Optional[float] = None
    retry_count: int = 0
    network_errors: int = 0
    success: bool = False
    
    @property
    def duration_seconds(self) -> Optional[float]:
        """Calculate total duration."""
        if self.end_time and self.start_time:
            return self.end_time - self.start_time
        return None
    
    @property
    def is_complete(self) -> bool:
        """Check if download is complete."""
        return self.end_time is not None and self.success


@dataclass
class NetworkCheckResult:
    """Result of network connectivity check."""
    is_online: bool
    dns_resolution: bool
    youtube_accessible: bool
    error_message: Optional[str] = None
    check_time: float = field(default_factory=time.time)


class DownloadMonitor:
    """
    Comprehensive download monitoring system.
    
    Provides real-time monitoring, network connectivity checks,
    error handling, and graceful failure management for YouTube downloads.
    """
    
    def __init__(self, 
                 log_file: Optional[Path] = None,
                 enable_network_checks: bool = True,
                 retry_attempts: int = 3,
                 retry_delay: float = 5.0):
        """
        Initialize the download monitor.
        
        Args:
            log_file: Optional custom log file path
            enable_network_checks: Whether to perform network connectivity checks
            retry_attempts: Number of retry attempts for failed downloads
            retry_delay: Delay between retry attempts in seconds
        """
        self.log_file = log_file or Path("logs/download_monitor.log")
        self.enable_network_checks = enable_network_checks
        self.retry_attempts = retry_attempts
        self.retry_delay = retry_delay
        
        # Ensure log directory exists
        self.log_file.parent.mkdir(parents=True, exist_ok=True)
        
        # Active downloads tracking
        self.active_downloads: Dict[str, DownloadMetrics] = {}
        self.completed_downloads: List[DownloadMetrics] = []
        
        # Network status
        self.network_status = NetworkStatus.UNKNOWN
        self.last_network_check = 0.0
        self.network_check_interval = 30.0  # Check every 30 seconds
        
        # Event callbacks
        self.event_callbacks: List[Callable] = []
        
        logger.info(f"DownloadMonitor initialized: network_checks={enable_network_checks}, "
                   f"retry_attempts={retry_attempts}")
    
    def add_event_callback(self, callback: Callable):
        """Add an event callback function."""
        self.event_callbacks.append(callback)
        logger.debug(f"Added event callback: {callback.__name__}")
    
    def _emit_event(self, event_type: DownloadEvent, data: Dict[str, Any]):
        """Emit an event to all registered callbacks."""
        event_data = {
            'event_type': event_type,
            'timestamp': time.time(),
            'data': data
        }
        
        for callback in self.event_callbacks:
            try:
                callback(event_data)
            except Exception as e:
                logger.error(f"Error in event callback {callback.__name__}: {e}")
    
    def check_network_connectivity(self) -> NetworkCheckResult:
        """
        Check network connectivity and YouTube accessibility.
        
        Returns:
            NetworkCheckResult with connectivity status
        """
        logger.debug("Checking network connectivity...")
        
        try:
            # Check DNS resolution
            socket.gethostbyname('www.youtube.com')
            dns_resolution = True
            logger.debug("DNS resolution successful")
        except socket.gaierror as e:
            dns_resolution = False
            logger.warning(f"DNS resolution failed: {e}")
        
        # Check if we can reach YouTube
        youtube_accessible = False
        error_message = None
        
        if dns_resolution:
            try:
                import urllib.request
                with urllib.request.urlopen('https://www.youtube.com', timeout=10) as response:
                    if response.status == 200:
                        youtube_accessible = True
                        logger.debug("YouTube is accessible")
                    else:
                        error_message = f"HTTP {response.status}"
            except Exception as e:
                error_message = str(e)
                logger.warning(f"YouTube accessibility check failed: {e}")
        else:
            error_message = "DNS resolution failed"
        
        is_online = dns_resolution and youtube_accessible
        
        result = NetworkCheckResult(
            is_online=is_online,
            dns_resolution=dns_resolution,
            youtube_accessible=youtube_accessible,
            error_message=error_message
        )
        
        # Update network status
        self.network_status = NetworkStatus.ONLINE if is_online else NetworkStatus.OFFLINE
        self.last_network_check = time.time()
        
        logger.info(f"Network check result: online={is_online}, "
                   f"dns={dns_resolution}, youtube={youtube_accessible}")
        
        return result
    
    def should_check_network(self) -> bool:
        """Check if we should perform a network check."""
        if not self.enable_network_checks:
            return False
        
        return (time.time() - self.last_network_check) > self.network_check_interval
    
    def start_download_monitoring(self, download_id: str, url: str) -> bool:
        """
        Start monitoring a download.
        
        Args:
            download_id: Unique identifier for the download
            url: URL being downloaded
            
        Returns:
            True if monitoring started successfully, False if network issues
        """
        logger.info(f"Starting download monitoring: {download_id}")
        
        # Check network connectivity if needed
        if self.should_check_network():
            network_result = self.check_network_connectivity()
            if not network_result.is_online:
                logger.error(f"Network check failed: {network_result.error_message}")
                self._emit_event(DownloadEvent.NETWORK_ERROR, {
                    'download_id': download_id,
                    'url': url,
                    'error': network_result.error_message
                })
                return False
        
        # Initialize download metrics
        metrics = DownloadMetrics(start_time=time.time())
        self.active_downloads[download_id] = metrics
        
        self._emit_event(DownloadEvent.STARTED, {
            'download_id': download_id,
            'url': url,
            'timestamp': metrics.start_time
        })
        
        logger.info(f"Download monitoring started: {download_id}")
        return True
    
    def update_download_progress(self, 
                               download_id: str, 
                               progress_data: Dict[str, Any]):
        """
        Update download progress.
        
        Args:
            download_id: Download identifier
            progress_data: Progress information from yt-dlp
        """
        if download_id not in self.active_downloads:
            logger.warning(f"Received progress update for unknown download: {download_id}")
            return
        
        metrics = self.active_downloads[download_id]
        
        # Update metrics
        metrics.downloaded_bytes = progress_data.get('downloaded_bytes', 0)
        metrics.total_bytes = progress_data.get('total_bytes')
        metrics.current_speed = progress_data.get('speed')
        metrics.eta_seconds = progress_data.get('eta')
        
        if metrics.total_bytes and metrics.total_bytes > 0:
            metrics.progress_percent = (metrics.downloaded_bytes / metrics.total_bytes) * 100
        
        # Calculate average speed
        if metrics.duration_seconds and metrics.duration_seconds > 0:
            metrics.average_speed = metrics.downloaded_bytes / metrics.duration_seconds
        
        self._emit_event(DownloadEvent.PROGRESS, {
            'download_id': download_id,
            'progress_percent': metrics.progress_percent,
            'downloaded_bytes': metrics.downloaded_bytes,
            'total_bytes': metrics.total_bytes,
            'current_speed': metrics.current_speed,
            'eta_seconds': metrics.eta_seconds
        })
        
        logger.debug(f"Progress update for {download_id}: {metrics.progress_percent:.1f}%")
    
    def complete_download(self, download_id: str, success: bool, error_message: Optional[str] = None):
        """
        Mark download as completed.
        
        Args:
            download_id: Download identifier
            success: Whether download was successful
            error_message: Error message if failed
        """
        if download_id not in self.active_downloads:
            logger.warning(f"Received completion for unknown download: {download_id}")
            return
        
        metrics = self.active_downloads[download_id]
        metrics.end_time = time.time()
        metrics.success = success
        
        # Move to completed downloads
        self.completed_downloads.append(metrics)
        del self.active_downloads[download_id]
        
        event_type = DownloadEvent.COMPLETED if success else DownloadEvent.FAILED
        
        self._emit_event(event_type, {
            'download_id': download_id,
            'success': success,
            'duration_seconds': metrics.duration_seconds,
            'total_bytes': metrics.total_bytes,
            'error_message': error_message
        })
        
        status_msg = "completed successfully" if success else f"failed: {error_message}"
        logger.info(f"Download {download_id} {status_msg} in {metrics.duration_seconds:.1f}s")
    
    def handle_network_error(self, download_id: str, error: Exception) -> bool:
        """
        Handle network-related errors with retry logic.
        
        Args:
            download_id: Download identifier
            error: The network error that occurred
            
        Returns:
            True if retry should be attempted, False if max retries exceeded
        """
        if download_id not in self.active_downloads:
            return False
        
        metrics = self.active_downloads[download_id]
        metrics.network_errors += 1
        metrics.retry_count += 1
        
        # Classify the error type for better handling
        error_str = str(error).lower()
        error_type = "unknown"
        
        if "failed to resolve" in error_str or "getaddrinfo failed" in error_str:
            error_type = "dns_resolution"
        elif "bytes read" in error_str and "more expected" in error_str:
            error_type = "partial_download"
        elif "connection" in error_str and ("timeout" in error_str or "refused" in error_str):
            error_type = "connection_issue"
        elif "connection broken" in error_str or "incomplete read" in error_str or "download interrupted" in error_str:
            error_type = "download_interruption"
        elif "network is unreachable" in error_str:
            error_type = "network_unreachable"
        elif "http error 5" in error_str:
            error_type = "server_error"
        
        logger.warning(f"Network error for {download_id} (type: {error_type}): {error} (attempt {metrics.retry_count})")
        
        self._emit_event(DownloadEvent.NETWORK_ERROR, {
            'download_id': download_id,
            'error': str(error),
            'error_type': error_type,
            'retry_count': metrics.retry_count,
            'max_retries': self.retry_attempts
        })
        
        if metrics.retry_count < self.retry_attempts:
            # Adjust retry delay based on error type
            delay = self.retry_delay
            if error_type == "dns_resolution":
                delay = min(self.retry_delay * 2, 30)  # Longer delay for DNS issues
            elif error_type == "partial_download" or error_type == "download_interruption":
                delay = min(self.retry_delay * 0.5, 3)  # Shorter delay for download interruptions
            elif error_type == "server_error":
                delay = min(self.retry_delay * 1.5, 20)  # Moderate delay for server errors
            
            logger.info(f"Will retry download {download_id} in {delay}s (error type: {error_type})")
            self._emit_event(DownloadEvent.RETRY_ATTEMPT, {
                'download_id': download_id,
                'retry_count': metrics.retry_count,
                'delay_seconds': delay,
                'error_type': error_type
            })
            
            # Don't sleep here - let the calling code handle retry timing
            return True
        else:
            logger.error(f"Max retries exceeded for {download_id}")
            user_friendly_error = self._get_user_friendly_error_message(error_type, error)
            self.complete_download(download_id, False, user_friendly_error)
            return False
    
    def _get_user_friendly_error_message(self, error_type: str, original_error: Exception) -> str:
        """
        Get a user-friendly error message based on the error type.
        
        Args:
            error_type: Classified error type
            original_error: Original exception
            
        Returns:
            User-friendly error message
        """
        base_message = f"Network error after multiple retries"
        
        if error_type == "dns_resolution":
            return (
                f"{base_message}. DNS resolution failed - this usually indicates:\n"
                "• Internet connection issues\n"
                "• DNS server problems\n"
                "• Firewall or proxy blocking access\n"
                "Please check your internet connection and try again."
            )
        elif error_type == "connection_issue":
            return (
                f"{base_message}. Connection problems detected:\n"
                "• Server may be temporarily unavailable\n"
                "• Network congestion or timeout issues\n"
                "• Firewall blocking connections\n"
                "Please try again in a few minutes."
            )
        elif error_type == "network_unreachable":
            return (
                f"{base_message}. Network unreachable:\n"
                "• Internet connection is down\n"
                "• Network configuration issues\n"
                "Please check your internet connection."
            )
        elif error_type == "partial_download":
            return (
                f"{base_message}. Partial download detected:\n"
                "• Download was interrupted during transfer\n"
                "• Connection may have been unstable\n"
                "• File transfer was incomplete\n"
                "Please try again - the download will resume."
            )
        elif error_type == "download_interruption":
            return (
                f"{base_message}. Download interruption detected:\n"
                "• Connection was broken during download\n"
                "• Network instability or interference\n"
                "• Server connection was reset\n"
                "Please try again in a moment."
            )
        elif error_type == "server_error":
            return (
                f"{base_message}. YouTube server errors detected:\n"
                "• YouTube servers may be experiencing issues\n"
                "• Rate limiting or access restrictions\n"
                "Please try again later."
            )
        else:
            return f"{base_message}: {original_error}"
    
    def get_download_status(self, download_id: str) -> Optional[Dict[str, Any]]:
        """
        Get current status of a download.
        
        Args:
            download_id: Download identifier
            
        Returns:
            Dictionary with download status or None if not found
        """
        if download_id in self.active_downloads:
            metrics = self.active_downloads[download_id]
            return {
                'status': 'active',
                'progress_percent': metrics.progress_percent,
                'downloaded_bytes': metrics.downloaded_bytes,
                'total_bytes': metrics.total_bytes,
                'current_speed': metrics.current_speed,
                'eta_seconds': metrics.eta_seconds,
                'duration_seconds': metrics.duration_seconds,
                'retry_count': metrics.retry_count,
                'network_errors': metrics.network_errors
            }
        
        # Check completed downloads
        for metrics in self.completed_downloads:
            if metrics.success:
                return {
                    'status': 'completed',
                    'success': True,
                    'duration_seconds': metrics.duration_seconds,
                    'total_bytes': metrics.total_bytes
                }
            else:
                return {
                    'status': 'failed',
                    'success': False,
                    'duration_seconds': metrics.duration_seconds,
                    'retry_count': metrics.retry_count,
                    'network_errors': metrics.network_errors
                }
        
        return None
    
    def get_all_downloads_status(self) -> Dict[str, Any]:
        """
        Get status of all downloads.
        
        Returns:
            Dictionary with summary of all downloads
        """
        active_count = len(self.active_downloads)
        completed_count = len([d for d in self.completed_downloads if d.success])
        failed_count = len([d for d in self.completed_downloads if not d.success])
        
        return {
            'active_downloads': active_count,
            'completed_downloads': completed_count,
            'failed_downloads': failed_count,
            'total_downloads': active_count + completed_count + failed_count,
            'network_status': self.network_status.value,
            'last_network_check': self.last_network_check
        }
    
    def log_download_summary(self):
        """Log a summary of all downloads."""
        summary = self.get_all_downloads_status()
        
        logger.info("=== Download Summary ===")
        logger.info(f"Active: {summary['active_downloads']}")
        logger.info(f"Completed: {summary['completed_downloads']}")
        logger.info(f"Failed: {summary['failed_downloads']}")
        logger.info(f"Network Status: {summary['network_status']}")
        
        # Log individual download details
        for download_id, metrics in self.active_downloads.items():
            logger.info(f"Active: {download_id} - {metrics.progress_percent:.1f}% complete")
        
        for metrics in self.completed_downloads[-5:]:  # Last 5 completed
            status = "SUCCESS" if metrics.success else "FAILED"
            logger.info(f"Completed: {status} - {metrics.duration_seconds:.1f}s")
    
    def cleanup_old_downloads(self, max_age_hours: int = 24):
        """
        Clean up old completed downloads from memory.
        
        Args:
            max_age_hours: Maximum age in hours for completed downloads
        """
        current_time = time.time()
        max_age_seconds = max_age_hours * 3600
        
        # Remove old completed downloads
        self.completed_downloads = [
            d for d in self.completed_downloads
            if d.end_time and (current_time - d.end_time) < max_age_seconds
        ]
        
        logger.debug(f"Cleaned up old downloads, {len(self.completed_downloads)} remaining")


# Global monitor instance
_global_monitor: Optional[DownloadMonitor] = None


def get_global_monitor() -> DownloadMonitor:
    """Get the global download monitor instance."""
    global _global_monitor
    if _global_monitor is None:
        _global_monitor = DownloadMonitor()
    return _global_monitor


def setup_download_monitoring(log_file: Optional[Path] = None) -> DownloadMonitor:
    """
    Set up download monitoring with custom configuration.
    
    Args:
        log_file: Optional custom log file path
        
    Returns:
        Configured DownloadMonitor instance
    """
    global _global_monitor
    _global_monitor = DownloadMonitor(log_file=log_file)
    return _global_monitor