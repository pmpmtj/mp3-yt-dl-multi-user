# Database Package

Independent database package for PostgreSQL operations in the YT-DL project.

## Overview

This package provides a comprehensive database solution with:
- **Configuration Management**: Load and validate database settings from environment variables
- **Connection Management**: Handle database connections with proper error handling and cleanup
- **Model System**: Object-oriented database models with CRUD operations
- **Migration System**: Database schema versioning and migration management
- **Utilities**: Common database operations and helper functions
- **Testing**: Comprehensive test suite for all database functionality

## Architecture

The package follows the project's architecture guidelines:
- Uses centralized logging from `/src/common/logging_config.py`
- Uses path utilities from `/path_utils/path_utils.py`
- Handles both frozen (PyInstaller) and regular Python execution
- Self-contained modules with proper error handling
- Production-minded development approach

## Package Structure

```
src/database/
├── __init__.py                 # Package initialization and exports
├── README.md                   # This documentation
├── config/                     # Database configuration
│   ├── __init__.py
│   └── database_config.py      # Configuration management
├── connection/                 # Database connections
│   ├── __init__.py
│   └── connection_manager.py   # Connection management
├── models/                     # Database models
│   ├── __init__.py
│   ├── base_model.py          # Base model class
│   ├── user_model.py          # User model
│   └── session_model.py       # Session model
├── utils/                      # Database utilities
│   ├── __init__.py
│   ├── database_utils.py      # Common utilities
│   └── migration_utils.py     # Migration utilities
└── tests/                      # Test suite
    ├── __init__.py
    ├── test_database_connection.py    # Connection tests
    ├── test_database_operations.py    # Operations tests
    └── run_all_tests.py              # Test runner
```

## Quick Start

### 1. Environment Setup

Create a `.env` file in the project root with your database configuration:

```env
DATABASE_URL=postgresql+psycopg://username:password@localhost:5432/database_name
```

### 2. Basic Usage

```python
from src.database import DatabaseConfig, DatabaseConnectionManager, DatabaseUtils

# Initialize configuration
config = DatabaseConfig()
config.load_config()

# Create connection manager
conn_manager = DatabaseConnectionManager(config)

# Connect to database
if conn_manager.connect():
    print("Connected to database!")
    
    # Use the connection
    with conn_manager.get_cursor() as cursor:
        cursor.execute("SELECT version();")
        version = cursor.fetchone()[0]
        print(f"PostgreSQL version: {version}")
    
    conn_manager.disconnect()
```

### 3. Using Models

```python
from src.database.models import UserModel, SessionModel

# Create user
user_model = UserModel()
user_data = user_model.create_user(
    username="john_doe",
    email="john@example.com",
    password_hash="hashed_password",
    first_name="John",
    last_name="Doe"
)

# Create session
session_model = SessionModel()
session_data = session_model.create_session(
    user_id=user_data['id'],
    session_token="session_token_123",
    ip_address="127.0.0.1"
)
```

### 4. Running Tests

```bash
# Run all database tests
python test_database.py

# Run specific tests
python -m src.database.tests.test_database_connection
python -m src.database.tests.test_database_operations
```

## Components

### Configuration (`config/`)

- **DatabaseConfig**: Loads and validates database configuration from environment variables
- Supports both frozen (PyInstaller) and regular Python execution
- Validates connection parameters and provides connection strings

### Connection Management (`connection/`)

- **DatabaseConnectionManager**: Manages database connections with proper error handling
- Context manager support for automatic cleanup
- Connection pooling and health checking
- Cursor management with automatic cleanup

### Models (`models/`)

- **BaseModel**: Base class for all database models
- **UserModel**: User-related database operations
- **SessionModel**: Session-related database operations
- Automatic ID generation and timestamp management
- Data validation and preparation

### Utilities (`utils/`)

- **DatabaseUtils**: Common database operations and utilities
- **MigrationUtils**: Database schema migration management
- Database initialization and validation
- Statistics and monitoring

### Testing (`tests/`)

- **DatabaseConnectionTester**: Tests database connectivity and basic operations
- **DatabaseOperationsTester**: Tests CRUD operations, models, and utilities
- **DatabaseTestRunner**: Runs all tests with comprehensive reporting

## Features

### ✅ **Connection Management**
- Automatic connection handling
- Error recovery and retry logic
- Connection health monitoring
- Proper resource cleanup

### ✅ **Model System**
- Object-oriented database models
- Automatic ID and timestamp management
- Data validation and preparation
- CRUD operation support

### ✅ **Migration System**
- Database schema versioning
- Migration tracking and validation
- Rollback support
- Initial schema creation

### ✅ **Testing Suite**
- Comprehensive test coverage
- Connection testing
- Operations testing
- Model testing
- Migration testing

### ✅ **Logging Integration**
- Centralized logging configuration
- Debug and error logging
- Performance monitoring
- Operation tracking

### ✅ **Error Handling**
- Graceful error handling
- Detailed error logging
- Resource cleanup on errors
- Transaction rollback support

## Configuration

The package uses the following environment variables:

- `DATABASE_URL`: PostgreSQL connection URL
- `DATABASE_ENABLED`: Enable/disable database functionality (optional)

## Logging

The package integrates with the project's centralized logging system:

- `db_config`: Configuration logging
- `db_connection`: Connection management logging
- `db_model_*`: Model operation logging
- `db_utils`: Utility operation logging
- `db_migration`: Migration logging
- `db_test`: Test logging

## Dependencies

- `psycopg[binary]`: PostgreSQL adapter
- `python-dotenv`: Environment variable loading
- `path_utils`: Project path utilities
- `src.common.logging_config`: Centralized logging

## Production Considerations

- Use connection pooling for high-traffic applications
- Implement proper backup strategies
- Monitor database performance and connections
- Use prepared statements for security
- Implement proper error handling and logging
- Consider database replication for high availability

## Troubleshooting

### Common Issues

1. **Connection Failed**: Check database URL and credentials
2. **Import Errors**: Ensure all dependencies are installed
3. **Permission Denied**: Check database user permissions
4. **Table Not Found**: Run migrations to create required tables

### Debug Mode

Enable debug logging for detailed information:

```python
from src.common.logging_config import setup_logging
setup_logging(debug_mode=True)
```

## Contributing

When adding new features:

1. Follow the existing architecture patterns
2. Add comprehensive tests
3. Update documentation
4. Ensure proper error handling
5. Add appropriate logging

## License

This package is part of the YT-DL project and follows the same licensing terms.
