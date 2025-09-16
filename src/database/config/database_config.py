"""
database_config.py

Database configuration management for PostgreSQL.
Loads and validates database configuration from environment variables.
"""

import os
import sys
from pathlib import Path
from typing import Optional, Dict, Any
from urllib.parse import urlparse
from dotenv import load_dotenv

# Add project root to Python path for imports
SCRIPT_DIR = Path(__file__).resolve().parent.parent.parent.parent
sys.path.insert(0, str(SCRIPT_DIR))

from src.common.logging_config import get_logger
from path_utils.path_utils import get_script_directories, resolve_path


class DatabaseConfig:
    """
    Database configuration manager.
    
    Handles loading and validation of database configuration from environment variables.
    Supports both frozen (PyInstaller) and regular Python execution.
    """
    
    def __init__(self, env_file_path: Optional[Path] = None):
        """
        Initialize database configuration.
        
        Args:
            env_file_path: Optional path to .env file. If None, will search for .env in project root.
        """
        self.logger = get_logger('db_config')
        
        # Get script directories
        self.script_dir, self.base_dir = get_script_directories()
        self.logger.debug(f"Script directories: SCRIPT_DIR={self.script_dir}, BASE_DIR={self.base_dir}")
        
        # Set environment file path
        if env_file_path is None:
            self.env_path = resolve_path('.env', self.base_dir)
        else:
            self.env_path = env_file_path
        
        self.logger.debug(f"Environment file path: {self.env_path}")
        
        # Database configuration
        self.database_url = None
        self.connection_params = {}
        self.is_loaded = False
        
        self.logger.info("DatabaseConfig initialized")
    
    def load_config(self) -> bool:
        """
        Load database configuration from environment file.
        
        Returns:
            bool: True if configuration loaded successfully, False otherwise
        """
        try:
            if not self.env_path.exists():
                self.logger.error(f"Environment file not found: {self.env_path}")
                return False
            
            # Load environment variables
            load_dotenv(self.env_path)
            
            # Get database URL
            self.database_url = os.getenv('DATABASE_URL')
            if not self.database_url:
                self.logger.error("DATABASE_URL not found in environment file")
                return False
            
            # Parse database URL
            if not self._parse_database_url():
                return False
            
            self.is_loaded = True
            self.logger.info("Database configuration loaded successfully")
            self.logger.debug(f"DATABASE_URL loaded: {self.database_url[:20]}...")
            return True
            
        except Exception as e:
            self.logger.error(f"Failed to load database configuration: {e}")
            return False
    
    def _parse_database_url(self) -> bool:
        """
        Parse the DATABASE_URL and extract connection parameters.
        
        Returns:
            bool: True if parsing successful, False otherwise
        """
        try:
            # Parse the database URL
            parsed_url = urlparse(self.database_url)
            
            # Extract connection parameters
            self.connection_params = {
                'host': parsed_url.hostname or 'localhost',
                'port': parsed_url.port or 5432,
                'user': parsed_url.username,
                'password': parsed_url.password,
                'dbname': parsed_url.path.lstrip('/') if parsed_url.path else 'postgres',
                'scheme': parsed_url.scheme
            }
            
            # Validate required parameters
            required_params = ['host', 'port', 'user', 'password', 'dbname']
            missing_params = [param for param in required_params if not self.connection_params.get(param)]
            
            if missing_params:
                self.logger.error(f"Missing required database parameters: {missing_params}")
                return False
            
            self.logger.info("Database URL parsed successfully")
            self.logger.debug(f"Connection parameters: {self._mask_password(self.connection_params)}")
            return True
            
        except Exception as e:
            self.logger.error(f"Failed to parse DATABASE_URL: {e}")
            return False
    
    def _mask_password(self, params: Dict[str, Any]) -> Dict[str, Any]:
        """Mask password in connection parameters for logging."""
        masked_params = params.copy()
        if 'password' in masked_params and masked_params['password']:
            masked_params['password'] = '*' * len(masked_params['password'])
        return masked_params
    
    def get_connection_string(self) -> str:
        """
        Get psycopg connection string.
        
        Returns:
            str: Connection string for psycopg
            
        Raises:
            RuntimeError: If configuration is not loaded
        """
        if not self.is_loaded:
            raise RuntimeError("Database configuration not loaded. Call load_config() first.")
        
        return (f"host={self.connection_params['host']} "
                f"port={self.connection_params['port']} "
                f"user={self.connection_params['user']} "
                f"password={self.connection_params['password']} "
                f"dbname={self.connection_params['dbname']}")
    
    def get_connection_params(self) -> Dict[str, Any]:
        """
        Get connection parameters dictionary.
        
        Returns:
            Dict[str, Any]: Connection parameters
            
        Raises:
            RuntimeError: If configuration is not loaded
        """
        if not self.is_loaded:
            raise RuntimeError("Database configuration not loaded. Call load_config() first.")
        
        return self.connection_params.copy()
    
    def get_database_url(self) -> str:
        """
        Get the original DATABASE_URL.
        
        Returns:
            str: Original DATABASE_URL
            
        Raises:
            RuntimeError: If configuration is not loaded
        """
        if not self.is_loaded:
            raise RuntimeError("Database configuration not loaded. Call load_config() first.")
        
        return self.database_url
    
    def validate_config(self) -> bool:
        """
        Validate database configuration.
        
        Returns:
            bool: True if configuration is valid, False otherwise
        """
        if not self.is_loaded:
            self.logger.error("Configuration not loaded")
            return False
        
        # Check if all required parameters are present
        required_params = ['host', 'port', 'user', 'password', 'dbname']
        missing_params = [param for param in required_params if not self.connection_params.get(param)]
        
        if missing_params:
            self.logger.error(f"Missing required parameters: {missing_params}")
            return False
        
        # Validate port is numeric
        try:
            port = int(self.connection_params['port'])
            if not (1 <= port <= 65535):
                self.logger.error(f"Invalid port number: {port}")
                return False
        except (ValueError, TypeError):
            self.logger.error(f"Port must be a number: {self.connection_params['port']}")
            return False
        
        self.logger.info("Database configuration validation passed")
        return True
    
    def get_config_summary(self) -> Dict[str, Any]:
        """
        Get configuration summary for logging/debugging.
        
        Returns:
            Dict[str, Any]: Configuration summary with masked password
        """
        if not self.is_loaded:
            return {"status": "not_loaded"}
        
        return {
            "status": "loaded",
            "database_url": self.database_url[:20] + "..." if self.database_url else None,
            "connection_params": self._mask_password(self.connection_params),
            "env_file": str(self.env_path)
        }
