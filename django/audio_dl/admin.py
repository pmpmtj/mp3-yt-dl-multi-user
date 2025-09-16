"""
Admin configuration for the audio_dl app.

This module configures the Django admin interface for managing
download sessions, audio downloads, and related data.
"""

from django.contrib import admin
from django.utils.html import format_html
from django.urls import reverse
from django.utils.safestring import mark_safe

from .models import DownloadSession, AudioDownload, DownloadHistory


@admin.register(DownloadSession)
class DownloadSessionAdmin(admin.ModelAdmin):
    """Admin interface for DownloadSession model."""
    
    list_display = [
        'session_name', 'user', 'status', 'progress_display', 
        'total_downloads', 'completed_downloads', 'created_at'
    ]
    list_filter = ['status', 'created_at', 'user']
    search_fields = ['session_name', 'user__username', 'user__email']
    readonly_fields = ['id', 'created_at', 'updated_at', 'progress_display']
    list_per_page = 20
    
    fieldsets = (
        ('Basic Information', {
            'fields': ('id', 'user', 'session_name', 'status')
        }),
        ('Statistics', {
            'fields': ('total_downloads', 'completed_downloads', 'progress_display')
        }),
        ('Timestamps', {
            'fields': ('created_at', 'updated_at'),
            'classes': ('collapse',)
        }),
    )
    
    def progress_display(self, obj):
        """Display progress as a progress bar."""
        percentage = obj.progress_percentage
        color = 'green' if percentage == 100 else 'orange' if percentage > 0 else 'gray'
        return format_html(
            '<div style="width: 100px; background-color: #f0f0f0; border-radius: 3px;">'
            '<div style="width: {}%; background-color: {}; height: 20px; border-radius: 3px; '
            'display: flex; align-items: center; justify-content: center; color: white; '
            'font-size: 12px; font-weight: bold;">{:.1f}%</div></div>',
            percentage, color, percentage
        )
    progress_display.short_description = 'Progress'
    
    def get_queryset(self, request):
        """Filter sessions based on user permissions."""
        qs = super().get_queryset(request)
        if request.user.is_superuser:
            return qs
        return qs.filter(user=request.user)


@admin.register(AudioDownload)
class AudioDownloadAdmin(admin.ModelAdmin):
    """Admin interface for AudioDownload model."""
    
    list_display = [
        'title', 'artist', 'session_link', 'status', 'quality', 
        'file_size_display', 'created_at'
    ]
    list_filter = ['status', 'quality', 'created_at', 'session__user']
    search_fields = ['title', 'artist', 'url', 'session__session_name']
    readonly_fields = ['id', 'created_at', 'updated_at', 'completed_at', 'file_size_display']
    list_per_page = 30
    
    fieldsets = (
        ('Basic Information', {
            'fields': ('id', 'session', 'url', 'title', 'artist')
        }),
        ('Download Settings', {
            'fields': ('quality', 'status')
        }),
        ('File Information', {
            'fields': ('file_path', 'file_size_display', 'duration')
        }),
        ('Error Information', {
            'fields': ('error_message',),
            'classes': ('collapse',)
        }),
        ('Timestamps', {
            'fields': ('created_at', 'updated_at', 'completed_at'),
            'classes': ('collapse',)
        }),
    )
    
    def session_link(self, obj):
        """Create a link to the session detail page."""
        url = reverse('admin:audio_dl_downloadsession_change', args=[obj.session.id])
        return format_html('<a href="{}">{}</a>', url, obj.session.session_name)
    session_link.short_description = 'Session'
    
    def file_size_display(self, obj):
        """Display file size in human-readable format."""
        if not obj.file_size:
            return 'Unknown'
        
        size = obj.file_size
        for unit in ['B', 'KB', 'MB', 'GB']:
            if size < 1024.0:
                return f"{size:.1f} {unit}"
            size /= 1024.0
        return f"{size:.1f} TB"
    file_size_display.short_description = 'File Size'
    
    def get_queryset(self, request):
        """Filter downloads based on user permissions."""
        qs = super().get_queryset(request)
        if request.user.is_superuser:
            return qs
        return qs.filter(session__user=request.user)


@admin.register(DownloadHistory)
class DownloadHistoryAdmin(admin.ModelAdmin):
    """Admin interface for DownloadHistory model."""
    
    list_display = [
        'download_title', 'file_format', 'bitrate', 'sample_rate', 
        'channels', 'download_speed', 'processing_time'
    ]
    list_filter = ['file_format', 'bitrate', 'sample_rate', 'channels']
    search_fields = ['download__title', 'download__artist']
    readonly_fields = ['download_link']
    
    fieldsets = (
        ('Download Information', {
            'fields': ('download_link', 'download')
        }),
        ('File Properties', {
            'fields': ('file_format', 'bitrate', 'sample_rate', 'channels')
        }),
        ('Performance Metrics', {
            'fields': ('download_speed', 'processing_time')
        }),
    )
    
    def download_title(self, obj):
        """Display the download title."""
        return obj.download.title
    download_title.short_description = 'Download Title'
    
    def download_link(self, obj):
        """Create a link to the download detail page."""
        url = reverse('admin:audio_dl_audiodownload_change', args=[obj.download.id])
        return format_html('<a href="{}">{}</a>', url, obj.download.title)
    download_link.short_description = 'Download'
    
    def get_queryset(self, request):
        """Filter history based on user permissions."""
        qs = super().get_queryset(request)
        if request.user.is_superuser:
            return qs
        return qs.filter(download__session__user=request.user)


# Customize admin site
admin.site.site_header = "Audio Downloader Administration"
admin.site.site_title = "Audio DL Admin"
admin.site.index_title = "Welcome to Audio Downloader Administration"
