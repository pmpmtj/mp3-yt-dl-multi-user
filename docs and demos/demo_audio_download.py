#!/usr/bin/env python3
"""
Demo script for audio download functionality.

This script demonstrates the audio download capabilities including
CLI usage, API integration, and session management.
"""

import sys
import time
from pathlib import Path

# Add src directory to Python path
SCRIPT_DIR = Path(__file__).resolve().parent
PROJECT_ROOT = SCRIPT_DIR.parent
sys.path.insert(0, str(PROJECT_ROOT / "src"))

from src.common import setup_logging
from src.yt_audio_dl import AudioDownloader, AudioDownloadError

def demo_audio_downloader():
    """Demo the core audio downloader functionality."""
    print("=== Audio Downloader Demo ===\n")
    
    # Setup logging
    setup_logging()
    
    # Test URLs (safe, public domain content)
    test_urls = [
        "https://www.youtube.com/watch?v=dQw4w9WgXcQ",  # Rick Roll (short, well-known)
        "https://www.youtube.com/watch?v=9bZkp7q19f0",  # Gangnam Style (popular)
    ]
    
    # Create output directory
    output_dir = Path("./demo_downloads")
    output_dir.mkdir(exist_ok=True)
    
    print("1. Testing Audio Downloader Core Functionality")
    print("-" * 50)
    
    # Test 1: Basic audio download
    print("Testing basic audio download...")
    downloader = AudioDownloader(
        output_dir=output_dir,
        quality="bestaudio",
        format="mp3"
    )
    
    # Test URL validation
    print(f"Validating URL: {test_urls[0]}")
    is_valid = downloader.validate_url(test_urls[0])
    print(f"URL is valid: {is_valid}")
    
    if is_valid:
        # Get video info
        print("\nGetting video information...")
        try:
            video_info = downloader.get_video_info(test_urls[0])
            print(f"Title: {video_info.get('title', 'Unknown')}")
            print(f"Uploader: {video_info.get('uploader', 'Unknown')}")
            print(f"Duration: {video_info.get('duration', 0)} seconds")
            print(f"View count: {video_info.get('view_count', 'Unknown')}")
        except AudioDownloadError as e:
            print(f"Error getting video info: {e}")
        
        # Download audio with progress tracking
        print("\nStarting audio download...")
        
        def progress_callback(progress_data):
            if progress_data['status'] == 'downloading':
                percent = progress_data.get('progress_percent', 0)
                downloaded = progress_data.get('downloaded_bytes', 0)
                total = progress_data.get('total_bytes', 0)
                
                if total:
                    downloaded_mb = downloaded / (1024 * 1024)
                    total_mb = total / (1024 * 1024)
                    print(f"\rProgress: {percent:.1f}% ({downloaded_mb:.1f}/{total_mb:.1f} MB)", 
                          end='', flush=True)
            elif progress_data['status'] == 'finished':
                print(f"\nDownload completed: {progress_data['filename']}")
        
        # Create downloader with progress callback
        downloader_with_progress = AudioDownloader(
            output_dir=output_dir,
            quality="bestaudio",
            format="mp3",
            progress_callback=progress_callback
        )
        
        try:
            result = downloader_with_progress.download_audio(test_urls[0])
            
            if result.success:
                print(f"\n✅ Download successful!")
                print(f"   Output file: {result.output_path}")
                print(f"   File size: {result.file_size_bytes / (1024*1024):.1f} MB")
                print(f"   Duration: {result.duration_seconds:.0f} seconds")
                print(f"   Title: {result.title}")
                if result.artist:
                    print(f"   Artist: {result.artist}")
                print(f"   Download time: {result.download_time_seconds:.1f} seconds")
            else:
                print(f"\n❌ Download failed: {result.error_message}")
                
        except Exception as e:
            print(f"\n❌ Download error: {e}")
    
    print("\n" + "="*60)
    print("2. Testing Different Audio Formats")
    print("-" * 50)
    
    # Test different formats
    formats_to_test = ['mp3', 'm4a', 'wav']
    
    for fmt in formats_to_test:
        print(f"\nTesting {fmt.upper()} format...")
        
        format_downloader = AudioDownloader(
            output_dir=output_dir / f"format_test_{fmt}",
            quality="bestaudio",
            format=fmt
        )
        
        try:
            # Use a shorter URL for format testing
            result = format_downloader.download_audio(test_urls[0])
            
            if result.success:
                print(f"   ✅ {fmt.upper()} download successful")
                print(f"   File: {result.output_path}")
                print(f"   Size: {result.file_size_bytes / (1024*1024):.1f} MB")
            else:
                print(f"   ❌ {fmt.upper()} download failed: {result.error_message}")
                
        except Exception as e:
            print(f"   ❌ {fmt.upper()} download error: {e}")
    
    print("\n" + "="*60)
    print("3. Testing Session Integration")
    print("-" * 50)
    
    # Test session-based download
    print("Testing session-based download...")
    
    # Import session management
    from src.common import create_session, get_session, get_session_manager
    
    # Create a session
    session_uuid = create_session()
    print(f"Created session: {session_uuid}")
    
    # Get user context
    user_context = get_session(session_uuid)
    if user_context:
        job_uuid = user_context.get_url_uuid(test_urls[1])
        print(f"Generated job UUID: {job_uuid}")
        
        # Get download paths
        audio_path = user_context.get_audio_download_path(test_urls[1])
        print(f"Audio download path: {audio_path}")
        
        # Test session-based download
        session_downloader = AudioDownloader(
            output_dir=output_dir / "session_test",
            quality="bestaudio",
            format="mp3"
        )
        
        try:
            result = session_downloader.download_audio_with_session(
                url=test_urls[1],
                session_uuid=session_uuid,
                job_uuid=job_uuid
            )
            
            if result.success:
                print(f"✅ Session-based download successful")
                print(f"   Output: {result.output_path}")
                print(f"   Size: {result.file_size_bytes / (1024*1024):.1f} MB")
                
                # Show session info
                session_info = user_context.get_session_info()
                print(f"\nSession Info:")
                print(f"   Session UUID: {session_info['session_uuid']}")
                print(f"   Total Jobs: {session_info['total_jobs']}")
                print(f"   Job URLs: {session_info['job_urls']}")
            else:
                print(f"❌ Session-based download failed: {result.error_message}")
                
        except Exception as e:
            print(f"❌ Session-based download error: {e}")
    
    print("\n" + "="*60)
    print("4. Testing Error Handling")
    print("-" * 50)
    
    # Test invalid URLs
    invalid_urls = [
        "https://www.youtube.com/watch?v=invalid",
        "https://example.com/not-youtube",
        "not-a-url",
        ""
    ]
    
    for invalid_url in invalid_urls:
        print(f"\nTesting invalid URL: {invalid_url}")
        
        try:
            is_valid = downloader.validate_url(invalid_url)
            print(f"   Validation result: {is_valid}")
            
            if not is_valid:
                print(f"   ✅ Correctly identified as invalid")
            else:
                print(f"   ⚠️  Incorrectly identified as valid")
                
        except Exception as e:
            print(f"   ❌ Validation error: {e}")
    
    print("\n" + "="*60)
    print("5. Testing Supported Formats")
    print("-" * 50)
    
    supported_formats = downloader.get_supported_formats()
    print(f"Supported audio formats: {', '.join(supported_formats)}")
    
    print("\n=== Demo Complete ===")
    print("\nKey Features Demonstrated:")
    print("✅ Audio download with yt-dlp")
    print("✅ Progress tracking and callbacks")
    print("✅ Multiple audio format support")
    print("✅ Session-based download isolation")
    print("✅ Error handling and validation")
    print("✅ Video information extraction")
    print("✅ File size and metadata tracking")


def demo_cli_usage():
    """Demo CLI usage examples."""
    print("\n=== CLI Usage Examples ===\n")
    
    print("1. Download single video:")
    print("   python -m src.yt_audio_dl --url 'https://youtube.com/watch?v=...' --output ./downloads")
    
    print("\n2. Download with custom quality and format:")
    print("   python -m src.yt_audio_dl --url 'https://youtube.com/watch?v=...' --quality bestaudio --format mp3")
    
    print("\n3. Batch download from file:")
    print("   python -m src.yt_audio_dl --urls-file urls.txt --output ./downloads")
    
    print("\n4. Show session information:")
    print("   python -m src.yt_audio_dl --session-info")
    
    print("\n5. Show supported formats:")
    print("   python -m src.yt_audio_dl --formats")
    
    print("\n6. Verbose logging:")
    print("   python -m src.yt_audio_dl --url 'https://youtube.com/watch?v=...' --verbose")


if __name__ == "__main__":
    try:
        demo_audio_downloader()
        demo_cli_usage()
    except KeyboardInterrupt:
        print("\nDemo cancelled by user")
    except Exception as e:
        print(f"\nDemo error: {e}")
        import traceback
        traceback.print_exc()
