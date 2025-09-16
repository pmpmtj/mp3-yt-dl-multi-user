#!/usr/bin/env python3
"""
Django management command to fix session statuses that are incorrect.

This command checks for sessions with incorrect statuses and updates them
based on their download statuses.

Usage:
    python manage.py fix_session_status
    python manage.py fix_session_status --dry-run
"""

from django.core.management.base import BaseCommand
from audio_dl.models import DownloadSession


class Command(BaseCommand):
    help = 'Fix session statuses that are incorrect based on download statuses'

    def add_arguments(self, parser):
        parser.add_argument(
            '--dry-run',
            action='store_true',
            help='Show what would be fixed without actually doing it'
        )

    def handle(self, *args, **options):
        dry_run = options['dry_run']
        
        # Find sessions that might have incorrect statuses
        sessions_to_check = DownloadSession.objects.all()
        
        fixed_count = 0
        
        for session in sessions_to_check:
            # Get current download counts by status
            total_downloads = session.downloads.count()
            completed_downloads = session.downloads.filter(status='completed').count()
            cancelled_downloads = session.downloads.filter(status='cancelled').count()
            failed_downloads = session.downloads.filter(status='failed').count()
            active_downloads = session.downloads.filter(status__in=['downloading', 'pending']).count()
            
            # Determine what the correct status should be
            correct_status = session.status
            
            if total_downloads == 0:
                correct_status = 'pending'
            elif completed_downloads == total_downloads:
                correct_status = 'completed'
            elif active_downloads > 0:
                correct_status = 'in_progress'
            elif failed_downloads > 0 and active_downloads == 0:
                correct_status = 'failed'
            elif cancelled_downloads == total_downloads and active_downloads == 0:
                correct_status = 'cancelled'
            
            # Check if status needs to be fixed
            if session.status != correct_status:
                if dry_run:
                    self.stdout.write(
                        f"[DRY RUN] Would fix session '{session.session_name}' "
                        f"from '{session.status}' to '{correct_status}' "
                        f"(downloads: {total_downloads}, completed: {completed_downloads}, "
                        f"cancelled: {cancelled_downloads}, failed: {failed_downloads}, active: {active_downloads})"
                    )
                else:
                    session.status = correct_status
                    session.save(update_fields=['status'])
                    fixed_count += 1
                    self.stdout.write(
                        f"Fixed session '{session.session_name}' from '{session.status}' to '{correct_status}'"
                    )
        
        if not dry_run:
            self.stdout.write(
                self.style.SUCCESS(f'Successfully fixed {fixed_count} session statuses')
            )
        else:
            self.stdout.write(
                self.style.SUCCESS(f'Would fix {fixed_count} session statuses')
            )