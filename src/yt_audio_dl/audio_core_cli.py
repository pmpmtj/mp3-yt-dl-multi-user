"""
CLI interface for audio download functionality.

This module provides a command-line interface for downloading audio
from YouTube videos with session management integration.
"""

import argparse
import sys
import logging
import time
from pathlib import Path
from typing import List, Optional

# Add src directory to path
SCRIPT_DIR = Path(__file__).resolve().parent
PROJECT_ROOT = SCRIPT_DIR.parent.parent
sys.path.insert(0, str(PROJECT_ROOT / "src"))

from src.common import setup_logging, create_session, get_session, get_session_manager
from .audio_core import AudioDownloader, AudioDownloadError, DownloadStatus
from src.common.download_monitor import get_global_monitor, DownloadEvent

# Initialize logger
logger = logging.getLogger("audio_cli")


class AudioDownloadCLI:
    """
    Command-line interface for audio downloads.
    
    Provides a user-friendly CLI for downloading audio from YouTube videos
    with session management and progress tracking.
    """
    
    def __init__(self):
        """Initialize the CLI interface."""
        self.session_manager = None
        self.session_uuid = None
        
    def setup_logging(self, verbose: bool = False):
        """Setup logging configuration."""
        if verbose:
            logging.getLogger().setLevel(logging.DEBUG)
        else:
            logging.getLogger().setLevel(logging.INFO)
    
    def create_or_get_session(self) -> str:
        """Create or get existing session."""
        try:
            if not self.session_manager:
                self.session_manager = get_session_manager()
            
            # For CLI, create a new session each time
            self.session_uuid = create_session()
            logger.info(f"Created new session: {self.session_uuid}")
            
            return self.session_uuid
            
        except Exception as e:
            logger.error(f"Error creating session: {e}")
            raise
    
    def progress_callback(self, progress_data: dict):
        """Progress callback for download updates."""
        if progress_data['status'] == 'downloading':
            percent = progress_data.get('progress_percent', 0)
            downloaded = progress_data.get('downloaded_bytes', 0)
            total = progress_data.get('total_bytes', 0)
            speed = progress_data.get('speed', 0)
            
            if total:
                downloaded_mb = downloaded / (1024 * 1024)
                total_mb = total / (1024 * 1024)
                print(f"\rDownloading: {percent:.1f}% ({downloaded_mb:.1f}/{total_mb:.1f} MB) "
                      f"Speed: {speed or 'Unknown'} bytes/s", end='', flush=True)
        
        elif progress_data['status'] == 'finished':
            print(f"\nDownload completed: {progress_data['filename']}")
    
    def download_single_url(self, 
                           url: str, 
                           output_dir: Path,
                           quality: str = "bestaudio",
                           format: str = "mp3",
                           custom_filename: Optional[str] = None) -> bool:
        """
        Download audio from a single URL.
        
        Args:
            url: YouTube video URL
            output_dir: Output directory for downloads
            quality: Audio quality preference
            format: Output audio format
            custom_filename: Optional custom filename
            
        Returns:
            True if download successful, False otherwise
        """
        try:
            print(f"Starting download: {url}")
            
            # Create session
            session_uuid = self.create_or_get_session()
            
            # Get user context
            user_context = get_session(session_uuid)
            if not user_context:
                print("Error: Could not get user context")
                return False
            
            # Get job UUID for this URL
            job_uuid = user_context.get_url_uuid(url)
            
            # Create downloader
            downloader = AudioDownloader(
                output_dir=output_dir,
                quality=quality,
                format=format,
                progress_callback=self.progress_callback
            )
            
            # Validate URL
            if not downloader.validate_url(url):
                print(f"Error: Invalid or unsupported URL: {url}")
                return False
            
            # Start job in session manager
            if not self.session_manager.start_job(session_uuid):
                print("Error: Maximum jobs per session exceeded")
                return False
            
            try:
                # Download with session integration and retry logic
                max_retries = 3
                retry_delay = 5  # seconds
                
                for attempt in range(max_retries):
                    if attempt > 0:
                        print(f"\n🔄 Retry attempt {attempt}/{max_retries - 1}...")
                        time.sleep(retry_delay)
                    
                    result = downloader.download_audio_with_session(
                        url=url,
                        session_uuid=session_uuid,
                        job_uuid=job_uuid,
                        progress_callback=self.progress_callback
                    )
                    
                    if result.success:
                        print(f"\n✅ Download successful!")
                        print(f"   File: {result.output_path}")
                        print(f"   Size: {result.file_size_bytes / (1024*1024):.1f} MB")
                        print(f"   Duration: {result.duration_seconds:.0f} seconds" if result.duration_seconds else "   Duration: Unknown")
                        print(f"   Title: {result.title}")
                        if result.artist:
                            print(f"   Artist: {result.artist}")
                        
                        # Complete job in session manager
                        self.session_manager.complete_job(session_uuid, result.file_size_bytes or 0)
                        return True
                    
                    # Check if this is a retryable network error
                    elif result.status == DownloadStatus.PENDING:
                        print(f"\n⚠️  {result.error_message}")
                        continue  # Retry
                    
                    # Check for network-related errors that should be retried
                    elif any(network_error in result.error_message.lower() for network_error in [
                        'network', 'connection', 'timeout', 'resolve', 'getaddrinfo', 
                        'bytes read', 'more expected', 'incomplete read', 'partial download',
                        'connection broken', 'download interrupted'
                    ]):
                        print(f"\n⚠️  Network issue detected: {result.error_message}")
                        if attempt < max_retries - 1:
                            print(f"🔄 Will retry in {retry_delay} seconds...")
                        continue
                    else:
                        # Non-retryable error
                        print(f"\n❌ Download failed: {result.error_message}")
                        self.session_manager.fail_job(session_uuid)
                        return False
                
                # All retries exhausted
                print(f"\n❌ Download failed after {max_retries} attempts due to persistent network issues.")
                print("💡 Suggestions:")
                print("   • Check your internet connection")
                print("   • Try again in a few minutes") 
                print("   • Check if YouTube is accessible in your region")
                self.session_manager.fail_job(session_uuid)
                return False
                    
            except Exception as e:
                print(f"\n❌ Download error: {e}")
                self.session_manager.fail_job(session_uuid)
                return False
                
        except Exception as e:
            print(f"Error: {e}")
            return False
    
    def download_multiple_urls(self, 
                              urls: List[str], 
                              output_dir: Path,
                              quality: str = "bestaudio",
                              format: str = "mp3") -> int:
        """
        Download audio from multiple URLs.
        
        Args:
            urls: List of YouTube video URLs
            output_dir: Output directory for downloads
            quality: Audio quality preference
            format: Output audio format
            
        Returns:
            Number of successful downloads
        """
        successful_downloads = 0
        total_urls = len(urls)
        
        print(f"Starting batch download of {total_urls} URLs...")
        print("-" * 50)
        
        for i, url in enumerate(urls, 1):
            print(f"\n[{i}/{total_urls}] Processing: {url}")
            
            if self.download_single_url(url, output_dir, quality, format):
                successful_downloads += 1
            
            print("-" * 50)
        
        print(f"\nBatch download complete: {successful_downloads}/{total_urls} successful")
        return successful_downloads
    
    def show_session_info(self):
        """Show current session information."""
        if not self.session_uuid or not self.session_manager:
            print("No active session")
            return
        
        try:
            session_info = self.session_manager.get_session_info(self.session_uuid)
            if session_info:
                print(f"Session UUID: {session_info['session_uuid']}")
                print(f"Created: {session_info['created_at']}")
                print(f"Active: {session_info['is_active']}")
                print(f"Total Jobs: {session_info['total_jobs']}")
                print(f"Completed Jobs: {session_info['completed_jobs']}")
                print(f"Failed Jobs: {session_info['failed_jobs']}")
                print(f"Storage Used: {session_info['storage_used_bytes'] / (1024*1024):.1f} MB")
            else:
                print("Session not found")
        except Exception as e:
            print(f"Error getting session info: {e}")
    
    def show_supported_formats(self):
        """Show supported audio formats."""
        downloader = AudioDownloader(Path("./temp"))
        formats = downloader.get_supported_formats()
        print("Supported audio formats:")
        for fmt in formats:
            print(f"  - {fmt.upper()}")
    
    def run(self, args):
        """Run the CLI with parsed arguments."""
        try:
            # Setup logging
            self.setup_logging(args.verbose)
            
            # Ensure output directory exists
            output_dir = Path(args.output_dir)
            output_dir.mkdir(parents=True, exist_ok=True)
            
            if args.url:
                # Single URL download
                success = self.download_single_url(
                    url=args.url,
                    output_dir=output_dir,
                    quality=args.quality,
                    format=args.format,
                    custom_filename=args.filename
                )
                sys.exit(0 if success else 1)
            
            elif args.urls_file:
                # Multiple URLs from file
                try:
                    with open(args.urls_file, 'r') as f:
                        urls = [line.strip() for line in f if line.strip()]
                    
                    if not urls:
                        print("No URLs found in file")
                        sys.exit(1)
                    
                    successful = self.download_multiple_urls(
                        urls=urls,
                        output_dir=output_dir,
                        quality=args.quality,
                        format=args.format
                    )
                    sys.exit(0 if successful > 0 else 1)
                    
                except FileNotFoundError:
                    print(f"Error: File not found: {args.urls_file}")
                    sys.exit(1)
            
            elif args.session_info:
                # Show session information
                self.create_or_get_session()
                self.show_session_info()
            
            elif args.formats:
                # Show supported formats
                self.show_supported_formats()
            
            else:
                print("No action specified. Use --help for usage information.")
                sys.exit(1)
                
        except KeyboardInterrupt:
            print("\nDownload cancelled by user")
            sys.exit(1)
        except Exception as e:
            print(f"Error: {e}")
            if args.verbose:
                import traceback
                traceback.print_exc()
            sys.exit(1)


