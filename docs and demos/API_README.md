# YouTube Downloader API

A multiuser YouTube downloader API built with FastAPI, featuring session management, job processing, and comprehensive monitoring.

## 🚀 Quick Start

### 1. Install Dependencies
```bash
pip install -r requirements.txt
```

### 2. Start the API Server
```bash
python run_api.py
```

### 3. Access the API
- **API Documentation**: http://localhost:8000/docs
- **Health Check**: http://localhost:8000/api/health
- **Root Endpoint**: http://localhost:8000/

## 📋 API Endpoints

### Session Management

#### Create Session
```http
POST /api/sessions/
```
Creates a new anonymous user session with isolated download directories.

**Response:**
```json
{
  "session_uuid": "550e8400-e29b-41d4-a716-446655440000",
  "created_at": "2024-01-15T10:30:00Z",
  "last_activity": "2024-01-15T10:30:00Z",
  "is_active": true,
  "total_jobs": 0,
  "active_jobs": 0,
  "completed_jobs": 0,
  "failed_jobs": 0,
  "storage_used_bytes": 0,
  "age_hours": 0.0
}
```

#### Get Session Info
```http
GET /api/sessions/{session_uuid}
```

#### List Active Sessions
```http
GET /api/sessions/
```

#### Get Session Statistics
```http
GET /api/sessions/stats/overview
```

### Job Management

#### Create Download Job
```http
POST /api/jobs/
Headers: X-Session-ID: {session_uuid}
Content-Type: application/json

{
  "url": "https://www.youtube.com/watch?v=dQw4w9WgXcQ",
  "media_type": "video",
  "quality": "best",
  "output_format": "mp4"
}
```

**Response:**
```json
{
  "job_uuid": "job-1-1705312200",
  "session_uuid": "550e8400-e29b-41d4-a716-446655440000",
  "job_url": "https://www.youtube.com/watch?v=dQw4w9WgXcQ",
  "media_type": "video",
  "status": "pending",
  "created_at": "2024-01-15T10:30:00Z",
  "progress_percent": null,
  "error_message": null,
  "output_path": null,
  "file_size_bytes": null
}
```

#### Get Job Status
```http
GET /api/jobs/{job_id}
Headers: X-Session-ID: {session_uuid}
```

#### List Session Jobs
```http
GET /api/jobs/
Headers: X-Session-ID: {session_uuid}
```

#### Get Download Paths
```http
GET /api/jobs/{job_id}/paths
Headers: X-Session-ID: {session_uuid}
```

### Health & Monitoring

#### Health Check
```http
GET /api/health
```

#### Simple Health Check
```http
GET /api/health/simple
```

#### System Metrics
```http
GET /api/metrics
```

#### Detailed Status
```http
GET /api/status
```

## 🔧 Configuration

### Session Limits
- **Max Concurrent Sessions**: 100
- **Max Jobs per Session**: 10
- **Session Timeout**: 24 hours

### Download Structure
```
downloads/
├── session-uuid-1/
│   ├── job-uuid-1/
│   │   ├── audio/
│   │   ├── video/
│   │   └── transcripts/
│   └── job-uuid-2/
└── session-uuid-2/
```

## 🧪 Testing

### Run API Tests
```bash
python "docs and demos/test_api.py"
```

### Manual Testing with curl

#### 1. Create Session
```bash
curl -X POST "http://localhost:8000/api/sessions/" \
  -H "Content-Type: application/json"
```

#### 2. Create Job
```bash
curl -X POST "http://localhost:8000/api/jobs/" \
  -H "X-Session-ID: YOUR_SESSION_UUID" \
  -H "Content-Type: application/json" \
  -d '{
    "url": "https://www.youtube.com/watch?v=dQw4w9WgXcQ",
    "media_type": "video",
    "quality": "best"
  }'
```

#### 3. Check Job Status
```bash
curl -X GET "http://localhost:8000/api/jobs/JOB_ID" \
  -H "X-Session-ID: YOUR_SESSION_UUID"
```

## 🏗️ Architecture

### Components
- **FastAPI**: Web framework and API endpoints
- **Session Manager**: Thread-safe session management
- **Job Queue**: In-memory job processing
- **User Context**: Isolated user environments
- **Health Monitoring**: System status and metrics

### Key Features
- ✅ **Multiuser Support**: Anonymous session-based users
- ✅ **Thread Safety**: Concurrent access with proper locking
- ✅ **Session Isolation**: Separate download directories per user
- ✅ **Job Tracking**: Complete job lifecycle management
- ✅ **Health Monitoring**: System status and performance metrics
- ✅ **Background Processing**: Async job execution
- ✅ **Rate Limiting**: Per-session job limits
- ✅ **Error Handling**: Comprehensive error responses

## 🔄 Job Lifecycle

1. **Pending**: Job created, waiting to start
2. **Processing**: Job actively downloading
3. **Completed**: Job finished successfully
4. **Failed**: Job encountered an error
5. **Cancelled**: Job was cancelled by user

## 📊 Monitoring

### Health Status
- **Healthy**: All systems normal
- **Degraded**: High resource usage or approaching limits
- **Unhealthy**: Critical system issues

### Metrics Tracked
- Active/total sessions
- Active/total jobs
- Storage usage
- System resources (CPU, memory, disk)
- Uptime and performance

## 🚀 Next Steps

### Planned Features
- [ ] **Database Integration**: PostgreSQL for persistent storage
- [ ] **User Authentication**: Registration and login system
- [ ] **Real Download Engine**: yt-dlp integration
- [ ] **WebSocket Support**: Real-time job progress updates
- [ ] **File Management**: Download cleanup and organization
- [ ] **Rate Limiting**: Advanced per-user limits
- [ ] **Caching**: Redis for improved performance

### Migration Path
The current in-memory system is designed for easy migration to PostgreSQL:
- Session data → User profiles table
- Job storage → Jobs table
- In-memory queue → Database-backed queue
- Anonymous sessions → Registered users

## 🐛 Troubleshooting

### Common Issues

#### API Not Starting
- Check if port 8000 is available
- Verify all dependencies are installed
- Check logs for error messages

#### Session Not Found
- Verify session UUID is correct
- Check if session has expired (24-hour timeout)
- Ensure session is active

#### Job Creation Failed
- Verify session exists and is active
- Check if session has reached job limit (10 jobs)
- Ensure valid YouTube URL format

### Logs
- Application logs: `logs/app.log`
- Error logs: `logs/error.log`
- Console output shows real-time activity

## 📝 API Examples

See `docs and demos/test_api.py` for comprehensive usage examples and `docs and demos/demo_session_manager.py` for session management examples.
