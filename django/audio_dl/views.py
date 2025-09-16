"""
Views for the audio_dl app.

This module contains view functions and classes for handling
audio download requests and session management.
"""

from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.http import JsonResponse, HttpResponse
from django.views.decorators.csrf import csrf_exempt
from django.views.decorators.http import require_http_methods
from django.core.paginator import Paginator
from django.db.models import Q
from django.utils import timezone
from django.conf import settings
import json
import logging
import os
import sys
from pathlib import Path

# Add the src directory to Python path for imports
current_dir = Path(__file__).resolve().parent
project_root = current_dir.parent.parent  # Go up to my_project
src_path = project_root / 'src'
sys.path.insert(0, str(src_path))

# Also add the project root to find the src modules
sys.path.insert(0, str(project_root))

from .models import DownloadSession, AudioDownload, DownloadHistory
from .forms import DownloadSessionForm, AudioDownloadForm

# Audio downloader components will be imported when needed

logger = logging.getLogger('audio_dl')

# Initialize logging if not already done
try:
    setup_logging()
except:
    pass


def update_download_progress(download_id, progress_data):
    """Update download progress in the database."""
    try:
        download = AudioDownload.objects.get(id=download_id)
        if progress_data.get('status') == 'downloading':
            # Store progress in a custom field or use a cache system
            # For now, we'll just log it
            logger.debug(f"Download {download_id} progress: {progress_data.get('progress_percent', 0)}%")
        elif progress_data.get('status') == 'finished':
            logger.info(f"Download {download_id} finished: {progress_data.get('filename', 'unknown')}")
    except AudioDownload.DoesNotExist:
        logger.warning(f"Download {download_id} not found for progress update")
    except Exception as e:
        logger.error(f"Error updating download progress: {e}")


def index(request):
    """Home page view."""
    context = {
        'title': 'Audio Downloader',
        'description': 'Download audio from various sources with ease',
    }
    return render(request, 'audio_dl/index.html', context)


@login_required
def session_list(request):
    """List all download sessions for the current user."""
    sessions = DownloadSession.objects.filter(user=request.user)
    
    # Search functionality
    search_query = request.GET.get('search', '')
    if search_query:
        sessions = sessions.filter(
            Q(session_name__icontains=search_query) |
            Q(status__icontains=search_query)
        )
    
    # Pagination
    paginator = Paginator(sessions, 10)
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)
    
    context = {
        'page_obj': page_obj,
        'search_query': search_query,
        'title': 'Download Sessions',
    }
    return render(request, 'audio_dl/session_list.html', context)


@login_required
def session_detail(request, session_id):
    """Detail view for a specific download session."""
    session = get_object_or_404(DownloadSession, id=session_id, user=request.user)
    downloads = session.downloads.all()
    
    # Calculate download counts by status
    in_progress_count = downloads.filter(status='downloading').count()
    failed_count = downloads.filter(status='failed').count()
    
    # Pagination for downloads
    paginator = Paginator(downloads, 20)
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)
    
    context = {
        'session': session,
        'page_obj': page_obj,
        'in_progress_count': in_progress_count,
        'failed_count': failed_count,
        'title': f'Session: {session.session_name}',
    }
    return render(request, 'audio_dl/session_detail.html', context)


@login_required
def create_session(request):
    """Create a new download session."""
    if request.method == 'POST':
        form = DownloadSessionForm(request.POST)
        if form.is_valid():
            session = form.save(commit=False)
            session.user = request.user
            session.save()
            messages.success(request, f'Session "{session.session_name}" created successfully.')
            return redirect('audio_dl:session_detail', session_id=session.id)
    else:
        form = DownloadSessionForm()
    
    context = {
        'form': form,
        'title': 'Create New Session',
    }
    return render(request, 'audio_dl/session_form.html', context)


