"""
Unit tests for user context management.

This module tests the UserContext class with various scenarios including
session management, path generation, and job tracking.
"""

import pytest
from unittest.mock import Mock, patch, MagicMock
from pathlib import Path
from src.common.user_context import UserContext, create_user_context, get_default_user_context


class TestUserContext:
    """Test UserContext functionality."""
    
    @pytest.mark.unit
    def test_user_context_initialization_with_session_uuid(self, mock_session_manager):
        """Test UserContext initialization with provided session UUID."""
        session_uuid = "test-session-123"
        context = UserContext(session_uuid=session_uuid)
        
        assert context.session_uuid == session_uuid
        assert context._job_sessions == {}
        assert context._path_generator is not None
    
    @pytest.mark.unit
    def test_user_context_initialization_without_session_uuid(self):
        """Test UserContext initialization without session UUID."""
        with patch('src.common.user_context.generate_session_uuid') as mock_generate:
            mock_generate.return_value = "generated-session-456"
            
            context = UserContext()
            
            assert context.session_uuid == "generated-session-456"
            mock_generate.assert_called_once()
    
    @pytest.mark.unit
    def test_user_context_with_custom_path_generator(self):
        """Test UserContext with custom path generator."""
        def custom_path_generator(session_uuid, job_uuid, media_type, base_dir=None):
            return Path("/custom/path") / session_uuid / job_uuid / media_type
        
        context = UserContext(path_generator=custom_path_generator)
        
        # Test that custom path generator is used
        path = context._path_generator("session", "job", "audio")
        assert path == Path("/custom/path/session/job/audio")
    
    @pytest.mark.unit
    def test_user_context_with_base_download_dir(self):
        """Test UserContext with custom base download directory."""
        base_dir = Path("/custom/downloads")
        context = UserContext(base_download_dir=base_dir)
        
        # Test default path generator with custom base dir
        path = context._default_path_generator("session", "job", "audio", base_dir)
        expected_path = base_dir / "session" / "job" / "audio"
        assert path == expected_path
    
    @pytest.mark.unit
    def test_get_session_id(self):
        """Test getting session ID."""
        session_uuid = "test-session-789"
        context = UserContext(session_uuid=session_uuid)
        
        assert context.get_session_id() == session_uuid
    
    @pytest.mark.unit
    def test_get_url_uuid_creates_new_uuid(self):
        """Test that get_url_uuid creates new UUID for new URL."""
        context = UserContext()
        test_url = "https://youtube.com/watch?v=test"
        
        with patch('src.common.user_context.generate_job_uuid') as mock_generate:
            mock_generate.return_value = "generated-job-uuid"
            
            job_uuid = context.get_url_uuid(test_url)
            
            assert job_uuid == "generated-job-uuid"
            assert test_url in context._job_sessions
            assert context._job_sessions[test_url] == "generated-job-uuid"
    
    @pytest.mark.unit
    def test_get_url_uuid_returns_existing_uuid(self):
        """Test that get_url_uuid returns existing UUID for known URL."""
        context = UserContext()
        test_url = "https://youtube.com/watch?v=test"
        existing_uuid = "existing-job-uuid"
        
        # Manually set existing UUID
        context._job_sessions[test_url] = existing_uuid
        
        job_uuid = context.get_url_uuid(test_url)
        
        assert job_uuid == existing_uuid
    
    @pytest.mark.unit
    def test_get_audio_download_path(self):
        """Test getting audio download path."""
        context = UserContext()
        test_url = "https://youtube.com/watch?v=test"
        
        with patch.object(context, 'get_url_uuid') as mock_get_uuid:
            mock_get_uuid.return_value = "test-job-uuid"
            
            path = context.get_audio_download_path(test_url)
            
            # Should call the path generator with correct parameters
            context._path_generator.assert_called_with(
                context.session_uuid, "test-job-uuid", "audio", None
            )
    
    @pytest.mark.unit
    def test_get_video_download_path(self):
        """Test getting video download path."""
        context = UserContext()
        test_url = "https://youtube.com/watch?v=test"
        
        with patch.object(context, 'get_url_uuid') as mock_get_uuid:
            mock_get_uuid.return_value = "test-job-uuid"
            
            path = context.get_video_download_path(test_url)
            
            context._path_generator.assert_called_with(
                context.session_uuid, "test-job-uuid", "video", None
            )
    
    @pytest.mark.unit
    def test_get_transcript_download_path(self):
        """Test getting transcript download path."""
        context = UserContext()
        test_url = "https://youtube.com/watch?v=test"
        
        with patch.object(context, 'get_url_uuid') as mock_get_uuid:
            mock_get_uuid.return_value = "test-job-uuid"
            
            path = context.get_transcript_download_path(test_url)
            
            context._path_generator.assert_called_with(
                context.session_uuid, "test-job-uuid", "transcripts", None
            )
    
    @pytest.mark.unit
    def test_get_session_info(self):
        """Test getting session information."""
        context = UserContext(session_uuid="test-session")
        
        # Add some job sessions
        context._job_sessions = {
            "url1": "uuid1",
            "url2": "uuid2"
        }
        
        info = context.get_session_info()
        
        assert info['session_uuid'] == "test-session"
        assert info['total_jobs'] == 2
        assert info['job_urls'] == ["url1", "url2"]
        assert info['job_uuids'] == ["uuid1", "uuid2"]
    
    @pytest.mark.unit
    def test_get_job_info(self):
        """Test getting job information."""
        context = UserContext(session_uuid="test-session")
        test_url = "https://youtube.com/watch?v=test"
        
        with patch.object(context, 'get_url_uuid') as mock_get_uuid:
            mock_get_uuid.return_value = "test-job-uuid"
            
            job_info = context.get_job_info(test_url)
            
            assert job_info['job_url'] == test_url
            assert job_info['job_uuid'] == "test-job-uuid"
            assert job_info['session_uuid'] == "test-session"
    
    @pytest.mark.unit
    def test_default_path_generator(self):
        """Test the default path generator."""
        context = UserContext()
        base_dir = Path("/test/downloads")
        
        path = context._default_path_generator("session123", "job456", "audio", base_dir)
        
        expected = base_dir / "session123" / "job456" / "audio"
        assert path == expected
    
    @pytest.mark.unit
    def test_default_path_generator_with_none_base_dir(self):
        """Test default path generator with None base directory."""
        context = UserContext()
        
        path = context._default_path_generator("session123", "job456", "audio", None)
        
        expected = Path("./downloads") / "session123" / "job456" / "audio"
        assert path == expected
    
    @pytest.mark.unit
    def test_multiple_jobs_same_url(self):
        """Test that same URL always returns same job UUID."""
        context = UserContext()
        test_url = "https://youtube.com/watch?v=test"
        
        # Get UUID multiple times
        uuid1 = context.get_url_uuid(test_url)
        uuid2 = context.get_url_uuid(test_url)
        uuid3 = context.get_url_uuid(test_url)
        
        assert uuid1 == uuid2 == uuid3
        assert len(context._job_sessions) == 1
    
    @pytest.mark.unit
    def test_multiple_urls_different_uuids(self):
        """Test that different URLs get different job UUIDs."""
        context = UserContext()
        urls = [
            "https://youtube.com/watch?v=test1",
            "https://youtube.com/watch?v=test2",
            "https://youtube.com/watch?v=test3"
        ]
        
        uuids = [context.get_url_uuid(url) for url in urls]
        
        # All UUIDs should be different
        assert len(set(uuids)) == 3
        assert len(context._job_sessions) == 3


