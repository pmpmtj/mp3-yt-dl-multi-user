#!/usr/bin/env python3
"""
Test script for download monitoring functionality.
"""

import sys
import logging
from pathlib import Path

# Add src to path
sys.path.insert(0, str(Path(__file__).parent / "src"))

from src.common.download_monitor import setup_download_monitoring, DownloadEvent
from src.yt_audio_dl.audio_core import AudioDownloader

def test_event_callback(event_data):
    """Test event callback for monitoring."""
    event_type = event_data['event_type']
    data = event_data['data']
    
    if event_type == DownloadEvent.STARTED:
        print(f"🚀 Download started: {data['download_id']}")
    elif event_type == DownloadEvent.PROGRESS:
        progress = data.get('progress_percent', 0)
        print(f"📊 Progress: {progress:.1f}%")
    elif event_type == DownloadEvent.COMPLETED:
        print(f"✅ Download completed: {data['download_id']}")
    elif event_type == DownloadEvent.FAILED:
        print(f"❌ Download failed: {data['error_message']}")
    elif event_type == DownloadEvent.NETWORK_ERROR:
        error_type = data.get('error_type', 'unknown')
        print(f"🌐 Network error ({error_type}): {data['error']}")
        print(f"   Retry {data['retry_count']}/{data['max_retries']}")
    elif event_type == DownloadEvent.RETRY_ATTEMPT:
        error_type = data.get('error_type', 'unknown')
        print(f"🔄 Retrying in {data['delay_seconds']}s (error type: {error_type})...")

def main():
    """Test the monitoring system."""
    # Set up logging
    logging.basicConfig(level=logging.INFO)
    
    # Set up monitoring
    monitor = setup_download_monitoring()
    monitor.add_event_callback(test_event_callback)
    
    # Test network connectivity
    print("Testing network connectivity...")
    network_result = monitor.check_network_connectivity()
    
    if network_result.is_online:
        print("✅ Network is online")
    else:
        print(f"❌ Network is offline: {network_result.error_message}")
        return 1
    
    # Test downloader with session-based structure
    print("\nTesting downloader with session management...")
    from src.yt_audio_dl.audio_core_cli import AudioDownloadCLI
    from pathlib import Path
    
    cli = AudioDownloadCLI()
    test_url = "https://www.youtube.com/watch?v=dQw4w9WgXcQ"  # Rick Roll for testing
    
    try:
        success = cli.download_single_url(
            url=test_url,
            output_dir=Path("test_downloads"),
            quality="bestaudio",
            format="mp3"
        )
        if success:
            print(f"✅ Test download successful with session structure")
        else:
            print(f"❌ Test download failed")
    except Exception as e:
        print(f"❌ Test failed with exception: {e}")
    
    # Show monitoring summary
    print("\n📊 Monitoring Summary:")
    monitor.log_download_summary()
    
    return 0

if __name__ == "__main__":
    sys.exit(main())