@login_required
def add_download(request, session_id):
    """Add a new download to a session."""
    session = get_object_or_404(DownloadSession, id=session_id, user=request.user)
    
    if request.method == 'POST':
        form = AudioDownloadForm(request.POST)
        if form.is_valid():
            download = form.save(commit=False)
            download.session = session
            download.save()
            messages.success(request, f'Download added to session "{session.session_name}".')
            return redirect('audio_dl:session_detail', session_id=session.id)
    else:
        form = AudioDownloadForm()
    
    context = {
        'form': form,
        'session': session,
        'title': f'Add Download to {session.session_name}',
    }
    return render(request, 'audio_dl/download_form.html', context)


@login_required
@require_http_methods(["POST"])
def start_download(request, download_id):
    """Start downloading a specific audio file."""
    download = get_object_or_404(AudioDownload, id=download_id, session__user=request.user)
    
    if download.status != 'pending':
        return JsonResponse({'error': 'Download is not in pending status'}, status=400)
    
    # Import audio downloader components when needed
    try:
        # Ensure path resolution is done in the function context
        current_dir = Path(__file__).resolve().parent
        project_root = current_dir.parent.parent  # Go up to my_project
        src_path = project_root / 'src'
        if str(src_path) not in sys.path:
            sys.path.insert(0, str(src_path))
        if str(project_root) not in sys.path:
            sys.path.insert(0, str(project_root))
            
        from yt_audio_dl.audio_core import AudioDownloader, AudioDownloadError, DownloadStatus
        from common.logging_config import setup_logging
    except ImportError as e:
        logger.error(f"Failed to import audio downloader components: {e}")
        return JsonResponse({
            'success': False,
            'error': 'Audio downloader not available'
        }, status=500)
    
    try:
        # Update status to downloading
        download.status = 'downloading'
        download.save()
        
        logger.info(f"Starting download for {download.title or download.url}")
        
        # Set up download directory
        download_dir = Path(settings.MEDIA_ROOT) / 'downloads' / str(download.session.id)
        download_dir.mkdir(parents=True, exist_ok=True)
        
        # Create audio downloader instance
        downloader = AudioDownloader(
            output_dir=download_dir,
            progress_callback=lambda progress: update_download_progress(download.id, progress)
        )
        
        # Get video info first to populate title and artist if not set
        try:
            video_info = downloader.get_video_info(download.url)
            if not download.title and video_info.get('title'):
                download.title = video_info['title']
            if not download.artist and video_info.get('uploader'):
                download.artist = video_info['uploader']
            if video_info.get('duration'):
                from datetime import timedelta
                duration_seconds = float(video_info['duration'])
                download.duration = timedelta(seconds=duration_seconds)
            download.save()
        except Exception as e:
            logger.warning(f"Could not get video info: {e}")
        
        # Start the download
        result = downloader.download_audio(download.url)
        
        if result.success:
            # Update download record with results
            download.status = 'completed'
            download.file_path = str(result.output_path) if result.output_path else ''
            download.file_size = result.file_size_bytes
            download.completed_at = timezone.now()
            if result.error_message:
                download.error_message = result.error_message
            download.save()
            
            # Create download history record
            from datetime import timedelta
            DownloadHistory.objects.create(
                download=download,
                download_speed=result.download_time_seconds,
                processing_time=timedelta(seconds=result.download_time_seconds) if result.download_time_seconds else None,
                file_format=result.format or 'mp3',
                bitrate=192,  # Default bitrate
                sample_rate=44100,  # Default sample rate
                channels=2  # Default stereo
            )
            
            logger.info(f"Download completed successfully: {download.title}")
            
            return JsonResponse({
                'success': True,
                'message': 'Download completed successfully',
                'download_id': str(download.id),
                'file_path': download.file_path,
                'file_size': download.file_size
            })
        else:
            # Download failed
            download.status = 'failed'
            download.error_message = result.error_message or 'Download failed'
            download.save()
            
            logger.error(f"Download failed: {result.error_message}")
            
            return JsonResponse({
                'success': False,
                'error': result.error_message or 'Download failed'
            }, status=500)
            
    except AudioDownloadError as e:
        logger.error(f"Audio download error: {str(e)}")
        download.status = 'failed'
        download.error_message = str(e)
        download.save()
        
        return JsonResponse({
            'success': False,
            'error': str(e)
        }, status=500)
    except Exception as e:
        logger.error(f"Unexpected error starting download: {str(e)}")
        download.status = 'failed'
        download.error_message = str(e)
        download.save()
        
        return JsonResponse({
            'success': False,
            'error': f'Unexpected error: {str(e)}'
        }, status=500)


