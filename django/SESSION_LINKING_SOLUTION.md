# Session Linking Solution

## Problem
When using the auto-download API (via `auto_download_client.py`), download sessions were not appearing in the user's account when logged into the Django web interface. This happened because:

1. The auto-download API created sessions without linking them to any user (`user=null`)
2. The Django session list view only shows sessions for the logged-in user
3. The auto-download client didn't support user linking

## Solution

### 1. Enhanced Auto-Download API
- **Modified**: `django/audio_dl/views.py` - `auto_download` view
- **Changes**:
  - Added optional `username` parameter to API request
  - Modified session creation to link to user if username is provided and exists
  - Kept `@csrf_exempt` for simplicity (no complex authentication required)
  - Sessions created via API are now linked to the specified user

### 2. Enhanced Auto-Download Client
- **Modified**: `django/auto_download_client.py`
- **Changes**:
  - Added simple `username` parameter support
  - Sends username in API request payload for session linking
  - No complex authentication required - just pass the username
  - Added command-line argument for username

### 3. Session Linking Management
- **Added**: `django/audio_dl/management/commands/link_sessions_to_user.py`
- **Purpose**: Link existing unlinked sessions to users
- **Usage**: `python manage.py link_sessions_to_user --username admin --hours 24`

### 4. Additional API Endpoints
- **Added**: `link_session_to_user` view - Link specific sessions to current user
- **Added**: `unlinked_sessions` view - Get list of unlinked sessions
- **URLs**: Added to `django/audio_dl/urls.py`

## Usage

### For New Downloads (Recommended)
Use the enhanced auto-download client with username parameter:

```bash
# With username (sessions will appear in your account)
python src/api/auto_download_client.py "https://youtu.be/dQw4w9WgXcQ" --username your_username

# Without username (sessions won't appear in your account)
python src/api/auto_download_client.py "https://youtu.be/dQw4w9WgXcQ"
```

### For Existing Unlinked Sessions
Link existing sessions to your account:

```bash
# Link all sessions from the last 24 hours to a user
python django/my_downloader/manage.py link_sessions_to_user --username your_username --hours 24

# Link a specific session
python django/my_downloader/manage.py link_sessions_to_user --username your_username --session-id 12345678-1234-1234-1234-123456789abc

# Dry run to see what would be linked
python django/my_downloader/manage.py link_sessions_to_user --username your_username --hours 24 --dry-run
```

### Via Django Web Interface
1. Log into your Django account
2. Visit `/api/unlinked-sessions/` to see unlinked sessions
3. Use the link endpoints to associate sessions with your account

## Technical Details

### Database Changes
- No database migrations required
- The `DownloadSession.user` field already supports `null=True, blank=True`
- Existing sessions remain unlinked until explicitly linked

### User Linking Flow
1. Client sends API request with optional `username` parameter
2. Django looks up the user by username
3. If user exists, session is linked to that user
4. If user doesn't exist, session remains unlinked (with warning logged)
5. No complex authentication required - simple username lookup

### Backward Compatibility
- API calls without username still work (sessions just won't be linked)
- Existing unlinked sessions can be linked later using management command
- No breaking changes to existing functionality

## Files Modified

1. `django/audio_dl/views.py` - Enhanced auto-download view and added linking views
2. `src/api/auto_download_client.py` - Added username parameter support (moved from django/)
3. `django/audio_dl/urls.py` - Added new URL patterns
4. `django/audio_dl/management/commands/link_sessions_to_user.py` - New management command

## Testing

To test the solution:

1. **Test downloads with username**:
   ```bash
   python src/api/auto_download_client.py "https://youtu.be/dQw4w9WgXcQ" --username your_username
   ```

2. **Check sessions appear in Django interface**:
   - Log into Django admin or web interface
   - Navigate to sessions list
   - Verify the session appears

3. **Test linking existing sessions**:
   ```bash
   python django/my_downloader/manage.py link_sessions_to_user --username your_username --hours 24 --dry-run
   ```

4. **Verify all sessions are linked**:
   ```bash
   python django/my_downloader/manage.py shell -c "from audio_dl.models import DownloadSession; from django.contrib.auth.models import User; user = User.objects.get(username='your_username'); sessions = DownloadSession.objects.filter(user=user); print(f'Found {sessions.count()} sessions for user {user.username}')"
   ```

## Results

✅ **Successfully tested and working:**
- New downloads with `--username` parameter are automatically linked to user accounts
- Existing unlinked sessions can be linked using the management command
- All sessions now appear in the Django web interface when logged in
- Backward compatibility maintained for API calls without username

The solution ensures that all future downloads via the API will be properly linked to user accounts, and provides tools to link existing unlinked sessions.
