"""
test_database_operations.py

Database operations test for PostgreSQL.
Tests various database operations including CRUD operations, migrations, and utilities.

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
from ..utils.migration_utils import MigrationUtils
from ..models.user_model import UserModel
from ..models.session_model import SessionModel


class DatabaseOperationsTester:
    """
    Database operations tester for PostgreSQL.
    
    Tests various database operations including:
    - CRUD operations
    - Model operations
    - Migration operations
    - Utility operations
    """
    
    def __init__(self):
        """Initialize the database operations tester."""
        # Setup logging
        setup_logging(debug_mode=True)
        self.logger = get_logger('db_ops_test')
        
        # Get script directories
        self.script_dir, self.base_dir = get_script_directories()
        self.logger.debug(f"Script directories: SCRIPT_DIR={self.script_dir}, BASE_DIR={self.base_dir}")
        
        # Initialize database components
        self.config = None
        self.connection_manager = None
        self.db_utils = None
        self.migration_utils = None
        self.user_model = None
        self.session_model = None
        
        self.logger.info("DatabaseOperationsTester initialized")
    
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
            
            # Initialize migration utils
            self.migration_utils = MigrationUtils(self.config)
            
            # Initialize models
            self.user_model = UserModel()
            self.session_model = SessionModel()
            
            self.logger.info("Database components initialized successfully")
            return True
            
        except Exception as e:
            self.logger.error(f"Failed to initialize database components: {e}")
            return False
    
    def test_model_operations(self) -> bool:
        """
        Test model operations.
        
        Returns:
            bool: True if operations successful, False otherwise
        """
        try:
            if not self.connection_manager or not self.user_model or not self.session_model:
                self.logger.error("Components not initialized")
                return False
            
            self.logger.info("Testing model operations...")
            
            if not self.connection_manager.connect():
                self.logger.error("Failed to connect to database")
                return False
            
            # Test user model operations
            self.logger.info("Testing user model operations...")
            
            # Create test user data
            test_user = self.user_model.create_user(
                username="test_user",
                email="test@example.com",
                password_hash="hashed_password_123",
                first_name="Test",
                last_name="User"
            )
            
            if not test_user:
                self.logger.error("Failed to create test user data")
                return False
            
            self.logger.debug(f"Created test user: {test_user['username']}")
            
            # Test session model operations
            self.logger.info("Testing session model operations...")
            
            # Create test session data
            test_session = self.session_model.create_session(
                user_id=test_user['id'],
                session_token="test_session_token_12345678901234567890",
                ip_address="127.0.0.1",
                user_agent="Test Agent"
            )
            
            if not test_session:
                self.logger.error("Failed to create test session data")
                return False
            
            self.logger.debug(f"Created test session: {test_session['session_token'][:10]}...")
            
            self.logger.info("Model operations test successful")
            return True
            
        except Exception as e:
            self.logger.error(f"Model operations test failed: {e}")
            return False
        finally:
            if self.connection_manager:
                self.connection_manager.disconnect()
    
    def test_crud_operations(self) -> bool:
        """
        Test CRUD operations.
        
        Returns:
            bool: True if operations successful, False otherwise
        """
        try:
            if not self.connection_manager:
                self.logger.error("Connection manager not initialized")
                return False
            
            self.logger.info("Testing CRUD operations...")
            
            if not self.connection_manager.connect():
                self.logger.error("Failed to connect to database")
                return False
            
            # Test table creation
            test_table = "test_crud_table"
            create_sql = f"""
                CREATE TABLE IF NOT EXISTS {test_table} (
                    id SERIAL PRIMARY KEY,
                    name VARCHAR(100) NOT NULL,
                    email VARCHAR(100) UNIQUE NOT NULL,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                );
            """
            
            if not self.connection_manager.execute_command(create_sql):
                self.logger.error("Failed to create test table")
                return False
            
            self.logger.debug(f"Created test table: {test_table}")
            
            # Test INSERT
            insert_sql = f"""
                INSERT INTO {test_table} (name, email) 
                VALUES (%s, %s) RETURNING id;
            """
            
            with self.connection_manager.get_cursor() as cur:
                cur.execute(insert_sql, ("Test User", "test@example.com"))
                test_id = cur.fetchone()[0]
                self.connection_manager.connection.commit()
                self.logger.debug(f"Inserted record with ID: {test_id}")
            
            # Test SELECT
            select_sql = f"SELECT * FROM {test_table} WHERE id = %s;"
            results = self.connection_manager.execute_query(select_sql, (test_id,))
            if not results:
                self.logger.error("SELECT operation failed")
                return False
            
            self.logger.debug(f"Selected record: {results[0]}")
            
            # Test UPDATE
            update_sql = f"UPDATE {test_table} SET name = %s WHERE id = %s;"
            if not self.connection_manager.execute_command(update_sql, ("Updated User", test_id)):
                self.logger.error("UPDATE operation failed")
                return False
            
            self.logger.debug(f"Updated record ID: {test_id}")
            
            # Test DELETE
            delete_sql = f"DELETE FROM {test_table} WHERE id = %s;"
            if not self.connection_manager.execute_command(delete_sql, (test_id,)):
                self.logger.error("DELETE operation failed")
                return False
            
            self.logger.debug(f"Deleted record ID: {test_id}")
            
            # Clean up test table
            drop_sql = f"DROP TABLE IF EXISTS {test_table};"
            if not self.connection_manager.execute_command(drop_sql):
                self.logger.warning("Failed to drop test table")
            
            self.logger.info("CRUD operations test successful")
            return True
            
        except Exception as e:
            self.logger.error(f"CRUD operations test failed: {e}")
            return False
        finally:
            if self.connection_manager:
                self.connection_manager.disconnect()
    
    def test_migration_operations(self) -> bool:
        """
        Test migration operations.
        
        Returns:
            bool: True if operations successful, False otherwise
        """
        try:
            if not self.migration_utils:
                self.logger.error("Migration utils not initialized")
                return False
            
            self.logger.info("Testing migration operations...")
            
            # Test initial migration
            if not self.migration_utils.run_initial_migration():
                self.logger.error("Initial migration failed")
                return False
            
            self.logger.info("Initial migration completed")
            
            # Test migration status
            status = self.migration_utils.get_migration_status()
            self.logger.info(f"Migration status: {status}")
            
            # Test migration validation
            if not self.migration_utils.validate_migrations():
                self.logger.error("Migration validation failed")
                return False
            
            self.logger.info("Migration validation passed")
            
            self.logger.info("Migration operations test successful")
            return True
            
        except Exception as e:
            self.logger.error(f"Migration operations test failed: {e}")
            return False
    
    def test_utility_operations(self) -> bool:
        """
        Test utility operations.
        
        Returns:
            bool: True if operations successful, False otherwise
        """
        try:
            if not self.db_utils:
                self.logger.error("Database utils not initialized")
                return False
            
            self.logger.info("Testing utility operations...")
            
            # Test database stats
            stats = self.db_utils.get_database_stats()
            if stats:
                self.logger.info(f"Database stats: {stats}")
            
            # Test table info
            table_info = self.db_utils.get_table_info("users")
            if table_info:
                self.logger.info(f"Users table info: {len(table_info)} columns")
            
            # Test schema validation
            if not self.db_utils.validate_database_schema():
                self.logger.error("Schema validation failed")
                return False
            
            self.logger.info("Schema validation passed")
            
            self.logger.info("Utility operations test successful")
            return True
            
        except Exception as e:
            self.logger.error(f"Utility operations test failed: {e}")
            return False
    
    def run_comprehensive_test(self) -> bool:
        """
        Run comprehensive database operations test.
        
        Returns:
            bool: True if all tests pass, False otherwise
        """
        self.logger.info("=== Starting Comprehensive Database Operations Test ===")
        
        # Step 1: Initialize components
        if not self.initialize_components():
            self.logger.error("Failed to initialize components - aborting test")
            return False
        
        # Step 2: Test model operations
        if not self.test_model_operations():
            self.logger.error("Model operations test failed")
            return False
        
        # Step 3: Test CRUD operations
        if not self.test_crud_operations():
            self.logger.error("CRUD operations test failed")
            return False
        
        # Step 4: Test migration operations
        if not self.test_migration_operations():
            self.logger.error("Migration operations test failed")
            return False
        
        # Step 5: Test utility operations
        if not self.test_utility_operations():
            self.logger.error("Utility operations test failed")
            return False
        
        self.logger.info("=== Database Operations Test Completed Successfully ===")
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
    """Main function to run the database operations test."""
    print("PostgreSQL Database Operations Test")
    print("=" * 40)
    
    tester = DatabaseOperationsTester()
    
    try:
        success = tester.run_comprehensive_test()
        
        if success:
            print("\n✅ Database operations test PASSED")
            print("All database operations are working correctly")
            return 0
        else:
            print("\n❌ Database operations test FAILED")
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
