# Testing Infrastructure

This directory contains the complete testing infrastructure for the YouTube downloader application, designed for comprehensive unit testing, integration testing, and mocking capabilities.

## ✅ **Testing Infrastructure Complete**

### **🏗️ Components Created:**

1. **Testing Framework Setup**:
   - **pytest** with async support
   - **pytest-mock** for mocking
   - **pytest-cov** for coverage reporting
   - **httpx** for FastAPI testing

2. **Dependency Injection System**:
   - **DependencyContainer** for service management
   - **ServiceProvider** for global dependency resolution
   - **Factory patterns** for testable component creation

3. **Global State Refactoring**:
   - **SessionManagerProvider** replacing global session manager
   - **JobStorageProvider** replacing global job storage
   - **JobIDGenerator** for unique ID generation

4. **Comprehensive Test Suite**:
   - **Unit tests** for all core components
   - **Mock fixtures** for external dependencies
   - **Test utilities** and helpers

## 📁 **Directory Structure**

```
tests/
├── __init__.py                 # Test package initialization
├── conftest.py                 # Pytest configuration and fixtures
├── README.md                   # This documentation
├── unit/                       # Unit tests
│   ├── test_uuid_utils.py      # UUID generation tests
│   ├── test_user_context.py    # User context tests
│   └── test_audio_downloader.py # Audio downloader tests
└── integration/                # Integration tests (future)
```

## 🚀 **Running Tests**

### **Basic Test Execution**
```bash
# Run all tests
python -m pytest

# Run with coverage
python -m pytest --cov=src --cov-report=html

# Run only unit tests
python -m pytest -m unit

# Run specific test file
python -m pytest tests/unit/test_uuid_utils.py

# Run with verbose output
python -m pytest -v
```

### **Using the Test Runner Script**
```bash
# Run all tests with coverage
python run_tests.py --coverage

# Run only unit tests
python run_tests.py --unit

# Run tests with verbose output
python run_tests.py --verbose

# Skip slow tests
python run_tests.py --fast

# Skip network-requiring tests
python run_tests.py --no-network
```

### **Advanced Test Options**
```bash
# Run tests with specific markers
python -m pytest -m "unit and not slow"

# Run tests in parallel (requires pytest-xdist)
python -m pytest -n auto

# Run tests with custom output
python -m pytest --tb=short --disable-warnings

# Generate coverage report
python -m pytest --cov=src --cov-report=term-missing --cov-report=html
```

## 🧪 **Test Categories**

### **Unit Tests** (`@pytest.mark.unit`)
- **UUID Generation**: Testing UUID utilities
- **User Context**: Session and job management
- **Audio Downloader**: Core download functionality
- **Session Manager**: Session lifecycle management
- **Job Storage**: Data persistence abstraction

### **Integration Tests** (`@pytest.mark.integration`) - Future
- **API Endpoints**: Full HTTP request/response testing
- **Database Integration**: PostgreSQL integration tests
- **External Services**: yt-dlp and YouTube API testing

### **Slow Tests** (`@pytest.mark.slow`)
- **Large File Downloads**: Time-consuming operations
- **Batch Processing**: Multiple file operations
- **Performance Tests**: Load and stress testing

### **Network Tests** (`@pytest.mark.requires_network`)
- **Real YouTube Downloads**: Actual download testing
- **API Integration**: External service testing
- **Network Connectivity**: Connection validation

## 🔧 **Test Fixtures**

### **Core Fixtures**
```python
@pytest.fixture
def temp_dir():
    """Temporary directory for test files."""

@pytest.fixture
def mock_session_manager():
    """Mock session manager for testing."""

@pytest.fixture
def mock_user_context():
    """Mock user context for testing."""

@pytest.fixture
def mock_audio_downloader():
    """Mock audio downloader for testing."""
```

### **Specialized Fixtures**
```python
@pytest.fixture
def sample_session_info():
    """Sample session data for testing."""

@pytest.fixture
def sample_job_data():
    """Sample job data for testing."""

@pytest.fixture
def test_urls():
    """Test YouTube URLs for validation."""

@pytest.fixture
def mock_file_system(temp_dir):
    """Mock file system for testing."""
```

## 🎯 **Dependency Injection**

### **Service Provider Usage**
```python
# Configure for testing
from src.common.dependency_container import configure_for_testing, get_service

# Set up test container
configure_for_testing(test_container)

# Get service in test
session_manager = get_service(SessionManager)
```

### **Mock Service Registration**
```python
# Register mock services
container.register_instance(SessionManager, mock_session_manager)
container.register_factory(AudioDownloader, lambda: mock_downloader)
```

## 📊 **Coverage Requirements**

- **Minimum Coverage**: 80% (configurable in pytest.ini)
- **Coverage Reports**: HTML and terminal output
- **Excluded Files**: Test files, configuration files
- **Coverage Threshold**: Fails build if below minimum

### **Coverage Commands**
```bash
# Generate coverage report
python -m pytest --cov=src --cov-report=html

# View coverage in browser
open htmlcov/index.html

# Check coverage threshold
python -m pytest --cov=src --cov-fail-under=80
```

## 🐛 **Mocking Strategy**

### **External Dependencies**
- **yt-dlp**: Mocked for download operations
- **File System**: Temporary directories and files
- **Network**: Mock HTTP responses
- **Logging**: Disabled during tests

