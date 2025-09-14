"""
Unit tests for audio downloader functionality.

This module tests the AudioDownloader class with various scenarios including
download validation, progress tracking, and error handling.
"""

import pytest
from unittest.mock import Mock, patch, MagicMock, mock_open
from pathlib import Path
from src.yt_audio_dl.audio_core import (
    AudioDownloader, 
    AudioDownloadResult, 
    AudioDownloadError,
    DownloadStatus,
    ProgressHook
)


class TestAudioDownloader:
    """Test AudioDownloader functionality."""
    
    @pytest.mark.unit
    def test_audio_downloader_initialization(self, temp_download_dir):
        """Test AudioDownloader initialization."""
        downloader = AudioDownloader(
            output_dir=temp_download_dir,
            quality="bestaudio",
            format="mp3"
        )
        
        assert downloader.output_dir == temp_download_dir
        assert downloader.quality == "bestaudio"
        assert downloader.format == "mp3"
        assert downloader.progress_callback is None
        assert temp_download_dir.exists()
    
    @pytest.mark.unit
    def test_audio_downloader_with_progress_callback(self, temp_download_dir, mock_progress_callback):
        """Test AudioDownloader with progress callback."""
        downloader = AudioDownloader(
            output_dir=temp_download_dir,
            progress_callback=mock_progress_callback
        )
        
        assert downloader.progress_callback == mock_progress_callback
    
    @pytest.mark.unit
    def test_get_ydl_opts(self, temp_download_dir):
        """Test yt-dlp options generation."""
        downloader = AudioDownloader(output_dir=temp_download_dir)
        
        opts = downloader.get_ydl_opts("%(title)s.%(ext)s")
        
        assert 'format' in opts
        assert 'outtmpl' in opts
        assert 'postprocessors' in opts
        assert 'progress_hooks' in opts
        assert opts['format'] == 'bestaudio'
        assert 'extractaudio' in opts
        assert opts['audioformat'] == 'mp3'
    
    @pytest.mark.unit
    def test_get_ydl_opts_with_custom_quality_and_format(self, temp_download_dir):
        """Test yt-dlp options with custom quality and format."""
        downloader = AudioDownloader(
            output_dir=temp_download_dir,
            quality="worstaudio",
            format="wav"
        )
        
        opts = downloader.get_ydl_opts("%(title)s.%(ext)s")
        
        assert opts['format'] == 'worstaudio'
        assert opts['audioformat'] == 'wav'
    
    @pytest.mark.unit
    @patch('src.yt_audio_dl.audio_core.yt_dlp.YoutubeDL')
    def test_get_video_info_success(self, mock_ydl_class, temp_download_dir):
        """Test successful video info retrieval."""
        downloader = AudioDownloader(output_dir=temp_download_dir)
        
        # Mock yt-dlp response
        mock_info = {
            'id': 'test-video-id',
            'title': 'Test Video',
            'uploader': 'Test Channel',
            'duration': 120,
            'view_count': 1000
        }
        
        mock_ydl_instance = Mock()
        mock_ydl_instance.extract_info.return_value = mock_info
        mock_ydl_class.return_value.__enter__.return_value = mock_ydl_instance
        
        result = downloader.get_video_info("https://youtube.com/watch?v=test")
        
        assert result['id'] == 'test-video-id'
        assert result['title'] == 'Test Video'
        assert result['uploader'] == 'Test Channel'
        assert result['duration'] == 120
        assert result['view_count'] == 1000
    
    @pytest.mark.unit
    @patch('src.yt_audio_dl.audio_core.yt_dlp.YoutubeDL')
    def test_get_video_info_failure(self, mock_ydl_class, temp_download_dir):
        """Test video info retrieval failure."""
        downloader = AudioDownloader(output_dir=temp_download_dir)
        
        # Mock yt-dlp failure
        mock_ydl_instance = Mock()
        mock_ydl_instance.extract_info.return_value = None
        mock_ydl_class.return_value.__enter__.return_value = mock_ydl_instance
        
        with pytest.raises(AudioDownloadError, match="Unable to extract video information"):
            downloader.get_video_info("https://youtube.com/watch?v=test")
    
    @pytest.mark.unit
    def test_validate_url_valid_youtube(self, temp_download_dir):
        """Test URL validation with valid YouTube URL."""
        downloader = AudioDownloader(output_dir=temp_download_dir)
        
        with patch.object(downloader, 'get_video_info') as mock_get_info:
            mock_get_info.return_value = {'title': 'Test'}
            
            result = downloader.validate_url("https://www.youtube.com/watch?v=test")
            assert result is True
    
    @pytest.mark.unit
    def test_validate_url_invalid_domain(self, temp_download_dir):
        """Test URL validation with invalid domain."""
        downloader = AudioDownloader(output_dir=temp_download_dir)
        
        result = downloader.validate_url("https://example.com/not-youtube")
        assert result is False
    
    @pytest.mark.unit
    def test_validate_url_malformed(self, temp_download_dir):
        """Test URL validation with malformed URL."""
        downloader = AudioDownloader(output_dir=temp_download_dir)
        
        result = downloader.validate_url("not-a-url")
        assert result is False
    
    @pytest.mark.unit
    def test_get_supported_formats(self, temp_download_dir):
        """Test getting supported formats."""
        downloader = AudioDownloader(output_dir=temp_download_dir)
        
        formats = downloader.get_supported_formats()
        
        assert isinstance(formats, list)
        assert 'mp3' in formats
        assert 'm4a' in formats
        assert 'wav' in formats
    
    @pytest.mark.unit
    @patch('src.yt_audio_dl.audio_core.yt_dlp.YoutubeDL')
    def test_download_audio_success(self, mock_ydl_class, temp_download_dir):
        """Test successful audio download."""
        downloader = AudioDownloader(output_dir=temp_download_dir)
        
        # Mock yt-dlp download
        mock_info = {
            'title': 'Test Video',
            'uploader': 'Test Channel',
            'duration': 120
        }
        
        mock_ydl_instance = Mock()
        mock_ydl_instance.extract_info.return_value = mock_info
        mock_ydl_class.return_value.__enter__.return_value = mock_ydl_instance
        
        # Create a mock output file
        output_file = temp_download_dir / "Test Video.mp3"
        output_file.write_text("fake audio content")
        
        # Mock glob to return our test file
        with patch.object(temp_download_dir, 'glob') as mock_glob:
            mock_glob.return_value = [output_file]
            
            result = downloader.download_audio("https://youtube.com/watch?v=test")
            
            assert result.success is True
            assert result.status == DownloadStatus.COMPLETED
            assert result.output_path == output_file
            assert result.title == "Test Video"
            assert result.artist == "Test Channel"
            assert result.duration_seconds == 120
    
    @pytest.mark.unit
    @patch('src.yt_audio_dl.audio_core.yt_dlp.YoutubeDL')
    def test_download_audio_with_custom_filename(self, mock_ydl_class, temp_download_dir):
        """Test audio download with custom filename."""
        downloader = AudioDownloader(output_dir=temp_download_dir)
        
        mock_ydl_instance = Mock()
        mock_ydl_instance.extract_info.return_value = {'title': 'Test'}
        mock_ydl_class.return_value.__enter__.return_value = mock_ydl_instance
        
        # Create mock output file
        output_file = temp_download_dir / "custom_name.mp3"
        output_file.write_text("fake audio content")
        
        with patch.object(temp_download_dir, 'glob') as mock_glob:
            mock_glob.return_value = [output_file]
            
            result = downloader.download_audio(
                "https://youtube.com/watch?v=test",
                output_filename="custom_name.%(ext)s"
            )
            
            assert result.success is True
            assert result.output_path == output_file
    
    @pytest.mark.unit
    @patch('src.yt_audio_dl.audio_core.yt_dlp.YoutubeDL')
    def test_download_audio_failure_no_output_file(self, mock_ydl_class, temp_download_dir):
        """Test audio download failure when no output file is found."""
        downloader = AudioDownloader(output_dir=temp_download_dir)
        
        mock_ydl_instance = Mock()
        mock_ydl_instance.extract_info.return_value = {'title': 'Test'}
        mock_ydl_class.return_value.__enter__.return_value = mock_ydl_instance
        
        # Mock empty glob result (no output files)
        with patch.object(temp_download_dir, 'glob') as mock_glob:
            mock_glob.return_value = []
            
            result = downloader.download_audio("https://youtube.com/watch?v=test")
            
            assert result.success is False
            assert result.status == DownloadStatus.FAILED
            assert "no output file found" in result.error_message
    
    @pytest.mark.unit
    def test_download_audio_with_session(self, temp_download_dir):
        """Test session-based audio download."""
        downloader = AudioDownloader(output_dir=temp_download_dir)
        
        with patch.object(downloader, 'download_audio') as mock_download:
            mock_result = Mock()
            mock_result.success = True
            mock_result.output_path = temp_download_dir / "output.mp3"
            mock_result.file_size_bytes = 1024
            mock_download.return_value = mock_result
            
            result = downloader.download_audio_with_session(
                url="https://youtube.com/watch?v=test",
                session_uuid="test-session",
                job_uuid="test-job"
            )
            
            assert result.success is True
            mock_download.assert_called_once()
    
    @pytest.mark.unit
    def test_download_audio_with_session_error(self, temp_download_dir):
        """Test session-based audio download with error."""
        downloader = AudioDownloader(output_dir=temp_download_dir)
        
        with patch.object(downloader, 'download_audio') as mock_download:
            mock_download.side_effect = Exception("Download error")
            
            result = downloader.download_audio_with_session(
                url="https://youtube.com/watch?v=test",
                session_uuid="test-session",
                job_uuid="test-job"
            )
            
            assert result.success is False
            assert result.status == DownloadStatus.FAILED
            assert "Session download error" in result.error_message


