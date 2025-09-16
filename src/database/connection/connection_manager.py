"""
connection_manager.py

Database connection manager for PostgreSQL.
Handles connection creation, management, and cleanup.
"""

import sys
from pathlib import Path
from typing import Optional, Dict, Any, ContextManager
import psycopg
from psycopg import Connection
from contextlib import contextmanager

# Add project root to Python path for imports
SCRIPT_DIR = Path(__file__).resolve().parent.parent.parent.parent
sys.path.insert(0, str(SCRIPT_DIR))

from src.common.logging_config import get_logger
from ..config.database_config import DatabaseConfig


class DatabaseConnectionManager:
    """
    Database connection manager for PostgreSQL.
    
    Manages database connections with proper error handling and cleanup.
    Supports both single connections and connection pooling.
    """
    
    def __init__(self, config: Optional[DatabaseConfig] = None):
        """
        Initialize database connection manager.
        
        Args:
            config: Database configuration. If None, will create a new one.
        """
        self.logger = get_logger('db_connection')
        
        if config is None:
            self.config = DatabaseConfig()
            if not self.config.load_config():
                raise RuntimeError("Failed to load database configuration")
        else:
            self.config = config
        
        self.connection = None
        self.is_connected = False
        
        self.logger.info("DatabaseConnectionManager initialized")
    
    def connect(self) -> bool:
        """
        Establish database connection.
        
        Returns:
            bool: True if connection successful, False otherwise
        """
        try:
            if self.is_connected:
                self.logger.warning("Already connected to database")
                return True
            
            self.logger.info("Connecting to database...")
            
            # Get connection string
            conn_string = self.config.get_connection_string()
            self.logger.debug(f"Connecting to: {self.config.connection_params['host']}:{self.config.connection_params['port']}")
            
            # Create connection
            self.connection = psycopg.connect(conn_string)
            self.is_connected = True
            
            # Test connection
            with self.connection.cursor() as cur:
                cur.execute("SELECT 1;")
                result = cur.fetchone()
                if result[0] != 1:
                    raise Exception("Connection test failed")
            
            self.logger.info("Database connection established successfully")
            return True
            
        except psycopg.OperationalError as e:
            self.logger.error(f"Database connection failed: {e}")
            self.is_connected = False
            return False
        except psycopg.Error as e:
            self.logger.error(f"Database error during connection: {e}")
            self.is_connected = False
            return False
        except Exception as e:
            self.logger.error(f"Unexpected error during connection: {e}")
            self.is_connected = False
            return False
    
    def disconnect(self):
        """Disconnect from database."""
        if self.connection and self.is_connected:
            try:
                self.connection.close()
                self.logger.info("Database connection closed")
            except Exception as e:
                self.logger.warning(f"Error closing database connection: {e}")
            finally:
                self.connection = None
                self.is_connected = False
    
    def get_connection(self) -> Optional[Connection]:
        """
        Get the current database connection.
        
        Returns:
            Optional[Connection]: Database connection or None if not connected
        """
        if not self.is_connected or not self.connection:
            self.logger.warning("No active database connection")
            return None
        
        return self.connection
    
    def is_connection_active(self) -> bool:
        """
        Check if connection is active and working.
        
        Returns:
            bool: True if connection is active, False otherwise
        """
        if not self.is_connected or not self.connection:
            return False
        
        try:
            with self.connection.cursor() as cur:
                cur.execute("SELECT 1;")
                cur.fetchone()
            return True
        except Exception:
            self.logger.warning("Connection is no longer active")
            self.is_connected = False
            return False
    
    @contextmanager
    def get_cursor(self) -> ContextManager[psycopg.Cursor]:
        """
        Get a database cursor as a context manager.
        
        Yields:
            psycopg.Cursor: Database cursor
            
        Raises:
            RuntimeError: If not connected to database
        """
        if not self.is_connected or not self.connection:
            raise RuntimeError("Not connected to database. Call connect() first.")
        
        cursor = None
        try:
            cursor = self.connection.cursor()
            self.logger.debug("Database cursor created")
            yield cursor
        except Exception as e:
            self.logger.error(f"Error with database cursor: {e}")
            raise
        finally:
            if cursor:
                cursor.close()
                self.logger.debug("Database cursor closed")
    
    def execute_query(self, query: str, params: Optional[tuple] = None) -> Optional[list]:
        """
        Execute a SELECT query and return results.
        
        Args:
            query: SQL query string
            params: Query parameters
            
        Returns:
            Optional[list]: Query results or None if error
        """
        try:
            with self.get_cursor() as cur:
                cur.execute(query, params)
                results = cur.fetchall()
                self.logger.debug(f"Query executed successfully: {query[:50]}...")
                return results
        except Exception as e:
            self.logger.error(f"Error executing query: {e}")
            return None
    
    def execute_command(self, command: str, params: Optional[tuple] = None) -> bool:
        """
        Execute a command (INSERT, UPDATE, DELETE) and commit.
        
        Args:
            command: SQL command string
            params: Command parameters
            
        Returns:
            bool: True if successful, False otherwise
        """
        try:
            with self.get_cursor() as cur:
                cur.execute(command, params)
                self.connection.commit()
                self.logger.debug(f"Command executed successfully: {command[:50]}...")
                return True
        except Exception as e:
            self.logger.error(f"Error executing command: {e}")
            try:
                self.connection.rollback()
                self.logger.debug("Transaction rolled back due to error")
            except Exception as rollback_error:
                self.logger.error(f"Error during rollback: {rollback_error}")
            return False
    
    def get_database_info(self) -> Optional[Dict[str, Any]]:
        """
        Get database information.
        
        Returns:
            Optional[Dict[str, Any]]: Database information or None if error
        """
        try:
            query = """
                SELECT 
                    current_database() as database_name,
                    current_user as current_user,
                    inet_server_addr() as server_address,
                    inet_server_port() as server_port,
                    version() as postgresql_version
            """
            
            results = self.execute_query(query)
            if results and len(results) > 0:
                row = results[0]
                return {
                    'database_name': row[0],
                    'current_user': row[1],
                    'server_address': row[2] or 'localhost',
                    'server_port': row[3] or 'default',
                    'postgresql_version': row[4]
                }
            return None
            
        except Exception as e:
            self.logger.error(f"Error getting database info: {e}")
            return None
    
    def test_connection(self) -> bool:
        """
        Test database connection.
        
        Returns:
            bool: True if connection test successful, False otherwise
        """
        try:
            if not self.is_connected:
                self.logger.warning("Not connected to database")
                return False
            
            with self.get_cursor() as cur:
                cur.execute("SELECT version();")
                version = cur.fetchone()[0]
                self.logger.info(f"Connection test successful - PostgreSQL version: {version}")
                return True
                
        except Exception as e:
            self.logger.error(f"Connection test failed: {e}")
            return False
    
    def __enter__(self):
        """Context manager entry."""
        if not self.connect():
            raise RuntimeError("Failed to connect to database")
        return self
    
    def __exit__(self, exc_type, exc_val, exc_tb):
        """Context manager exit."""
        self.disconnect()
    
    def __del__(self):
        """Destructor to ensure connection is closed."""
        self.disconnect()
