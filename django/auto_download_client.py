#!/usr/bin/env python3
"""
Auto-Download API Client Library

A simple Python client for the Auto-Download API service.
This library provides easy integration for external applications.
"""

import requests
import json
from typing import Dict, Optional, Union
from pathlib import Path


class AutoDownloadClient:
    """
    Client for the Auto-Download API service.
    
    Provides a simple interface for downloading audio files from YouTube URLs
    using the Django-based auto-download service.
    """
    
    def __init__(self, base_url: str = "http://localhost:8000", username: str = None, password: str = None):
        """
        Initialize the Auto-Download client.
        
        Args:
            base_url: Base URL of the Django server (default: http://localhost:8000)
            username: Django username for linking sessions (optional)
            password: Not used in current implementation (optional)
        """
        self.base_url = base_url.rstrip('/')
        self.api_endpoint = f"{self.base_url}/api/auto-download/"
        self.username = username
        self.session = requests.Session()
    
    
    def download(self, 
                url: str, 
                quality: str = "best", 
                format_type: str = "mp3") -> Dict:
        """
        Download audio from a YouTube URL.
        
        Args:
            url: YouTube video URL
            quality: Audio quality ("best", "worst", "128k", "192k", "320k")
            format_type: Audio format ("mp3", "wav", "flac")
            
        Returns:
            Dictionary containing download information or error details
            
        Example:
            >>> client = AutoDownloadClient()
            >>> result = client.download("https://youtube.com/watch?v=VIDEO_ID")
            >>> if result["success"]:
            ...     print(f"Download URL: {result['download_url']}")
        """
        payload = {
            "url": url,
            "quality": quality,
            "format": format_type
        }
        
        # Add username if provided for session linking
        if self.username:
            payload["username"] = self.username
        
        try:
            response = self.session.post(
                self.api_endpoint,
                json=payload,
                timeout=300  # 5 minute timeout
            )
            
            # Check if response is successful
            if response.status_code != 200:
                return {
                    "success": False,
                    "error": f"HTTP {response.status_code}: {response.text}"
                }
            
            # Try to parse JSON response
            try:
                return response.json()
            except json.JSONDecodeError as e:
                return {
                    "success": False,
                    "error": f"Invalid JSON response: {str(e)}. Response: {response.text[:200]}"
                }
            
        except requests.exceptions.RequestException as e:
            return {
                "success": False,
                "error": f"Request failed: {str(e)}"
            }
    
    def download_and_save(self, 
                         url: str, 
                         output_dir: Union[str, Path] = "./downloads",
                         quality: str = "best", 
                         format_type: str = "mp3") -> Dict:
        """
        Download audio and save it to a local directory.
        
        Args:
            url: YouTube video URL
            output_dir: Local directory to save the file
            quality: Audio quality
            format_type: Audio format
            
        Returns:
            Dictionary containing download information and local file path
        """
        # First, download the file
        result = self.download(url, quality, format_type)
        
        if not result["success"]:
            return result
        
        try:
            # Create output directory
            output_path = Path(output_dir)
            output_path.mkdir(parents=True, exist_ok=True)
            
            # Download the file from the provided URL
            file_response = self.session.get(result["download_url"])
            file_response.raise_for_status()
            
            # Generate local filename with proper sanitization
            title = result.get('title', 'Unknown Title')
            # Remove invalid characters for filenames
            import re
            safe_title = re.sub(r'[<>:"/\\|?*]', '_', title)
            filename = f"{safe_title}.{format_type}"
            local_file_path = output_path / filename
            
            # Save the file
            with open(local_file_path, 'wb') as f:
                f.write(file_response.content)
            
            # Update result with local file info
            result["local_file_path"] = str(local_file_path)
            result["local_file_size"] = local_file_path.stat().st_size
            
            return result
            
        except Exception as e:
            return {
                "success": False,
                "error": f"Failed to save file locally: {str(e)}"
            }
    
    def get_video_info(self, url: str) -> Dict:
        """
        Get video information without downloading.
        
        Args:
            url: YouTube video URL
            
        Returns:
            Dictionary containing video metadata
        """
        # Use a minimal download to get video info
        result = self.download(url, quality="worst", format_type="mp3")
        
        if result["success"]:
            return {
                "success": True,
                "title": result.get("title"),
                "artist": result.get("artist"),
                "duration": result.get("duration"),
                "file_size": result.get("file_size"),
                "quality": result.get("quality"),
                "format": result.get("format")
            }
        else:
            return result


def main():
    """
    Command-line interface for the Auto-Download client.
    
    Usage:
        python auto_download_client.py "https://youtube.com/watch?v=VIDEO_ID"
    """
    import sys
    import argparse
    
    parser = argparse.ArgumentParser(description="Auto-Download API Client")
    parser.add_argument("url", help="YouTube video URL")
    parser.add_argument("--quality", default="best", help="Audio quality")
    parser.add_argument("--format", default="mp3", help="Audio format")
    parser.add_argument("--save", help="Save to local directory")
    parser.add_argument("--server", default="http://localhost:8000", help="Server URL")
    parser.add_argument("--username", help="Django username for linking sessions")
    parser.add_argument("--password", help="Not used (kept for compatibility)")
    
    args = parser.parse_args()
    
    client = AutoDownloadClient(
        base_url=args.server,
        username=args.username
    )
    
    if args.save:
        result = client.download_and_save(
            args.url, 
            args.save, 
            args.quality, 
            args.format
        )
    else:
        result = client.download(args.url, args.quality, args.format)
    
    if result["success"]:
        print("✅ Download successful!")
        print(f"Title: {result['title']}")
        print(f"Artist: {result['artist']}")
        print(f"Duration: {result['duration']}")
        print(f"File Size: {result['file_size']:,} bytes")
        print(f"Download URL: {result['download_url']}")
        
        if "local_file_path" in result:
            print(f"Local File: {result['local_file_path']}")
    else:
        print(f"❌ Download failed: {result['error']}")
        sys.exit(1)


if __name__ == "__main__":
    main()