class TestProgressHook:
    """Test ProgressHook functionality."""
    
    @pytest.mark.unit
    def test_progress_hook_initialization(self):
        """Test ProgressHook initialization."""
        callback = Mock()
        hook = ProgressHook(callback)
        
        assert hook.progress_callback == callback
        assert hook.start_time is None
        assert hook.total_bytes is None
        assert hook.downloaded_bytes == 0
    
    @pytest.mark.unit
    def test_progress_hook_without_callback(self):
        """Test ProgressHook without callback."""
        hook = ProgressHook()
        
        # Should not raise any errors
        hook({'status': 'downloading', 'downloaded_bytes': 1000})
        assert hook.downloaded_bytes == 1000
    
    @pytest.mark.unit
    def test_progress_hook_downloading_status(self, mock_progress_callback):
        """Test ProgressHook with downloading status."""
        hook = ProgressHook(mock_progress_callback)
        
        progress_data = {
            'status': 'downloading',
            'total_bytes': 10000,
            'downloaded_bytes': 5000,
            'speed': 1000,
            'eta': 5
        }
        
        hook(progress_data)
        
        assert hook.total_bytes == 10000
        assert hook.downloaded_bytes == 5000
        assert hook.speed == 1000
        assert hook.eta == 5
        
        # Check that callback was called
        mock_progress_callback.assert_called_once()
        call_args = mock_progress_callback.call_args[0][0]
        assert call_args['status'] == 'downloading'
        assert call_args['progress_percent'] == 50.0
        assert call_args['downloaded_bytes'] == 5000
        assert call_args['total_bytes'] == 10000
    
    @pytest.mark.unit
    def test_progress_hook_finished_status(self, mock_progress_callback):
        """Test ProgressHook with finished status."""
        hook = ProgressHook(mock_progress_callback)
        
        progress_data = {
            'status': 'finished',
            'filename': 'output.mp3'
        }
        
        hook(progress_data)
        
        # Check that callback was called
        mock_progress_callback.assert_called_once()
        call_args = mock_progress_callback.call_args[0][0]
        assert call_args['status'] == 'finished'
        assert call_args['filename'] == 'output.mp3'
    
    @pytest.mark.unit
    def test_progress_hook_with_estimate_bytes(self, mock_progress_callback):
        """Test ProgressHook with estimated total bytes."""
        hook = ProgressHook(mock_progress_callback)
        
        progress_data = {
            'status': 'downloading',
            'total_bytes_estimate': 8000,
            'downloaded_bytes': 2000
        }
        
        hook(progress_data)
        
        assert hook.total_bytes == 8000
        assert hook.downloaded_bytes == 2000
        
        # Check callback
        call_args = mock_progress_callback.call_args[0][0]
        assert call_args['progress_percent'] == 25.0
    
    @pytest.mark.unit
    def test_progress_hook_no_total_bytes(self, mock_progress_callback):
        """Test ProgressHook when no total bytes available."""
        hook = ProgressHook(mock_progress_callback)
        
        progress_data = {
            'status': 'downloading',
            'downloaded_bytes': 1000
        }
        
        hook(progress_data)
        
        assert hook.downloaded_bytes == 1000
        
        # Check callback
        call_args = mock_progress_callback.call_args[0][0]
        assert call_args['progress_percent'] is None


