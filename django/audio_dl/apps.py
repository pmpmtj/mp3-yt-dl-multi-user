from django.apps import AppConfig


class AudioDlConfig(AppConfig):
    """Configuration for the audio_dl app."""
    
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'audio_dl'
    verbose_name = 'Audio Downloader'
    
    def ready(self):
        """Called when the app is ready."""
        # Import signal handlers here if needed
        pass
