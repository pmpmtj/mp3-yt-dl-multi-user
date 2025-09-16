# Audio Downloader Django Application

This Django application provides a web interface for managing audio downloads with session-based organization.

## Project Structure

```
django/
├── my_downloader/          # Main Django project
│   ├── manage.py           # Django management script
│   └── my_downloader/      # Project settings
│       ├── __init__.py
│       ├── settings.py     # Django settings
│       ├── urls.py         # Main URL configuration
│       ├── wsgi.py         # WSGI configuration
│       └── asgi.py         # ASGI configuration
└── audio_dl/               # Audio downloader app
    ├── __init__.py
    ├── apps.py             # App configuration
    ├── models.py           # Database models
    ├── views.py            # View functions
    ├── urls.py             # App URL patterns
    ├── admin.py            # Admin interface
    ├── forms.py            # Form definitions
    ├── tests.py            # Test cases
    ├── migrations/         # Database migrations
    ├── templates/          # HTML templates
    │   └── audio_dl/
    └── static/             # Static files (CSS, JS)
        └── audio_dl/
```

## Features

### Models
- **DownloadSession**: Organizes downloads into sessions
- **AudioDownload**: Individual audio download records
- **DownloadHistory**: Tracks download performance metrics

### Views
- Session management (list, create, detail, delete)
- Download management (add, start, cancel, delete)
- Real-time status updates via AJAX
- Search and filtering capabilities

### Admin Interface
- Full CRUD operations for all models
- Custom admin configurations with progress bars
- User-based filtering for security

### Templates
- Responsive Bootstrap-based UI
- Real-time status updates
- Form validation and error handling
- Pagination for large datasets

## Installation

1. Navigate to the Django project directory:
   ```bash
   cd django/my_downloader
   ```

2. Install dependencies:
   ```bash
   pip install -r ../../requirements.txt
   ```

3. Run migrations:
   ```bash
   python manage.py migrate
   ```

4. Create a superuser:
   ```bash
   python manage.py createsuperuser
   ```

5. Run the development server:
   ```bash
   python manage.py runserver
   ```

## Usage

1. Access the application at `http://localhost:8000`
2. Log in with your superuser credentials
3. Create a new download session
4. Add audio URLs to the session
5. Start downloads and monitor progress

## API Endpoints

### Sessions
- `GET /` - Home page
- `GET /sessions/` - List all sessions
- `POST /sessions/create/` - Create new session
- `GET /sessions/<id>/` - Session detail
- `DELETE /sessions/<id>/delete/` - Delete session
- `GET /sessions/<id>/status/` - Session status (JSON)

### Downloads
- `POST /sessions/<id>/add/` - Add download to session
- `POST /downloads/<id>/start/` - Start download
- `POST /downloads/<id>/cancel/` - Cancel download
- `DELETE /downloads/<id>/delete/` - Delete download
- `GET /downloads/<id>/status/` - Download status (JSON)

## Configuration

The application uses SQLite by default. To use a different database, update the `DATABASES` setting in `my_downloader/settings.py`.

## Security

- User authentication required for all operations
- CSRF protection enabled
- User-based data filtering in admin interface
- Input validation and sanitization

## Development

### Running Tests
```bash
python manage.py test audio_dl
```

### Creating Migrations
```bash
python manage.py makemigrations audio_dl
```

### Collecting Static Files
```bash
python manage.py collectstatic
```

## Integration

This Django application is designed to integrate with the existing audio downloader backend. The views in `audio_dl/views.py` contain placeholder code for starting downloads - these should be connected to your existing download functionality.

## License

This project is part of the Audio Downloader application.
