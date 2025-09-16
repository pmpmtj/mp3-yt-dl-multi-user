"""
URL configuration for audio_dl app.

The `urlpatterns` list routes URLs to views.
"""

from django.urls import path
from . import views

app_name = 'audio_dl'

urlpatterns = [
    # Home page
    path('', views.index, name='index'),
    
    # Session management
    path('sessions/', views.session_list, name='session_list'),
    path('sessions/create/', views.create_session, name='create_session'),
    path('sessions/<uuid:session_id>/', views.session_detail, name='session_detail'),
    path('sessions/<uuid:session_id>/delete/', views.delete_session, name='delete_session'),
    path('sessions/<uuid:session_id>/status/', views.session_status, name='session_status'),
    
    # Download management
    path('sessions/<uuid:session_id>/add/', views.add_download, name='add_download'),
    path('downloads/<uuid:download_id>/start/', views.start_download, name='start_download'),
    path('downloads/<uuid:download_id>/cancel/', views.cancel_download, name='cancel_download'),
    path('downloads/<uuid:download_id>/status/', views.download_status, name='download_status'),
    path('downloads/<uuid:download_id>/delete/', views.delete_download, name='delete_download'),
]
