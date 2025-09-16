"""
Tests for the audio_dl app.

This module contains unit tests for models, views, forms, and other components.
"""

from django.test import TestCase, Client
from django.contrib.auth.models import User
from django.urls import reverse
from django.utils import timezone
from django.core.exceptions import ValidationError

from .models import DownloadSession, AudioDownload, DownloadHistory


class DownloadSessionModelTest(TestCase):
    """Test cases for DownloadSession model."""
    
    def setUp(self):
        """Set up test data."""
        self.user = User.objects.create_user(
            username='testuser',
            email='test@example.com',
            password='testpass123'
        )
        self.session = DownloadSession.objects.create(
            user=self.user,
            session_name='Test Session'
        )
    
    def test_session_creation(self):
        """Test session creation."""
        self.assertEqual(self.session.session_name, 'Test Session')
        self.assertEqual(self.session.user, self.user)
        self.assertEqual(self.session.status, 'pending')
        self.assertEqual(self.session.total_downloads, 0)
        self.assertEqual(self.session.completed_downloads, 0)
    
    def test_progress_percentage(self):
        """Test progress percentage calculation."""
        # No downloads
        self.assertEqual(self.session.progress_percentage, 0)
        
        # Add some downloads
        AudioDownload.objects.create(
            session=self.session,
            url='https://example.com/audio1.mp3',
            status='completed'
        )
        AudioDownload.objects.create(
            session=self.session,
            url='https://example.com/audio2.mp3',
            status='pending'
        )
        
        # Refresh from database
        self.session.refresh_from_db()
        self.assertEqual(self.session.progress_percentage, 50.0)
    
    def test_session_str(self):
        """Test string representation."""
        self.assertEqual(str(self.session), 'Test Session (pending)')


class AudioDownloadModelTest(TestCase):
    """Test cases for AudioDownload model."""
    
    def setUp(self):
        """Set up test data."""
        self.user = User.objects.create_user(
            username='testuser',
            email='test@example.com',
            password='testpass123'
        )
        self.session = DownloadSession.objects.create(
            user=self.user,
            session_name='Test Session'
        )
        self.download = AudioDownload.objects.create(
            session=self.session,
            url='https://example.com/audio.mp3',
            title='Test Audio',
            artist='Test Artist'
        )
    
    def test_download_creation(self):
        """Test download creation."""
        self.assertEqual(self.download.url, 'https://example.com/audio.mp3')
        self.assertEqual(self.download.title, 'Test Audio')
        self.assertEqual(self.download.artist, 'Test Artist')
        self.assertEqual(self.download.status, 'pending')
        self.assertEqual(self.download.quality, 'best')
    
    def test_download_str(self):
        """Test string representation."""
        self.assertEqual(str(self.download), 'Test Audio - Test Artist')
    
    def test_session_counters_update(self):
        """Test that session counters are updated when download is saved."""
        # Initially no downloads
        self.assertEqual(self.session.total_downloads, 0)
        self.assertEqual(self.session.completed_downloads, 0)
        
        # Add a download
        AudioDownload.objects.create(
            session=self.session,
            url='https://example.com/audio2.mp3'
        )
        
        # Session should have 2 total downloads
        self.session.refresh_from_db()
        self.assertEqual(self.session.total_downloads, 2)
        self.assertEqual(self.session.completed_downloads, 0)
        
        # Mark one as completed
        self.download.status = 'completed'
        self.download.save()
        
        # Session should have 1 completed download
        self.session.refresh_from_db()
        self.assertEqual(self.session.completed_downloads, 1)


class DownloadHistoryModelTest(TestCase):
    """Test cases for DownloadHistory model."""
    
    def setUp(self):
        """Set up test data."""
        self.user = User.objects.create_user(
            username='testuser',
            email='test@example.com',
            password='testpass123'
        )
        self.session = DownloadSession.objects.create(
            user=self.user,
            session_name='Test Session'
        )
        self.download = AudioDownload.objects.create(
            session=self.session,
            url='https://example.com/audio.mp3',
            title='Test Audio'
        )
        self.history = DownloadHistory.objects.create(
            download=self.download,
            file_format='mp3',
            bitrate=320,
            sample_rate=44100,
            channels=2
        )
    
    def test_history_creation(self):
        """Test history creation."""
        self.assertEqual(self.history.download, self.download)
        self.assertEqual(self.history.file_format, 'mp3')
        self.assertEqual(self.history.bitrate, 320)
        self.assertEqual(self.history.sample_rate, 44100)
        self.assertEqual(self.history.channels, 2)
    
    def test_history_str(self):
        """Test string representation."""
        self.assertEqual(str(self.history), 'History for Test Audio')


