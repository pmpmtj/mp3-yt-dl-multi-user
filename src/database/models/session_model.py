"""
session_model.py

Session model for database operations.
Handles session-related database operations.
"""

import sys
from pathlib import Path
from typing import Optional, Dict, Any, List
from datetime import datetime

# Add project root to Python path for imports
SCRIPT_DIR = Path(__file__).resolve().parent.parent.parent.parent
sys.path.insert(0, str(SCRIPT_DIR))

from .base_model import BaseModel


class SessionModel(BaseModel):
    """
    Session model for database operations.
    
    Handles session-related database operations including:
    - Session creation and management
    - Session tracking and monitoring
    - Session cleanup and expiration
    """
    
    def __init__(self):
        """Initialize session model."""
        super().__init__("sessions")
    
    def create_table_sql(self) -> str:
        """
        Create sessions table SQL statement.
        
        Returns:
            str: SQL CREATE TABLE statement
        """
        return """
            CREATE TABLE IF NOT EXISTS sessions (
                id VARCHAR(36) PRIMARY KEY,
                user_id VARCHAR(36),
                session_token VARCHAR(255) UNIQUE NOT NULL,
                ip_address VARCHAR(45),
                user_agent TEXT,
                is_active BOOLEAN DEFAULT TRUE,
                expires_at TIMESTAMP,
                last_activity TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE
            );
        """
    
    def insert_sql(self) -> str:
        """
        Insert session SQL statement.
        
        Returns:
            str: SQL INSERT statement
        """
        return """
            INSERT INTO sessions (
                id, user_id, session_token, ip_address, user_agent,
                is_active, expires_at, last_activity, created_at, updated_at
            ) VALUES (
                %(id)s, %(user_id)s, %(session_token)s, %(ip_address)s, %(user_agent)s,
                %(is_active)s, %(expires_at)s, %(last_activity)s, %(created_at)s, %(updated_at)s
            );
        """
    
    def select_sql(self, conditions: Optional[Dict[str, Any]] = None) -> str:
        """
        Select sessions SQL statement.
        
        Args:
            conditions: Optional conditions for WHERE clause
            
        Returns:
            str: SQL SELECT statement
        """
        where_clause, _ = self.build_where_clause(conditions)
        return f"SELECT * FROM sessions {where_clause};"
    
    def update_sql(self, conditions: Optional[Dict[str, Any]] = None) -> str:
        """
        Update session SQL statement.
        
        Args:
            conditions: Optional conditions for WHERE clause
            
        Returns:
            str: SQL UPDATE statement
        """
        where_clause, _ = self.build_where_clause(conditions)
        return f"""
            UPDATE sessions SET
                user_id = %(user_id)s,
                session_token = %(session_token)s,
                ip_address = %(ip_address)s,
                user_agent = %(user_agent)s,
                is_active = %(is_active)s,
                expires_at = %(expires_at)s,
                last_activity = %(last_activity)s,
                updated_at = %(updated_at)s
            {where_clause};
        """
    
    def delete_sql(self, conditions: Optional[Dict[str, Any]] = None) -> str:
        """
        Delete session SQL statement.
        
        Args:
            conditions: Optional conditions for WHERE clause
            
        Returns:
            str: SQL DELETE statement
        """
        where_clause, _ = self.build_where_clause(conditions)
        return f"DELETE FROM sessions {where_clause};"
    
    def validate_data(self, data: Dict[str, Any]) -> bool:
        """
        Validate session data.
        
        Args:
            data: Session data to validate
            
        Returns:
            bool: True if valid, False otherwise
        """
        if not super().validate_data(data):
            return False
        
        # Required fields
        required_fields = ['session_token']
        for field in required_fields:
            if field not in data or not data[field]:
                self.logger.error(f"Missing required field: {field}")
                return False
        
        # Validate session token length
        session_token = data.get('session_token', '')
        if len(session_token) < 32:
            self.logger.error("Session token must be at least 32 characters")
            return False
        
        return True
    
    def create_session(self, user_id: str, session_token: str, 
                      ip_address: Optional[str] = None, user_agent: Optional[str] = None,
                      expires_at: Optional[datetime] = None) -> Dict[str, Any]:
        """
        Create a new session.
        
        Args:
            user_id: User ID
            session_token: Session token
            ip_address: Optional IP address
            user_agent: Optional user agent
            expires_at: Optional expiration time
            
        Returns:
            Dict[str, Any]: Created session data
        """
        session_data = {
            'user_id': user_id,
            'session_token': session_token,
            'ip_address': ip_address,
            'user_agent': user_agent,
            'is_active': True,
            'expires_at': expires_at
        }
        
        if not self.validate_data(session_data):
            return {}
        
        prepared_data = self.prepare_data_for_insert(session_data)
        self.log_operation("create_session", True, f"User ID: {user_id}")
        
        return prepared_data
    
    def get_session_by_token(self, session_token: str) -> Optional[Dict[str, Any]]:
        """
        Get session by token.
        
        Args:
            session_token: Session token to search for
            
        Returns:
            Optional[Dict[str, Any]]: Session data or None if not found
        """
        conditions = {'session_token': session_token, 'is_active': True}
        where_clause, params = self.build_where_clause(conditions)
        sql = f"SELECT * FROM sessions {where_clause};"
        
        self.log_operation("get_session_by_token", True, f"Token: {session_token[:10]}...")
        return {'sql': sql, 'params': params}
    
    def update_last_activity(self, session_id: str) -> Dict[str, Any]:
        """
        Update session's last activity timestamp.
        
        Args:
            session_id: Session ID
            
        Returns:
            Dict[str, Any]: Update data
        """
        update_data = {
            'last_activity': self.get_current_timestamp(),
            'updated_at': self.get_current_timestamp()
        }
        
        conditions = {'id': session_id}
        where_clause, params = self.build_where_clause(conditions)
        sql = f"UPDATE sessions SET last_activity = %(last_activity)s, updated_at = %(updated_at)s {where_clause};"
        
        self.log_operation("update_last_activity", True, f"Session ID: {session_id}")
        return {'sql': sql, 'params': params, 'data': update_data}
    
    def deactivate_session(self, session_id: str) -> Dict[str, Any]:
        """
        Deactivate a session.
        
        Args:
            session_id: Session ID
            
        Returns:
            Dict[str, Any]: Update data
        """
        update_data = {
            'is_active': False,
            'updated_at': self.get_current_timestamp()
        }
        
        conditions = {'id': session_id}
        where_clause, params = self.build_where_clause(conditions)
        sql = f"UPDATE sessions SET is_active = %(is_active)s, updated_at = %(updated_at)s {where_clause};"
        
        self.log_operation("deactivate_session", True, f"Session ID: {session_id}")
        return {'sql': sql, 'params': params, 'data': update_data}
    
    def cleanup_expired_sessions(self) -> Dict[str, Any]:
        """
        Clean up expired sessions.
        
        Returns:
            Dict[str, Any]: Cleanup data
        """
        current_time = self.get_current_timestamp()
        conditions = {'expires_at': current_time}
        where_clause, params = self.build_where_clause(conditions)
        sql = f"UPDATE sessions SET is_active = FALSE, updated_at = %(updated_at)s WHERE expires_at < %(expires_at)s;"
        
        self.log_operation("cleanup_expired_sessions", True, f"Current time: {current_time}")
        return {'sql': sql, 'params': [current_time, current_time]}