class TestAudioDownloadResult:
    """Test AudioDownloadResult functionality."""
    
    @pytest.mark.unit
    def test_audio_download_result_success(self):
        """Test successful AudioDownloadResult."""
        result = AudioDownloadResult(
            success=True,
            status=DownloadStatus.COMPLETED,
            output_path=Path("/test/output.mp3"),
            file_size_bytes=1024,
            title="Test Video",
            artist="Test Artist"
        )
        
        assert result.success is True
        assert result.status == DownloadStatus.COMPLETED
        assert result.output_path == Path("/test/output.mp3")
        assert result.file_size_bytes == 1024
        assert result.title == "Test Video"
        assert result.artist == "Test Artist"
        assert result.error_message is None
    
    @pytest.mark.unit
    def test_audio_download_result_failure(self):
        """Test failed AudioDownloadResult."""
        result = AudioDownloadResult(
            success=False,
            status=DownloadStatus.FAILED,
            error_message="Download failed"
        )
        
        assert result.success is False
        assert result.status == DownloadStatus.FAILED
        assert result.error_message == "Download failed"
        assert result.output_path is None
        assert result.file_size_bytes is None
    
    @pytest.mark.unit
    def test_audio_download_result_defaults(self):
        """Test AudioDownloadResult with minimal parameters."""
        result = AudioDownloadResult(
            success=True,
            status=DownloadStatus.PENDING
        )
        
        assert result.success is True
        assert result.status == DownloadStatus.PENDING
        assert result.output_path is None
        assert result.file_size_bytes is None
        assert result.title is None
        assert result.artist is None
        assert result.error_message is None


class TestAudioDownloadError:
    """Test AudioDownloadError functionality."""
    
    @pytest.mark.unit
    def test_audio_download_error_creation(self):
        """Test AudioDownloadError creation."""
        error = AudioDownloadError("Test error message")
        
        assert str(error) == "Test error message"
        assert isinstance(error, Exception)
    
    @pytest.mark.unit
    def test_audio_download_error_inheritance(self):
        """Test AudioDownloadError inheritance."""
        error = AudioDownloadError("Test error")
        
        assert isinstance(error, Exception)
        assert isinstance(error, AudioDownloadError)
