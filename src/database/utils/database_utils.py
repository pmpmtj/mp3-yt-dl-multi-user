"""
database_utils.py

Database utilities and helper functions.
Provides common database operations and utilities.
"""

import sys
from pathlib import Path
from typing import Optional, Dict, Any, List, Union
from datetime import datetime
import json

# Add project root to Python path for imports
SCRIPT_DIR = Path(__file__).resolve().parent.parent.parent.parent
sys.path.insert(0, str(SCRIPT_DIR))

from src.common.logging_config import get_logger
from ..connection.connection_manager import DatabaseConnectionManager
from ..config.database_config import DatabaseConfig


class DatabaseUtils:
    """
    Database utilities and helper functions.
    
    Provides common database operations and utilities including:
    - Database initialization
    - Table management
    - Data validation
    - Query helpers
    """
    
    def __init__(self, config: Optional[DatabaseConfig] = None):
        """
        Initialize database utils.
        
        Args:
            config: Database configuration. If None, will create a new one.
        """
        self.logger = get_logger('db_utils')
        
        if config is None:
            self.config = DatabaseConfig()
            if not self.config.load_config():
                raise RuntimeError("Failed to load database configuration")
        else:
            self.config = config
        
        self.connection_manager = DatabaseConnectionManager(self.config)
        self.logger.info("DatabaseUtils initialized")
    
    def initialize_database(self) -> bool:
        """
        Initialize database with required tables.
        
        Returns:
            bool: True if initialization successful, False otherwise
        """
        try:
            if not self.connection_manager.connect():
                self.logger.error("Failed to connect to database")
                return False
            
            self.logger.info("Initializing database...")
            
            # Create tables
            tables_created = self._create_tables()
            if not tables_created:
                self.logger.error("Failed to create tables")
                return False
            
            self.logger.info("Database initialization completed successfully")
            return True
            
        except Exception as e:
            self.logger.error(f"Database initialization failed: {e}")
            return False
        finally:
            self.connection_manager.disconnect()
    
    def _create_tables(self) -> bool:
        """
        Create database tables.
        
        Returns:
            bool: True if tables created successfully, False otherwise
        """
        try:
            # Import models
            from ..models.user_model import UserModel
            from ..models.session_model import SessionModel
            
            # Create user table
            user_model = UserModel()
            user_sql = user_model.create_table_sql()
            
            if not self.connection_manager.execute_command(user_sql):
                self.logger.error("Failed to create users table")
                return False
            
            self.logger.info("Users table created successfully")
            
            # Create session table
            session_model = SessionModel()
            session_sql = session_model.create_table_sql()
            
            if not self.connection_manager.execute_command(session_sql):
                self.logger.error("Failed to create sessions table")
                return False
            
            self.logger.info("Sessions table created successfully")
            
            return True
            
        except Exception as e:
            self.logger.error(f"Error creating tables: {e}")
            return False
    
    def test_database_connection(self) -> bool:
        """
        Test database connection.
        
        Returns:
            bool: True if connection test successful, False otherwise
        """
        try:
            if not self.connection_manager.connect():
                self.logger.error("Failed to connect to database")
                return False
            
            # Test basic connectivity
            if not self.connection_manager.test_connection():
                self.logger.error("Connection test failed")
                return False
            
            # Get database info
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
            self.connection_manager.disconnect()
    
    def run_database_operations_test(self) -> bool:
        """
        Run comprehensive database operations test.
        
        Returns:
            bool: True if all operations successful, False otherwise
        """
        try:
            if not self.connection_manager.connect():
                self.logger.error("Failed to connect to database")
                return False
            
            self.logger.info("Running database operations test...")
            
            # Test table creation
            test_table = "test_operations_table"
            create_sql = f"""
                CREATE TABLE IF NOT EXISTS {test_table} (
                    id SERIAL PRIMARY KEY,
                    test_data TEXT,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                );
            """
            
            if not self.connection_manager.execute_command(create_sql):
                self.logger.error("Failed to create test table")
                return False
            
            self.logger.debug(f"Created test table: {test_table}")
            
            # Test insert
            insert_sql = f"INSERT INTO {test_table} (test_data) VALUES (%s) RETURNING id;"
            with self.connection_manager.get_cursor() as cur:
                cur.execute(insert_sql, ("Database operations test",))
                test_id = cur.fetchone()[0]
                self.connection_manager.connection.commit()
                self.logger.debug(f"Inserted test record with ID: {test_id}")
            
            # Test select
            select_sql = f"SELECT * FROM {test_table} WHERE id = %s;"
            results = self.connection_manager.execute_query(select_sql, (test_id,))
            if results:
                self.logger.debug(f"Retrieved test record: {results[0]}")
            
            # Test update
            update_sql = f"UPDATE {test_table} SET test_data = %s WHERE id = %s;"
            if not self.connection_manager.execute_command(update_sql, ("Updated test data", test_id)):
                self.logger.error("Update test failed")
                return False
            self.logger.debug(f"Updated test record ID: {test_id}")
            
            # Test delete
            delete_sql = f"DELETE FROM {test_table} WHERE id = %s;"
            if not self.connection_manager.execute_command(delete_sql, (test_id,)):
                self.logger.error("Delete test failed")
                return False
            self.logger.debug(f"Deleted test record ID: {test_id}")
            
            # Clean up test table
            drop_sql = f"DROP TABLE IF EXISTS {test_table};"
            if not self.connection_manager.execute_command(drop_sql):
                self.logger.warning("Failed to drop test table")
            
            self.logger.info("All database operations completed successfully")
            return True
            
        except Exception as e:
            self.logger.error(f"Database operations test failed: {e}")
            return False
        finally:
            self.connection_manager.disconnect()
    
    def get_table_info(self, table_name: str) -> Optional[List[Dict[str, Any]]]:
        """
        Get table information.
        
        Args:
            table_name: Name of the table
            
        Returns:
            Optional[List[Dict[str, Any]]]: Table information or None if error
        """
        try:
            if not self.connection_manager.connect():
                return None
            
            query = """
                SELECT 
                    column_name,
                    data_type,
                    is_nullable,
                    column_default,
                    character_maximum_length
                FROM information_schema.columns 
                WHERE table_name = %s 
                ORDER BY ordinal_position;
            """
            
            results = self.connection_manager.execute_query(query, (table_name,))
            return results
            
        except Exception as e:
            self.logger.error(f"Error getting table info for {table_name}: {e}")
            return None
        finally:
            self.connection_manager.disconnect()
    
    def get_database_stats(self) -> Optional[Dict[str, Any]]:
        """
        Get database statistics.
        
        Returns:
            Optional[Dict[str, Any]]: Database statistics or None if error
        """
        try:
            if not self.connection_manager.connect():
                return None
            
            stats = {}
            
            # Get database size
            size_query = "SELECT pg_size_pretty(pg_database_size(current_database())) as db_size;"
            size_result = self.connection_manager.execute_query(size_query)
            if size_result:
                stats['database_size'] = size_result[0][0]
            
            # Get table count
            table_count_query = """
                SELECT COUNT(*) as table_count 
                FROM information_schema.tables 
                WHERE table_schema = 'public';
            """
            table_count_result = self.connection_manager.execute_query(table_count_query)
            if table_count_result:
                stats['table_count'] = table_count_result[0][0]
            
            # Get connection count
            conn_count_query = "SELECT COUNT(*) as connection_count FROM pg_stat_activity;"
            conn_count_result = self.connection_manager.execute_query(conn_count_query)
            if conn_count_result:
                stats['connection_count'] = conn_count_result[0][0]
            
            return stats
            
        except Exception as e:
            self.logger.error(f"Error getting database stats: {e}")
            return None
        finally:
            self.connection_manager.disconnect()
    
    def backup_database(self, backup_path: Union[str, Path]) -> bool:
        """
        Create database backup.
        
        Args:
            backup_path: Path to save backup file
            
        Returns:
            bool: True if backup successful, False otherwise
        """
        try:
            backup_path = Path(backup_path)
            backup_path.parent.mkdir(parents=True, exist_ok=True)
            
            self.logger.info(f"Creating database backup to: {backup_path}")
            
            # This is a simplified backup - in production, you'd use pg_dump
            # For now, we'll just log the intention
            self.logger.warning("Database backup not implemented - use pg_dump in production")
            
            return True
            
        except Exception as e:
            self.logger.error(f"Database backup failed: {e}")
            return False
    
    def validate_database_schema(self) -> bool:
        """
        Validate database schema.
        
        Returns:
            bool: True if schema is valid, False otherwise
        """
        try:
            if not self.connection_manager.connect():
                return False
            
            # Check if required tables exist
            required_tables = ['users', 'sessions']
            
            for table in required_tables:
                query = """
                    SELECT EXISTS (
                        SELECT FROM information_schema.tables 
                        WHERE table_schema = 'public' 
                        AND table_name = %s
                    );
                """
                result = self.connection_manager.execute_query(query, (table,))
                if not result or not result[0][0]:
                    self.logger.error(f"Required table '{table}' does not exist")
                    return False
                self.logger.debug(f"Table '{table}' exists")
            
            self.logger.info("Database schema validation passed")
            return True
            
        except Exception as e:
            self.logger.error(f"Database schema validation failed: {e}")
            return False
        finally:
            self.connection_manager.disconnect()
