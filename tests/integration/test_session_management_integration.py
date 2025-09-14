"""
Integration tests for session management functionality.

This module tests the integration between SessionManager, UserContext,
and other components with real session operations.
"""

import pytest
import tempfile
import shutil
from pathlib import Path
from unittest.mock import patch, Mock
import time
import threading
import asyncio

from src.common.session_manager import SessionManager, SessionInfo
from src.common.user_context import UserContext
from src.yt_audio_dl.audio_core import AudioDownloader, AudioDownloadResult, DownloadStatus


class TestSessionManagementIntegration:
    """Integration tests for session management components."""
    
    @pytest.fixture
    def temp_download_dir(self):
        """Create a temporary download directory for session tests."""
        temp_path = Path(tempfile.mkdtemp())
        yield temp_path
        shutil.rmtree(temp_path, ignore_errors=True)
    
    @pytest.fixture
    def session_manager(self):
        """Create a real SessionManager for integration tests."""
        return SessionManager()
    
    @pytest.mark.integration
    def test_session_creation_and_management_integration(self, session_manager):
        """Test complete session lifecycle integration."""
        # Create session
        session_uuid = session_manager.create_session()
        assert session_uuid is not None
        assert isinstance(session_uuid, str)
        
        # Verify session exists
        session_info = session_manager.get_session_info(session_uuid)
        assert session_info is not None
        assert session_info.session_uuid == session_uuid
        assert session_info.is_active is True
        
        # Get session stats
        stats = session_manager.get_session_stats()
        assert stats['total_sessions'] >= 1
        assert stats['active_sessions'] >= 1
        
        # Create user context with session
        user_context = UserContext(session_uuid=session_uuid)
        assert user_context.session_uuid == session_uuid
        
        # Verify session is tracked
        session_info_after_context = session_manager.get_session_info(session_uuid)
        assert session_info_after_context is not None
    
    @pytest.mark.integration
    def test_multiple_sessions_integration(self, session_manager):
        """Test multiple concurrent sessions integration."""
        # Create multiple sessions
        sessions = []
        for i in range(5):
            session_uuid = session_manager.create_session()
            sessions.append(session_uuid)
            assert session_uuid is not None
        
        # Verify all sessions exist
        for session_uuid in sessions:
            session_info = session_manager.get_session_info(session_uuid)
            assert session_info is not None
            assert session_info.session_uuid == session_uuid
        
        # Get all active sessions
        active_sessions = session_manager.get_active_sessions()
        assert len(active_sessions) >= 5
        
        # Verify session stats
        stats = session_manager.get_session_stats()
        assert stats['total_sessions'] >= 5
        assert stats['active_sessions'] >= 5
    
    @pytest.mark.integration
    def test_session_with_job_management_integration(self, session_manager, temp_download_dir):
        """Test session integration with job management."""
        # Create session
        session_uuid = session_manager.create_session()
        
        # Create user context
        user_context = UserContext(session_uuid=session_uuid)
        
        # Create audio downloader
        downloader = AudioDownloader(output_dir=temp_download_dir)
        
        # Mock yt-dlp for job processing
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
            output_file = temp_download_dir / session_uuid / "test-job" / "audio" / "Test Video.mp3"
            output_file.parent.mkdir(parents=True, exist_ok=True)
            output_file.write_text("fake audio content")
            
            with patch('pathlib.Path.glob') as mock_glob:
                mock_glob.return_value = [output_file]
                
                # Start job
                job_started = session_manager.start_job(
                    session_uuid=session_uuid,
                    job_uuid="test-job",
                    job_url="https://youtube.com/watch?v=test",
                    media_type="audio"
                )
                assert job_started is True
                
                # Verify job is tracked in session
                session_info = session_manager.get_session_info(session_uuid)
                assert session_info.total_jobs >= 1
                assert session_info.active_jobs >= 1
                
                # Complete job
                session_manager.complete_job(
                    session_uuid=session_uuid,
                    job_uuid="test-job",
                    output_path=output_file,
                    file_size_bytes=1024
                )
                
                # Verify job completion
                session_info_after = session_manager.get_session_info(session_uuid)
                assert session_info_after.completed_jobs >= 1
                assert session_info_after.active_jobs == 0
    
    @pytest.mark.integration
    def test_session_cleanup_integration(self, session_manager):
        """Test session cleanup and expiration integration."""
        # Create session
        session_uuid = session_manager.create_session()
        
        # Verify session exists
        session_info = session_manager.get_session_info(session_uuid)
        assert session_info is not None
        
        # Simulate session expiration by manually setting old timestamp
        with patch.object(session_manager, '_sessions') as mock_sessions:
            # Create expired session info
            expired_session = SessionInfo(
                session_uuid=session_uuid,
                created_at=time.time() - 3600,  # 1 hour ago
                last_activity=time.time() - 3600,
                is_active=True,
                total_jobs=0,
                active_jobs=0,
                completed_jobs=0,
                failed_jobs=0,
                storage_used_bytes=0,
                age_hours=1.0
            )
            mock_sessions.__getitem__.return_value = expired_session
            
            # Cleanup expired sessions
            cleaned_count = session_manager.cleanup_expired_sessions()
            assert cleaned_count >= 0
    
    @pytest.mark.integration
    def test_concurrent_session_operations_integration(self, session_manager):
        """Test concurrent session operations integration."""
        sessions = []
        errors = []
        
        def create_session_worker():
            try:
                session_uuid = session_manager.create_session()
                sessions.append(session_uuid)
            except Exception as e:
                errors.append(e)
        
        # Create multiple sessions concurrently
        threads = []
        for _ in range(10):
            thread = threading.Thread(target=create_session_worker)
            threads.append(thread)
            thread.start()
        
        # Wait for all threads to complete
        for thread in threads:
            thread.join()
        
        # Verify no errors occurred
        assert len(errors) == 0
        
        # Verify all sessions were created
        assert len(sessions) == 10
        
        # Verify all sessions exist
        for session_uuid in sessions:
            session_info = session_manager.get_session_info(session_uuid)
            assert session_info is not None
            assert session_info.session_uuid == session_uuid
    
    @pytest.mark.integration
    def test_session_storage_tracking_integration(self, session_manager, temp_download_dir):
        """Test session storage usage tracking integration."""
        # Create session
        session_uuid = session_manager.create_session()
        
        # Create user context
        user_context = UserContext(session_uuid=session_uuid)
        
        # Simulate file creation in session directory
        session_dir = temp_download_dir / session_uuid
        session_dir.mkdir(parents=True, exist_ok=True)
        
        # Create test files
        test_files = []
        total_size = 0
        for i in range(3):
            file_path = session_dir / f"test_file_{i}.mp3"
            content = f"fake audio content {i}" * 100  # Make it larger
            file_path.write_text(content)
            test_files.append(file_path)
            total_size += file_path.stat().st_size
        
        # Update session storage
        session_manager.update_session_storage(session_uuid, total_size)
        
        # Verify storage tracking
        session_info = session_manager.get_session_info(session_uuid)
        assert session_info.storage_used_bytes == total_size
        
        # Get session stats
        stats = session_manager.get_session_stats()
        assert stats['total_storage_bytes'] >= total_size
    
    @pytest.mark.integration
    def test_session_with_audio_downloader_integration(self, session_manager, temp_download_dir):
        """Test session integration with AudioDownloader."""
        # Create session
        session_uuid = session_manager.create_session()
        
        # Create audio downloader
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
    def test_session_error_handling_integration(self, session_manager):
        """Test session error handling integration."""
        # Test invalid session operations
        invalid_session_uuid = "invalid-session-uuid"
        
        # Get non-existent session
        session_info = session_manager.get_session_info(invalid_session_uuid)
        assert session_info is None
        
        # Start job in non-existent session
        job_started = session_manager.start_job(
            session_uuid=invalid_session_uuid,
            job_uuid="test-job",
            job_url="https://youtube.com/watch?v=test",
            media_type="audio"
        )
        assert job_started is False
        
        # Complete job in non-existent session
        session_manager.complete_job(
            session_uuid=invalid_session_uuid,
            job_uuid="test-job",
            output_path=Path("/fake/path"),
            file_size_bytes=1024
        )
        # Should not raise exception
    
    @pytest.mark.integration
    def test_session_with_user_context_integration(self, session_manager):
        """Test session integration with UserContext."""
        # Create session
        session_uuid = session_manager.create_session()
        
        # Create user context with session
        user_context = UserContext(session_uuid=session_uuid)
        
        # Test URL UUID generation
        test_url = "https://youtube.com/watch?v=test"
        job_uuid = user_context.get_url_uuid(test_url)
        assert job_uuid is not None
        assert isinstance(job_uuid, str)
        
        # Test path generation
        audio_path = user_context.get_audio_download_path(test_url)
        assert audio_path is not None
        assert isinstance(audio_path, Path)
        
        # Test session info retrieval
        session_info = user_context.get_session_info()
        assert session_info is not None
        assert session_info['session_uuid'] == session_uuid
        
        # Test job info retrieval
        job_info = user_context.get_job_info(test_url)
        assert job_info is not None
        assert job_info['job_url'] == test_url
        assert job_info['session_uuid'] == session_uuid
    
    @pytest.mark.integration
    def test_session_lifecycle_with_jobs_integration(self, session_manager, temp_download_dir):
        """Test complete session lifecycle with multiple jobs."""
        # Create session
        session_uuid = session_manager.create_session()
        
        # Create multiple jobs
        job_uuids = []
        for i in range(3):
            job_uuid = f"job-{i}"
            job_uuids.append(job_uuid)
            
            # Start job
            job_started = session_manager.start_job(
                session_uuid=session_uuid,
                job_uuid=job_uuid,
                job_url=f"https://youtube.com/watch?v=test{i}",
                media_type="audio"
            )
            assert job_started is True
        
        # Verify session stats
        session_info = session_manager.get_session_info(session_uuid)
        assert session_info.total_jobs == 3
        assert session_info.active_jobs == 3
        
        # Complete some jobs
        for i, job_uuid in enumerate(job_uuids[:2]):
            # Create mock output file
            output_file = temp_download_dir / f"output_{i}.mp3"
            output_file.write_text(f"fake content {i}")
            
            session_manager.complete_job(
                session_uuid=session_uuid,
                job_uuid=job_uuid,
                output_path=output_file,
                file_size_bytes=1024 * (i + 1)
            )
        
        # Fail one job
        session_manager.fail_job(
            session_uuid=session_uuid,
            job_uuid=job_uuids[2],
            error_message="Test error"
        )
        
        # Verify final session stats
        final_session_info = session_manager.get_session_info(session_uuid)
        assert final_session_info.total_jobs == 3
        assert final_session_info.completed_jobs == 2
        assert final_session_info.failed_jobs == 1
        assert final_session_info.active_jobs == 0
        assert final_session_info.storage_used_bytes > 0
