"""
CLI interface for audio download functionality.

This module provides a command-line interface for downloading audio
from YouTube videos with session management integration.
"""

import argparse
import sys
import logging
from pathlib import Path
from typing import List, Optional

# Add src directory to path
SCRIPT_DIR = Path(__file__).resolve().parent
PROJECT_ROOT = SCRIPT_DIR.parent.parent
sys.path.insert(0, str(PROJECT_ROOT / "src"))

from src.common import setup_logging, create_session, get_session, get_session_manager
from .audio_core import AudioDownloader, AudioDownloadError

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
                # Download with session integration
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
                else:
                    print(f"\n❌ Download failed: {result.error_message}")
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
    parser = argparse.ArgumentParser(
        description="YouTube Audio Downloader CLI",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  # Download single video
  python -m src.yt_audio_dl --url "https://youtube.com/watch?v=..." --output ./downloads
  
  # Download with custom quality and format
  python -m src.yt_audio_dl --url "https://youtube.com/watch?v=..." --quality bestaudio --format mp3
  
  # Batch download from file
  python -m src.yt_audio_dl --urls-file urls.txt --output ./downloads
  
  # Show session info
  python -m src.yt_audio_dl --session-info
  
  # Show supported formats
  python -m src.yt_audio_dl --formats
        """
    )
    
    # URL options (mutually exclusive)
    url_group = parser.add_mutually_exclusive_group(required=False)
    url_group.add_argument(
        '--url', 
        help='Single YouTube video URL to download'
    )
    url_group.add_argument(
        '--urls-file', 
        help='File containing YouTube URLs (one per line)'
    )
    url_group.add_argument(
        '--session-info', 
        action='store_true',
        help='Show current session information'
    )
    url_group.add_argument(
        '--formats', 
        action='store_true',
        help='Show supported audio formats'
    )
    
    # Output options
    parser.add_argument(
        '--output', 
        '--output-dir',
        dest='output_dir',
        default='./downloads',
        help='Output directory for downloads (default: ./downloads)'
    )
    parser.add_argument(
        '--filename',
        help='Custom filename template (e.g., "%(title)s.%(ext)s")'
    )
    
    # Quality and format options
    parser.add_argument(
        '--quality',
        choices=['bestaudio', 'worstaudio', 'best', 'worst'],
        default='bestaudio',
        help='Audio quality preference (default: bestaudio)'
    )
    parser.add_argument(
        '--format',
        choices=['mp3', 'm4a', 'wav', 'flac', 'ogg', 'opus'],
        default='mp3',
        help='Output audio format (default: mp3)'
    )
    
    # Other options
    parser.add_argument(
        '--verbose', '-v',
        action='store_true',
        help='Enable verbose logging'
    )
    
    # Parse arguments and run
    args = parser.parse_args()
    
    # Setup logging
    setup_logging()
    
    # Create and run CLI
    cli = AudioDownloadCLI()
    cli.run(args)


if __name__ == "__main__":
    main()
