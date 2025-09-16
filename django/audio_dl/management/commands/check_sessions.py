"""
Django management command to check sessions in the database.
"""

from django.core.management.base import BaseCommand
from audio_dl.models import DownloadSession, AudioDownload


class Command(BaseCommand):
    help = 'Check sessions and downloads in the database'

    def handle(self, *args, **options):
        self.stdout.write("=== Database Check ===")
        
        # Check sessions
        session_count = DownloadSession.objects.count()
        self.stdout.write(f"Total sessions: {session_count}")
        
        if session_count > 0:
            self.stdout.write("\nSessions:")
            for session in DownloadSession.objects.all()[:10]:
                self.stdout.write(f"  - {session.session_name} ({session.id}) - {session.status}")
                self.stdout.write(f"    User: {session.user}")
                self.stdout.write(f"    Created: {session.created_at}")
                self.stdout.write(f"    Downloads: {session.total_downloads} total, {session.completed_downloads} completed")
                self.stdout.write("")
        else:
            self.stdout.write("No sessions found in database")
        
        # Check downloads
        download_count = AudioDownload.objects.count()
        self.stdout.write(f"Total downloads: {download_count}")
        
        if download_count > 0:
            self.stdout.write("\nRecent downloads:")
            for download in AudioDownload.objects.all()[:5]:
                self.stdout.write(f"  - {download.title or 'Unknown'} - {download.status}")
                self.stdout.write(f"    Session: {download.session.session_name if download.session else 'None'}")
                self.stdout.write(f"    URL: {download.url}")
                self.stdout.write("")
        else:
            self.stdout.write("No downloads found in database")
