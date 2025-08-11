# diary/urls.py
from django.urls import path
from . import views

app_name = 'diary'

urlpatterns = [
    # View the latest active diary session for the class
    path('', views.view_diary, name='view_diary_active'), 
    # View a specific diary session by ID
    path('session/<int:session_id>/', views.view_diary, name='view_diary_session'), 
    # Add entry to a specific session
    path('session/<int:session_id>/add/', views.add_diary_entry, name='add_diary_entry'),
    # Action to archive current session and start a new one
    path('start_new/', views.archive_and_start_new_session, name='start_new_session'),
    # List all sessions (active + archived)
    path('archived/', views.list_diary_sessions, name='list_sessions'), 
] 