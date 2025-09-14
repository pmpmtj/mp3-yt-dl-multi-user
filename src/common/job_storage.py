"""
Job storage abstraction for better testability.

This module provides an abstraction for job storage that can be easily
mocked and tested, replacing the global job storage dictionary.
"""

import logging
import time
from typing import Dict, Any, Optional, List
from abc import ABC, abstractmethod
from dataclasses import dataclass
from enum import Enum

# Initialize logger
logger = logging.getLogger("job_storage")


class JobStatus(Enum):
    """Job status enumeration."""
    PENDING = "pending"
    PROCESSING = "processing"
    COMPLETED = "completed"
    FAILED = "failed"
    CANCELLED = "cancelled"


@dataclass
class JobData:
    """Data structure for job information."""
    job_uuid: str
    job_id: str
    session_uuid: str
    job_url: str
    media_type: str
    quality: Optional[str] = None
    output_format: Optional[str] = None
    status: str = "pending"
    created_at: str = ""
    started_at: Optional[str] = None
    completed_at: Optional[str] = None
    progress_percent: Optional[float] = None
    error_message: Optional[str] = None
    output_path: Optional[str] = None
    file_size_bytes: Optional[int] = None
    
    def __post_init__(self):
        """Set default values after initialization."""
        if not self.created_at:
            self.created_at = time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime())


class IJobStorage(ABC):
    """Interface for job storage implementations."""
    
    @abstractmethod
    def store_job(self, job_id: str, job_data: JobData) -> None:
        """Store a job in the storage."""
        pass
    
    @abstractmethod
    def get_job(self, job_id: str) -> Optional[JobData]:
        """Get a job from the storage."""
        pass
    
    @abstractmethod
    def update_job(self, job_id: str, updates: Dict[str, Any]) -> bool:
        """Update a job in the storage."""
        pass
    
    @abstractmethod
    def delete_job(self, job_id: str) -> bool:
        """Delete a job from the storage."""
        pass
    
    @abstractmethod
    def list_jobs(self, session_uuid: Optional[str] = None) -> List[JobData]:
        """List jobs, optionally filtered by session."""
        pass
    
    @abstractmethod
    def get_job_count(self) -> int:
        """Get the total number of jobs."""
        pass
    
    @abstractmethod
    def clear_all(self) -> None:
        """Clear all jobs from storage."""
        pass


class InMemoryJobStorage(IJobStorage):
    """
    In-memory job storage implementation.
    
    This implementation stores jobs in memory using a dictionary.
    Suitable for development and testing.
    """
    
    def __init__(self):
        """Initialize the in-memory job storage."""
        self._jobs: Dict[str, JobData] = {}
        logger.debug("InMemoryJobStorage initialized")
    
    def store_job(self, job_id: str, job_data: JobData) -> None:
        """Store a job in memory."""
        self._jobs[job_id] = job_data
        logger.debug(f"Stored job {job_id} in memory storage")
    
    def get_job(self, job_id: str) -> Optional[JobData]:
        """Get a job from memory."""
        job_data = self._jobs.get(job_id)
        if job_data:
            logger.debug(f"Retrieved job {job_id} from memory storage")
        return job_data
    
    def update_job(self, job_id: str, updates: Dict[str, Any]) -> bool:
        """Update a job in memory."""
        if job_id not in self._jobs:
            logger.warning(f"Cannot update job {job_id}: not found")
            return False
        
        job_data = self._jobs[job_id]
        
        # Update fields
        for key, value in updates.items():
            if hasattr(job_data, key):
                setattr(job_data, key, value)
            else:
                logger.warning(f"Unknown field '{key}' for job {job_id}")
        
        logger.debug(f"Updated job {job_id} in memory storage")
        return True
    
    def delete_job(self, job_id: str) -> bool:
        """Delete a job from memory."""
        if job_id in self._jobs:
            del self._jobs[job_id]
            logger.debug(f"Deleted job {job_id} from memory storage")
            return True
        else:
            logger.warning(f"Cannot delete job {job_id}: not found")
            return False
    
    def list_jobs(self, session_uuid: Optional[str] = None) -> List[JobData]:
        """List jobs, optionally filtered by session."""
        jobs = list(self._jobs.values())
        
        if session_uuid:
            jobs = [job for job in jobs if job.session_uuid == session_uuid]
        
        logger.debug(f"Listed {len(jobs)} jobs (filtered by session: {session_uuid is not None})")
        return jobs
    
    def get_job_count(self) -> int:
        """Get the total number of jobs."""
        count = len(self._jobs)
        logger.debug(f"Job count: {count}")
        return count
    
    def clear_all(self) -> None:
        """Clear all jobs from memory."""
        self._jobs.clear()
        logger.info("Cleared all jobs from memory storage")