@login_required
@require_http_methods(["POST"])
def cancel_download(request, download_id):
    """Cancel a download."""
    download = get_object_or_404(AudioDownload, id=download_id, session__user=request.user)
    
    if download.status in ['completed', 'cancelled']:
        return JsonResponse({'error': 'Download cannot be cancelled'}, status=400)
    
    download.status = 'cancelled'
    download.save()
    
    return JsonResponse({
        'success': True,
        'message': 'Download cancelled successfully'
    })


@login_required
def download_status(request, download_id):
    """Get the status of a specific download."""
    download = get_object_or_404(AudioDownload, id=download_id, session__user=request.user)
    
    # Calculate progress based on status
    progress = 0
    if download.status == 'completed':
        progress = 100
    elif download.status == 'downloading':
        progress = 50  # Placeholder - would need real-time progress tracking
    elif download.status == 'failed':
        progress = 0
    
    response_data = {
        'id': str(download.id),
        'title': download.title or 'Unknown',
        'artist': download.artist or 'Unknown',
        'url': download.url,
        'status': download.status,
        'progress': progress,
        'error_message': download.error_message,
        'file_size': download.file_size,
        'duration': str(download.duration) if download.duration else None,
        'quality': download.quality,
        'file_path': download.file_path,
        'created_at': download.created_at.isoformat(),
        'updated_at': download.updated_at.isoformat(),
        'completed_at': download.completed_at.isoformat() if download.completed_at else None,
    }
    
    # Add download history if available
    try:
        history = download.history
        response_data.update({
            'download_speed': history.download_speed,
            'processing_time': str(history.processing_time) if history.processing_time else None,
            'file_format': history.file_format,
            'bitrate': history.bitrate,
            'sample_rate': history.sample_rate,
            'channels': history.channels,
        })
    except DownloadHistory.DoesNotExist:
        pass
    
    return JsonResponse(response_data)


@login_required
def session_status(request, session_id):
    """Get the status of a download session."""
    session = get_object_or_404(DownloadSession, id=session_id, user=request.user)
    
    downloads = session.downloads.all()
    status_counts = {}
    for status, _ in AudioDownload.STATUS_CHOICES:
        status_counts[status] = downloads.filter(status=status).count()
    
    return JsonResponse({
        'id': str(session.id),
        'session_name': session.session_name,
        'status': session.status,
        'total_downloads': session.total_downloads,
        'completed_downloads': session.completed_downloads,
        'progress_percentage': session.progress_percentage,
        'status_counts': status_counts,
        'created_at': session.created_at.isoformat(),
        'updated_at': session.updated_at.isoformat(),
    })


@login_required
@require_http_methods(["DELETE"])
def delete_session(request, session_id):
    """Delete a download session."""
    session = get_object_or_404(DownloadSession, id=session_id, user=request.user)
    session_name = session.session_name
    session.delete()
    
    return JsonResponse({
        'success': True,
        'message': f'Session "{session_name}" deleted successfully'
    })


@login_required
@require_http_methods(["DELETE"])
def delete_download(request, download_id):
    """Delete a download."""
    download = get_object_or_404(AudioDownload, id=download_id, session__user=request.user)
    download_title = download.title
    download.delete()
    
    return JsonResponse({
        'success': True,
        'message': f'Download "{download_title}" deleted successfully'
    })
