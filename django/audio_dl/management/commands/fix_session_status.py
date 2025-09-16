"""
Django management command to fix session statuses based on download progress.
"""

from django.core.management.base import BaseCommand
from audio_dl.models import DownloadSession


class Command(BaseCommand):
    help = 'Fix session statuses based on download progress'

    def handle(self, *args, **options):
        self.stdout.write("=== Fixing Session Statuses ===")
        
        sessions = DownloadSession.objects.all()
        fixed_count = 0
        
        for session in sessions:
            old_status = session.status
            
            # Update counters first
            session.total_downloads = session.downloads.count()
            session.completed_downloads = session.downloads.filter(status='completed').count()
            
            # Update session status based on download progress
            if session.total_downloads == 0:
                session.status = 'pending'
            elif session.completed_downloads == session.total_downloads:
                session.status = 'completed'
            elif session.downloads.filter(status__in=['downloading', 'pending']).exists():
                session.status = 'in_progress'
            elif session.downloads.filter(status='failed').exists():
                # If there are failed downloads but no active ones
                if not session.downloads.filter(status__in=['downloading', 'pending']).exists():
                    session.status = 'failed'
            
            if old_status != session.status:
                session.save(update_fields=['total_downloads', 'completed_downloads', 'status'])
                self.stdout.write(f"Session '{session.session_name}': {old_status} → {session.status}")
                fixed_count += 1
            else:
                session.save(update_fields=['total_downloads', 'completed_downloads'])
        
        self.stdout.write(f"\nFixed {fixed_count} sessions")
        
        # Show current status
        self.stdout.write("\n=== Current Session Statuses ===")
        for session in sessions:
            self.stdout.write(f"  - {session.session_name}: {session.status} ({session.completed_downloads}/{session.total_downloads} completed)")
