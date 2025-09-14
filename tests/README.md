# Test Suite Documentation

A comprehensive test suite for the YouTube Audio Downloader application, featuring unit tests, integration tests, and monitoring validation.

## 🚀 Quick Start

### **Run All Unit Tests**
```powershell
python -m pytest tests/unit/ -v
```

### **Run YTAudioDL Package Tests Only**
```powershell
python -m pytest tests/unit/test_audio_downloader.py tests/unit/test_monitoring.py -v
```

### **Using the Custom Test Runner**
```powershell
python run_tests.py --unit --path tests/unit/test_audio_downloader.py
```

## 📁 Test Structure

```
tests/
├── README.md                 # This file
├── conftest.py              # Shared fixtures and configuration
├── unit/                    # Unit tests
│   ├── test_audio_downloader.py    # YTAudioDL core functionality
│   ├── test_monitoring.py          # Download monitoring integration
│   ├── test_user_context.py        # User session management
│   └── test_uuid_utils.py          # UUID generation utilities
└── integration/             # Integration tests
    ├── test_api_integration.py     # API endpoint testing
    ├── test_audio_downloader_integration.py  # Real download tests
    ├── test_end_to_end_integration.py       # Full workflow tests
    └── test_simple_integration.py           # Basic integration tests
```

## 🧪 Test Categories

### **Unit Tests** (`@pytest.mark.unit`)
Fast, isolated tests that mock external dependencies:
- **AudioDownloader**: Core download engine functionality
- **UserContext**: Session and path management
- **UUID Utils**: Unique identifier generation
- **Download Monitoring**: Progress tracking and network monitoring

### **Integration Tests** (`@pytest.mark.integration`)
Tests that verify component interactions:
- **API Integration**: REST API endpoint testing
- **Download Integration**: Real YouTube download tests
- **End-to-End**: Complete workflow validation

### **Network Tests** (`@pytest.mark.requires_network`)
Tests requiring internet connectivity:
- **Real Downloads**: Actual YouTube video downloads
- **Network Validation**: Connectivity and DNS resolution
- **Monitoring Integration**: Live download monitoring

## 🔧 Available Test Commands

### **Basic Test Execution**
```powershell
# Run all tests
python -m pytest

# Run with verbose output
python -m pytest -v

# Run specific test file
python -m pytest tests/unit/test_audio_downloader.py -v

# Run specific test function
python -m pytest tests/unit/test_audio_downloader.py::TestAudioDownloader::test_audio_downloader_initialization -v
```

### **Test Filtering by Markers**
```powershell
# Run only unit tests
python -m pytest -m unit

# Run only integration tests
python -m pytest -m integration

# Skip network-dependent tests
python -m pytest -m "not requires_network"

# Run fast tests only
python -m pytest -m "not slow"
```

### **Coverage Reports**
```powershell
# Generate coverage report
python -m pytest --cov=src --cov-report=term-missing

# Generate HTML coverage report
python -m pytest --cov=src --cov-report=html:htmlcov

# Coverage with minimum threshold
python -m pytest --cov=src --cov-fail-under=80
```

### **Custom Test Runner Options**
```powershell
# Run unit tests only
python run_tests.py --unit

# Run integration tests only
python run_tests.py --integration

# Run with coverage
python run_tests.py --coverage

# Skip slow tests
python run_tests.py --fast

# Skip network tests
python run_tests.py --no-network

# Run specific test path
python run_tests.py --path tests/unit/test_audio_downloader.py

# Verbose output
python run_tests.py --verbose
```

## 🎯 YTAudioDL Specific Testing

### **Core Functionality Tests**
```powershell
# Test AudioDownloader class
python -m pytest tests/unit/test_audio_downloader.py::TestAudioDownloader -v

# Test Progress tracking
python -m pytest tests/unit/test_audio_downloader.py::TestProgressHook -v

# Test Download results
python -m pytest tests/unit/test_audio_downloader.py::TestAudioDownloadResult -v
```

### **Integration & Monitoring Tests**
```powershell
# Test download monitoring (requires network)
python -m pytest tests/unit/test_monitoring.py -v

# Real download integration test
python -m pytest tests/integration/test_audio_downloader_integration.py -v -s

# End-to-end workflow test
python -m pytest tests/integration/test_end_to_end_integration.py -v -s
```

## 📊 Test Configuration

### **pytest.ini Settings**
- **Coverage**: Minimum 80% required
- **Timeout**: 300 seconds for long-running tests
- **Markers**: Proper test categorization
- **Output**: HTML and terminal coverage reports

### **Available Fixtures**
- `temp_dir`: Temporary directory for test files
- `temp_download_dir`: Temporary download directory
- `mock_session_manager`: Mock session management
- `mock_progress_callback`: Mock progress tracking
- `test_urls`: Sample YouTube URLs for testing

## 🚨 Important Notes

### **Network-Dependent Tests**
Some tests require internet connectivity and will:
- Download actual YouTube videos (marked with `@pytest.mark.requires_network`)
- Take longer to execute (marked with `@pytest.mark.slow`)
- May fail if YouTube is unreachable

### **Test File Cleanup**
- Temporary files are automatically cleaned up
- Test downloads go to isolated temporary directories
- No permanent files are created during testing

### **Mocking Strategy**
- External dependencies (yt-dlp, network) are mocked in unit tests
- Real dependencies are used in integration tests
- Session management is mocked for isolation

## 🛠️ Troubleshooting

### **Common Issues**

**Import Errors:**
```powershell
# Ensure you're in the project root
cd C:\path\to\my_project

# Run tests from project root
python -m pytest tests/unit/ -v
```

**Network Test Failures:**
```powershell
# Skip network tests if offline
python -m pytest -m "not requires_network"

# Check network connectivity first
python -c "import requests; print('✅ Network OK' if requests.get('https://youtube.com').ok else '❌ Network Issue')"
```

**Slow Test Performance:**
```powershell
# Skip slow tests
python -m pytest -m "not slow"

# Or use the fast flag
python run_tests.py --fast
```

### **Debug Mode**
```powershell
# Run with debug output
python -m pytest -v -s --tb=long

# Run single test with full output
python -m pytest tests/unit/test_audio_downloader.py::test_specific_function -v -s --tb=long
```

## 📈 Coverage Goals

- **Overall Coverage**: 80% minimum
- **Core YTAudioDL**: 90%+ coverage target
- **Critical Paths**: 100% coverage (download, session management)
- **Integration Points**: Full workflow coverage

## 🔄 Continuous Testing

For development, consider running tests automatically:
```powershell
# Watch mode (if you have pytest-watch installed)
ptw tests/unit/

# Or run specific tests repeatedly during development
python -m pytest tests/unit/test_audio_downloader.py -v --tb=short
```

---

## 💡 Tips for Developers

1. **Run unit tests frequently** during development
2. **Use integration tests** to verify real functionality
3. **Check coverage** before committing changes
4. **Mock external dependencies** in unit tests
5. **Test edge cases** and error conditions
6. **Keep tests fast** by avoiding unnecessary network calls

For more information about the testing framework and available fixtures, see `conftest.py` and the individual test files.