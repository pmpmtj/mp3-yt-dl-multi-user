"""
Forms for the audio_dl app.

This module contains Django forms for handling user input
related to download sessions and audio downloads.
"""

from django import forms
from django.core.exceptions import ValidationError
from django.utils.translation import gettext_lazy as _

from .models import DownloadSession, AudioDownload


class DownloadSessionForm(forms.ModelForm):
    """Form for creating and editing download sessions."""
    
    class Meta:
        model = DownloadSession
        fields = ['session_name']
        widgets = {
            'session_name': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'Enter a name for this download session',
                'maxlength': '200'
            })
        }
        labels = {
            'session_name': 'Session Name'
        }
        help_texts = {
            'session_name': 'Give your download session a descriptive name'
        }
    
    def clean_session_name(self):
        """Validate session name."""
        session_name = self.cleaned_data.get('session_name')
        if not session_name or not session_name.strip():
            raise ValidationError(_('Session name cannot be empty.'))
        
        # Check for duplicate session names for the same user
        if self.instance.pk:  # Editing existing session
            existing = DownloadSession.objects.filter(
                user=self.instance.user,
                session_name=session_name
            ).exclude(pk=self.instance.pk)
        else:  # Creating new session
            existing = DownloadSession.objects.filter(
                user=self.instance.user if hasattr(self.instance, 'user') and self.instance.user else None,
                session_name=session_name
            )
        
        if existing.exists():
            raise ValidationError(_('A session with this name already exists.'))
        
        return session_name.strip()


class AudioDownloadForm(forms.ModelForm):
    """Form for adding audio downloads to a session."""
    
    class Meta:
        model = AudioDownload
        fields = ['url', 'title', 'artist', 'quality']
        widgets = {
            'url': forms.URLInput(attrs={
                'class': 'form-control',
                'placeholder': 'https://example.com/audio-url',
                'required': True
            }),
            'title': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'Audio title (optional - will be auto-detected)',
                'maxlength': '300'
            }),
            'artist': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'Artist name (optional - will be auto-detected)',
                'maxlength': '200'
            }),
            'quality': forms.Select(attrs={
                'class': 'form-control'
            })
        }
        labels = {
            'url': 'Audio URL',
            'title': 'Title',
            'artist': 'Artist',
            'quality': 'Audio Quality'
        }
        help_texts = {
            'url': 'Enter the URL of the audio file you want to download',
            'title': 'Optional: Specify the title (will be auto-detected if not provided)',
            'artist': 'Optional: Specify the artist (will be auto-detected if not provided)',
            'quality': 'Select the desired audio quality'
        }
    
    def clean_url(self):
        """Validate the URL."""
        url = self.cleaned_data.get('url')
        if not url:
            raise ValidationError(_('URL is required.'))
        
        # Basic URL validation
        if not url.startswith(('http://', 'https://')):
            raise ValidationError(_('Please enter a valid URL starting with http:// or https://'))
        
        # Check for duplicate URLs in the same session
        if hasattr(self, 'session') and self.session:
            existing = AudioDownload.objects.filter(
                session=self.session,
                url=url
            )
            if self.instance.pk:  # Editing existing download
                existing = existing.exclude(pk=self.instance.pk)
            
            if existing.exists():
                raise ValidationError(_('This URL has already been added to this session.'))
        
        return url
    
    def clean_title(self):
        """Clean and validate title."""
        title = self.cleaned_data.get('title', '')
        return title.strip() if title else ''
    
    def clean_artist(self):
        """Clean and validate artist."""
        artist = self.cleaned_data.get('artist', '')
        return artist.strip() if artist else ''


class BulkDownloadForm(forms.Form):
    """Form for adding multiple downloads at once."""
    
    urls = forms.CharField(
        widget=forms.Textarea(attrs={
            'class': 'form-control',
            'placeholder': 'Enter one URL per line',
            'rows': 10,
            'cols': 50
        }),
        label='URLs',
        help_text='Enter one audio URL per line. Titles and artists will be auto-detected.'
    )
    quality = forms.ChoiceField(
        choices=AudioDownload.QUALITY_CHOICES,
        widget=forms.Select(attrs={'class': 'form-control'}),
        label='Audio Quality',
        initial='best'
    )
    
    def clean_urls(self):
        """Validate and clean the URLs."""
        urls_text = self.cleaned_data.get('urls', '')
        if not urls_text.strip():
            raise ValidationError(_('Please enter at least one URL.'))
        
        urls = [url.strip() for url in urls_text.split('\n') if url.strip()]
        
        if not urls:
            raise ValidationError(_('Please enter at least one valid URL.'))
        
        if len(urls) > 50:  # Limit bulk downloads
            raise ValidationError(_('Maximum 50 URLs allowed per bulk operation.'))
        
        # Validate each URL
        valid_urls = []
        for i, url in enumerate(urls, 1):
            if not url.startswith(('http://', 'https://')):
                raise ValidationError(_(f'Line {i}: Please enter a valid URL starting with http:// or https://'))
            valid_urls.append(url)
        
        return valid_urls


class SessionSearchForm(forms.Form):
    """Form for searching download sessions."""
    
    search = forms.CharField(
        required=False,
        widget=forms.TextInput(attrs={
            'class': 'form-control',
            'placeholder': 'Search sessions by name or status...',
            'maxlength': '100'
        }),
        label='Search'
    )
    status = forms.ChoiceField(
        choices=[('', 'All Statuses')] + DownloadSession.STATUS_CHOICES,
        required=False,
        widget=forms.Select(attrs={'class': 'form-control'}),
        label='Status'
    )
