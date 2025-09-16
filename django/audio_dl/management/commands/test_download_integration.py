"""
Django management command to test download integration.
"""

from django.core.management.base import BaseCommand, CommandError
from django.contrib.auth.models import User
from audio_dl.models import DownloadSession, AudioDownload
import sys
from pathlib import Path

# Add the src directory to Python path for imports
current_dir = Path(__file__).resolve().parent
project_root = current_dir.parent.parent.parent.parent.parent / 'my_project'
src_path = project_root / 'src'
sys.path.insert(0, str(src_path))

# Also add the project root to find the src modules
sys.path.insert(0, str(project_root))

try:
    from yt_audio_dl.audio_core import AudioDownloader, AudioDownloadError
    from common.logging_config import setup_logging
    AUDIO_DOWNLOADER_AVAILABLE = True
except ImportError as e:
    AUDIO_DOWNLOADER_AVAILABLE = False
    setup_logging = None


class Command(BaseCommand):
    help = 'Test download integration with Django models'

    def handle(self, *args, **options):
        if not AUDIO_DOWNLOADER_AVAILABLE:
            self.stdout.write(self.style.ERROR("Audio downloader components not available"))
            return
            
        # Initialize logging
        setup_logging()
        
        self.stdout.write("Testing download integration...")
        
        # Get or create a test user
        user, created = User.objects.get_or_create(
            username='testuser',
            defaults={'email': 'test@example.com'}
        )
        if created:
            user.set_password('testpass123')
            user.save()
            self.stdout.write("Created test user")
        else:
            self.stdout.write("Using existing test user")
        
        # Create a test session
        session, created = DownloadSession.objects.get_or_create(
            session_name='Test Session',
            user=user,
            defaults={'status': 'pending'}
        )
        if created:
            self.stdout.write("Created test session")
        else:
            self.stdout.write("Using existing test session")
        
        # Create a test download
        test_url = "https://www.youtube.com/watch?v=dQw4w9WgXcQ"
        download, created = AudioDownload.objects.get_or_create(
            url=test_url,
            session=session,
            defaults={
                'title': 'Test Download',
                'status': 'pending'
            }
        )
        if created:
            self.stdout.write("Created test download")
        else:
            self.stdout.write("Using existing test download")
        
        self.stdout.write(f"Download ID: {download.id}")
        self.stdout.write(f"Download Status: {download.status}")
        self.stdout.write(f"Download URL: {download.url}")
        
        # Test the start_download view logic
        self.stdout.write("\nTesting download logic...")
        
        if download.status != 'pending':
            self.stdout.write(self.style.ERROR(f"Download is not in pending status: {download.status}"))
            return
        
        # Audio downloader components are already imported
        self.stdout.write("✓ Audio downloader components imported successfully")
        
        # Test downloader creation
        try:
            downloader = AudioDownloader(output_dir=Path.cwd() / 'test_downloads')
            self.stdout.write("✓ AudioDownloader created successfully")
        except Exception as e:
            self.stdout.write(self.style.ERROR(f"Failed to create AudioDownloader: {e}"))
            return
        
        # Test URL validation
        try:
            if downloader.validate_url(download.url):
                self.stdout.write("✓ URL validation passed")
            else:
                self.stdout.write(self.style.ERROR("URL validation failed"))
                return
        except Exception as e:
            self.stdout.write(self.style.ERROR(f"URL validation error: {e}"))
            return
        
        self.stdout.write(self.style.SUCCESS("All tests passed! Download integration should work."))
        self.stdout.write(f"\nTo test in the browser:")
        self.stdout.write(f"1. Go to http://127.0.0.1:8000/sessions/{session.id}/")
        self.stdout.write(f"2. Click the green play button for download {download.id}")
        self.stdout.write(f"3. Check browser console for any JavaScript errors")
