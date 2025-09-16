"""
Models for the audio_dl app.

This module contains database models for managing audio downloads,
user sessions, and download history.
"""

from django.db import models
from django.contrib.auth.models import User
from django.utils import timezone
import uuid


class DownloadSession(models.Model):
    """Represents a user's download session."""
    
    STATUS_CHOICES = [
        ('pending', 'Pending'),
        ('in_progress', 'In Progress'),
        ('completed', 'Completed'),
        ('failed', 'Failed'),
        ('cancelled', 'Cancelled'),
    ]
    
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    user = models.ForeignKey(User, on_delete=models.CASCADE, null=True, blank=True)
    session_name = models.CharField(max_length=200, default='Untitled Session')
    created_at = models.DateTimeField(default=timezone.now)
    updated_at = models.DateTimeField(auto_now=True)
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='pending')
    total_downloads = models.PositiveIntegerField(default=0)
    completed_downloads = models.PositiveIntegerField(default=0)
    
    class Meta:
        ordering = ['-created_at']
        verbose_name = 'Download Session'
        verbose_name_plural = 'Download Sessions'
    
    def __str__(self):
        return f"{self.session_name} ({self.status})"
    
    @property
    def progress_percentage(self):
        """Calculate download progress as percentage."""
        if self.total_downloads == 0:
            return 0
        return (self.completed_downloads / self.total_downloads) * 100


class AudioDownload(models.Model):
    """Represents an individual audio download."""
    
    STATUS_CHOICES = [
        ('pending', 'Pending'),
        ('downloading', 'Downloading'),
        ('completed', 'Completed'),
        ('failed', 'Failed'),
        ('cancelled', 'Cancelled'),
    ]
    
    QUALITY_CHOICES = [
        ('best', 'Best Quality'),
        ('worst', 'Worst Quality'),
        ('128k', '128 kbps'),
        ('192k', '192 kbps'),
        ('320k', '320 kbps'),
    ]
    
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    session = models.ForeignKey(DownloadSession, on_delete=models.CASCADE, related_name='downloads')
    url = models.URLField(max_length=500)
    title = models.CharField(max_length=300, blank=True)
    artist = models.CharField(max_length=200, blank=True)
    duration = models.DurationField(null=True, blank=True)
    file_size = models.BigIntegerField(null=True, blank=True)  # Size in bytes
    quality = models.CharField(max_length=10, choices=QUALITY_CHOICES, default='best')
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='pending')
    file_path = models.CharField(max_length=500, blank=True)
    error_message = models.TextField(blank=True)
    created_at = models.DateTimeField(default=timezone.now)
    updated_at = models.DateTimeField(auto_now=True)
    completed_at = models.DateTimeField(null=True, blank=True)
    
    class Meta:
        ordering = ['-created_at']
        verbose_name = 'Audio Download'
        verbose_name_plural = 'Audio Downloads'
    
    def __str__(self):
        return f"{self.title or 'Unknown'} - {self.artist or 'Unknown Artist'}"
    
    def save(self, *args, **kwargs):
        """Override save to update session counters."""
        super().save(*args, **kwargs)
        self.update_session_counters()
    
    def update_session_counters(self):
        """Update the parent session's download counters and status."""
        session = self.session
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
        
        session.save(update_fields=['total_downloads', 'completed_downloads', 'status'])


class DownloadHistory(models.Model):
    """Stores historical data about completed downloads."""
    
    download = models.OneToOneField(AudioDownload, on_delete=models.CASCADE, related_name='history')
    download_speed = models.FloatField(null=True, blank=True)  # MB/s
    processing_time = models.DurationField(null=True, blank=True)
    file_format = models.CharField(max_length=10, blank=True)
    bitrate = models.PositiveIntegerField(null=True, blank=True)
    sample_rate = models.PositiveIntegerField(null=True, blank=True)
    channels = models.PositiveSmallIntegerField(null=True, blank=True)
    
    class Meta:
        verbose_name = 'Download History'
        verbose_name_plural = 'Download Histories'
    
    def __str__(self):
        return f"History for {self.download.title}"
