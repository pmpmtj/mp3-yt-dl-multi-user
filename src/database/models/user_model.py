"""
user_model.py

User model for database operations.
Handles user-related database operations.
"""

import sys
from pathlib import Path
from typing import Optional, Dict, Any, List

# Add project root to Python path for imports
SCRIPT_DIR = Path(__file__).resolve().parent.parent.parent.parent
sys.path.insert(0, str(SCRIPT_DIR))

from .base_model import BaseModel


class UserModel(BaseModel):
    """
    User model for database operations.
    
    Handles user-related database operations including:
    - User creation and management
    - User authentication data
    - User preferences and settings
    """
    
    def __init__(self):
        """Initialize user model."""
        super().__init__("users")
    
    def create_table_sql(self) -> str:
        """
        Create users table SQL statement.
        
        Returns:
            str: SQL CREATE TABLE statement
        """
        return """
            CREATE TABLE IF NOT EXISTS users (
                id VARCHAR(36) PRIMARY KEY,
                username VARCHAR(50) UNIQUE NOT NULL,
                email VARCHAR(100) UNIQUE NOT NULL,
                password_hash VARCHAR(255) NOT NULL,
                first_name VARCHAR(50),
                last_name VARCHAR(50),
                is_active BOOLEAN DEFAULT TRUE,
                is_admin BOOLEAN DEFAULT FALSE,
                last_login TIMESTAMP,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            );
        """
    
    def insert_sql(self) -> str:
        """
        Insert user SQL statement.
        
        Returns:
            str: SQL INSERT statement
        """
        return """
            INSERT INTO users (
                id, username, email, password_hash, first_name, last_name,
                is_active, is_admin, last_login, created_at, updated_at
            ) VALUES (
                %(id)s, %(username)s, %(email)s, %(password_hash)s, %(first_name)s,
                %(last_name)s, %(is_active)s, %(is_admin)s, %(last_login)s,
                %(created_at)s, %(updated_at)s
            );
        """
    
    def select_sql(self, conditions: Optional[Dict[str, Any]] = None) -> str:
        """
        Select users SQL statement.
        
        Args:
            conditions: Optional conditions for WHERE clause
            
        Returns:
            str: SQL SELECT statement
        """
        where_clause, _ = self.build_where_clause(conditions)
        return f"SELECT * FROM users {where_clause};"
    
    def update_sql(self, conditions: Optional[Dict[str, Any]] = None) -> str:
        """
        Update user SQL statement.
        
        Args:
            conditions: Optional conditions for WHERE clause
            
        Returns:
            str: SQL UPDATE statement
        """
        where_clause, _ = self.build_where_clause(conditions)
        return f"""
            UPDATE users SET
                username = %(username)s,
                email = %(email)s,
                password_hash = %(password_hash)s,
                first_name = %(first_name)s,
                last_name = %(last_name)s,
                is_active = %(is_active)s,
                is_admin = %(is_admin)s,
                last_login = %(last_login)s,
                updated_at = %(updated_at)s
            {where_clause};
        """
    
    def delete_sql(self, conditions: Optional[Dict[str, Any]] = None) -> str:
        """
        Delete user SQL statement.
        
        Args:
            conditions: Optional conditions for WHERE clause
            
        Returns:
            str: SQL DELETE statement
        """
        where_clause, _ = self.build_where_clause(conditions)
        return f"DELETE FROM users {where_clause};"
    
    def validate_data(self, data: Dict[str, Any]) -> bool:
        """
        Validate user data.
        
        Args:
            data: User data to validate
            
        Returns:
            bool: True if valid, False otherwise
        """
        if not super().validate_data(data):
            return False
        
        # Required fields
        required_fields = ['username', 'email', 'password_hash']
        for field in required_fields:
            if field not in data or not data[field]:
                self.logger.error(f"Missing required field: {field}")
                return False
        
        # Validate email format (basic validation)
        email = data.get('email', '')
        if '@' not in email or '.' not in email.split('@')[-1]:
            self.logger.error("Invalid email format")
            return False
        
        # Validate username length
        username = data.get('username', '')
        if len(username) < 3 or len(username) > 50:
            self.logger.error("Username must be between 3 and 50 characters")
            return False
        
        return True
    
    def create_user(self, username: str, email: str, password_hash: str, 
                   first_name: Optional[str] = None, last_name: Optional[str] = None,
                   is_admin: bool = False) -> Dict[str, Any]:
        """
        Create a new user.
        
        Args:
            username: Username
            email: Email address
            password_hash: Hashed password
            first_name: Optional first name
            last_name: Optional last name
            is_admin: Whether user is admin
            
        Returns:
            Dict[str, Any]: Created user data
        """
        user_data = {
            'username': username,
            'email': email,
            'password_hash': password_hash,
            'first_name': first_name,
            'last_name': last_name,
            'is_admin': is_admin,
            'is_active': True
        }
        
        if not self.validate_data(user_data):
            return {}
        
        prepared_data = self.prepare_data_for_insert(user_data)
        self.log_operation("create_user", True, f"User: {username}")
        
        return prepared_data
    
    def get_user_by_username(self, username: str) -> Optional[Dict[str, Any]]:
        """
        Get user by username.
        
        Args:
            username: Username to search for
            
        Returns:
            Optional[Dict[str, Any]]: User data or None if not found
        """
        conditions = {'username': username}
        where_clause, params = self.build_where_clause(conditions)
        sql = f"SELECT * FROM users {where_clause};"
        
        self.log_operation("get_user_by_username", True, f"Username: {username}")
        return {'sql': sql, 'params': params}
    
    def get_user_by_email(self, email: str) -> Optional[Dict[str, Any]]:
        """
        Get user by email.
        
        Args:
            email: Email to search for
            
        Returns:
            Optional[Dict[str, Any]]: User data or None if not found
        """
        conditions = {'email': email}
        where_clause, params = self.build_where_clause(conditions)
        sql = f"SELECT * FROM users {where_clause};"
        
        self.log_operation("get_user_by_email", True, f"Email: {email}")
        return {'sql': sql, 'params': params}
    
    def update_last_login(self, user_id: str) -> Dict[str, Any]:
        """
        Update user's last login timestamp.
        
        Args:
            user_id: User ID
            
        Returns:
            Dict[str, Any]: Update data
        """
        update_data = {
            'last_login': self.get_current_timestamp(),
            'updated_at': self.get_current_timestamp()
        }
        
        conditions = {'id': user_id}
        where_clause, params = self.build_where_clause(conditions)
        sql = f"UPDATE users SET last_login = %(last_login)s, updated_at = %(updated_at)s {where_clause};"
        
        self.log_operation("update_last_login", True, f"User ID: {user_id}")
        return {'sql': sql, 'params': params, 'data': update_data}