class JobStorageProvider:
    """
    Provider for job storage with dependency injection support.
    
    This class manages the job storage implementation and can be easily
    mocked for testing.
    """
    
    def __init__(self, storage: Optional[IJobStorage] = None):
        """
        Initialize the job storage provider.
        
        Args:
            storage: Optional custom storage implementation
        """
        self._storage = storage or InMemoryJobStorage()
        logger.debug("JobStorageProvider initialized")
    
    def get_storage(self) -> IJobStorage:
        """Get the job storage instance."""
        return self._storage
    
    def configure_storage(self, storage: IJobStorage) -> None:
        """Configure a new storage implementation."""
        self._storage = storage
        logger.info("JobStorageProvider reconfigured with new storage")
    
    def is_test_mode(self) -> bool:
        """Check if using test storage."""
        return isinstance(self._storage, InMemoryJobStorage)


# Global job storage provider
_job_storage_provider: Optional[JobStorageProvider] = None
_provider_lock = None


def get_job_storage_provider() -> JobStorageProvider:
    """Get the global job storage provider."""
    global _job_storage_provider, _provider_lock
    
    if _job_storage_provider is None:
        import threading
        if _provider_lock is None:
            _provider_lock = threading.Lock()
        
        with _provider_lock:
            if _job_storage_provider is None:
                _job_storage_provider = JobStorageProvider()
                logger.info("Created global JobStorageProvider instance")
    
    return _job_storage_provider


def get_job_storage() -> IJobStorage:
    """Get the job storage from the global provider."""
    return get_job_storage_provider().get_storage()


def configure_job_storage_for_testing(storage: Optional[IJobStorage] = None) -> None:
    """
    Configure job storage for testing.
    
    Args:
        storage: Optional custom storage for testing
    """
    provider = get_job_storage_provider()
    test_storage = storage or InMemoryJobStorage()
    provider.configure_storage(test_storage)
    logger.info("JobStorage configured for testing")


def reset_job_storage() -> None:
    """Reset the job storage (useful for testing)."""
    provider = get_job_storage_provider()
    storage = provider.get_storage()
    storage.clear_all()
    logger.info("JobStorage reset")


class JobIDGenerator:
    """Generator for unique job IDs."""
    
    def __init__(self):
        """Initialize the job ID generator."""
        self._counter = 0
    
    def generate_job_id(self) -> str:
        """Generate a unique job ID."""
        self._counter += 1
        timestamp = int(time.time())
        return f"job-{self._counter}-{timestamp}"
    
    def reset(self) -> None:
        """Reset the counter (useful for testing)."""
        self._counter = 0


# Global job ID generator
_job_id_generator: Optional[JobIDGenerator] = None


def get_job_id_generator() -> JobIDGenerator:
    """Get the global job ID generator."""
    global _job_id_generator
    
    if _job_id_generator is None:
        _job_id_generator = JobIDGenerator()
        logger.debug("Created global JobIDGenerator instance")
    
    return _job_id_generator


def generate_job_id() -> str:
    """Generate a unique job ID using the global generator."""
    return get_job_id_generator().generate_job_id()


def reset_job_id_generator() -> None:
    """Reset the job ID generator (useful for testing)."""
    global _job_id_generator
    if _job_id_generator:
        _job_id_generator.reset()
    logger.info("JobIDGenerator reset")
