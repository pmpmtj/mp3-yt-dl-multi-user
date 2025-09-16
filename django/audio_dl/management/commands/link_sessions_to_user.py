#!/usr/bin/env python3
"""
Django management command to link existing download sessions to a user.

This command helps link sessions that were created via the API (without authentication)
to a specific user account.

Usage:
    python manage.py link_sessions_to_user --username admin --hours 24
    python manage.py link_sessions_to_user --username admin --session-id 12345678-1234-1234-1234-123456789abc
"""

from django.core.management.base import BaseCommand, CommandError
from django.contrib.auth.models import User
from django.utils import timezone
from datetime import timedelta
from audio_dl.models import DownloadSession


class Command(BaseCommand):
    help = 'Link existing download sessions to a user account'

    def add_arguments(self, parser):
        parser.add_argument(
            '--username',
            type=str,
            required=True,
            help='Username to link sessions to'
        )
        parser.add_argument(
            '--hours',
            type=int,
            default=24,
            help='Number of hours back to look for unlinked sessions (default: 24)'
        )
        parser.add_argument(
            '--session-id',
            type=str,
            help='Specific session ID to link (UUID format)'
        )
        parser.add_argument(
            '--dry-run',
            action='store_true',
            help='Show what would be linked without actually doing it'
        )

    def handle(self, *args, **options):
        username = options['username']
        hours = options['hours']
        session_id = options.get('session_id')
        dry_run = options['dry_run']

        # Get the user
        try:
            user = User.objects.get(username=username)
        except User.DoesNotExist:
            raise CommandError(f'User "{username}" does not exist')

        if session_id:
            # Link a specific session
            try:
                session = DownloadSession.objects.get(id=session_id)
                if session.user is not None:
                    self.stdout.write(
                        self.style.WARNING(
                            f'Session {session_id} is already linked to user: {session.user.username}'
                        )
                    )
                    return

                if dry_run:
                    self.stdout.write(
                        self.style.SUCCESS(
                            f'[DRY RUN] Would link session "{session.session_name}" to user "{username}"'
                        )
                    )
                else:
                    session.user = user
                    session.save()
                    self.stdout.write(
                        self.style.SUCCESS(
                            f'Linked session "{session.session_name}" to user "{username}"'
                        )
                    )

            except DownloadSession.DoesNotExist:
                raise CommandError(f'Session with ID "{session_id}" does not exist')

        else:
            # Link sessions from the last N hours
            cutoff_time = timezone.now() - timedelta(hours=hours)
            
            unlinked_sessions = DownloadSession.objects.filter(
                user__isnull=True,
                created_at__gte=cutoff_time
            ).order_by('-created_at')

            if not unlinked_sessions.exists():
                self.stdout.write(
                    self.style.WARNING(
                        f'No unlinked sessions found in the last {hours} hours'
                    )
                )
                return

            self.stdout.write(
                self.style.SUCCESS(
                    f'Found {unlinked_sessions.count()} unlinked sessions in the last {hours} hours'
                )
            )

            linked_count = 0
            for session in unlinked_sessions:
                if dry_run:
                    self.stdout.write(
                        f'[DRY RUN] Would link: "{session.session_name}" '
                        f'(created: {session.created_at.strftime("%Y-%m-%d %H:%M")}, '
                        f'downloads: {session.total_downloads})'
                    )
                else:
                    session.user = user
                    session.save()
                    linked_count += 1
                    self.stdout.write(
                        f'Linked: "{session.session_name}" '
                        f'(created: {session.created_at.strftime("%Y-%m-%d %H:%M")}, '
                        f'downloads: {session.total_downloads})'
                    )

            if not dry_run:
                self.stdout.write(
                    self.style.SUCCESS(
                        f'Successfully linked {linked_count} sessions to user "{username}"'
                    )
                )
