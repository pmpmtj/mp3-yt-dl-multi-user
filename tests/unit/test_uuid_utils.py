"""
Unit tests for UUID utilities.

This module tests the UUID generation functionality with various scenarios
including edge cases and validation.
"""

import pytest
from unittest.mock import patch
from src.common.uuid_utils import (
    generate_session_uuid, 
    generate_job_uuid, 
    generate_uuid,
    generate_video_uuid
)


class TestUUIDGeneration:
    """Test UUID generation functions."""
    
    @pytest.mark.unit
    def test_generate_session_uuid_returns_string(self):
        """Test that generate_session_uuid returns a string."""
        uuid = generate_session_uuid()
        assert isinstance(uuid, str)
        assert len(uuid) > 0
    
    @pytest.mark.unit
    def test_generate_session_uuid_returns_unique_values(self):
        """Test that generate_session_uuid returns unique values."""
        uuids = [generate_session_uuid() for _ in range(10)]
        assert len(set(uuids)) == 10, "All UUIDs should be unique"
    
    @pytest.mark.unit
    def test_generate_job_uuid_returns_string(self):
        """Test that generate_job_uuid returns a string."""
        uuid = generate_job_uuid()
        assert isinstance(uuid, str)
        assert len(uuid) > 0
    
    @pytest.mark.unit
    def test_generate_job_uuid_returns_unique_values(self):
        """Test that generate_job_uuid returns unique values."""
        uuids = [generate_job_uuid() for _ in range(10)]
        assert len(set(uuids)) == 10, "All UUIDs should be unique"
    
    @pytest.mark.unit
    def test_generate_uuid_without_prefix(self):
        """Test generate_uuid without prefix."""
        uuid = generate_uuid()
        assert isinstance(uuid, str)
        assert len(uuid) > 0
    
    @pytest.mark.unit
    def test_generate_uuid_with_prefix(self):
        """Test generate_uuid with prefix."""
        prefix = "test"
        uuid = generate_uuid(prefix=prefix)
        assert isinstance(uuid, str)
        assert uuid.startswith(f"{prefix}-")
        assert len(uuid) > len(prefix) + 1
    
    @pytest.mark.unit
    def test_generate_uuid_with_none_prefix(self):
        """Test generate_uuid with None prefix."""
        uuid = generate_uuid(prefix=None)
        assert isinstance(uuid, str)
        assert len(uuid) > 0
    
    @pytest.mark.unit
    def test_generate_video_uuid_deprecated(self):
        """Test that generate_video_uuid still works (deprecated)."""
        uuid = generate_video_uuid()
        assert isinstance(uuid, str)
        assert len(uuid) > 0
    
    @pytest.mark.unit
    def test_uuid_format_is_valid(self):
        """Test that generated UUIDs have valid format."""
        uuid = generate_session_uuid()
        # UUID4 format: 8-4-4-4-12 hexadecimal digits
        parts = uuid.split('-')
        assert len(parts) == 5, f"Invalid UUID format: {uuid}"
        assert all(len(part) == expected for part, expected in zip(parts, [8, 4, 4, 4, 12])), \
            f"Invalid UUID format: {uuid}"
    
    @pytest.mark.unit
    def test_generate_multiple_types_unique(self):
        """Test that different UUID types generate unique values."""
        session_uuid = generate_session_uuid()
        job_uuid = generate_job_uuid()
        video_uuid = generate_video_uuid()
        prefixed_uuid = generate_uuid("test")
        
        uuids = [session_uuid, job_uuid, video_uuid, prefixed_uuid]
        assert len(set(uuids)) == 4, "All different UUID types should be unique"
    
    @pytest.mark.unit
    @patch('src.common.uuid_utils.logger')
    def test_uuid_generation_logs_debug(self, mock_logger):
        """Test that UUID generation logs debug messages."""
        generate_session_uuid()
        mock_logger.debug.assert_called()
    
    @pytest.mark.unit
    def test_uuid_consistency(self):
        """Test that UUID generation is consistent."""
        # Generate multiple UUIDs and ensure they're all strings
        uuids = [
            generate_session_uuid(),
            generate_job_uuid(),
            generate_uuid(),
            generate_uuid("test"),
            generate_video_uuid()
        ]
        
        for uuid in uuids:
            assert isinstance(uuid, str)
            assert len(uuid) > 0
            assert '-' in uuid  # All should contain hyphens (UUID format)
    
    @pytest.mark.unit
    def test_large_batch_uniqueness(self):
        """Test uniqueness with a larger batch of UUIDs."""
        batch_size = 100
        uuids = [generate_session_uuid() for _ in range(batch_size)]
        
        assert len(set(uuids)) == batch_size, f"Expected {batch_size} unique UUIDs"
        
        # Also test that they're all different from job UUIDs
        job_uuids = [generate_job_uuid() for _ in range(batch_size)]
        assert len(set(job_uuids)) == batch_size, f"Expected {batch_size} unique job UUIDs"
        
        # Ensure no overlap between session and job UUIDs
        all_uuids = uuids + job_uuids
        assert len(set(all_uuids)) == batch_size * 2, "No overlap between session and job UUIDs"
