"""
Integration tests for audio downloader functionality.

This module tests the integration between AudioDownloader, UserContext,
and other components with real file system operations.
"""

import pytest
import tempfile
import shutil
from pathlib import Path
from unittest.mock import patch, Mock
import time

from src.yt_audio_dl.audio_core import AudioDownloader, AudioDownloadResult, DownloadStatus
from src.common.user_context import UserContext
from src.common.session_manager import SessionManager


class TestAudioDownloaderIntegration:
    """Integration tests for AudioDownloader with real components."""
    
    @pytest.fixture
    def temp_download_dir(self):
        """Create a temporary download directory for integration tests."""
        temp_path = Path(tempfile.mkdtemp())
        yield temp_path
        shutil.rmtree(temp_path, ignore_errors=True)
    
    @pytest.fixture
    def user_context(self):
        """Create a real UserContext for integration tests."""
        return UserContext(session_uuid="integration-test-session")
    
    @pytest.fixture
    def session_manager(self):
        """Create a real SessionManager for integration tests."""
        return SessionManager()
    
    @pytest.mark.integration
    def test_audio_downloader_with_user_context_integration(self, temp_download_dir, user_context):
        """Test AudioDownloader integration with UserContext."""
        # Create downloader with user context
        downloader = AudioDownloader(output_dir=temp_download_dir)
        
        # Test URL for integration testing (using a real but short video)
        test_url = "https://www.youtube.com/watch?v=dQw4w9WgXcQ"  # Rick Roll - short video
        
        # Mock yt-dlp to avoid actual download but test integration
        with patch('src.yt_audio_dl.audio_core.yt_dlp.YoutubeDL') as mock_ydl_class:
            # Setup mock yt-dlp
            mock_ydl_instance = Mock()
            mock_ydl_instance.extract_info.return_value = {
                'id': 'dQw4w9WgXcQ',
                'title': 'Rick Astley - Never Gonna Give You Up',
                'uploader': 'Rick Astley',
                'duration': 212,
                'view_count': 1000000000
            }
            mock_ydl_class.return_value.__enter__.return_value = mock_ydl_instance
            
            # Create a mock output file to simulate successful download
            output_file = temp_download_dir / "Rick Astley - Never Gonna Give You Up.mp3"
            output_file.write_text("fake audio content")
            
            with patch('pathlib.Path.glob') as mock_glob:
                mock_glob.return_value = [output_file]
                
                # Test download with user context
                result = downloader.download_audio_with_session(
                    url=test_url,
                    session_uuid=user_context.session_uuid,
                    job_uuid="integration-test-job"
                )
                
                # Verify integration worked
                assert result.success is True
                assert result.status == DownloadStatus.COMPLETED
                assert result.title == "Rick Astley - Never Gonna Give You Up"
                assert result.artist == "Rick Astley"
                assert result.duration_seconds == 212
    
    @pytest.mark.integration
    def test_audio_downloader_with_session_manager_integration(self, temp_download_dir, session_manager):
        """Test AudioDownloader integration with SessionManager."""
        # Create session
        session_uuid = session_manager.create_session()
        assert session_uuid is not None
        
        # Create downloader
        downloader = AudioDownloader(output_dir=temp_download_dir)
        
        # Test URL
        test_url = "https://www.youtube.com/watch?v=dQw4w9WgXcQ"
        
        # Mock yt-dlp
        with patch('src.yt_audio_dl.audio_core.yt_dlp.YoutubeDL') as mock_ydl_class:
            mock_ydl_instance = Mock()
            mock_ydl_instance.extract_info.return_value = {
                'id': 'dQw4w9WgXcQ',
                'title': 'Test Video',
                'uploader': 'Test Channel',
                'duration': 120
            }
            mock_ydl_class.return_value.__enter__.return_value = mock_ydl_instance
            
            # Create mock output file
            output_file = temp_download_dir / session_uuid / "test-job" / "audio" / "Test Video.mp3"
            output_file.parent.mkdir(parents=True, exist_ok=True)
            output_file.write_text("fake audio content")
            
            with patch('pathlib.Path.glob') as mock_glob:
                mock_glob.return_value = [output_file]
                
                # Test download with session manager
                result = downloader.download_audio_with_session(
                    url=test_url,
                    session_uuid=session_uuid,
                    job_uuid="test-job"
                )
                
                # Verify session-specific directory was created
                session_dir = temp_download_dir / session_uuid / "test-job" / "audio"
                assert session_dir.exists()
                
                # Verify result
                assert result.success is True
                assert result.status == DownloadStatus.COMPLETED
    
    @pytest.mark.integration
    def test_audio_downloader_progress_tracking_integration(self, temp_download_dir):
        """Test AudioDownloader progress tracking integration."""
        # Track progress calls
        progress_calls = []
        
        def progress_callback(data):
            progress_calls.append(data)
        
        # Create downloader with progress callback
        downloader = AudioDownloader(
            output_dir=temp_download_dir,
            progress_callback=progress_callback
        )
        
        # Mock yt-dlp with progress simulation
        with patch('src.yt_audio_dl.audio_core.yt_dlp.YoutubeDL') as mock_ydl_class:
            mock_ydl_instance = Mock()
            mock_ydl_instance.extract_info.return_value = {
                'id': 'test',
                'title': 'Test Video',
                'uploader': 'Test Channel',
                'duration': 120
            }
            
            # Mock download method to simulate progress
            def mock_download(urls):
                # Simulate progress updates
                progress_hook = mock_ydl_instance.add_progress_hook.call_args[0][0]
                progress_hook({'status': 'downloading', 'downloaded_bytes': 1000, 'total_bytes': 5000})
                progress_hook({'status': 'downloading', 'downloaded_bytes': 2500, 'total_bytes': 5000})
                progress_hook({'status': 'downloading', 'downloaded_bytes': 5000, 'total_bytes': 5000})
                progress_hook({'status': 'finished', 'filename': 'test.mp3'})
                return []
            
            mock_ydl_instance.download = mock_download
            mock_ydl_class.return_value.__enter__.return_value = mock_ydl_instance
            
            # Create mock output file
            output_file = temp_download_dir / "Test Video.mp3"
            output_file.write_text("fake audio content")
            
            with patch('pathlib.Path.glob') as mock_glob:
                mock_glob.return_value = [output_file]
                
                # Test download
                result = downloader.download_audio("https://youtube.com/watch?v=test")
                
                # Verify progress tracking worked
                assert result.success is True
                assert len(progress_calls) > 0
                
                # Check that progress was tracked
                downloading_calls = [call for call in progress_calls if call.get('status') == 'downloading']
                assert len(downloading_calls) > 0
                
                # Verify progress percentages were calculated
                for call in downloading_calls:
                    if 'progress_percent' in call and call['progress_percent'] is not None:
                        assert 0 <= call['progress_percent'] <= 100
    
    @pytest.mark.integration
    def test_audio_downloader_multiple_formats_integration(self, temp_download_dir):
        """Test AudioDownloader with different audio formats."""
        formats = ['mp3', 'm4a', 'wav']
        
        for format_type in formats:
            downloader = AudioDownloader(
                output_dir=temp_download_dir,
                format=format_type
            )
            
            # Verify format is set correctly
            assert downloader.format == format_type
            
            # Test yt-dlp options generation
            opts = downloader._get_ydl_opts()
            assert opts['format'] == f'bestaudio[ext={format_type}]'
    
    @pytest.mark.integration
    def test_audio_downloader_error_handling_integration(self, temp_download_dir):
        """Test AudioDownloader error handling integration."""
        downloader = AudioDownloader(output_dir=temp_download_dir)
        
        # Test with invalid URL
        result = downloader.download_audio("invalid-url")
        assert result.success is False
        assert result.status == DownloadStatus.FAILED
        assert result.error_message is not None
        
        # Test with non-existent directory
        non_existent_dir = temp_download_dir / "non_existent"
        downloader_bad_dir = AudioDownloader(output_dir=non_existent_dir)
        
        with patch('src.yt_audio_dl.audio_core.yt_dlp.YoutubeDL') as mock_ydl_class:
            mock_ydl_instance = Mock()
            mock_ydl_instance.extract_info.return_value = {
                'id': 'test',
                'title': 'Test Video',
                'uploader': 'Test Channel',
                'duration': 120
            }
            mock_ydl_class.return_value.__enter__.return_value = mock_ydl_instance
            
            # Mock download to not create any files
            mock_ydl_instance.download.return_value = []
            
            with patch('pathlib.Path.glob') as mock_glob:
                mock_glob.return_value = []  # No files found
                
                result = downloader_bad_dir.download_audio("https://youtube.com/watch?v=test")
                assert result.success is False
                assert "no output file found" in result.error_message
    
    @pytest.mark.integration
    @pytest.mark.slow
    def test_audio_downloader_real_download_integration(self, temp_download_dir):
        """Test AudioDownloader with real YouTube download (slow test)."""
        # This test actually downloads a short video - use sparingly
        downloader = AudioDownloader(
            output_dir=temp_download_dir,
            format='mp3',
            quality='worstaudio'  # Use worst quality for faster download
        )
        
        # Use a very short video for testing
        test_url = "https://www.youtube.com/watch?v=dQw4w9WgXcQ"
        
        # Track progress
        progress_calls = []
        
        def progress_callback(data):
            progress_calls.append(data)
        
        downloader.progress_callback = progress_callback
        
        # Perform real download
        result = downloader.download_audio(test_url)
        
        # Verify download succeeded
        assert result.success is True
        assert result.status == DownloadStatus.COMPLETED
        assert result.output_path is not None
        assert result.output_path.exists()
        assert result.file_size_bytes > 0
        assert result.title is not None
        assert result.artist is not None
        assert result.duration_seconds > 0
        
        # Verify progress was tracked
        assert len(progress_calls) > 0
        
        # Clean up
        if result.output_path.exists():
            result.output_path.unlink()
    
    @pytest.mark.integration
    def test_audio_downloader_concurrent_sessions_integration(self, temp_download_dir):
        """Test AudioDownloader with multiple concurrent sessions."""
        # Create multiple user contexts
        contexts = [
            UserContext(session_uuid=f"session-{i}")
            for i in range(3)
        ]
        
        downloader = AudioDownloader(output_dir=temp_download_dir)
        
        # Mock yt-dlp for all sessions
        with patch('src.yt_audio_dl.audio_core.yt_dlp.YoutubeDL') as mock_ydl_class:
            mock_ydl_instance = Mock()
            mock_ydl_instance.extract_info.return_value = {
                'id': 'test',
                'title': 'Test Video',
                'uploader': 'Test Channel',
                'duration': 120
            }
            mock_ydl_class.return_value.__enter__.return_value = mock_ydl_instance
            
            results = []
            
            # Simulate concurrent downloads
            for i, context in enumerate(contexts):
                # Create session-specific output file
                output_file = temp_download_dir / context.session_uuid / f"job-{i}" / "audio" / f"Test Video {i}.mp3"
                output_file.parent.mkdir(parents=True, exist_ok=True)
                output_file.write_text(f"fake audio content {i}")
            
            with patch('pathlib.Path.glob') as mock_glob:
                # Mock glob to return appropriate files for each session
                def mock_glob_func(pattern):
                    # Find the session directory from the calling context
                    # This is a simplified mock - in real scenario, each session would have its own directory
                    return [temp_download_dir / f"session-{i}" / f"job-{i}" / "audio" / f"Test Video {i}.mp3" for i in range(3)]
                
                mock_glob.side_effect = mock_glob_func
                
                # Test concurrent downloads
                for i, context in enumerate(contexts):
                    result = downloader.download_audio_with_session(
                        url="https://youtube.com/watch?v=test",
                        session_uuid=context.session_uuid,
                        job_uuid=f"job-{i}"
                    )
                    results.append(result)
                
                # Verify all downloads succeeded
                for i, result in enumerate(results):
                    assert result.success is True
                    assert result.status == DownloadStatus.COMPLETED
                    
                    # Verify session-specific directory exists
                    session_dir = temp_download_dir / f"session-{i}" / f"job-{i}" / "audio"
                    assert session_dir.exists()
