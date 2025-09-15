# YouTube Audio Downloader

A comprehensive Python application for downloading audio from YouTube videos with session management, progress tracking, and both CLI and API interfaces.

## 🚀 Features

- **🎵 Audio Downloads**: High-quality MP3 downloads from YouTube videos
- **🔗 URL Sanitization**: Handles complex YouTube URLs with timestamps and parameters
- **👥 Session Management**: Multi-user support with isolated download directories
- **📊 Progress Tracking**: Real-time download progress and status monitoring
- **🖥️ CLI Interface**: Command-line tool for easy audio downloads
- **🌐 REST API**: Full REST API for programmatic access
- **📱 Multiple URL Formats**: Supports standard, mobile, short, and embed YouTube URLs
- **⚡ Background Processing**: Asynchronous job processing for API requests
- **🔧 Configurable**: Flexible configuration for different use cases

## 📋 Quick Start

### Prerequisites

- Python 3.8+
- FFmpeg (for audio processing)
- yt-dlp

### Installation

1. **Clone the repository**
   ```bash
   git clone <your-repo-url>
   cd youtube-audio-downloader
   ```

2. **Install dependencies**
   ```bash
   pip install -r requirements.txt
   ```

3. **Test the installation**
   ```bash
   python -m src.yt_audio_dl --url "https://www.youtube.com/watch?v=dQw4w9WgXcQ" --output-dir test_downloads
   ```

## 🎯 Usage Examples

### Command Line Interface

**Single Download**
```bash
python -m src.yt_audio_dl --url "https://www.youtube.com/watch?v=dQw4w9WgXcQ" --output-dir ./downloads
```

**Download with URL Sanitization**
```bash
# Handles URLs with timestamps and parameters automatically
python -m src.yt_audio_dl --url "https://www.youtube.com/watch?v=dQw4w9WgXcQ&t=24s" --output-dir ./downloads
```

**Verbose Logging**
```bash
python -m src.yt_audio_dl --url "https://www.youtube.com/watch?v=dQw4w9WgXcQ" --verbose
```

### REST API

**Start the API server**
```bash
python run_api.py
```

**Create a download job**
```bash
curl -X POST "http://localhost:8000/api/sessions/"
curl -X POST "http://localhost:8000/api/jobs/" \
  -H "X-Session-ID: YOUR_SESSION_UUID" \
  -H "Content-Type: application/json" \
  -d '{
    "url": "https://www.youtube.com/watch?v=dQw4w9WgXcQ",
    "media_type": "audio",
    "quality": "best",
    "output_format": "mp3"
  }'
```

### Python Integration

```python
from src.yt_audio_dl import AudioDownloader

# Create downloader
downloader = AudioDownloader(output_dir="./downloads")

# Download audio
result = downloader.download_audio("https://www.youtube.com/watch?v=dQw4w9WgXcQ")

if result.success:
    print(f"Downloaded: {result.output_path}")
    print(f"Title: {result.title}")
    print(f"Duration: {result.duration_seconds} seconds")
```

## 📁 Project Structure

```
youtube-audio-downloader/
├── src/
│   ├── yt_audio_dl/          # Core audio download functionality
│   ├── api/                  # REST API endpoints
│   └── common/               # Shared utilities and configuration
├── tests/                    # Test suite
├── downloads/                # Default download directory
├── logs/                     # Application logs
├── requirements.txt          # Python dependencies
├── run_api.py               # API server launcher
└── run_tests.py             # Test runner
```

## 🧪 Testing

**Run all tests**
```bash
python run_tests.py
```

**Run specific test categories**
```bash
python run_tests.py --unit          # Unit tests only
python run_tests.py --integration   # Integration tests only
python run_tests.py --coverage      # With coverage report
```

**Run individual test files**
```bash
python -m pytest tests/unit/test_audio_downloader.py -v
python -m pytest tests/unit/test_url_utils.py -v
```

## 🔧 Configuration

### Environment Variables

- `LOG_LEVEL`: Set logging level (DEBUG, INFO, WARNING, ERROR)
- `MAX_SESSIONS`: Maximum concurrent sessions (default: 100)
- `SESSION_TIMEOUT`: Session timeout in hours (default: 24)

### Audio Settings

- **Format**: MP3 (configurable)
- **Quality**: Best available audio quality
- **Bitrate**: 192 kbps (default)

## 📊 API Endpoints

| Method | Endpoint | Description |
|--------|----------|-------------|
| POST | `/api/sessions/` | Create new session |
| GET | `/api/sessions/{id}` | Get session info |
| POST | `/api/jobs/` | Create download job |
| GET | `/api/jobs/{id}` | Get job status |
| GET | `/api/jobs/{id}/paths` | Get download paths |
| GET | `/api/health` | Health check |

## 🛠️ Development

### Setup Development Environment

1. **Install development dependencies**
   ```bash
   pip install -r requirements.txt
   pip install pytest pytest-cov
   ```

2. **Run tests with coverage**
   ```bash
   python run_tests.py --coverage
   ```

3. **Start development server**
   ```bash
   python run_api.py
   ```

### Code Quality

- **Linting**: Code follows PEP 8 standards
- **Testing**: Comprehensive test coverage (>80%)
- **Type Hints**: Full type annotation support
- **Documentation**: Detailed docstrings and comments

## 🐛 Troubleshooting

### Common Issues

**Download fails**
- Verify YouTube URL format
- Check internet connection
- Ensure sufficient disk space
- Verify yt-dlp installation

**API errors**
- Check session UUID validity
- Verify session hasn't expired
- Check job limits per session

**URL parsing issues**
- The app automatically sanitizes URLs
- Supports timestamps, playlists, and mobile URLs
- Check logs for detailed error messages

### Debug Mode

```bash
# Enable verbose logging
python -m src.yt_audio_dl --url "https://youtube.com/watch?v=..." --verbose

# Check application logs
tail -f logs/app.log
tail -f logs/error.log
```

## 📚 Documentation

- **[Detailed Audio Download Guide](src/yt_audio_dl/readme.md)** - Comprehensive documentation for audio download functionality
- **[API Documentation](docs/api.md)** - Complete API reference
- **[Configuration Guide](docs/configuration.md)** - Setup and configuration options

## 🤝 Contributing

1. Fork the repository
2. Create a feature branch (`git checkout -b feature/amazing-feature`)
3. Commit your changes (`git commit -m 'Add amazing feature'`)
4. Push to the branch (`git push origin feature/amazing-feature`)
5. Open a Pull Request

## 📄 License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

## 🙏 Acknowledgments

- [yt-dlp](https://github.com/yt-dlp/yt-dlp) - YouTube video downloader
- [FastAPI](https://fastapi.tiangolo.com/) - Modern web framework
- [pytest](https://pytest.org/) - Testing framework

## 📞 Support

- **Issues**: [GitHub Issues](https://github.com/your-username/youtube-audio-downloader/issues)
- **Discussions**: [GitHub Discussions](https://github.com/your-username/youtube-audio-downloader/discussions)
- **Documentation**: [Wiki](https://github.com/your-username/youtube-audio-downloader/wiki)

---

**⭐ Star this repository if you find it useful!**
