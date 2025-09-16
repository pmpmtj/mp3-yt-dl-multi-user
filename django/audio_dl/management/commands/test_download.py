"""
Django management command to test audio download functionality.
"""

from django.core.management.base import BaseCommand, CommandError
from django.conf import settings
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
except ImportError as e:
    raise CommandError(f"Failed to import audio downloader components: {e}")


class Command(BaseCommand):
    help = 'Test audio download functionality'

    def add_arguments(self, parser):
        parser.add_argument(
            'url',
            type=str,
            help='YouTube URL to test download'
        )
        parser.add_argument(
            '--output-dir',
            type=str,
            default=str(Path(settings.MEDIA_ROOT) / 'test_downloads'),
            help='Output directory for downloads'
        )

    def handle(self, *args, **options):
        url = options['url']
        output_dir = Path(options['output_dir'])
        
        # Initialize logging
        setup_logging()
        
        self.stdout.write(f"Testing audio download for: {url}")
        self.stdout.write(f"Output directory: {output_dir}")
        
        try:
            # Create output directory
            output_dir.mkdir(parents=True, exist_ok=True)
            
            # Create downloader instance
            downloader = AudioDownloader(output_dir=output_dir)
            
            # Test URL validation
            if not downloader.validate_url(url):
                raise CommandError(f"Invalid YouTube URL: {url}")
            
            self.stdout.write("✓ URL validation passed")
            
            # Get video info
            try:
                video_info = downloader.get_video_info(url)
                self.stdout.write(f"✓ Video info retrieved: {video_info.get('title', 'Unknown')}")
            except Exception as e:
                self.stdout.write(self.style.WARNING(f"Could not get video info: {e}"))
            
            # Test download
            self.stdout.write("Starting download...")
            result = downloader.download_audio(url)
            
            if result.success:
                self.stdout.write(
                    self.style.SUCCESS(
                        f"✓ Download completed successfully!\n"
                        f"  File: {result.output_path}\n"
                        f"  Size: {result.file_size_bytes} bytes\n"
                        f"  Duration: {result.duration_seconds} seconds\n"
                        f"  Title: {result.title}\n"
                        f"  Artist: {result.artist}"
                    )
                )
            else:
                raise CommandError(f"Download failed: {result.error_message}")
                
        except AudioDownloadError as e:
            raise CommandError(f"Audio download error: {e}")
        except Exception as e:
            raise CommandError(f"Unexpected error: {e}")
