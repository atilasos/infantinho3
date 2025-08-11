from django.shortcuts import render, get_object_or_404, redirect
from django.utils import timezone
from django.views.decorators.http import require_POST
from django.http import JsonResponse, HttpResponseBadRequest
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.utils.translation import gettext_lazy as _
import json # For potential AJAX requests
from django.db import transaction

from .models import DiarySession, DiaryEntry
from classes.models import Class
# Assuming a permission decorator exists or using inline checks
from users.decorators import group_required 
from users.permissions import can_access_class, can_moderate_class

# --- Helper to check if user can moderate diary (teacher/admin) ---
def _can_moderate_diary(user, turma):
    return can_moderate_class(user, turma)

# --- Helper to check if user can view/add to diary (member) ---
def _can_access_diary(user, turma):
    return can_access_class(user, turma)

@login_required
def view_diary(request, class_id, session_id=None):
    """Displays the diary for a specific session or the latest active one."""
    turma = get_object_or_404(Class, id=class_id)
    
    if not _can_access_diary(request.user, turma):
        messages.error(request, _("You do not have permission to view this diary."))
        return redirect('/')

    diary_session = None
    if session_id:
        diary_session = get_object_or_404(DiarySession, id=session_id, turma=turma)
    else:
        # Find the latest active session for this class
        diary_session = DiarySession.objects.filter(turma=turma, status='ACTIVE').order_by('-start_date').first()

    if not diary_session:
        # No active session found, maybe render a page prompting to start one?
        can_moderate = _can_moderate_diary(request.user, turma)
        return render(request, 'diary/no_active_diary.html', {'turma': turma, 'can_moderate': can_moderate})

    # Fetch entries grouped by column
    entries_by_column = {col_key: [] for col_key, _ in DiaryEntry.COLUMN_CHOICES}
    entries = diary_session.entries.select_related('author').order_by('created_at')
    for entry in entries:
        if entry.column in entries_by_column:
            entries_by_column[entry.column].append(entry)
            
    context = {
        'turma': turma,
        'diary_session': diary_session,
        'entries_by_column': entries_by_column,
        'column_choices': DiaryEntry.COLUMN_CHOICES,
        'can_moderate': _can_moderate_diary(request.user, turma), # Pass moderation flag
    }
    return render(request, 'diary/view_diary.html', context)


@login_required
def list_diary_sessions(request, class_id):
    turma = get_object_or_404(Class, id=class_id)
    if not _can_access_diary(request.user, turma):
        messages.error(request, _("You do not have permission to view this diary."))
        return redirect('/')
    sessions = DiarySession.objects.filter(turma=turma).order_by('-start_date')
    return render(request, 'diary/list_diary_sessions.html', {"turma": turma, "sessions": sessions})

@require_POST
@login_required
def add_diary_entry(request, class_id, session_id):
    """Adds a new entry to a specific diary session column."""
    diary_session = get_object_or_404(DiarySession.objects.select_related('turma'), id=session_id, turma_id=class_id)
    turma = diary_session.turma
    
    if not _can_access_diary(request.user, turma):
        messages.error(request, _("You do not have permission to add entries to this diary."))
        # Redirect back to the specific session view
        return redirect('diary:view_diary_session', class_id=turma.id, session_id=session_id)
        
    # Prevent adding to archived sessions
    if diary_session.status != 'ACTIVE':
        messages.error(request, _("Cannot add entries to an archived diary session."))
        return redirect('diary:view_diary_session', class_id=turma.id, session_id=session_id)

    column = request.POST.get('column')
    content = request.POST.get('content')
    
    valid_columns = [key for key, _ in DiaryEntry.COLUMN_CHOICES]
    if not column or column not in valid_columns:
        messages.error(request, _("Invalid column specified."))
        return redirect('diary:view_diary_session', class_id=turma.id, session_id=session_id)
    if not content or not content.strip():
        messages.error(request, _("Content cannot be empty."))
        return redirect('diary:view_diary_session', class_id=turma.id, session_id=session_id)
        
    DiaryEntry.objects.create(
        session=diary_session,
        column=column,
        content=content.strip(),
        author=request.user
    )
    messages.success(request, _("Diary entry added successfully."))
    # Redirect back to the specific session view
    return redirect('diary:view_diary_session', class_id=turma.id, session_id=session_id)

@require_POST
@login_required
# @group_required('professor', 'admin') # Use helper
def archive_and_start_new_session(request, class_id):
    """Archives the current active session and starts a new one."""
    turma = get_object_or_404(Class, id=class_id)
    
    if not _can_moderate_diary(request.user, turma):
        messages.error(request, _("Only teachers or admins can start/archive diary sessions."))
        return redirect('diary:view_diary_active', class_id=turma.id)
        
    with transaction.atomic():
        # Find and archive the current active session (if any)
        active_session = DiarySession.objects.filter(turma=turma, status='ACTIVE').order_by('-start_date').first()
        if active_session:
            active_session.status = 'ARCHIVED'
            active_session.end_date = timezone.localdate() # Set end date to today
            active_session.save(update_fields=['status', 'end_date'])
            messages.info(request, _("Previous diary session archived."))
        
        # Create a new active session starting today
        new_session = DiarySession.objects.create(turma=turma, status='ACTIVE')
        messages.success(request, _("New diary session started."))
        
        # Redirect to the new active session
        return redirect('diary:view_diary_session', class_id=turma.id, session_id=new_session.id)

# TODO: Add list_diary_sessions view
# TODO: Add edit/delete entry views