class ViewsTest(TestCase):
    """Test cases for views."""
    
    def setUp(self):
        """Set up test data."""
        self.client = Client()
        self.user = User.objects.create_user(
            username='testuser',
            email='test@example.com',
            password='testpass123'
        )
        self.session = DownloadSession.objects.create(
            user=self.user,
            session_name='Test Session'
        )
    
    def test_index_view(self):
        """Test index view."""
        response = self.client.get(reverse('audio_dl:index'))
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'Audio Downloader')
    
    def test_session_list_view_requires_login(self):
        """Test that session list view requires login."""
        response = self.client.get(reverse('audio_dl:session_list'))
        self.assertEqual(response.status_code, 302)  # Redirect to login
    
    def test_session_list_view_authenticated(self):
        """Test session list view for authenticated user."""
        self.client.login(username='testuser', password='testpass123')
        response = self.client.get(reverse('audio_dl:session_list'))
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'Test Session')
    
    def test_session_detail_view(self):
        """Test session detail view."""
        self.client.login(username='testuser', password='testpass123')
        response = self.client.get(reverse('audio_dl:session_detail', args=[self.session.id]))
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'Test Session')
    
    def test_create_session_view_requires_login(self):
        """Test that create session view requires login."""
        response = self.client.get(reverse('audio_dl:create_session'))
        self.assertEqual(response.status_code, 302)  # Redirect to login
    
    def test_create_session_view_authenticated(self):
        """Test create session view for authenticated user."""
        self.client.login(username='testuser', password='testpass123')
        response = self.client.get(reverse('audio_dl:create_session'))
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'Create New Session')


class FormsTest(TestCase):
    """Test cases for forms."""
    
    def setUp(self):
        """Set up test data."""
        self.user = User.objects.create_user(
            username='testuser',
            email='test@example.com',
            password='testpass123'
        )
        self.session = DownloadSession.objects.create(
            user=self.user,
            session_name='Test Session'
        )
    
    def test_download_session_form_valid(self):
        """Test valid download session form."""
        form_data = {'session_name': 'New Session'}
        form = DownloadSessionForm(data=form_data)
        self.assertTrue(form.is_valid())
    
    def test_download_session_form_invalid_empty_name(self):
        """Test invalid download session form with empty name."""
        form_data = {'session_name': ''}
        form = DownloadSessionForm(data=form_data)
        self.assertFalse(form.is_valid())
        self.assertIn('session_name', form.errors)
    
    def test_audio_download_form_valid(self):
        """Test valid audio download form."""
        form_data = {
            'url': 'https://example.com/audio.mp3',
            'title': 'Test Audio',
            'artist': 'Test Artist',
            'quality': 'best'
        }
        form = AudioDownloadForm(data=form_data)
        self.assertTrue(form.is_valid())
    
    def test_audio_download_form_invalid_url(self):
        """Test invalid audio download form with invalid URL."""
        form_data = {
            'url': 'invalid-url',
            'title': 'Test Audio',
            'quality': 'best'
        }
        form = AudioDownloadForm(data=form_data)
        self.assertFalse(form.is_valid())
        self.assertIn('url', form.errors)
    
    def test_bulk_download_form_valid(self):
        """Test valid bulk download form."""
        form_data = {
            'urls': 'https://example.com/audio1.mp3\nhttps://example.com/audio2.mp3',
            'quality': 'best'
        }
        form = BulkDownloadForm(data=form_data)
        self.assertTrue(form.is_valid())
    
    def test_bulk_download_form_invalid_too_many_urls(self):
        """Test invalid bulk download form with too many URLs."""
        urls = '\n'.join([f'https://example.com/audio{i}.mp3' for i in range(51)])
        form_data = {
            'urls': urls,
            'quality': 'best'
        }
        form = BulkDownloadForm(data=form_data)
        self.assertFalse(form.is_valid())
        self.assertIn('urls', form.errors)
