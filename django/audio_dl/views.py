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
import json
import logging

from .models import DownloadSession, AudioDownload, DownloadHistory
from .forms import DownloadSessionForm, AudioDownloadForm

logger = logging.getLogger('audio_dl')


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
    
    # Pagination for downloads
    paginator = Paginator(downloads, 20)
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)
    
    context = {
        'session': session,
        'page_obj': page_obj,
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
            return redirect('session_detail', session_id=session.id)
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
            return redirect('session_detail', session_id=session.id)
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
    
    try:
        # Update status to downloading
        download.status = 'downloading'
        download.save()
        
        # Here you would integrate with your existing audio downloader
        # For now, we'll just simulate the process
        logger.info(f"Starting download for {download.title}")
        
        return JsonResponse({
            'success': True,
            'message': 'Download started successfully',
            'download_id': str(download.id)
        })
    except Exception as e:
        logger.error(f"Error starting download: {str(e)}")
        download.status = 'failed'
        download.error_message = str(e)
        download.save()
        
        return JsonResponse({
            'success': False,
            'error': str(e)
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
    
    return JsonResponse({
        'id': str(download.id),
        'title': download.title,
        'status': download.status,
        'progress': 0,  # This would be calculated based on actual download progress
        'error_message': download.error_message,
        'created_at': download.created_at.isoformat(),
        'updated_at': download.updated_at.isoformat(),
    })


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
