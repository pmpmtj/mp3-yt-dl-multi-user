"""
Module for extracting available audio formats from YouTube URLs using yt-dlp.

This module provides functionality to dynamically retrieve actual available audio formats
for a given YouTube URL instead of using hardcoded format lists. This ensures accuracy
and can be reused by other applications including video downloaders.

Functions:
    get_audio_formats_from_url(url): Extract audio-only formats from a YouTube URL
    get_all_formats_from_url(url): Extract all formats (audio + video) from a YouTube URL
    get_supported_audio_extensions(): Get list of supported audio file extensions
"""

import logging
from typing import List, Dict, Any, Optional
from pathlib import Path
import yt_dlp

# Initialize paths - handling both frozen (PyInstaller) and regular Python execution
SCRIPT_DIR = Path(__file__).resolve().parent

# Initialize logger
logger = logging.getLogger("get_url_formats")


def get_audio_formats_from_url(url: str) -> List[Dict[str, Any]]:
    """
    Extract audio-only formats available for a given YouTube URL.
    
    This function uses yt-dlp to dynamically fetch the actual available audio formats
    for a specific YouTube video, providing accurate and up-to-date format information.
    
    Args:
        url (str): YouTube video URL to analyze
        
    Returns:
        List[Dict[str, Any]]: List of audio format dictionaries containing:
            - format_id: Format identifier (e.g., '140', '251')
            - ext: File extension (e.g., 'mp3', 'm4a', 'webm')
            - acodec: Audio codec (e.g., 'mp4a.40.2', 'opus')
            - abr: Audio bitrate in kbps
            - asr: Audio sample rate in Hz
            - filesize: Approximate file size in bytes (if available)
            - format_note: Additional format description
            
    Raises:
        Exception: If URL is invalid or extraction fails
        
    Example:
        >>> formats = get_audio_formats_from_url("https://www.youtube.com/watch?v=dQw4w9WgXcQ")
        >>> for fmt in formats:
        ...     print(f"Format: {fmt['ext']} ({fmt['format_id']}) - {fmt['abr']}kbps")
    """
    logger.debug(f"Extracting audio formats for URL: {url}")
    
    # Configure yt-dlp options for audio format extraction
    ydl_opts = {
        'quiet': True,                    # Suppress output
        'no_warnings': True,              # Suppress warnings
        'extract_flat': False,            # Get full info
        'skip_download': True,            # Don't download, just extract info
        'writeinfojson': False,           # Don't write info file
        'writethumbnail': False,          # Don't download thumbnail
        'writesubtitles': False,          # Don't download subtitles
    }
    
    try:
        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            # Extract video information without downloading
            info_dict = ydl.extract_info(url, download=False)
            
            if not info_dict:
                logger.error(f"Failed to extract info for URL: {url}")
                return []
            
            # Get all available formats
            all_formats = info_dict.get('formats', [])
            
            # Filter for audio-only formats
            audio_formats = []
            for fmt in all_formats:
                # Check if this is an audio-only format
                vcodec = fmt.get('vcodec')
                acodec = fmt.get('acodec')
                
                # Audio-only formats have vcodec as 'none' and valid acodec
                if vcodec == 'none' and acodec and acodec != 'none':
                    audio_format = {
                        'format_id': fmt.get('format_id', 'unknown'),
                        'ext': fmt.get('ext', 'unknown'),
                        'acodec': acodec,
                        'abr': fmt.get('abr', 0),  # Audio bitrate
                        'asr': fmt.get('asr', 0),  # Audio sample rate
                        'filesize': fmt.get('filesize'),  # May be None
                        'format_note': fmt.get('format_note', ''),
                        'url': fmt.get('url', ''),  # Direct download URL
                    }
                    audio_formats.append(audio_format)
            
            logger.debug(f"Found {len(audio_formats)} audio formats for URL: {url}")
            return audio_formats
            
    except Exception as e:
        logger.error(f"Error extracting audio formats from {url}: {e}")
        raise


def get_all_formats_from_url(url: str) -> List[Dict[str, Any]]:
    """
    Extract all available formats (audio + video) for a given YouTube URL.
    
    This function provides comprehensive format information including both audio-only
    and video formats, useful for applications that need complete format details.
    
    Args:
        url (str): YouTube video URL to analyze
        
    Returns:
        List[Dict[str, Any]]: List of all format dictionaries containing:
            - format_id: Format identifier
            - ext: File extension
            - vcodec: Video codec (or 'none' for audio-only)
            - acodec: Audio codec (or 'none' for video-only)
            - resolution: Video resolution (e.g., '1920x1080')
            - fps: Frames per second (for video)
            - abr: Audio bitrate in kbps
            - vbr: Video bitrate in kbps
            - filesize: Approximate file size in bytes (if available)
            - format_note: Additional format description
            
    Raises:
        Exception: If URL is invalid or extraction fails
    """
    logger.debug(f"Extracting all formats for URL: {url}")
    
    ydl_opts = {
        'quiet': True,
        'no_warnings': True,
        'extract_flat': False,
        'skip_download': True,
        'writeinfojson': False,
        'writethumbnail': False,
        'writesubtitles': False,
    }
    
    try:
        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            info_dict = ydl.extract_info(url, download=False)
            
            if not info_dict:
                logger.error(f"Failed to extract info for URL: {url}")
                return []
            
            all_formats = info_dict.get('formats', [])
            
            # Process and clean up format information
            processed_formats = []
            for fmt in all_formats:
                processed_format = {
                    'format_id': fmt.get('format_id', 'unknown'),
                    'ext': fmt.get('ext', 'unknown'),
                    'vcodec': fmt.get('vcodec', 'none'),
                    'acodec': fmt.get('acodec', 'none'),
                    'resolution': fmt.get('resolution', 'N/A'),
                    'fps': fmt.get('fps'),
                    'abr': fmt.get('abr', 0),
                    'vbr': fmt.get('vbr', 0),
                    'filesize': fmt.get('filesize'),
                    'format_note': fmt.get('format_note', ''),
                    'url': fmt.get('url', ''),
                }
                processed_formats.append(processed_format)
            
            logger.debug(f"Found {len(processed_formats)} total formats for URL: {url}")
            return processed_formats
            
    except Exception as e:
        logger.error(f"Error extracting all formats from {url}: {e}")
        raise