def main():
    """Main CLI entry point."""
    parser = argparse.ArgumentParser(description="YouTube Audio Downloader")
    parser.add_argument("--url", required=True, help="YouTube video URL")
    parser.add_argument("--output-dir", default="downloads", help="Output directory")
    parser.add_argument("--quality", default="bestaudio", help="Audio quality")
    parser.add_argument("--format", default="mp3", help="Output format")
    parser.add_argument("--verbose", "-v", action="store_true", help="Verbose output")
    
    args = parser.parse_args()
    
    # Set up logging
    if args.verbose:
        logging.getLogger().setLevel(logging.DEBUG)
    
    # Initialize download monitor
    monitor = get_global_monitor()
    
    try:
        # Check network connectivity first
        network_result = monitor.check_network_connectivity()
        if not network_result.is_online:
            print(f"❌ Network Error: {network_result.error_message}")
            print("Please check your internet connection and try again.")
            return 1
        
        print("✅ Network connection verified")
        
        # Use the CLI class for proper session management
        cli = AudioDownloadCLI()
        
        # Download with session support for proper multiuser directory structure
        print(f"Starting download: {args.url}")
        success = cli.download_single_url(
            url=args.url,
            output_dir=Path(args.output_dir),
            quality=args.quality,
            format=args.format
        )
        
        return 0 if success else 1
            
    except KeyboardInterrupt:
        print("\n⚠️  Download cancelled by user")
        return 1
    except Exception as e:
        print(f"❌ Unexpected error: {e}")
        return 1


if __name__ == "__main__":
    main()
