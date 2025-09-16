# Django Integration with Audio Downloader

This document explains how the Django application integrates with the existing audio downloader core.

## 🚀 Quick Start

### 1. Environment Setup

Create a `.env` file in the `django/` directory:

```bash
cp .env.example .env
```

Edit the `.env` file with your database configuration:

```env
DATABASE_NAME=audio_downloader
DATABASE_USER=postgres
DATABASE_PASSWORD=your_password_here
DATABASE_HOST=localhost
DATABASE_PORT=5432
```

### 2. Install Dependencies

```bash
pip install -r requirements.txt
```

### 3. Database Setup

```bash
cd django/my_downloader
python manage.py migrate
python manage.py createsuperuser
```

### 4. Run the Server

```bash
python manage.py runserver
```

Visit `http://localhost:8000` to access the application.

## 🔧 Integration Details

### Audio Downloader Integration

The Django views now integrate with the existing audio downloader core:

- **Location**: `django/audio_dl/views.py`
- **Core Module**: `src/yt_audio_dl/audio_core.py`
- **Session Manager**: `src/common/session_manager.py`

### Key Features

1. **Real Audio Downloads**: The `start_download` view now uses the actual `AudioDownloader` class
2. **Progress Tracking**: Downloads show real progress and status updates
3. **Error Handling**: Comprehensive error handling with user-friendly messages
4. **Metadata Extraction**: Automatically extracts title, artist, and duration
5. **File Management**: Downloads are organized by session in the media directory

### Database Integration

- **PostgreSQL**: Uses your existing PostgreSQL database configuration
- **Models**: Django models for `DownloadSession`, `AudioDownload`, and `DownloadHistory`
- **Migrations**: Automatic database schema management

### API Endpoints

The Django application provides both web interface and API endpoints:

#### Web Interface
- `/` - Home page
- `/sessions/` - List download sessions
- `/sessions/create/` - Create new session
- `/sessions/<id>/` - Session detail page
- `/sessions/<id>/add/` - Add downloads to session

#### API Endpoints (JSON)
- `POST /downloads/<id>/start/` - Start download
- `POST /downloads/<id>/cancel/` - Cancel download
- `GET /downloads/<id>/status/` - Get download status
- `DELETE /downloads/<id>/delete/` - Delete download

## 🧪 Testing

### Test the Integration

Run the integration test script:

```bash
python test_django_integration.py
```

### Test Audio Download

Use the Django management command:

```bash
cd django/my_downloader
python manage.py test_download "https://www.youtube.com/watch?v=dQw4w9WgXcQ"
```

### Manual Testing

1. Start the Django server
2. Create a superuser account
3. Log in and create a download session
4. Add a YouTube URL
5. Start the download
6. Monitor progress and completion

## 📁 File Structure

```
django/
├── my_downloader/           # Django project
│   ├── settings.py          # Updated with PostgreSQL config
│   └── ...
├── audio_dl/                # Django app
│   ├── views.py             # Integrated with audio downloader
│   ├── models.py            # Database models
│   ├── forms.py             # Form handling
│   ├── management/          # Custom commands
│   │   └── commands/
│   │       └── test_download.py
│   └── ...
├── .env.example             # Environment template
└── INTEGRATION_README.md    # This file
```

## 🔄 Migration from FastAPI

The integration maintains compatibility with your existing codebase:

- **Core Engine**: Uses the same `AudioDownloader` class
- **Session Management**: Integrates with your custom session manager
- **Database**: Uses your PostgreSQL configuration
- **Logging**: Uses your centralized logging system

## 🚨 Troubleshooting

### Common Issues

1. **Import Errors**: Make sure the `src/` directory is in the Python path
2. **Database Connection**: Check PostgreSQL is running and `.env` is configured
3. **Audio Downloads**: Ensure yt-dlp is installed and working
4. **Permissions**: Check file permissions for the media directory

### Debug Mode

Enable debug logging by setting `DEBUG=True` in settings.py and check the logs.

## 🎯 Next Steps

1. **Background Tasks**: Implement Celery for async downloads
2. **Real-time Updates**: Add WebSocket support for live progress
3. **User Management**: Enhance user authentication and permissions
4. **API Documentation**: Add Swagger/OpenAPI documentation
5. **Production Setup**: Configure for production deployment

## 📝 Notes

- The integration preserves all existing functionality
- No changes were made to the core audio downloader
- Database schema is managed by Django migrations
- All existing tests should continue to work
