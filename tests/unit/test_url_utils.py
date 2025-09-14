"""
Unit tests for URL utilities.

This module tests the YouTube URL sanitization functionality with various
URL formats, edge cases, and error conditions.
"""

import pytest
from unittest.mock import patch
from src.common.url_utils import (
    YouTubeURLSanitizer,
    YouTubeURLInfo,
    YouTubeURLError,
    sanitize_youtube_url,
    get_clean_youtube_url,
    is_youtube_url,
    extract_youtube_video_id
)


class TestYouTubeURLSanitizer:
    """Test YouTubeURLSanitizer functionality."""
    
    @pytest.mark.unit
    def test_standard_youtube_url(self):
        """Test standard YouTube URL format."""
        url = "https://www.youtube.com/watch?v=XNNjYas8Xo8"
        url_info = YouTubeURLSanitizer.sanitize_url(url)
        
        assert url_info.video_id == "XNNjYas8Xo8"
        assert url_info.clean_url == "https://www.youtube.com/watch?v=XNNjYas8Xo8"
        assert url_info.url_type == "standard"
        assert url_info.timestamp is None
        assert url_info.playlist_id is None
    
    @pytest.mark.unit
    def test_standard_url_with_timestamp(self):
        """Test standard URL with timestamp parameter."""
        url = "https://www.youtube.com/watch?v=XNNjYas8Xo8&t=24s"
        url_info = YouTubeURLSanitizer.sanitize_url(url)
        
        assert url_info.video_id == "XNNjYas8Xo8"
        assert url_info.clean_url == "https://www.youtube.com/watch?v=XNNjYas8Xo8"
        assert url_info.timestamp == 24
        assert url_info.url_type == "standard"
    
    @pytest.mark.unit
    def test_short_youtube_url(self):
        """Test short YouTube URL format."""
        url = "https://youtu.be/XNNjYas8Xo8"
        url_info = YouTubeURLSanitizer.sanitize_url(url)
        
        assert url_info.video_id == "XNNjYas8Xo8"
        assert url_info.clean_url == "https://www.youtube.com/watch?v=XNNjYas8Xo8"
        assert url_info.url_type == "short"
    
    @pytest.mark.unit
    def test_short_url_with_timestamp(self):
        """Test short URL with timestamp."""
        url = "https://youtu.be/XNNjYas8Xo8?t=24"
        url_info = YouTubeURLSanitizer.sanitize_url(url)
        
        assert url_info.video_id == "XNNjYas8Xo8"
        assert url_info.clean_url == "https://www.youtube.com/watch?v=XNNjYas8Xo8"
        assert url_info.timestamp == 24
        assert url_info.url_type == "short"
    
    @pytest.mark.unit
    def test_embed_url(self):
        """Test YouTube embed URL format."""
        url = "https://www.youtube.com/embed/XNNjYas8Xo8"
        url_info = YouTubeURLSanitizer.sanitize_url(url)
        
        assert url_info.video_id == "XNNjYas8Xo8"
        assert url_info.clean_url == "https://www.youtube.com/watch?v=XNNjYas8Xo8"
        assert url_info.url_type == "embed"
    
    @pytest.mark.unit
    def test_mobile_url(self):
        """Test mobile YouTube URL format."""
        url = "https://m.youtube.com/watch?v=XNNjYas8Xo8"
        url_info = YouTubeURLSanitizer.sanitize_url(url)
        
        assert url_info.video_id == "XNNjYas8Xo8"
        assert url_info.clean_url == "https://www.youtube.com/watch?v=XNNjYas8Xo8"
        assert url_info.url_type == "mobile"
    
    @pytest.mark.unit
    def test_url_without_protocol(self):
        """Test URL without protocol."""
        url = "youtube.com/watch?v=XNNjYas8Xo8"
        url_info = YouTubeURLSanitizer.sanitize_url(url)
        
        assert url_info.video_id == "XNNjYas8Xo8"
        assert url_info.clean_url == "https://www.youtube.com/watch?v=XNNjYas8Xo8"
    
    @pytest.mark.unit
    def test_playlist_url(self):
        """Test URL with playlist parameters."""
        url = "https://www.youtube.com/watch?v=XNNjYas8Xo8&list=PLxxxyyy&index=5"
        url_info = YouTubeURLSanitizer.sanitize_url(url)
        
        assert url_info.video_id == "XNNjYas8Xo8"
        assert url_info.clean_url == "https://www.youtube.com/watch?v=XNNjYas8Xo8"
        assert url_info.playlist_id == "PLxxxyyy"
        assert url_info.playlist_index == 5
    
    @pytest.mark.unit
    def test_complex_timestamp_formats(self):
        """Test various timestamp formats."""
        test_cases = [
            ("https://youtu.be/XNNjYas8Xo8?t=30", 30),
            ("https://youtu.be/XNNjYas8Xo8?t=30s", 30),
            ("https://youtu.be/XNNjYas8Xo8?t=1m30s", 90),
            ("https://youtu.be/XNNjYas8Xo8?t=1h2m30s", 3750),
            ("https://www.youtube.com/watch?v=XNNjYas8Xo8&t=45", 45),
        ]
        
        for url, expected_timestamp in test_cases:
            url_info = YouTubeURLSanitizer.sanitize_url(url)
            assert url_info.timestamp == expected_timestamp, f"Failed for {url}"
    
    @pytest.mark.unit
    def test_preserve_metadata_false(self):
        """Test with preserve_metadata=False."""
        url = "https://youtu.be/XNNjYas8Xo8?t=24&list=PLxxx"
        url_info = YouTubeURLSanitizer.sanitize_url(url, preserve_metadata=False)
        
        assert url_info.video_id == "XNNjYas8Xo8"
        assert url_info.clean_url == "https://www.youtube.com/watch?v=XNNjYas8Xo8"
        assert url_info.timestamp is None
        assert url_info.playlist_id is None
    
    @pytest.mark.unit
    def test_invalid_video_id_length(self):
        """Test with invalid video ID length."""
        url = "https://www.youtube.com/watch?v=short"
        
        with pytest.raises(YouTubeURLError):
            YouTubeURLSanitizer.sanitize_url(url)
    
    @pytest.mark.unit
    def test_invalid_youtube_url(self):
        """Test with non-YouTube URL."""
        url = "https://example.com/watch?v=XNNjYas8Xo8"
        
        with pytest.raises(YouTubeURLError):
            YouTubeURLSanitizer.sanitize_url(url)
    
    @pytest.mark.unit
    def test_empty_url(self):
        """Test with empty URL."""
        with pytest.raises(YouTubeURLError):
            YouTubeURLSanitizer.sanitize_url("")
    
    @pytest.mark.unit
    def test_none_url(self):
        """Test with None URL."""
        with pytest.raises(YouTubeURLError):
            YouTubeURLSanitizer.sanitize_url(None)
    
    @pytest.mark.unit
    def test_get_clean_url(self):
        """Test get_clean_url convenience method."""
        url = "https://youtu.be/XNNjYas8Xo8?t=24&list=PLxxx"
        clean_url = YouTubeURLSanitizer.get_clean_url(url)
        
        assert clean_url == "https://www.youtube.com/watch?v=XNNjYas8Xo8"
    
    @pytest.mark.unit
    def test_is_youtube_url(self):
        """Test is_youtube_url validation."""
        valid_urls = [
            "https://www.youtube.com/watch?v=XNNjYas8Xo8",
            "https://youtu.be/XNNjYas8Xo8",
            "youtube.com/watch?v=XNNjYas8Xo8",
            "https://m.youtube.com/watch?v=XNNjYas8Xo8",
        ]
        
        invalid_urls = [
            "https://example.com/watch?v=XNNjYas8Xo8",
            "not a url",
            "",
            "https://youtube.com/watch?v=short",
        ]
        
        for url in valid_urls:
            assert YouTubeURLSanitizer.is_youtube_url(url), f"Should be valid: {url}"
        
        for url in invalid_urls:
            assert not YouTubeURLSanitizer.is_youtube_url(url), f"Should be invalid: {url}"
    
    @pytest.mark.unit
    def test_extract_video_id(self):
        """Test video ID extraction."""
        url = "https://youtu.be/XNNjYas8Xo8?t=24"
        video_id = YouTubeURLSanitizer.extract_video_id(url)
        
        assert video_id == "XNNjYas8Xo8"
    
    @pytest.mark.unit
    def test_extract_video_id_invalid(self):
        """Test video ID extraction with invalid URL."""
        url = "https://example.com/not-youtube"
        video_id = YouTubeURLSanitizer.extract_video_id(url)
        
        assert video_id is None


