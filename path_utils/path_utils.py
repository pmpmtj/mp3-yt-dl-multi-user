# my_project/path_utils/path_utils.py
"""
path_utils.py

Generic path resolution and file/directory utilities for cross-platform compatibility.
Handles both frozen (PyInstaller) and regular Python execution.
"""

import sys
import logging
from pathlib import Path
from typing import Union, Optional

# Initialize logger for this module
logger = logging.getLogger("path_utils")

def get_script_directories() -> tuple[Path, Path]:
    """
    Get SCRIPT_DIR and BASE_DIR handling both frozen (PyInstaller) and regular Python execution.
    
    Returns:
        Tuple of (SCRIPT_DIR, BASE_DIR)
    """
    if getattr(sys, 'frozen', False):
        # Running as compiled executable
        script_dir = Path(sys._MEIPASS)
        base_dir = Path(sys.executable).parent
        logger.debug("Running as compiled executable (PyInstaller)")
    else:
        # Running as regular Python script
        script_dir = Path(__file__).resolve().parent.parent
        base_dir = script_dir
        logger.debug("Running as regular Python script")
    
    logger.debug(f"Script directories: SCRIPT_DIR={script_dir}, BASE_DIR={base_dir}")
    return script_dir, base_dir


def resolve_path(path_input: Union[str, Path], base_dir: Optional[Path] = None) -> Path:
    """
    Resolve a path input to an absolute Path object.

    Args:
        path_input: String or Path object to resolve
        base_dir: Base directory to resolve relative paths against (defaults to SCRIPT_DIR from get_script_directories())

    Returns:
        Resolved absolute Path object
    """
    if base_dir is None:
        _, base_dir = get_script_directories()

    path = Path(path_input)

    # If already absolute, return as-is
    if path.is_absolute():
        return path

    # Resolve relative to base_dir
    return (base_dir / path).resolve()


def ensure_directory_exists(path: Union[str, Path], log_creation: bool = False) -> Path:
    """
    Ensure a directory exists, creating it if necessary.

    Args:
        path: Directory path to ensure exists
        log_creation: Whether to log directory creation

    Returns:
        Path object of the created/existing directory
    """
    dir_path = Path(path)
    dir_path.mkdir(parents=True, exist_ok=True)
    if log_creation:
        logger.debug(f"Created directory: {dir_path}")
    return dir_path


def create_download_structure(base_dir: Union[str, Path], session_uuid: str, 
                            job_uuid: str, media_type: Optional[str] = None) -> Path:
    """
    Create the download directory structure for multiuser support.
    
    Creates a hierarchical structure: base_dir/session_uuid/job_uuid/ or base_dir/session_uuid/job_uuid/media_type/
    
    Args:
        base_dir: Base downloads directory
        session_uuid: Session identifier (user session)
        job_uuid: Job identifier (unique per download job)
        media_type: Media type (audio, video, transcripts) or None for audio downloads
    
    Returns:
        Path to the created directory
        
    Example:
        create_download_structure("./downloads", "session-123", "job-456", "audio")
        # Returns: Path("./downloads/session-123/job-456/audio")
        create_download_structure("./downloads", "session-123", "job-456", None)
        # Returns: Path("./downloads/session-123/job-456")
    """
    if media_type is None:
        download_path = Path(base_dir) / session_uuid / job_uuid
    else:
        download_path = Path(base_dir) / session_uuid / job_uuid / media_type
    created_path = ensure_directory_exists(download_path, log_creation=True)
    logger.debug(f"Created download structure: {created_path}")
    return created_path


def cleanup_empty_directories(path: Union[str, Path]) -> None:
    """
    Clean up empty directories recursively.
    
    Args:
        path: Directory path to clean up
    """
    dir_path = Path(path)
    if not dir_path.exists() or not dir_path.is_dir():
        return
    
    # Remove empty directories recursively
    for item in dir_path.rglob('*'):
        if item.is_dir() and not any(item.iterdir()):
            item.rmdir()
            logger.debug(f"Removed empty directory: {item}")
    
    # Remove the root directory if it's now empty
    if dir_path.exists() and not any(dir_path.iterdir()):
        dir_path.rmdir()
        logger.debug(f"Removed empty root directory: {dir_path}")