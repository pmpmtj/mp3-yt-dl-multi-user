#!/usr/bin/env python3
"""
Script to check if auto-download entries are being created in the database.
"""

import os
import sys
import django
from pathlib import Path

# Add Django project to path
project_root = Path(__file__).resolve().parent
django_path = project_root / 'django' / 'my_downloader'
sys.path.insert(0, str(django_path))

# Set up Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'my_downloader.settings')
django.setup()

from audio_dl.models import DownloadSession, AudioDownload

def check_recent_downloads():
    """Check recent downloads in the database."""
    print("=== Recent Download Sessions ===")
    recent_sessions = DownloadSession.objects.all().order_by('-created_at')[:5]
    
    for session in recent_sessions:
        print(f"\nSession ID: {session.id}")
        print(f"Session Name: {session.session_name}")
        print(f"Status: {session.status}")
        print(f"Created: {session.created_at}")
        print(f"Total Downloads: {session.total_downloads}")
        print(f"Completed Downloads: {session.completed_downloads}")
        
        # Show downloads in this session
        downloads = session.downloads.all()
        for download in downloads:
            print(f"  - Download ID: {download.id}")
            print(f"    Title: {download.title}")
            print(f"    Artist: {download.artist}")
            print(f"    URL: {download.url}")
            print(f"    Status: {download.status}")
            print(f"    File Size: {download.file_size}")
            print(f"    File Path: {download.file_path}")
            print(f"    Created: {download.created_at}")
            if download.completed_at:
                print(f"    Completed: {download.completed_at}")
            print()

if __name__ == "__main__":
    check_recent_downloads()