class TestTimestampParsing:
    """Test timestamp parsing functionality."""
    
    @pytest.mark.unit
    def test_parse_timestamp_formats(self):
        """Test various timestamp formats."""
        test_cases = [
            ("30", 30),
            ("30s", 30),
            ("1m", 60),
            ("1m30s", 90),
            ("2m", 120),
            ("1h", 3600),
            ("1h30m", 5400),
            ("1h2m30s", 3750),
            ("2h15m45s", 8145),
        ]
        
        for timestamp_str, expected in test_cases:
            result = YouTubeURLSanitizer._parse_timestamp(timestamp_str)
            assert result == expected, f"Failed for {timestamp_str}"
    
    @pytest.mark.unit
    def test_parse_invalid_timestamp(self):
        """Test parsing invalid timestamps."""
        invalid_cases = ["", "abc", "1x", "m30s", "1h2x30s"]
        
        for timestamp_str in invalid_cases:
            result = YouTubeURLSanitizer._parse_timestamp(timestamp_str)
            assert result is None, f"Should return None for {timestamp_str}"


class TestConvenienceFunctions:
    """Test convenience functions."""
    
    @pytest.mark.unit
    def test_sanitize_youtube_url(self):
        """Test sanitize_youtube_url convenience function."""
        url = "https://youtu.be/XNNjYas8Xo8?t=24"
        url_info = sanitize_youtube_url(url)
        
        assert isinstance(url_info, YouTubeURLInfo)
        assert url_info.video_id == "XNNjYas8Xo8"
        assert url_info.timestamp == 24
    
    @pytest.mark.unit
    def test_get_clean_youtube_url(self):
        """Test get_clean_youtube_url convenience function."""
        url = "https://youtu.be/XNNjYas8Xo8?t=24&list=PLxxx"
        clean_url = get_clean_youtube_url(url)
        
        assert clean_url == "https://www.youtube.com/watch?v=XNNjYas8Xo8"
    
    @pytest.mark.unit
    def test_is_youtube_url_function(self):
        """Test is_youtube_url convenience function."""
        assert is_youtube_url("https://youtu.be/XNNjYas8Xo8")
        assert not is_youtube_url("https://example.com")
    
    @pytest.mark.unit
    def test_extract_youtube_video_id_function(self):
        """Test extract_youtube_video_id convenience function."""
        url = "https://youtu.be/XNNjYas8Xo8?t=24"
        video_id = extract_youtube_video_id(url)
        
        assert video_id == "XNNjYas8Xo8"