def get_supported_audio_extensions(url: str) -> List[str]:
    """
    Get list of supported audio file extensions for a given YouTube URL.
    
    This function extracts actual available audio formats and returns a clean list
    of file extensions, useful for dynamic format validation and UI display.
    
    Args:
        url (str): YouTube video URL to analyze
        
    Returns:
        List[str]: List of audio file extensions (e.g., ['mp3', 'm4a', 'webm', 'opus'])
        
    Example:
        >>> extensions = get_supported_audio_extensions("https://www.youtube.com/watch?v=dQw4w9WgXcQ")
        >>> print("Supported formats:", ", ".join(extensions))
    """
    logger.debug(f"Getting supported audio extensions for URL: {url}")
    
    try:
        audio_formats = get_audio_formats_from_url(url)
        
        # Extract unique extensions
        extensions = set()
        for fmt in audio_formats:
            ext = fmt.get('ext', '').lower()
            if ext and ext != 'unknown':
                extensions.add(ext)
        
        # Convert to sorted list for consistent output
        result = sorted(list(extensions))
        logger.debug(f"Found audio extensions: {result}")
        return result
        
    except Exception as e:
        logger.error(f"Error getting audio extensions from {url}: {e}")
        # Return empty list on error to avoid breaking caller
        return []


def format_audio_info_display(url: str) -> str:
    """
    Create a formatted display string of available audio formats for a URL.
    
    This function provides a human-readable summary of available audio formats,
    useful for CLI display or debugging purposes.
    
    Args:
        url (str): YouTube video URL to analyze
        
    Returns:
        str: Formatted string with audio format information
    """
    try:
        audio_formats = get_audio_formats_from_url(url)
        
        if not audio_formats:
            return f"No audio formats found for URL: {url}"
        
        lines = [f"Available audio formats for {url}:", ""]
        
        for fmt in audio_formats:
            filesize_info = ""
            if fmt['filesize']:
                size_mb = fmt['filesize'] / (1024 * 1024)
                filesize_info = f" (~{size_mb:.1f} MB)"
            
            line = (f"  - {fmt['ext'].upper()} (ID: {fmt['format_id']}) "
                   f"- {fmt['abr']}kbps{filesize_info}")
            
            if fmt['format_note']:
                line += f" - {fmt['format_note']}"
            
            lines.append(line)
        
        return "\n".join(lines)
        
    except Exception as e:
        return f"Error retrieving format information: {e}"


# Example usage and testing
if __name__ == "__main__":
    # Test URLs - replace with actual URLs for testing
    test_urls = [
        "https://www.youtube.com/watch?v=dQw4w9WgXcQ",  # Rick Astley - Never Gonna Give You Up
        "https://www.youtube.com/watch?v=HUK8v2QDFWY"    # Example from user
    ]
    
    for test_url in test_urls:
        print(f"\n{'='*80}")
        print(f"Testing URL: {test_url}")
        print('='*80)
        
        try:
            # Test audio formats extraction
            print("\n1. Audio Formats:")
            audio_formats = get_audio_formats_from_url(test_url)
            for fmt in audio_formats:
                print(f"  Format ID: {fmt['format_id']}")
                print(f"  Extension: {fmt['ext']}")
                print(f"  Audio Codec: {fmt['acodec']}")
                print(f"  Bitrate: {fmt['abr']} kbps")
                print(f"  Sample Rate: {fmt['asr']} Hz")
                if fmt['filesize']:
                    print(f"  File Size: {fmt['filesize'] / (1024*1024):.1f} MB")
                print(f"  Note: {fmt['format_note']}")
                print("  " + "-"*40)
            
            # Test supported extensions
            print("\n2. Supported Audio Extensions:")
            extensions = get_supported_audio_extensions(test_url)
            print(f"  {', '.join(extensions)}")
            
            # Test formatted display
            print("\n3. Formatted Display:")
            display = format_audio_info_display(test_url)
            print(display)
            
        except Exception as e:
            print(f"Error testing URL {test_url}: {e}")
            
        print("\n" + "="*80)