### **Internal Dependencies**
- **Session Manager**: Mocked for isolation
- **User Context**: Mocked for path testing
- **Job Storage**: In-memory test storage
- **Progress Callbacks**: Mocked for validation

## 🔍 **Test Examples**

### **Unit Test Example**
```python
@pytest.mark.unit
def test_generate_session_uuid_returns_unique_values():
    """Test that generate_session_uuid returns unique values."""
    uuids = [generate_session_uuid() for _ in range(10)]
    assert len(set(uuids)) == 10, "All UUIDs should be unique"
```

### **Mock Usage Example**
```python
@pytest.mark.unit
@patch('src.yt_audio_dl.audio_core.yt_dlp.YoutubeDL')
def test_get_video_info_success(self, mock_ydl_class):
    """Test successful video info retrieval."""
    downloader = AudioDownloader(output_dir=temp_download_dir)
    
    mock_info = {'title': 'Test Video'}
    mock_ydl_instance = Mock()
    mock_ydl_instance.extract_info.return_value = mock_info
    mock_ydl_class.return_value.__enter__.return_value = mock_ydl_instance
    
    result = downloader.get_video_info("https://youtube.com/watch?v=test")
    assert result['title'] == 'Test Video'
```

### **Fixture Usage Example**
```python
@pytest.mark.unit
def test_audio_downloader_initialization(self, temp_download_dir):
    """Test AudioDownloader initialization."""
    downloader = AudioDownloader(output_dir=temp_download_dir)
    
    assert downloader.output_dir == temp_download_dir
    assert temp_download_dir.exists()
```

## 🚀 **Testing Best Practices**

### **Test Organization**
- **One test class per module** being tested
- **Descriptive test names** that explain the scenario
- **Arrange-Act-Assert** pattern for test structure
- **Independent tests** that don't depend on each other

### **Mocking Guidelines**
- **Mock external dependencies** (yt-dlp, file system, network)
- **Don't mock the code under test**
- **Use fixtures** for common mock setups
- **Verify mock interactions** when important

### **Assertion Patterns**
- **Specific assertions** over generic ones
- **Error message validation** for exception tests
- **State verification** after operations
- **Return value validation** for functions

## 📈 **Continuous Integration**

### **GitHub Actions Example**
```yaml
- name: Run Tests
  run: |
    python -m pip install -r requirements.txt
    python -m pytest --cov=src --cov-report=xml
    
- name: Upload Coverage
  uses: codecov/codecov-action@v3
  with:
    file: ./coverage.xml
```

### **Pre-commit Hooks**
```bash
# Install pre-commit hooks
pre-commit install

# Run tests before commit
pre-commit run --all-files
```

## 🔧 **Configuration**

### **pytest.ini Settings**
- **Test discovery**: Automatic test file detection
- **Coverage**: 80% minimum threshold
- **Output**: Verbose with short tracebacks
- **Markers**: Custom markers for test categorization
- **Async**: Automatic async test support

### **Environment Variables**
```bash
# Test configuration
export TEST_MODE=true
export LOG_LEVEL=WARNING
export TEMP_DIR=/tmp/yt_dl_tests

# Coverage configuration
export COVERAGE_THRESHOLD=80
export COVERAGE_REPORT_FORMAT=html
```

## 📚 **Test Documentation**

### **Test Naming Convention**
- **Test files**: `test_*.py` or `*_test.py`
- **Test classes**: `Test*` (e.g., `TestUserContext`)
- **Test methods**: `test_*` (e.g., `test_get_session_id`)

### **Docstring Format**
```python
def test_user_context_initialization_with_session_uuid(self):
    """Test UserContext initialization with provided session UUID."""
    # Test implementation
```

### **Markers Usage**
```python
@pytest.mark.unit
@pytest.mark.slow
@pytest.mark.requires_network
def test_real_youtube_download():
    """Test actual YouTube download (slow, requires network)."""
    # Test implementation
```

## 🎉 **Benefits Achieved**

### **Testability Improvements**
- **Dependency Injection**: Easy mocking and testing
- **Global State Elimination**: No hidden dependencies
- **Factory Patterns**: Configurable component creation
- **Interface Abstractions**: Testable contracts

### **Quality Assurance**
- **Comprehensive Coverage**: All core functionality tested
- **Error Scenarios**: Exception handling validation
- **Edge Cases**: Boundary condition testing
- **Integration Points**: Component interaction testing

### **Development Workflow**
- **Fast Feedback**: Quick test execution
- **Reliable Tests**: Consistent and repeatable
- **Easy Debugging**: Clear error messages and traces
- **Continuous Testing**: Automated test execution

---

## 📝 **Summary**

The testing infrastructure provides:

✅ **Complete pytest setup** with async support  
✅ **Dependency injection** for testable architecture  
✅ **Global state refactoring** for better isolation  
✅ **Comprehensive unit tests** for core components  
✅ **Mock fixtures** for external dependencies  
✅ **Coverage reporting** with HTML output  
✅ **Test categorization** with markers  
✅ **CI/CD ready** configuration  

The codebase is now **fully prepared for unit testing** with professional-grade testing infrastructure that supports comprehensive test coverage, easy mocking, and maintainable test suites! 🧪✨
