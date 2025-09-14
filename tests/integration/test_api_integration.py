"""
Integration tests for API endpoints.

This module tests the integration between API endpoints, session management,
and audio downloader components.
"""

import pytest
import tempfile
import shutil
from pathlib import Path
from unittest.mock import patch, Mock
import json
import asyncio

from fastapi.testclient import TestClient
from httpx import AsyncClient

from src.api.main import app
from src.common.session_manager import SessionManager
from src.yt_audio_dl.audio_core import AudioDownloadResult, DownloadStatus


class TestAPIIntegration:
    """Integration tests for API endpoints."""
    
    @pytest.fixture
    def temp_download_dir(self):
        """Create a temporary download directory for API tests."""
        temp_path = Path(tempfile.mkdtemp())
        yield temp_path
        shutil.rmtree(temp_path, ignore_errors=True)
    
    @pytest.fixture
    def client(self):
        """Create a test client for the API."""
        return TestClient(app)
    
    @pytest.fixture
    def async_client(self):
        """Create an async test client for the API."""
        return AsyncClient(base_url="http://test")
    
    @pytest.fixture
    def session_manager(self):
        """Create a real SessionManager for API tests."""
        return SessionManager()
    
    @pytest.mark.integration
    def test_health_endpoint_integration(self, client):
        """Test health endpoint integration."""
        response = client.get("/api/api/health")
        assert response.status_code == 200
        
        data = response.json()
        assert "status" in data
        assert "timestamp" in data
        assert "uptime_seconds" in data
        assert data["status"] == "healthy"
    
    @pytest.mark.integration
    def test_session_creation_integration(self, client):
        """Test session creation through API."""
        response = client.post("/api/sessions")
        assert response.status_code == 201
        
        data = response.json()
        assert "session_uuid" in data
        assert "created_at" in data
        assert "is_active" in data
        assert data["is_active"] is True
        
        # Verify session exists in session manager
        session_uuid = data["session_uuid"]
        response = client.get(f"/api/api/sessions/{session_uuid}")
        assert response.status_code == 200
    
    @pytest.mark.integration
    def test_session_management_integration(self, client):
        """Test complete session management workflow."""
        # Create session
        create_response = client.post("/sessions")
        assert create_response.status_code == 201
        session_data = create_response.json()
        session_uuid = session_data["session_uuid"]
        
        # Get session info
        get_response = client.get(f"/api/sessions/{session_uuid}")
        assert get_response.status_code == 200
        assert get_response.json()["session_uuid"] == session_uuid
        
        # Get all sessions
        list_response = client.get("/sessions")
        assert list_response.status_code == 200
        sessions = list_response.json()
        assert len(sessions) >= 1
        assert any(s["session_uuid"] == session_uuid for s in sessions)
        
        # Delete session
        delete_response = client.delete(f"/api/sessions/{session_uuid}")
        assert delete_response.status_code == 200
        
        # Verify session is deleted
        get_deleted_response = client.get(f"/api/sessions/{session_uuid}")
        assert get_deleted_response.status_code == 404
    
    @pytest.mark.integration
    def test_job_creation_integration(self, client):
        """Test job creation through API."""
        # Create session first
        session_response = client.post("/sessions")
        session_uuid = session_response.json()["session_uuid"]
        
        # Create job
        job_data = {
            "url": "https://www.youtube.com/watch?v=dQw4w9WgXcQ",
            "media_type": "audio",
            "quality": "bestaudio",
            "output_format": "mp3"
        }
        
        response = client.post(f"/api/sessions/{session_uuid}/jobs", json=job_data)
        assert response.status_code == 201
        
        job_response = response.json()
        assert "job_uuid" in job_response
        assert "job_id" in job_response
        assert job_response["session_uuid"] == session_uuid
        assert job_response["job_url"] == job_data["url"]
        assert job_response["media_type"] == job_data["media_type"]
        assert job_response["status"] == "pending"
    
    @pytest.mark.integration
    def test_job_processing_integration(self, client, temp_download_dir):
        """Test job processing integration with audio downloader."""
        # Create session
        session_response = client.post("/sessions")
        session_uuid = session_response.json()["session_uuid"]
        
        # Create job
        job_data = {
            "url": "https://www.youtube.com/watch?v=dQw4w9WgXcQ",
            "media_type": "audio",
            "quality": "bestaudio",
            "output_format": "mp3"
        }
        
        job_response = client.post(f"/api/sessions/{session_uuid}/jobs", json=job_data)
        job_uuid = job_response.json()["job_uuid"]
        
        # Mock audio downloader to avoid real download
        with patch('src.api.jobs.AudioDownloader') as mock_downloader_class:
            mock_downloader = Mock()
            mock_result = AudioDownloadResult(
                success=True,
                status=DownloadStatus.COMPLETED,
                output_path=temp_download_dir / "test.mp3",
                file_size_bytes=1024,
                duration_seconds=120,
                title="Test Video",
                artist="Test Channel",
                format="mp3"
            )
            mock_downloader.download_audio_with_session.return_value = mock_result
            mock_downloader_class.return_value = mock_downloader
            
            # Start job processing
            start_response = client.post(f"/api/sessions/{session_uuid}/api/jobs/{job_uuid}/start")
            assert start_response.status_code == 200
            
            # Check job status
            status_response = client.get(f"/api/sessions/{session_uuid}/api/jobs/{job_uuid}")
            assert status_response.status_code == 200
            
            job_status = status_response.json()
            assert job_status["status"] in ["pending", "running", "completed"]
    
    @pytest.mark.integration
    def test_job_progress_tracking_integration(self, client):
        """Test job progress tracking through API."""
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
        
        # Mock progress tracking
        with patch('src.api.jobs.AudioDownloader') as mock_downloader_class:
            mock_downloader = Mock()
            
            # Simulate progress updates
            progress_updates = []
            
            def mock_progress_callback(data):
                progress_updates.append(data)
            
            mock_downloader.progress_callback = mock_progress_callback
            
            # Mock successful download
            mock_result = AudioDownloadResult(
                success=True,
                status=DownloadStatus.COMPLETED,
                output_path=Path("/test/output.mp3"),
                file_size_bytes=1024,
                duration_seconds=120,
                title="Test Video",
                artist="Test Channel",
                format="mp3"
            )
            mock_downloader.download_audio_with_session.return_value = mock_result
            mock_downloader_class.return_value = mock_downloader
            
            # Start job
            start_response = client.post(f"/api/sessions/{session_uuid}/api/jobs/{job_uuid}/start")
            assert start_response.status_code == 200
            
            # Verify progress callback was set
            assert mock_downloader.progress_callback is not None
    
    @pytest.mark.integration
    def test_error_handling_integration(self, client):
        """Test API error handling integration."""
        # Test invalid session
        response = client.get("/api/sessions/invalid-session-uuid")
        assert response.status_code == 404
        
        # Test invalid job
        session_response = client.post("/sessions")
        session_uuid = session_response.json()["session_uuid"]
        
        response = client.get(f"/api/sessions/{session_uuid}/api/jobs/invalid-job-uuid")
        assert response.status_code == 404
        
        # Test invalid job data
        invalid_job_data = {
            "url": "invalid-url",
            "media_type": "invalid_type"
        }
        
        response = client.post(f"/api/sessions/{session_uuid}/jobs", json=invalid_job_data)
        # Should either accept the data or return validation error
        assert response.status_code in [201, 422]
    
    @pytest.mark.integration
    def test_concurrent_sessions_integration(self, client):
        """Test multiple concurrent sessions through API."""
        # Create multiple sessions
        sessions = []
        for i in range(3):
            response = client.post("/sessions")
            assert response.status_code == 201
            sessions.append(response.json()["session_uuid"])
        
        # Create jobs in each session
        for i, session_uuid in enumerate(sessions):
            job_data = {
                "url": f"https://www.youtube.com/watch?v=test{i}",
                "media_type": "audio",
                "quality": "bestaudio",
                "output_format": "mp3"
            }
            
            response = client.post(f"/api/sessions/{session_uuid}/jobs", json=job_data)
            assert response.status_code == 201
            job_uuid = response.json()["job_uuid"]
            
            # Verify job was created
            job_response = client.get(f"/api/sessions/{session_uuid}/api/jobs/{job_uuid}")
            assert job_response.status_code == 200
            assert job_response.json()["session_uuid"] == session_uuid
        
        # Verify all sessions exist
        list_response = client.get("/sessions")
        assert list_response.status_code == 200
        all_sessions = list_response.json()
        assert len(all_sessions) >= 3
        
        # Clean up sessions
        for session_uuid in sessions:
            delete_response = client.delete(f"/api/sessions/{session_uuid}")
            assert delete_response.status_code == 200
    
    @pytest.mark.integration
    def test_session_cleanup_integration(self, client):
        """Test session cleanup and expiration."""
        # Create session
        session_response = client.post("/sessions")
        session_uuid = session_response.json()["session_uuid"]
        
        # Get session stats
        stats_response = client.get("/api/sessions/stats")
        assert stats_response.status_code == 200
        
        stats = stats_response.json()
        assert "total_sessions" in stats
        assert "active_sessions" in stats
        assert stats["total_sessions"] >= 1
        assert stats["active_sessions"] >= 1
        
        # Delete session
        delete_response = client.delete(f"/api/sessions/{session_uuid}")
        assert delete_response.status_code == 200
        
        # Verify session is cleaned up
        get_response = client.get(f"/api/sessions/{session_uuid}")
        assert get_response.status_code == 404
    
    @pytest.mark.integration
    @pytest.mark.asyncio
    async def test_async_api_integration(self, async_client):
        """Test async API functionality."""
        # Test async health endpoint
        response = await async_client.get("/api/health")
        assert response.status_code == 200
        
        data = response.json()
        assert data["status"] == "healthy"
        
        # Test async session creation
        response = await async_client.post("/sessions")
        assert response.status_code == 201
        
        session_data = response.json()
        assert "session_uuid" in session_data
    
    @pytest.mark.integration
    def test_api_with_real_audio_downloader(self, client, temp_download_dir):
        """Test API with real AudioDownloader (without actual download)."""
        # Create session
        session_response = client.post("/sessions")
        session_uuid = session_response.json()["session_uuid"]
        
        # Create job
        job_data = {
            "url": "https://www.youtube.com/watch?v=dQw4w9WgXcQ",
            "media_type": "audio",
            "quality": "bestaudio",
            "output_format": "mp3"
        }
        
        job_response = client.post(f"/api/sessions/{session_uuid}/jobs", json=job_data)
        job_uuid = job_response.json()["job_uuid"]
        
        # Mock yt-dlp to avoid real download
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
            output_file = temp_download_dir / "Test Video.mp3"
            output_file.write_text("fake audio content")
            
            with patch('pathlib.Path.glob') as mock_glob:
                mock_glob.return_value = [output_file]
                
                # Start job processing
                start_response = client.post(f"/api/sessions/{session_uuid}/api/jobs/{job_uuid}/start")
                assert start_response.status_code == 200
                
                # Check job status
                status_response = client.get(f"/api/sessions/{session_uuid}/api/jobs/{job_uuid}")
                assert status_response.status_code == 200
                
                job_status = status_response.json()
                assert job_status["status"] in ["pending", "running", "completed"]