class TestYouTubeURLInfo:
    """Test YouTubeURLInfo dataclass."""
    
    @pytest.mark.unit
    def test_youtube_url_info_creation(self):
        """Test creating YouTubeURLInfo object."""
        url_info = YouTubeURLInfo(
            video_id="XNNjYas8Xo8",
            clean_url="https://www.youtube.com/watch?v=XNNjYas8Xo8",
            timestamp=24,
            playlist_id="PLxxx",
            playlist_index=5,
            original_url="https://youtu.be/XNNjYas8Xo8?t=24",
            url_type="short"
        )
        
        assert url_info.video_id == "XNNjYas8Xo8"
        assert url_info.clean_url == "https://www.youtube.com/watch?v=XNNjYas8Xo8"
        assert url_info.timestamp == 24
        assert url_info.playlist_id == "PLxxx"
        assert url_info.playlist_index == 5
        assert url_info.original_url == "https://youtu.be/XNNjYas8Xo8?t=24"
        assert url_info.url_type == "short"
    
    @pytest.mark.unit
    def test_youtube_url_info_defaults(self):
        """Test YouTubeURLInfo with default values."""
        url_info = YouTubeURLInfo(
            video_id="XNNjYas8Xo8",
            clean_url="https://www.youtube.com/watch?v=XNNjYas8Xo8"
        )
        
        assert url_info.timestamp is None
        assert url_info.playlist_id is None
        assert url_info.playlist_index is None
        assert url_info.original_url == ""
        assert url_info.url_type == "standard"


