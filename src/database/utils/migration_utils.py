"""
migration_utils.py

Database migration utilities.
Handles database schema migrations and versioning.
"""

import sys
from pathlib import Path
from typing import Optional, Dict, Any, List
from datetime import datetime
import json

# Add project root to Python path for imports
SCRIPT_DIR = Path(__file__).resolve().parent.parent.parent.parent
sys.path.insert(0, str(SCRIPT_DIR))

from src.common.logging_config import get_logger
from ..connection.connection_manager import DatabaseConnectionManager
from ..config.database_config import DatabaseConfig


class MigrationUtils:
    """
    Database migration utilities.
    
    Handles database schema migrations and versioning including:
    - Migration tracking
    - Schema versioning
    - Migration execution
    - Rollback support
    """
    
    def __init__(self, config: Optional[DatabaseConfig] = None):
        """
        Initialize migration utils.
        
        Args:
            config: Database configuration. If None, will create a new one.
        """
        self.logger = get_logger('db_migration')
        
        if config is None:
            self.config = DatabaseConfig()
            if not self.config.load_config():
                raise RuntimeError("Failed to load database configuration")
        else:
            self.config = config
        
        self.connection_manager = DatabaseConnectionManager(self.config)
        self.logger.info("MigrationUtils initialized")
    
    def create_migrations_table(self) -> bool:
        """
        Create migrations tracking table.
        
        Returns:
            bool: True if table created successfully, False otherwise
        """
        try:
            if not self.connection_manager.connect():
                self.logger.error("Failed to connect to database")
                return False
            
            create_sql = """
                CREATE TABLE IF NOT EXISTS migrations (
                    id SERIAL PRIMARY KEY,
                    version VARCHAR(50) UNIQUE NOT NULL,
                    name VARCHAR(255) NOT NULL,
                    applied_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    checksum VARCHAR(64),
                    description TEXT
                );
            """
            
            if not self.connection_manager.execute_command(create_sql):
                self.logger.error("Failed to create migrations table")
                return False
            
            self.logger.info("Migrations table created successfully")
            return True
            
        except Exception as e:
            self.logger.error(f"Error creating migrations table: {e}")
            return False
        finally:
            self.connection_manager.disconnect()
    
    def get_applied_migrations(self) -> List[Dict[str, Any]]:
        """
        Get list of applied migrations.
        
        Returns:
            List[Dict[str, Any]]: List of applied migrations
        """
        try:
            if not self.connection_manager.connect():
                return []
            
            query = "SELECT * FROM migrations ORDER BY applied_at;"
            results = self.connection_manager.execute_query(query)
            
            if results:
                migrations = []
                for row in results:
                    migrations.append({
                        'id': row[0],
                        'version': row[1],
                        'name': row[2],
                        'applied_at': row[3],
                        'checksum': row[4],
                        'description': row[5]
                    })
                return migrations
            
            return []
            
        except Exception as e:
            self.logger.error(f"Error getting applied migrations: {e}")
            return []
        finally:
            self.connection_manager.disconnect()
    
    def record_migration(self, version: str, name: str, description: str = "", checksum: str = "") -> bool:
        """
        Record a migration as applied.
        
        Args:
            version: Migration version
            name: Migration name
            description: Migration description
            checksum: Migration checksum
            
        Returns:
            bool: True if recorded successfully, False otherwise
        """
        try:
            if not self.connection_manager.connect():
                return False
            
            insert_sql = """
                INSERT INTO migrations (version, name, description, checksum)
                VALUES (%s, %s, %s, %s);
            """
            
            if not self.connection_manager.execute_command(insert_sql, (version, name, description, checksum)):
                self.logger.error("Failed to record migration")
                return False
            
            self.logger.info(f"Migration recorded: {version} - {name}")
            return True
            
        except Exception as e:
            self.logger.error(f"Error recording migration: {e}")
            return False
        finally:
            self.connection_manager.disconnect()
    
    def run_initial_migration(self) -> bool:
        """
        Run initial database migration.
        
        Returns:
            bool: True if migration successful, False otherwise
        """
        try:
            self.logger.info("Running initial database migration...")
            
            # Create migrations table first
            if not self.create_migrations_table():
                return False
            
            # Check if initial migration already applied
            applied_migrations = self.get_applied_migrations()
            initial_migration = next((m for m in applied_migrations if m['version'] == '001'), None)
            
            if initial_migration:
                self.logger.info("Initial migration already applied")
                return True
            
            # Run initial migration
            if not self._apply_initial_schema():
                return False
            
            # Record migration
            if not self.record_migration('001', 'initial_schema', 'Create initial database schema'):
                return False
            
            self.logger.info("Initial migration completed successfully")
            return True
            
        except Exception as e:
            self.logger.error(f"Initial migration failed: {e}")
            return False
    
    def _apply_initial_schema(self) -> bool:
        """
        Apply initial database schema.
        
        Returns:
            bool: True if schema applied successfully, False otherwise
        """
        try:
            if not self.connection_manager.connect():
                return False
            
            # Import models
            from ..models.user_model import UserModel
            from ..models.session_model import SessionModel
            
            # Create user table
            user_model = UserModel()
            user_sql = user_model.create_table_sql()
            
            if not self.connection_manager.execute_command(user_sql):
                self.logger.error("Failed to create users table")
                return False
            
            self.logger.info("Users table created")
            
            # Create session table
            session_model = SessionModel()
            session_sql = session_model.create_table_sql()
            
            if not self.connection_manager.execute_command(session_sql):
                self.logger.error("Failed to create sessions table")
                return False
            
            self.logger.info("Sessions table created")
            
            return True
            
        except Exception as e:
            self.logger.error(f"Error applying initial schema: {e}")
            return False
        finally:
            self.connection_manager.disconnect()
    
    def get_migration_status(self) -> Dict[str, Any]:
        """
        Get migration status information.
        
        Returns:
            Dict[str, Any]: Migration status information
        """
        try:
            applied_migrations = self.get_applied_migrations()
            
            status = {
                'total_migrations': len(applied_migrations),
                'latest_migration': applied_migrations[-1] if applied_migrations else None,
                'migrations': applied_migrations
            }
            
            return status
            
        except Exception as e:
            self.logger.error(f"Error getting migration status: {e}")
            return {'error': str(e)}
    
    def validate_migrations(self) -> bool:
        """
        Validate that all migrations are properly applied.
        
        Returns:
            bool: True if all migrations are valid, False otherwise
        """
        try:
            if not self.connection_manager.connect():
                return False
            
            # Check if migrations table exists
            query = """
                SELECT EXISTS (
                    SELECT FROM information_schema.tables 
                    WHERE table_schema = 'public' 
                    AND table_name = 'migrations'
                );
            """
            result = self.connection_manager.execute_query(query)
            if not result or not result[0][0]:
                self.logger.error("Migrations table does not exist")
                return False
            
            # Check if required tables exist
            required_tables = ['users', 'sessions']
            for table in required_tables:
                table_query = """
                    SELECT EXISTS (
                        SELECT FROM information_schema.tables 
                        WHERE table_schema = 'public' 
                        AND table_name = %s
                    );
                """
                table_result = self.connection_manager.execute_query(table_query, (table,))
                if not table_result or not table_result[0][0]:
                    self.logger.error(f"Required table '{table}' does not exist")
                    return False
            
            self.logger.info("Migration validation passed")
            return True
            
        except Exception as e:
            self.logger.error(f"Migration validation failed: {e}")
            return False
        finally:
            self.connection_manager.disconnect()
