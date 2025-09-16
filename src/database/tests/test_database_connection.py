"""
test_database_connection.py

Database connection test for PostgreSQL.
Tests connection using credentials from .env file and verifies database exists.

This script follows the project's architecture guidelines:
- Uses centralized logging from /src/common/logging_config.py
- Uses path utilities from /path_utils/path_utils.py
- Handles both frozen (PyInstaller) and regular Python execution
- Self-contained module with proper error handling
- Production-minded development approach
"""

import sys
from pathlib import Path
from typing import Optional, Dict, Any

# Add project root to Python path for imports
SCRIPT_DIR = Path(__file__).resolve().parent.parent.parent.parent
sys.path.insert(0, str(SCRIPT_DIR))

from src.common.logging_config import setup_logging, get_logger
from path_utils.path_utils import get_script_directories, resolve_path
from ..config.database_config import DatabaseConfig
from ..connection.connection_manager import DatabaseConnectionManager
from ..utils.database_utils import DatabaseUtils


class DatabaseConnectionTester:
    """
    Database connection tester for PostgreSQL.
    
    Tests database connectivity and verifies database existence using
    credentials from .env file.
    """
    
    def __init__(self):
        """Initialize the database connection tester."""
        # Setup logging
        setup_logging(debug_mode=True)
        self.logger = get_logger('db_test')
        
        # Get script directories
        self.script_dir, self.base_dir = get_script_directories()
        self.logger.debug(f"Script directories: SCRIPT_DIR={self.script_dir}, BASE_DIR={self.base_dir}")
        
        # Initialize database components
        self.config = None
        self.connection_manager = None
        self.db_utils = None
        
        self.logger.info("DatabaseConnectionTester initialized")
    
    def initialize_components(self) -> bool:
        """
        Initialize database components.
        
        Returns:
            bool: True if initialization successful, False otherwise
        """
        try:
            # Initialize configuration
            self.config = DatabaseConfig()
            if not self.config.load_config():
                self.logger.error("Failed to load database configuration")
                return False
            
            # Initialize connection manager
            self.connection_manager = DatabaseConnectionManager(self.config)
            
            # Initialize database utils
            self.db_utils = DatabaseUtils(self.config)
            
            self.logger.info("Database components initialized successfully")
            return True
            
        except Exception as e:
            self.logger.error(f"Failed to initialize database components: {e}")
            return False
    
    def test_connection(self) -> bool:
        """
        Test database connection.
        
        Returns:
            bool: True if connection successful, False otherwise
        """
        try:
            if not self.connection_manager:
                self.logger.error("Connection manager not initialized")
                return False
            
            self.logger.info("Testing database connection...")
            
            if not self.connection_manager.connect():
                self.logger.error("Failed to connect to database")
                return False
            
            # Test basic connectivity
            if not self.connection_manager.test_connection():
                self.logger.error("Connection test failed")
                return False
            
            # Get database information
            db_info = self.connection_manager.get_database_info()
            if db_info:
                self.logger.info("=== Database Information ===")
                self.logger.info(f"Database Name: {db_info['database_name']}")
                self.logger.info(f"Current User: {db_info['current_user']}")
                self.logger.info(f"Server Address: {db_info['server_address']}")
                self.logger.info(f"Server Port: {db_info['server_port']}")
                self.logger.info(f"PostgreSQL Version: {db_info['postgresql_version']}")
                self.logger.info("=== End Database Information ===")
            
            self.logger.info("Database connection test successful")
            return True
            
        except Exception as e:
            self.logger.error(f"Database connection test failed: {e}")
            return False
        finally:
            if self.connection_manager:
                self.connection_manager.disconnect()
    
    def test_database_operations(self) -> bool:
        """
        Test basic database operations.
        
        Returns:
            bool: True if operations successful, False otherwise
        """
        try:
            if not self.db_utils:
                self.logger.error("Database utils not initialized")
                return False
            
            self.logger.info("Testing database operations...")
            
            if not self.db_utils.run_database_operations_test():
                self.logger.error("Database operations test failed")
                return False
            
            self.logger.info("Database operations test successful")
            return True
            
        except Exception as e:
            self.logger.error(f"Database operations test failed: {e}")
            return False
    
    def test_database_initialization(self) -> bool:
        """
        Test database initialization.
        
        Returns:
            bool: True if initialization successful, False otherwise
        """
        try:
            if not self.db_utils:
                self.logger.error("Database utils not initialized")
                return False
            
            self.logger.info("Testing database initialization...")
            
            if not self.db_utils.initialize_database():
                self.logger.error("Database initialization failed")
                return False
            
            self.logger.info("Database initialization test successful")
            return True
            
        except Exception as e:
            self.logger.error(f"Database initialization test failed: {e}")
            return False
    
    def run_comprehensive_test(self) -> bool:
        """
        Run comprehensive database connection and functionality test.
        
        Returns:
            bool: True if all tests pass, False otherwise
        """
        self.logger.info("=== Starting Comprehensive Database Test ===")
        
        # Step 1: Initialize components
        if not self.initialize_components():
            self.logger.error("Failed to initialize components - aborting test")
            return False
        
        # Step 2: Test connection
        if not self.test_connection():
            self.logger.error("Database connection test failed - aborting test")
            return False
        
        # Step 3: Test database operations
        if not self.test_database_operations():
            self.logger.error("Database operations test failed")
            return False
        
        # Step 4: Test database initialization
        if not self.test_database_initialization():
            self.logger.error("Database initialization test failed")
            return False
        
        self.logger.info("=== Database Test Completed Successfully ===")
        return True
    
    def cleanup(self):
        """Clean up resources."""
        if self.connection_manager:
            try:
                self.connection_manager.disconnect()
                self.logger.debug("Database connection closed")
            except Exception as e:
                self.logger.warning(f"Error closing database connection: {e}")


def main():
    """Main function to run the database connection test."""
    print("PostgreSQL Database Connection Test")
    print("=" * 40)
    
    tester = DatabaseConnectionTester()
    
    try:
        success = tester.run_comprehensive_test()
        
        if success:
            print("\n✅ Database connection test PASSED")
            print("Database is accessible and functional")
            return 0
        else:
            print("\n❌ Database connection test FAILED")
            print("Check the logs for detailed error information")
            return 1
            
    except KeyboardInterrupt:
        print("\n\nTest interrupted by user")
        return 1
    except Exception as e:
        print(f"\nUnexpected error: {e}")
        return 1
    finally:
        tester.cleanup()


if __name__ == "__main__":
    sys.exit(main())
