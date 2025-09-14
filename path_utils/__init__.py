# my_project/path_utils/__init__.py
"""
Path utilities package for cross-platform path resolution and file operations.
"""

from .path_utils import (
    get_script_directories,
    resolve_path,
    ensure_directory_exists,
    create_download_structure,
    cleanup_empty_directories
)

__all__ = [
    'get_script_directories',
    'resolve_path',
    'ensure_directory_exists',
    'create_download_structure',
    'cleanup_empty_directories'
]