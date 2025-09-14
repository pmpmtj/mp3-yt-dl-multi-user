"""
Pytest configuration and shared fixtures.

This module provides common test fixtures, configuration,
and utilities used across all test modules.
"""

import pytest
import tempfile
import shutil
from pathlib import Path
from unittest.mock import Mock, MagicMock
from typing import Dict, Any, Optional

# Add src directory to path for imports
import sys
from pathlib import Path as PathLib
TEST_DIR = PathLib(__file__).resolve().parent
PROJECT_ROOT = TEST_DIR.parent
sys.path.insert(0, str(PROJECT_ROOT / "src"))

from src.common.session_manager import SessionManager, SessionInfo
from src.common.user_context import UserContext
from src.yt_audio_dl.audio_core import AudioDownloader


@pytest.fixture
def temp_dir():
    """Create a temporary directory for test files."""
    temp_path = Path(tempfile.mkdtemp())
    yield temp_path
    shutil.rmtree(temp_path, ignore_errors=True)


@pytest.fixture
def temp_download_dir(temp_dir):
    """Create a temporary download directory."""
    download_dir = temp_dir / "downloads"
    download_dir.mkdir()
    return download_dir


@pytest.fixture
def mock_session_manager():
    """Create a mock session manager for testing."""
    mock_manager = Mock(spec=SessionManager)
    mock_manager._sessions = {}
    mock_manager._lock = Mock()
    
    # Configure mock methods
    mock_manager.create_session.return_value = "test-session-uuid"
    mock_manager.get_session.return_value = None
    mock_manager.get_session_info.return_value = None
    mock_manager.start_job.return_value = True
    mock_manager.complete_job.return_value = None
    mock_manager.fail_job.return_value = None
    mock_manager.get_active_sessions.return_value = []
    mock_manager.get_session_stats.return_value = {
        'total_sessions': 0,
        'active_sessions': 0,
        'total_jobs': 0,
        'active_jobs': 0,
        'total_storage_bytes': 0,
        'max_concurrent_sessions': 100,
        'max_jobs_per_session': 10
    }
    mock_manager.cleanup_expired_sessions.return_value = 0
    
    return mock_manager


@pytest.fixture
def mock_user_context():
    """Create a mock user context for testing."""
    mock_context = Mock(spec=UserContext)
    mock_context.session_uuid = "test-session-uuid"
    mock_context._job_sessions = {}
    
    # Configure mock methods
    mock_context.get_session_id.return_value = "test-session-uuid"
    mock_context.get_url_uuid.return_value = "test-job-uuid"
    mock_context.get_audio_download_path.return_value = Path("/test/audio/path")
    mock_context.get_video_download_path.return_value = Path("/test/video/path")
    mock_context.get_transcript_download_path.return_value = Path("/test/transcript/path")
    mock_context.get_session_info.return_value = {
        'session_uuid': 'test-session-uuid',
        'total_jobs': 0,
        'job_urls': [],
        'job_uuids': []
    }
    mock_context.get_job_info.return_value = {
        'job_url': 'https://test.com',
        'job_uuid': 'test-job-uuid',
        'session_uuid': 'test-session-uuid'
    }
    
    return mock_context


@pytest.fixture
def mock_audio_downloader():
    """Create a mock audio downloader for testing."""
    mock_downloader = Mock(spec=AudioDownloader)
    
    # Configure mock methods
    mock_downloader.validate_url.return_value = True
    mock_downloader.get_video_info.return_value = {
        'id': 'test-video-id',
        'title': 'Test Video',
        'uploader': 'Test Channel',
        'duration': 120,
        'view_count': 1000
    }
    mock_downloader.download_audio.return_value = Mock(
        success=True,
        output_path=Path("/test/output.mp3"),
        file_size_bytes=1024*1024,
        title="Test Video",
        artist="Test Channel"
    )
    mock_downloader.download_audio_with_session.return_value = Mock(
        success=True,
        output_path=Path("/test/output.mp3"),
        file_size_bytes=1024*1024,
        title="Test Video",
        artist="Test Channel"
    )
    mock_downloader.get_supported_formats.return_value = ['mp3', 'm4a', 'wav']
    
    return mock_downloader


@pytest.fixture
def sample_session_info():
    """Create sample session info data for testing."""
    return {
        'session_uuid': 'test-session-uuid',
        'created_at': '2024-01-15T10:30:00Z',
        'last_activity': '2024-01-15T10:30:00Z',
        'is_active': True,
        'total_jobs': 0,
        'active_jobs': 0,
        'completed_jobs': 0,
        'failed_jobs': 0,
        'storage_used_bytes': 0,
        'age_hours': 0.0
    }