class TestErrorHandling:
    """Test error handling and edge cases."""
    
    @pytest.mark.unit
    def test_youtube_url_error(self):
        """Test YouTubeURLError exception."""
        error = YouTubeURLError("Test error message")
        assert str(error) == "Test error message"
        assert isinstance(error, Exception)
    
    @pytest.mark.unit
    def test_malformed_query_parameters(self):
        """Test handling malformed query parameters."""
        # This should not crash, just not extract metadata
        url = "https://youtu.be/XNNjYas8Xo8?t=invalid&list="
        url_info = YouTubeURLSanitizer.sanitize_url(url)
        
        assert url_info.video_id == "XNNjYas8Xo8"
        assert url_info.clean_url == "https://www.youtube.com/watch?v=XNNjYas8Xo8"
        # Invalid timestamp should result in None
        assert url_info.timestamp is None
    
    @pytest.mark.unit
    @patch('src.common.url_utils.logger')
    def test_metadata_extraction_error_handling(self, mock_logger):
        """Test error handling during metadata extraction."""
        # This should log a warning but not crash
        url = "https://youtu.be/XNNjYas8Xo8?t=24"
        
        # Mock urlparse to raise an exception
        with patch('src.common.url_utils.urlparse', side_effect=Exception("Parse error")):
            url_info = YouTubeURLSanitizer.sanitize_url(url)
            
            # Should still work, just without metadata
            assert url_info.video_id == "XNNjYas8Xo8"
            assert url_info.timestamp is None
            
            # Should have logged a warning
            mock_logger.warning.assert_called_once()


class TestRealWorldURLs:
    """Test with real-world YouTube URL examples."""
    
    @pytest.mark.unit
    def test_example_url_from_issue(self):
        """Test the specific URL from the issue."""
        url = "https://www.youtube.com/watch?v=XNNjYas8Xo8&t=24s"
        url_info = sanitize_youtube_url(url)
        
        assert url_info.video_id == "XNNjYas8Xo8"
        assert url_info.clean_url == "https://www.youtube.com/watch?v=XNNjYas8Xo8"
        assert url_info.timestamp == 24
        assert url_info.url_type == "standard"
    
    @pytest.mark.unit
    def test_complex_playlist_url(self):
        """Test complex playlist URL with multiple parameters."""
        url = "https://www.youtube.com/watch?v=XNNjYas8Xo8&list=PLrAXtmRdnEQy6nuLMfVUFomFgQwN_B_V3&index=10&t=1m30s&pp=ygUOcHl0aG9uIHR1dG9yaWFs"
        url_info = sanitize_youtube_url(url)
        
        assert url_info.video_id == "XNNjYas8Xo8"
        assert url_info.clean_url == "https://www.youtube.com/watch?v=XNNjYas8Xo8"
        assert url_info.timestamp == 90  # 1m30s = 90 seconds
        assert url_info.playlist_id == "PLrAXtmRdnEQy6nuLMfVUFomFgQwN_B_V3"
        assert url_info.playlist_index == 10
    
    @pytest.mark.unit
    def test_short_url_variations(self):
        """Test various short URL formats."""
        urls = [
            "youtu.be/XNNjYas8Xo8",
            "https://youtu.be/XNNjYas8Xo8",
            "http://youtu.be/XNNjYas8Xo8",
            "youtu.be/XNNjYas8Xo8?t=30",
        ]
        
        for url in urls:
            url_info = sanitize_youtube_url(url)
            assert url_info.video_id == "XNNjYas8Xo8"
            assert url_info.clean_url == "https://www.youtube.com/watch?v=XNNjYas8Xo8"
