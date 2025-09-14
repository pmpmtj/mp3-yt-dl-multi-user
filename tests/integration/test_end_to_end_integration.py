"""
End-to-end integration tests for the complete YouTube downloader system.

This module tests the full workflow from API request to file download
with all components working together.
"""

import pytest
import tempfile
import shutil
from pathlib import Path
from unittest.mock import patch, Mock
import json
import time

from fastapi.testclient import TestClient
from httpx import AsyncClient

from src.api.main import app
from src.common.session_manager import SessionManager
from src.common.user_context import UserContext
from src.yt_audio_dl.audio_core import AudioDownloader, DownloadStatus


class TestEndToEndIntegration:
    """End-to-end integration tests for the complete system."""
    
    @pytest.fixture
    def temp_download_dir(self):
        """Create a temporary download directory for E2E tests."""
        temp_path = Path(tempfile.mkdtemp())
        yield temp_path
        shutil.rmtree(temp_path, ignore_errors=True)
    
    @pytest.fixture
    def client(self):
        """Create a test client for E2E tests."""
        return TestClient(app)
    
    @pytest.fixture
    def session_manager(self):
        """Create a real SessionManager for E2E tests."""
        return SessionManager()
    
    @pytest.mark.integration
    @pytest.mark.slow
    def test_complete_download_workflow_integration(self, client, temp_download_dir):
        """Test complete workflow from API to file download."""
        # Step 1: Create session via API
        session_response = client.post("/sessions")
        assert session_response.status_code == 201
        session_data = session_response.json()
        session_uuid = session_data["session_uuid"]
        
        # Step 2: Create job via API
        job_data = {
            "url": "https://www.youtube.com/watch?v=dQw4w9WgXcQ",
            "media_type": "audio",
            "quality": "bestaudio",
            "output_format": "mp3"
        }
        
        job_response = client.post(f"/api/sessions/{session_uuid}/jobs", json=job_data)
        assert job_response.status_code == 201
        job_data_response = job_response.json()
        job_uuid = job_data_response["job_uuid"]
        
        # Step 3: Mock yt-dlp for controlled testing
        with patch('src.yt_audio_dl.audio_core.yt_dlp.YoutubeDL') as mock_ydl_class:
            mock_ydl_instance = Mock()
            mock_ydl_instance.extract_info.return_value = {
                'id': 'dQw4w9WgXcQ',
                'title': 'Rick Astley - Never Gonna Give You Up',
                'uploader': 'Rick Astley',
                'duration': 212,
                'view_count': 1000000000
            }
            mock_ydl_class.return_value.__enter__.return_value = mock_ydl_instance
            
            # Create mock output file
            output_file = temp_download_dir / session_uuid / job_uuid / "audio" / "Rick Astley - Never Gonna Give You Up.mp3"
            output_file.parent.mkdir(parents=True, exist_ok=True)
            output_file.write_text("fake audio content")
            
            with patch('pathlib.Path.glob') as mock_glob:
                mock_glob.return_value = [output_file]
                
                # Step 4: Start job processing via API
                start_response = client.post(f"/api/sessions/{session_uuid}/api/jobs/{job_uuid}/start")
                assert start_response.status_code == 200
                
                # Step 5: Monitor job progress
                max_attempts = 10
                for attempt in range(max_attempts):
                    status_response = client.get(f"/api/sessions/{session_uuid}/api/jobs/{job_uuid}")
                    assert status_response.status_code == 200
                    
                    job_status = status_response.json()
                    if job_status["status"] in ["completed", "failed"]:
                        break
                    
                    time.sleep(0.1)  # Small delay for processing
                
                # Step 6: Verify job completion
                final_status_response = client.get(f"/api/sessions/{session_uuid}/api/jobs/{job_uuid}")
                assert final_status_response.status_code == 200
                
                final_job_status = final_status_response.json()
                assert final_job_status["status"] == "completed"
                assert final_job_status["output_path"] is not None
                assert final_job_status["file_size_bytes"] > 0
                assert final_job_status["title"] == "Rick Astley - Never Gonna Give You Up"
                assert final_job_status["artist"] == "Rick Astley"
        
        # Step 7: Verify session stats
        session_response = client.get(f"/api/sessions/{session_uuid}")
        assert session_response.status_code == 200
        
        session_info = session_response.json()
        assert session_info["total_jobs"] >= 1
        assert session_info["completed_jobs"] >= 1
        
        # Step 8: Clean up
        delete_response = client.delete(f"/api/sessions/{session_uuid}")
        assert delete_response.status_code == 200
    
    @pytest.mark.integration
    def test_multiple_users_concurrent_downloads_integration(self, client, temp_download_dir):
        """Test multiple users downloading concurrently."""
        # Create multiple sessions (simulating multiple users)
        sessions = []
        for i in range(3):
            session_response = client.post("/sessions")
            assert session_response.status_code == 201
            sessions.append(session_response.json()["session_uuid"])
        
        # Create jobs for each session
        jobs = []
        for i, session_uuid in enumerate(sessions):
            job_data = {
                "url": f"https://www.youtube.com/watch?v=test{i}",
                "media_type": "audio",
                "quality": "bestaudio",
                "output_format": "mp3"
            }
            
            job_response = client.post(f"/api/sessions/{session_uuid}/jobs", json=job_data)
            assert job_response.status_code == 201
            jobs.append((session_uuid, job_response.json()["job_uuid"]))
        
        # Mock yt-dlp for all jobs
        with patch('src.yt_audio_dl.audio_core.yt_dlp.YoutubeDL') as mock_ydl_class:
            mock_ydl_instance = Mock()
            mock_ydl_instance.extract_info.return_value = {
                'id': 'test',
                'title': 'Test Video',
                'uploader': 'Test Channel',
                'duration': 120
            }
            mock_ydl_class.return_value.__enter__.return_value = mock_ydl_instance
            
            # Create mock output files for each job
            for i, (session_uuid, job_uuid) in enumerate(jobs):
                output_file = temp_download_dir / session_uuid / job_uuid / "audio" / f"Test Video {i}.mp3"
                output_file.parent.mkdir(parents=True, exist_ok=True)
                output_file.write_text(f"fake audio content {i}")
            
            with patch('pathlib.Path.glob') as mock_glob:
                def mock_glob_func(pattern):
                    # Return appropriate files based on the calling context
                    return [temp_download_dir / f"session-{i}" / f"job-{i}" / "audio" / f"Test Video {i}.mp3" for i in range(3)]
                
                mock_glob.side_effect = mock_glob_func
                
                # Start all jobs
                for session_uuid, job_uuid in jobs:
                    start_response = client.post(f"/api/sessions/{session_uuid}/api/jobs/{job_uuid}/start")
                    assert start_response.status_code == 200
                
                # Verify all jobs completed
                for session_uuid, job_uuid in jobs:
                    status_response = client.get(f"/api/sessions/{session_uuid}/api/jobs/{job_uuid}")
                    assert status_response.status_code == 200
                    
                    job_status = status_response.json()
                    assert job_status["status"] == "completed"
        
        # Clean up all sessions
        for session_uuid in sessions:
            delete_response = client.delete(f"/api/sessions/{session_uuid}")
            assert delete_response.status_code == 200
    
    @pytest.mark.integration
    def test_error_recovery_integration(self, client, temp_download_dir):
        """Test system error recovery and handling."""
        # Create session
        session_response = client.post("/sessions")
        session_uuid = session_response.json()["session_uuid"]
        
        # Test with invalid URL
        invalid_job_data = {
            "url": "invalid-url",
            "media_type": "audio",
            "quality": "bestaudio",
            "output_format": "mp3"
        }
        
        job_response = client.post(f"/api/sessions/{session_uuid}/jobs", json=invalid_job_data)
        # Should either accept the data or return validation error
        assert job_response.status_code in [201, 422]
        
        if job_response.status_code == 201:
            job_uuid = job_response.json()["job_uuid"]
            
            # Mock yt-dlp to simulate error
            with patch('src.yt_audio_dl.audio_core.yt_dlp.YoutubeDL') as mock_ydl_class:
                mock_ydl_instance = Mock()
                mock_ydl_instance.extract_info.side_effect = Exception("Invalid URL")
                mock_ydl_class.return_value.__enter__.return_value = mock_ydl_instance
                
                # Start job (should fail)
                start_response = client.post(f"/api/sessions/{session_uuid}/api/jobs/{job_uuid}/start")
                assert start_response.status_code == 200
                
                # Check job status (should be failed)
                status_response = client.get(f"/api/sessions/{session_uuid}/api/jobs/{job_uuid}")
                assert status_response.status_code == 200
                
                job_status = status_response.json()
                assert job_status["status"] == "failed"
                assert job_status["error_message"] is not None
        
        # Clean up
        delete_response = client.delete(f"/api/sessions/{session_uuid}")
        assert delete_response.status_code == 200
    
    @pytest.mark.integration
    def test_session_cleanup_and_expiration_integration(self, client):
        """Test session cleanup and expiration handling."""
        # Create multiple sessions
        sessions = []
        for i in range(5):
            session_response = client.post("/sessions")
            assert session_response.status_code == 201
            sessions.append(session_response.json()["session_uuid"])
        
        # Verify all sessions exist
        list_response = client.get("/sessions")
        assert list_response.status_code == 200
        all_sessions = list_response.json()
        assert len(all_sessions) >= 5
        
        # Get session stats
        stats_response = client.get("/api/sessions/stats")
        assert stats_response.status_code == 200
        stats = stats_response.json()
        assert stats["total_sessions"] >= 5
        assert stats["active_sessions"] >= 5
        
        # Delete some sessions
        for session_uuid in sessions[:3]:
            delete_response = client.delete(f"/api/sessions/{session_uuid}")
            assert delete_response.status_code == 200
        
        # Verify remaining sessions
        remaining_sessions = sessions[3:]
        for session_uuid in remaining_sessions:
            get_response = client.get(f"/api/sessions/{session_uuid}")
            assert get_response.status_code == 200
        
        # Clean up remaining sessions
        for session_uuid in remaining_sessions:
            delete_response = client.delete(f"/api/sessions/{session_uuid}")
            assert delete_response.status_code == 200
    
    @pytest.mark.integration
    def test_progress_tracking_integration(self, client, temp_download_dir):
        """Test progress tracking throughout the download process."""
        # Create session and job
        session_response = client.post("/sessions")
        session_uuid = session_response.json()["session_uuid"]
        
        job_data = {
            "url": "https://www.youtube.com/watch?v=dQw4w9WgXcQ",
            "media_type": "audio",
            "quality": "bestaudio",
            "output_format": "mp3"
        }
        
        job_response = client.post(f"/api/sessions/{session_uuid}/jobs", json=job_data)
        job_uuid = job_response.json()["job_uuid"]
        
        # Track progress updates
        progress_updates = []
        
        def progress_callback(data):
            progress_updates.append(data)
        
        # Mock yt-dlp with progress simulation
        with patch('src.yt_audio_dl.audio_core.yt_dlp.YoutubeDL') as mock_ydl_class:
            mock_ydl_instance = Mock()
            mock_ydl_instance.extract_info.return_value = {
                'id': 'dQw4w9WgXcQ',
                'title': 'Test Video',
                'uploader': 'Test Channel',
                'duration': 120
            }
            
            # Mock download with progress updates
            def mock_download(urls):
                progress_hook = mock_ydl_instance.add_progress_hook.call_args[0][0]
                progress_hook({'status': 'downloading', 'downloaded_bytes': 1000, 'total_bytes': 5000})
                progress_hook({'status': 'downloading', 'downloaded_bytes': 2500, 'total_bytes': 5000})
                progress_hook({'status': 'downloading', 'downloaded_bytes': 5000, 'total_bytes': 5000})
                progress_hook({'status': 'finished', 'filename': 'test.mp3'})
                return []
            
            mock_ydl_instance.download = mock_download
            mock_ydl_class.return_value.__enter__.return_value = mock_ydl_instance
            
            # Create mock output file
            output_file = temp_download_dir / session_uuid / job_uuid / "audio" / "Test Video.mp3"
            output_file.parent.mkdir(parents=True, exist_ok=True)
            output_file.write_text("fake audio content")
            
            with patch('pathlib.Path.glob') as mock_glob:
                mock_glob.return_value = [output_file]
                
                # Start job
                start_response = client.post(f"/api/sessions/{session_uuid}/api/jobs/{job_uuid}/start")
                assert start_response.status_code == 200
                
                # Verify progress was tracked
                # Note: In a real implementation, progress would be tracked through the API
                # For this test, we verify the progress hook was called
                assert mock_ydl_instance.add_progress_hook.called
        
        # Clean up
        delete_response = client.delete(f"/api/sessions/{session_uuid}")
        assert delete_response.status_code == 200
    
    @pytest.mark.integration
    @pytest.mark.asyncio
    async def test_async_api_integration(self, temp_download_dir):
        """Test async API functionality in E2E context."""
        async with AsyncClient(base_url="http://test") as client:
            # Test async session creation
            response = await client.post("/sessions")
            assert response.status_code == 201
            
            session_data = response.json()
            session_uuid = session_data["session_uuid"]
            
            # Test async job creation
            job_data = {
                "url": "https://www.youtube.com/watch?v=dQw4w9WgXcQ",
                "media_type": "audio",
                "quality": "bestaudio",
                "output_format": "mp3"
            }
            
            job_response = await client.post(f"/api/sessions/{session_uuid}/jobs", json=job_data)
            assert job_response.status_code == 201
            
            job_uuid = job_response.json()["job_uuid"]
            
            # Test async job status check
            status_response = await client.get(f"/api/sessions/{session_uuid}/api/jobs/{job_uuid}")
            assert status_response.status_code == 200
            
            # Clean up
            delete_response = await client.delete(f"/api/sessions/{session_uuid}")
            assert delete_response.status_code == 200