@pytest.fixture
def sample_job_data():
    """Create sample job data for testing."""
    return {
        'job_uuid': 'test-job-uuid',
        'job_id': 'job-1-1234567890',
        'session_uuid': 'test-session-uuid',
        'job_url': 'https://www.youtube.com/watch?v=test',
        'media_type': 'audio',
        'quality': 'bestaudio',
        'output_format': 'mp3',
        'status': 'pending',
        'created_at': '2024-01-15T10:30:00Z',
        'started_at': None,
        'completed_at': None,
        'progress_percent': None,
        'error_message': None,
        'output_path': None,
        'file_size_bytes': None
    }


@pytest.fixture
def mock_yt_dlp():
    """Create a mock yt-dlp for testing."""
    mock_ydl = Mock()
    mock_ydl.extract_info.return_value = {
        'id': 'test-video-id',
        'title': 'Test Video Title',
        'uploader': 'Test Channel',
        'duration': 180,
        'view_count': 5000,
        'description': 'Test video description',
        'thumbnail': 'https://test.com/thumbnail.jpg',
        'webpage_url': 'https://www.youtube.com/watch?v=test',
        'formats': []
    }
    return mock_ydl


@pytest.fixture
def mock_progress_callback():
    """Create a mock progress callback for testing."""
    callback = Mock()
    return callback


@pytest.fixture
def test_urls():
    """Provide test YouTube URLs for testing."""
    return {
        'valid': 'https://www.youtube.com/watch?v=dQw4w9WgXcQ',
        'invalid': 'https://example.com/not-youtube',
        'malformed': 'not-a-url',
        'empty': ''
    }


@pytest.fixture
def mock_file_system(temp_dir):
    """Create a mock file system for testing."""
    # Create test directory structure
    downloads_dir = temp_dir / "downloads"
    downloads_dir.mkdir()
    
    # Create some test files
    test_file = downloads_dir / "test.mp3"
    test_file.write_text("fake audio content")
    
    return {
        'base_dir': temp_dir,
        'downloads_dir': downloads_dir,
        'test_file': test_file
    }


@pytest.fixture
def mock_logger():
    """Create a mock logger for testing."""
    mock_logger = Mock()
    mock_logger.debug = Mock()
    mock_logger.info = Mock()
    mock_logger.warning = Mock()
    mock_logger.error = Mock()
    mock_logger.critical = Mock()
    return mock_logger


@pytest.fixture(autouse=True)
def disable_logging():
    """Disable logging during tests to reduce noise."""
    import logging
    logging.disable(logging.CRITICAL)
    yield
    logging.disable(logging.NOTSET)


@pytest.fixture
def async_client():
    """Create an async HTTP client for testing FastAPI endpoints."""
    from httpx import AsyncClient
    from src.api.main import app
    
    return AsyncClient(app=app, base_url="http://test")


# Test configuration
pytest_plugins = ["pytest_asyncio"]

# Configure pytest
def pytest_configure(config):
    """Configure pytest with custom markers."""
    config.addinivalue_line(
        "markers", "unit: mark test as a unit test"
    )
    config.addinivalue_line(
        "markers", "integration: mark test as an integration test"
    )
    config.addinivalue_line(
        "markers", "slow: mark test as slow running"
    )
    config.addinivalue_line(
        "markers", "requires_network: mark test as requiring network access"
    )


# Test utilities
class TestUtils:
    """Utility functions for testing."""
    
    @staticmethod
    def create_temp_file(content: str = "test content", suffix: str = ".txt") -> Path:
        """Create a temporary file with content."""
        import tempfile
        temp_file = Path(tempfile.mktemp(suffix=suffix))
        temp_file.write_text(content)
        return temp_file
    
    @staticmethod
    def assert_path_exists(path: Path, should_exist: bool = True):
        """Assert that a path exists or doesn't exist."""
        if should_exist:
            assert path.exists(), f"Expected path to exist: {path}"
        else:
            assert not path.exists(), f"Expected path to not exist: {path}"
    
    @staticmethod
    def create_mock_response(status_code: int = 200, json_data: Optional[Dict[str, Any]] = None):
        """Create a mock HTTP response."""
        mock_response = Mock()
        mock_response.status_code = status_code
        mock_response.json.return_value = json_data or {}
        return mock_response


@pytest.fixture
def test_utils():
    """Provide test utilities."""
    return TestUtils
