"""
Database Package

Independent database package for PostgreSQL operations.
Provides connection management, models, and utilities for database operations.

This package follows the project's architecture guidelines:
- Uses centralized logging from /src/common/logging_config.py
- Uses path utilities from /path_utils/path_utils.py
- Handles both frozen (PyInstaller) and regular Python execution
- Self-contained modules with proper error handling
- Production-minded development approach
"""

from .config.database_config import DatabaseConfig
from .connection.connection_manager import DatabaseConnectionManager
from .utils.database_utils import DatabaseUtils

__version__ = "1.0.0"
__author__ = "YT-DL Project"

# Package exports
__all__ = [
    "DatabaseConfig",
    "DatabaseConnectionManager", 
    "DatabaseUtils"
]