class TestUserContextFactory:
    """Test UserContext factory functions."""
    
    @pytest.mark.unit
    def test_create_user_context_with_parameters(self):
        """Test create_user_context with parameters."""
        session_uuid = "test-session"
        base_dir = Path("/test/downloads")
        
        context = create_user_context(
            session_uuid=session_uuid,
            base_download_dir=base_dir
        )
        
        assert isinstance(context, UserContext)
        assert context.session_uuid == session_uuid
        assert context._base_download_dir == base_dir
    
    @pytest.mark.unit
    def test_create_user_context_without_parameters(self):
        """Test create_user_context without parameters."""
        context = create_user_context()
        
        assert isinstance(context, UserContext)
        assert context.session_uuid is not None
    
    @pytest.mark.unit
    def test_get_default_user_context(self):
        """Test get_default_user_context."""
        context = get_default_user_context()
        
        assert isinstance(context, UserContext)
        assert context.session_uuid is not None
    
    @pytest.mark.unit
    def test_create_user_context_with_custom_path_generator(self):
        """Test create_user_context with custom path generator."""
        def custom_generator(session_uuid, job_uuid, media_type, base_dir=None):
            return Path("/custom") / media_type
        
        context = create_user_context(path_generator=custom_generator)
        
        assert context._path_generator == custom_generator
    
    @pytest.mark.unit
    @patch('src.common.user_context.logger')
    def test_user_context_logging(self, mock_logger):
        """Test that UserContext logs initialization."""
        UserContext(session_uuid="test-session")
        mock_logger.info.assert_called()
