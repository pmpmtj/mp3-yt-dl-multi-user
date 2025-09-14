"""
Simple integration tests that work with the actual API.

This module contains basic integration tests that verify core functionality
without complex mocking or API mismatches.
"""

import pytest
import tempfile
import shutil
from pathlib import Path
from unittest.mock import patch, Mock

from fastapi.testclient import TestClient

from src.api.main import app
from src.common.session_manager import SessionManager
from src.common.user_context import UserContext
from src.yt_audio_dl.audio_core import AudioDownloader, DownloadStatus


class TestSimpleIntegration:
    """Simple integration tests that work with the actual API."""
    
    @pytest.fixture
    def temp_download_dir(self):
        """Create a temporary download directory for tests."""
        temp_path = Path(tempfile.mkdtemp())
        yield temp_path
        shutil.rmtree(temp_path, ignore_errors=True)
    
    @pytest.fixture
    def client(self):
        """Create a test client for the API."""
        return TestClient(app)
    
    @pytest.fixture
    def session_manager(self):
        """Create a real SessionManager for tests."""
        return SessionManager()
    
    @pytest.mark.integration
    def test_api_health_endpoint(self, client):
        """Test API health endpoint."""
        response = client.get("/api/health")
        assert response.status_code == 200
        
        data = response.json()
        assert "status" in data
        assert data["status"] == "healthy"
    
    @pytest.mark.integration
    def test_api_root_endpoint(self, client):
        """Test API root endpoint."""
        response = client.get("/")
        assert response.status_code == 200
        
        data = response.json()
        assert "message" in data
        assert "YouTube Downloader API" in data["message"]
    
    @pytest.mark.integration
    def test_session_manager_basic_operations(self, session_manager):
        """Test basic SessionManager operations."""
        # Create session
        session_uuid = session_manager.create_session()
        assert session_uuid is not None
        assert isinstance(session_uuid, str)
        
        # Get session info
        session_info = session_manager.get_session_info(session_uuid)
        assert session_info is not None
        assert isinstance(session_info, dict)
        assert session_info["session_uuid"] == session_uuid
        assert session_info["is_active"] is True
        
        # Get session stats
        stats = session_manager.get_session_stats()
        assert isinstance(stats, dict)
        assert "total_sessions" in stats
        assert "active_sessions" in stats
        assert stats["total_sessions"] >= 1
        assert stats["active_sessions"] >= 1
        
        # Get active sessions
        active_sessions = session_manager.get_active_sessions()
        assert isinstance(active_sessions, list)
        assert len(active_sessions) >= 1
        assert any(s["session_uuid"] == session_uuid for s in active_sessions)
    
    @pytest.mark.integration
    def test_user_context_integration(self, session_manager):
        """Test UserContext integration with SessionManager."""
        # Create session
        session_uuid = session_manager.create_session()
        
        # Create user context
        user_context = UserContext(session_uuid=session_uuid)
        assert user_context.session_uuid == session_uuid
        
        # Test URL UUID generation
        test_url = "https://youtube.com/watch?v=test"
        job_uuid = user_context.get_url_uuid(test_url)
        assert job_uuid is not None
        assert isinstance(job_uuid, str)
        
        # Test path generation
        audio_path = user_context.get_audio_download_path(test_url)
        assert audio_path is not None
        assert isinstance(audio_path, Path)
        
        # Test session info
        session_info = user_context.get_session_info()
        assert session_info is not None
        assert session_info["session_uuid"] == session_uuid
    
    @pytest.mark.integration
    def test_audio_downloader_basic_integration(self, temp_download_dir):
        """Test basic AudioDownloader functionality."""
        # Create downloader
        downloader = AudioDownloader(output_dir=temp_download_dir)
        assert downloader.output_dir == temp_download_dir
        assert downloader.quality == "bestaudio"
        assert downloader.format == "mp3"
        
        # Test URL validation
        valid_url = "https://www.youtube.com/watch?v=dQw4w9WgXcQ"
        invalid_url = "https://example.com/not-youtube"
        
        assert downloader.validate_url(valid_url) is True
        assert downloader.validate_url(invalid_url) is False
        
        # Test supported formats
        formats = downloader.get_supported_formats()
        assert isinstance(formats, list)
        assert "mp3" in formats
        assert "m4a" in formats
    
    @pytest.mark.integration
    def test_audio_downloader_with_mocking(self, temp_download_dir):
        """Test AudioDownloader with mocked yt-dlp."""
        downloader = AudioDownloader(output_dir=temp_download_dir)
        
        # Mock yt-dlp
        with patch('src.yt_audio_dl.audio_core.yt_dlp.YoutubeDL') as mock_ydl_class:
            mock_ydl_instance = Mock()
            mock_ydl_instance.extract_info.return_value = {
                'id': 'test',
                'title': 'Test Video',
                'uploader': 'Test Channel',
                'duration': 120
            }
            mock_ydl_class.return_value.__enter__.return_value = mock_ydl_instance
            
            # Create mock output file
            output_file = temp_download_dir / "Test Video.mp3"
            output_file.write_text("fake audio content")
            
            with patch('pathlib.Path.glob') as mock_glob:
                mock_glob.return_value = [output_file]
                
                # Test download
                result = downloader.download_audio("https://youtube.com/watch?v=test")
                
                # Verify result
                assert result.success is True
                assert result.status == DownloadStatus.COMPLETED
                assert result.title == "Test Video"
                assert result.artist == "Test Channel"
                assert result.duration_seconds == 120
    
    @pytest.mark.integration
    def test_audio_downloader_with_session(self, temp_download_dir, session_manager):
        """Test AudioDownloader with session management."""
        # Create session
        session_uuid = session_manager.create_session()
        
        # Create downloader
        downloader = AudioDownloader(output_dir=temp_download_dir)
        
        # Mock yt-dlp
        with patch('src.yt_audio_dl.audio_core.yt_dlp.YoutubeDL') as mock_ydl_class:
            mock_ydl_instance = Mock()
            mock_ydl_instance.extract_info.return_value = {
                'id': 'test',
                'title': 'Test Video',
                'uploader': 'Test Channel',
                'duration': 120
            }
            mock_ydl_class.return_value.__enter__.return_value = mock_ydl_instance
            
            # Create mock output file in session directory
            output_file = temp_download_dir / session_uuid / "test-job" / "audio" / "Test Video.mp3"
            output_file.parent.mkdir(parents=True, exist_ok=True)
            output_file.write_text("fake audio content")
            
            with patch('pathlib.Path.glob') as mock_glob:
                mock_glob.return_value = [output_file]
                
                # Test session-based download
                result = downloader.download_audio_with_session(
                    url="https://youtube.com/watch?v=test",
                    session_uuid=session_uuid,
                    job_uuid="test-job"
                )
                
                # Verify download succeeded
                assert result.success is True
                assert result.status == DownloadStatus.COMPLETED
                
                # Verify session directory was created
                session_audio_dir = temp_download_dir / session_uuid / "test-job" / "audio"
                assert session_audio_dir.exists()
    
    @pytest.mark.integration
    def test_progress_tracking_integration(self, temp_download_dir):
        """Test progress tracking integration."""
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
                
                # Verify download succeeded
                assert result.success is True
                
                # Verify progress hook was set
                assert mock_ydl_instance.add_progress_hook.called
    
    @pytest.mark.integration
    def test_multiple_sessions_integration(self, session_manager):
        """Test multiple sessions integration."""
        # Create multiple sessions
        sessions = []
        for i in range(3):
            session_uuid = session_manager.create_session()
            sessions.append(session_uuid)
            assert session_uuid is not None
        
        # Verify all sessions exist
        for session_uuid in sessions:
            session_info = session_manager.get_session_info(session_uuid)
            assert session_info is not None
            assert session_info["session_uuid"] == session_uuid
        
        # Verify session stats
        stats = session_manager.get_session_stats()
        assert stats["total_sessions"] >= 3
        assert stats["active_sessions"] >= 3
        
        # Verify active sessions list
        active_sessions = session_manager.get_active_sessions()
        assert len(active_sessions) >= 3
        for session_uuid in sessions:
            assert any(s["session_uuid"] == session_uuid for s in active_sessions)
    
    @pytest.mark.integration
    def test_error_handling_integration(self, temp_download_dir):
        """Test error handling integration."""
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
