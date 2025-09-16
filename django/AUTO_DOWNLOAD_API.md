# Auto-Download API Documentation

## Overview

The Auto-Download API provides a simple, no-authentication-required endpoint for external applications to download audio files from YouTube URLs. This service automatically handles session management, file organization, and returns direct download links.

## Endpoint

```
POST /audio_dl/api/auto-download/
```

## Request

### Headers
```
Content-Type: application/json
```

### Request Body
```json
{
    "url": "https://youtube.com/watch?v=VIDEO_ID",
    "quality": "best",     // Optional: "best", "worst", "128k", "192k", "320k"
    "format": "mp3",       // Optional: "mp3", "wav", "flac"
    "username": "pmpmt"  // Optional: Django username for session linking
}
```

### Required Fields
- `url`: YouTube video URL (youtube.com or youtu.be)

### Optional Fields
- `quality`: Audio quality (default: "best")
- `format`: Audio format (default: "mp3")
- `username`: Django username to link the session to (default: null - unlinked session)

## Response

### Success Response (200 OK)
```json
{
    "success": true,
    "file_path": "/media/downloads/session_uuid/job_uuid/filename.mp3",
    "download_url": "http://localhost:8000/media/downloads/session_uuid/job_uuid/filename.mp3",
    "title": "Video Title",
    "artist": "Channel Name",
    "file_size": 4946683,
    "duration": "00:03:26",
    "quality": "best",
    "format": "mp3",
    "session_id": "session-uuid",
    "job_id": "job-uuid",
    "database_session_id": "database-session-uuid",
    "database_download_id": "database-download-uuid",
    "linked_to_user": "username"  // Present if username was provided and found
}
```

### Error Response (400/500)
```json
{
    "success": false,
    "error": "Error message description"
}
```

## Usage Examples

### Python
```python
import requests
import json

# Basic download
response = requests.post(
    "http://localhost:8000/audio_dl/api/auto-download/",
    headers={"Content-Type": "application/json"},
    data=json.dumps({
        "url": "https://youtube.com/watch?v=XNNjYas8Xo8"
    })
)

if response.json()["success"]:
    download_url = response.json()["download_url"]
    print(f"Download available at: {download_url}")
else:
    print(f"Error: {response.json()['error']}")
```

### JavaScript/Node.js
```javascript
const axios = require('axios');

async function downloadAudio(url) {
    try {
        const response = await axios.post('http://localhost:8000/audio_dl/api/auto-download/', {
            url: url,
            quality: 'best',
            format: 'mp3'
        });
        
        if (response.data.success) {
            console.log('Download URL:', response.data.download_url);
            return response.data.download_url;
        } else {
            console.error('Error:', response.data.error);
        }
    } catch (error) {
        console.error('Request failed:', error.message);
    }
}

// Usage
downloadAudio('https://youtube.com/watch?v=XNNjYas8Xo8');
```

### cURL
```bash
# Basic usage (unlinked session)
curl -X POST http://localhost:8000/audio_dl/api/auto-download/ \
  -H "Content-Type: application/json" \
  -d '{
    "url": "https://youtube.com/watch?v=XNNjYas8Xo8",
    "quality": "best",
    "format": "mp3"
  }'

# With username (linked session)
curl -X POST http://localhost:8000/audio_dl/api/auto-download/ \
  -H "Content-Type: application/json" \
  -d '{
    "url": "https://youtube.com/watch?v=XNNjYas8Xo8",
    "quality": "best",
    "format": "mp3",
    "username": "your_username"
  }'
```

### PowerShell
```powershell
# Basic usage (unlinked session)
$body = @{
    url = "https://youtube.com/watch?v=XNNjYas8Xo8"
    quality = "best"
    format = "mp3"
} | ConvertTo-Json

# With username (linked session)
$body = @{
    url = "https://youtube.com/watch?v=XNNjYas8Xo8"
    quality = "best"
    format = "mp3"
    username = "your_username"
} | ConvertTo-Json

$response = Invoke-RestMethod -Uri "http://localhost:8000/audio_dl/api/auto-download/" -Method POST -Body $body -ContentType "application/json"

if ($response.success) {
    Write-Host "Download URL: $($response.download_url)"
} else {
    Write-Host "Error: $($response.error)"
}
```

## File Organization

Downloaded files are organized using the following structure:
```
django/my_downloader/media/downloads/
├── session_uuid_1/
│   ├── job_uuid_1/
│   │   └── audio_file.mp3
│   └── job_uuid_2/
│       └── audio_file.mp3
└── session_uuid_2/
    └── job_uuid_3/
        └── audio_file.mp3
```

## Error Codes

| Status Code | Description |
|-------------|-------------|
| 400 | Bad Request - Invalid JSON, missing URL, or unsupported URL format |
| 500 | Internal Server Error - Download failed, service unavailable |

## Common Error Messages

- `"URL is required"` - No URL provided in request
- `"Only YouTube URLs are supported"` - URL is not from YouTube
- `"Invalid JSON in request body"` - Malformed JSON request
- `"Audio downloader not available"` - Service components not loaded
- `"Download failed"` - General download failure

## Rate Limiting

Currently no rate limiting is implemented. For production use, consider implementing:
- Request rate limiting per IP
- Concurrent download limits
- API key authentication

## Python Client Library

A Python client library is provided for easy integration:

```python
from auto_download_client import AutoDownloadClient

# Basic usage (unlinked session)
client = AutoDownloadClient()
result = client.download("https://youtube.com/watch?v=XNNjYas8Xo8")

# With username (linked session)
client = AutoDownloadClient(username="your_username")
result = client.download("https://youtube.com/watch?v=XNNjYas8Xo8")

# Command line usage
# python auto_download_client.py "https://youtu.be/VIDEO_ID" --username your_username
```

## Database Integration

The auto-download API automatically creates database entries for tracking:

- **DownloadSession**: Created for each auto-download request
- **AudioDownload**: Created for each individual download
- **DownloadHistory**: Created upon successful completion

**Session Linking:**
- Sessions with `username` parameter are linked to the specified Django user
- Sessions without `username` remain unlinked (`user=null`)
- Linked sessions appear in the Django web interface when logged in
- Unlinked sessions can be linked later using the management command

**Database Fields Populated:**
- Session name, status, timestamps
- Download title, artist, duration, file size
- File path, quality, format
- Error messages (if failed)
- Completion timestamps
- User association (if username provided)

**Accessing Downloads:**
- View in Django admin: `/admin/audio_dl/`
- Query via Django ORM
- Track via web interface (if user is logged in and session is linked)
- Link existing sessions: `python manage.py link_sessions_to_user --username your_username --hours 24`

## Security Notes

- No authentication required (public endpoint)
- Only YouTube URLs are accepted
- Files are stored in Django's MEDIA_ROOT
- Temporary sessions are created for each request
- All downloads are tracked in the database

## Integration Tips

1. **Handle Errors**: Always check the `success` field in the response
2. **Use Download URL**: The `download_url` field provides the direct file access
3. **File Cleanup**: Consider implementing cleanup for old temporary sessions
4. **Async Processing**: For large files, consider implementing async processing
5. **Progress Tracking**: Current implementation is synchronous; progress tracking can be added

## Testing

Test the API using the provided examples or with tools like Postman:

1. Start the Django server: `python manage.py runserver`
2. Send a POST request to `http://localhost:8000/audio_dl/api/auto-download/`
3. Check the response for success/error status
4. Access the file using the provided download URL
