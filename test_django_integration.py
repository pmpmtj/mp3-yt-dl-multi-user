#!/usr/bin/env python3
"""
Test script for Django integration with audio downloader.
"""

import os
import sys
import subprocess
from pathlib import Path

def run_command(cmd, cwd=None):
    """Run a command and return the result."""
    print(f"Running: {cmd}")
    try:
        result = subprocess.run(cmd, shell=True, cwd=cwd, capture_output=True, text=True)
        if result.returncode != 0:
            print(f"Error: {result.stderr}")
            return False
        print(f"Success: {result.stdout}")
        return True
    except Exception as e:
        print(f"Exception: {e}")
        return False

def main():
    """Test the Django integration."""
    print("🧪 Testing Django Integration with Audio Downloader")
    print("=" * 50)
    
    # Change to Django directory
    django_dir = Path(__file__).parent / "django" / "my_downloader"
    
    if not django_dir.exists():
        print("❌ Django directory not found!")
        return False
    
    print(f"📁 Working directory: {django_dir}")
    
    # Test 1: Check if Django can start
    print("\n1️⃣ Testing Django startup...")
    if not run_command("python manage.py check", cwd=django_dir):
        print("❌ Django check failed!")
        return False
    print("✅ Django check passed!")
    
    # Test 2: Test database connection
    print("\n2️⃣ Testing database connection...")
    if not run_command("python manage.py showmigrations", cwd=django_dir):
        print("❌ Database connection failed!")
        print("💡 Make sure PostgreSQL is running and configured in .env file")
        return False
    print("✅ Database connection successful!")
    
    # Test 3: Test audio downloader import
    print("\n3️⃣ Testing audio downloader import...")
    test_import_cmd = """
python -c "
import sys
from pathlib import Path
sys.path.insert(0, str(Path.cwd().parent.parent / 'src'))
try:
    from yt_audio_dl.audio_core import AudioDownloader
    from common.session_manager import get_session_manager
    print('✅ Audio downloader imports successful!')
except ImportError as e:
    print(f'❌ Import failed: {e}')
    sys.exit(1)
"
"""
    if not run_command(test_import_cmd, cwd=django_dir):
        print("❌ Audio downloader import failed!")
        return False
    
    # Test 4: Test management command
    print("\n4️⃣ Testing management command...")
    test_url = "https://www.youtube.com/watch?v=dQw4w9WgXcQ"  # Rick Roll for testing
    if not run_command(f"python manage.py test_download '{test_url}' --output-dir ./test_output", cwd=django_dir):
        print("❌ Management command test failed!")
        print("💡 This might be due to network issues or yt-dlp problems")
        return False
    print("✅ Management command test passed!")
    
    print("\n🎉 All tests passed! Django integration is working!")
    return True

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)
