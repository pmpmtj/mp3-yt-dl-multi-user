#!/usr/bin/env python
"""
Django development server runner for the Audio Downloader application.

This script provides a convenient way to run the Django development server
with proper configuration and logging.
"""

import os
import sys
import subprocess
from pathlib import Path

# Add the project root to Python path
SCRIPT_DIR = Path(__file__).resolve().parent
PROJECT_ROOT = SCRIPT_DIR.parent
sys.path.insert(0, str(PROJECT_ROOT))

def main():
    """Run the Django development server."""
    # Change to Django project directory
    django_dir = SCRIPT_DIR / "my_downloader"
    os.chdir(django_dir)
    
    print("=" * 60)
    print("Audio Downloader Django Application")
    print("=" * 60)
    print(f"Project directory: {django_dir}")
    print(f"Server will start at: http://127.0.0.1:8000")
    print("=" * 60)
    print()
    
    # Check if migrations need to be run
    try:
        result = subprocess.run(
            ["python", "manage.py", "showmigrations", "--plan"],
            capture_output=True,
            text=True,
            check=True
        )
        
        if "unapplied" in result.stdout:
            print("⚠️  Unapplied migrations detected. Running migrations...")
            subprocess.run(["python", "manage.py", "migrate"], check=True)
            print("✅ Migrations completed.")
            print()
    except subprocess.CalledProcessError as e:
        print(f"❌ Error checking migrations: {e}")
        print("Please run 'python manage.py migrate' manually.")
        print()
    
    # Start the development server
    try:
        print("🚀 Starting Django development server...")
        print("Press Ctrl+C to stop the server.")
        print()
        
        subprocess.run([
            "python", "manage.py", "runserver", 
            "127.0.0.1:8000",
            "--settings=my_downloader.settings"
        ])
        
    except KeyboardInterrupt:
        print("\n\n🛑 Server stopped by user.")
    except subprocess.CalledProcessError as e:
        print(f"\n❌ Error starting server: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main()
