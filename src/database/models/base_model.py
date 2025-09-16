"""
base_model.py

Base model class for database operations.
Provides common functionality for all database models.
"""

import sys
from pathlib import Path
from typing import Optional, Dict, Any, List
from datetime import datetime
import uuid

# Add project root to Python path for imports
SCRIPT_DIR = Path(__file__).resolve().parent.parent.parent.parent
sys.path.insert(0, str(SCRIPT_DIR))

from src.common.logging_config import get_logger


class BaseModel:
    """
    Base model class for database operations.
    
    Provides common functionality for all database models including:
    - ID generation
    - Timestamp management
    - Common CRUD operations
    - Logging
    """
    
    def __init__(self, table_name: str):
        """
        Initialize base model.
        
        Args:
            table_name: Name of the database table
        """
        self.table_name = table_name
        self.logger = get_logger(f'db_model_{table_name}')
        self.logger.debug(f"BaseModel initialized for table: {table_name}")
    
    def generate_id(self) -> str:
        """
        Generate a unique ID for the record.
        
        Returns:
            str: Unique identifier
        """
        return str(uuid.uuid4())
    
    def get_current_timestamp(self) -> datetime:
        """
        Get current timestamp.
        
        Returns:
            datetime: Current timestamp
        """
        return datetime.utcnow()
    
    def format_timestamp(self, timestamp: datetime) -> str:
        """
        Format timestamp for database storage.
        
        Args:
            timestamp: Datetime object
            
        Returns:
            str: Formatted timestamp string
        """
        return timestamp.isoformat()
    
    def create_table_sql(self) -> str:
        """
        Create table SQL statement.
        Should be overridden by subclasses.
        
        Returns:
            str: SQL CREATE TABLE statement
        """
        raise NotImplementedError("Subclasses must implement create_table_sql")
    
    def insert_sql(self) -> str:
        """
        Insert record SQL statement.
        Should be overridden by subclasses.
        
        Returns:
            str: SQL INSERT statement
        """
        raise NotImplementedError("Subclasses must implement insert_sql")
    
    def select_sql(self, conditions: Optional[Dict[str, Any]] = None) -> str:
        """
        Select records SQL statement.
        Should be overridden by subclasses.
        
        Args:
            conditions: Optional conditions for WHERE clause
            
        Returns:
            str: SQL SELECT statement
        """
        raise NotImplementedError("Subclasses must implement select_sql")
    
    def update_sql(self, conditions: Optional[Dict[str, Any]] = None) -> str:
        """
        Update record SQL statement.
        Should be overridden by subclasses.
        
        Args:
            conditions: Optional conditions for WHERE clause
            
        Returns:
            str: SQL UPDATE statement
        """
        raise NotImplementedError("Subclasses must implement update_sql")
    
    def delete_sql(self, conditions: Optional[Dict[str, Any]] = None) -> str:
        """
        Delete record SQL statement.
        Should be overridden by subclasses.
        
        Args:
            conditions: Optional conditions for WHERE clause
            
        Returns:
            str: SQL DELETE statement
        """
        raise NotImplementedError("Subclasses must implement delete_sql")
    
    def validate_data(self, data: Dict[str, Any]) -> bool:
        """
        Validate data before database operations.
        Should be overridden by subclasses.
        
        Args:
            data: Data to validate
            
        Returns:
            bool: True if valid, False otherwise
        """
        if not isinstance(data, dict):
            self.logger.error("Data must be a dictionary")
            return False
        
        if not data:
            self.logger.error("Data cannot be empty")
            return False
        
        return True
    
    def prepare_data_for_insert(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Prepare data for insert operation.
        Adds ID and timestamps if not present.
        
        Args:
            data: Data to prepare
            
        Returns:
            Dict[str, Any]: Prepared data
        """
        prepared_data = data.copy()
        
        # Add ID if not present
        if 'id' not in prepared_data:
            prepared_data['id'] = self.generate_id()
        
        # Add timestamps if not present
        current_time = self.get_current_timestamp()
        if 'created_at' not in prepared_data:
            prepared_data['created_at'] = current_time
        if 'updated_at' not in prepared_data:
            prepared_data['updated_at'] = current_time
        
        return prepared_data
    
    def prepare_data_for_update(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Prepare data for update operation.
        Updates the updated_at timestamp.
        
        Args:
            data: Data to prepare
            
        Returns:
            Dict[str, Any]: Prepared data
        """
        prepared_data = data.copy()
        
        # Update timestamp
        prepared_data['updated_at'] = self.get_current_timestamp()
        
        return prepared_data
    
    def build_where_clause(self, conditions: Optional[Dict[str, Any]] = None) -> tuple[str, List[Any]]:
        """
        Build WHERE clause and parameters for SQL queries.
        
        Args:
            conditions: Conditions for WHERE clause
            
        Returns:
            tuple: (WHERE clause string, parameter list)
        """
        if not conditions:
            return "", []
        
        where_parts = []
        params = []
        
        for column, value in conditions.items():
            if value is not None:
                where_parts.append(f"{column} = %s")
                params.append(value)
        
        where_clause = " AND ".join(where_parts)
        if where_clause:
            where_clause = f"WHERE {where_clause}"
        
        return where_clause, params
    
    def log_operation(self, operation: str, success: bool, details: Optional[str] = None):
        """
        Log database operation.
        
        Args:
            operation: Operation name
            success: Whether operation was successful
            details: Optional details about the operation
        """
        level = "info" if success else "error"
        message = f"Database operation '{operation}' on table '{self.table_name}'"
        if details:
            message += f" - {details}"
        
        if success:
            self.logger.info(message)
        else:
            self.logger.error(message)
