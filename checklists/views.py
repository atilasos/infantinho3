# checklists/views.py
from django.shortcuts import render, get_object_or_404, redirect
from django.contrib.auth.decorators import login_required
from django.utils.decorators import method_decorator
from django.views.generic import ListView, TemplateView, View
from django.contrib import messages
from django.core.mail import send_mail
from django.conf import settings
from django.urls import reverse
from django.utils.translation import gettext_lazy as _
from django.utils import timezone # Needed for update_or_create
from collections import OrderedDict
import itertools
from django.db.models import Q # Import Q for query

from .models import ChecklistStatus, ChecklistTemplate, ChecklistItem, ChecklistMark
from classes.models import Class
from users.decorators import group_required # Import the new decorator
from users.permissions import class_student_required, class_teacher_required
# TODO: Import permission decorators once created

# Helper function for permission check (to be replaced by decorator)
# TODO: Create a proper decorator in permissions.py
def is_prof_or_admin(user, student_class):
    """Checks if user is admin or a teacher for the given class."""
    if not user or not user.is_authenticated:
        return False
    if user.is_superuser or (hasattr(user, 'role') and user.role == 'admin'):
        return True
    if hasattr(user, 'role') and user.role == 'professor':
        return student_class in getattr(user, 'classes_taught', Class.objects.none()).all()
    return False

@method_decorator(login_required, name='dispatch')
@method_decorator(group_required('aluno'), name='dispatch')
class MyChecklistsView(ListView):
    """
    Displays a list of checklist statuses for the logged-in student.
    Separates lists into active and completed based on percentage.
    """
    model = ChecklistStatus
    template_name = 'checklists/my_checklists.html'
    context_object_name = 'checklist_statuses'

    def get_queryset(self):
        """Fetches checklist statuses only for the logged-in user (student)."""
        return ChecklistStatus.objects.filter(
            student=self.request.user
        ).select_related('template', 'student_class').order_by('student_class__name', 'template__name')

    def get_context_data(self, **kwargs):
        """Adds separate lists for active and completed checklists."""
        context = super().get_context_data(**kwargs)
        all_status = context['checklist_statuses']
        context['active_checklists'] = [s for s in all_status if s.percent_complete < 100]
        context['completed_checklists'] = [s for s in all_status if s.percent_complete >= 100]
        return context

@method_decorator(login_required, name='dispatch')
@method_decorator(group_required('aluno'), name='dispatch')
class ChecklistDetailView(View):
    """
    Displays the details of one checklist for the logged-in student.
    Handles GET requests to show items and marks.
    Handles POST requests when a student updates the status of an item.
    """
    template_name = 'checklists/checklist_detail.html'

    def get(self, request, template_id):
        """Renders the checklist detail page for the student."""
        template = get_object_or_404(ChecklistTemplate, id=template_id)
        status = get_object_or_404(
            ChecklistStatus.objects.select_related('student_class'), 
            template=template, 
            student=request.user
        )
        items = ChecklistItem.objects.filter(template=template).order_by('order')
        
        # Fetch the latest mark for each item for this student's status
        marks_qs = ChecklistMark.objects.filter(status_record=status).order_by('item_id', '-marked_at')
        
        latest_marks_by_item = {}
        for mark in marks_qs:
            if mark.item_id not in latest_marks_by_item:
                latest_marks_by_item[mark.item_id] = mark 
                
        items_and_marks = [(item, latest_marks_by_item.get(item.id)) for item in items]
        
        highlight = request.GET.get('highlight') 
        context = {
            'template': template,
            'status': status,
            'items_and_marks': items_and_marks,
            'highlight_item_id': highlight,
            'total_items': items.count(),
            'mark_status_choices': ChecklistMark.STATUS_CHOICES,
        }
        return render(request, self.template_name, context)

    def post(self, request, template_id):
        """Handles student submission updating an item's status."""
        template = get_object_or_404(ChecklistTemplate, id=template_id)
        status = get_object_or_404(ChecklistStatus, template=template, student=request.user)
        
        item_id = request.POST.get('item_id')
        new_mark_status = request.POST.get('mark_status')
        comment_text = request.POST.get('comment', '')
        
        item = get_object_or_404(ChecklistItem, id=item_id, template=template)
        
        if new_mark_status not in dict(ChecklistMark.STATUS_CHOICES):
            messages.error(request, _('Invalid status provided.'))
            return redirect(request.path)

        # --- Logic to update or create mark (respecting unique constraint) ---
        mark, created = ChecklistMark.objects.update_or_create(
            status_record=status,
            item=item,
            defaults={
                'mark_status': new_mark_status,
                'comment': comment_text,
                'marked_by': request.user,
                # 'marked_at' is handled by model save
                # 'teacher_validated' is handled by model save based on status change
            }
        )
        # Model's save() method handles updating parent %, marked_at, and teacher_validated reset
        
        # --- Send Notification to Teachers --- 
        student_class = status.student_class
        teachers = student_class.teachers.all()
        teacher_emails = [t.email for t in teachers if t.email]
        if teacher_emails:
            subject = f"[Infantinho] {request.user.get_full_name() or request.user.username} updated item in {template.name}"
            try:
                turma_url = request.build_absolute_uri(
                    reverse('checklists:checklist_turma', args=[student_class.id, template.id])
                )
                message = f"""Student {request.user.get_full_name() or request.user.username} updated the item '{item.text}' to '{mark.get_mark_status_display()}'.
Comment: {comment_text}

View class progress: {turma_url}"""
                send_mail(subject, message, settings.DEFAULT_FROM_EMAIL, teacher_emails, fail_silently=False)
            except Exception as e:
                print(f"Error sending checklist update notification to teachers: {e}")

        messages.success(request, _('Objective updated successfully!'))
        return redirect(f'{request.path}?highlight={item_id}')


@method_decorator(login_required, name='dispatch')
@method_decorator(group_required('professor'), name='dispatch')
class ChecklistTurmaView(View):
    """
    Displays the checklist progress overview for an entire class (teacher/admin view).
    Handles GET requests to show the grid.
    Handles POST requests when a teacher validates or rectifies a student's mark.
    """
    template_name = 'checklists/checklist_turma.html'

    def get(self, request, class_id, template_id):
        """Renders the class overview grid."""
        turma = get_object_or_404(Class, id=class_id)
        # --- Add specific teacher check --- 
        if not request.user.is_superuser and request.user not in turma.teachers.all():
            messages.error(request, _('You do not have permission to view this class checklist.'))
            # Redirect to class list as expected by tests
            return redirect('classes:class_list')
        # ----------------------------------
            
        template = get_object_or_404(ChecklistTemplate, id=template_id)
        
        students = turma.students.all().order_by('first_name', 'last_name')
        items = ChecklistItem.objects.filter(template=template).order_by('order')
        
        # Get all ChecklistStatus objects for this class and template
        status_qs = ChecklistStatus.objects.filter(template=template, student_class=turma)
        # status_map = {s.student_id: s for s in status_qs} # No longer needed directly
        
        # Fetch all relevant marks ordered to easily find the latest per student/item
        # Filter by status_record being in the status_qs for this class/template
        all_marks = ChecklistMark.objects.filter(
            status_record__in=status_qs
        ).select_related('marked_by', 'status_record__student', 'item').order_by('status_record__student_id', 'item__order', '-marked_at')

        # Optimized way to get the latest mark per (student, item) pair
        latest_marks_by_student_item = {}
        processed_keys = set()
        for mark in all_marks:
            key = (mark.status_record.student_id, mark.item_id)
            if key not in processed_keys:
                latest_marks_by_student_item[key] = mark
                processed_keys.add(key)

        # Calculate individual progress using the status objects (already updated by signals/saves)
        progresso_individual = {s.student_id: s.percent_complete for s in status_qs}
        # Recalculate collective progress based on fetched statuses
        progresso_coletivo = 0
        if status_qs.exists():
            total_percentage = sum(s.percent_complete for s in status_qs)
            progresso_coletivo = int(total_percentage / status_qs.count()) if status_qs.count() > 0 else 0
            
        context = {
            'turma': turma,
            'template': template,
            'students': students,
            'items': items,
            'marks_by_student_item': latest_marks_by_student_item, # Pass the calculated latest marks
            'progresso_individual': progresso_individual,
            'progresso_coletivo': progresso_coletivo,
            'mark_status_choices': ChecklistMark.STATUS_CHOICES, 
        }
        return render(request, self.template_name, context)

    def post(self, request, class_id, template_id):
        """Handles teacher validation/rectification of a student's mark."""
        turma = get_object_or_404(Class, id=class_id)
        # --- Add specific teacher check --- 
        if not request.user.is_superuser and request.user not in turma.teachers.all():
            messages.error(request, _('You do not have permission to modify this class checklist.'))
            # Redirect to class list as expected by tests
            return redirect('classes:class_list')
        # ----------------------------------
            
        template = get_object_or_404(ChecklistTemplate, id=template_id)
        
        student_id = request.POST.get('student_id') 
        item_id = request.POST.get('item_id')
        new_mark_status = request.POST.get('mark_status') 
        comment_text = request.POST.get('comment', '') 
        
        if not (student_id and item_id and new_mark_status):
            messages.error(request, _('Insufficient data to validate/rectify.'))
            return redirect(request.path)
            
        if new_mark_status not in dict(ChecklistMark.STATUS_CHOICES):
            messages.error(request, _('Invalid status provided.'))
            return redirect(request.path)
            
        student_user = get_object_or_404(turma.students, id=student_id)
        item = get_object_or_404(ChecklistItem, id=item_id, template=template)
        # Get the ChecklistStatus object for this student/template/class
        status = get_object_or_404(ChecklistStatus, template=template, student_class=turma, student=student_user)
        
        # --- Logic for teacher update (update or create, set validated=True if completed) --- 
        mark, created = ChecklistMark.objects.update_or_create(
            status_record=status,
            item=item,
            defaults={
                'mark_status': new_mark_status,
                'comment': comment_text,
                'marked_by': request.user,    # Teacher is the marker
                # Set teacher_validated based on status ONLY if teacher is marking
                'teacher_validated': (new_mark_status == 'COMPLETED') 
                # 'marked_at' is handled by model save
            }
        )
        # Model save() handles updating parent %, marked_at

        # --- Send Notification to Student --- 
        if student_user.email:
            subject = f"[Infantinho] Checklist item updated by teacher in {template.name}"
            try:
                detail_url = request.build_absolute_uri(
                    reverse('checklists:checklist_detail', args=[template.id]) + f'?highlight={item_id}' # Add highlight
                )
                message = f"""Your teacher {request.user.get_full_name() or request.user.username} updated the item '{item.text}' to '{mark.get_mark_status_display()}'.
Comment: {comment_text}

View your checklist: {detail_url}"""
                send_mail(subject, message, settings.DEFAULT_FROM_EMAIL, [student_user.email], fail_silently=False)
            except Exception as e:
                 print(f"Error sending checklist update notification to student: {e}")
                 
        messages.success(request, _('Mark validated/rectified for {student_name}.'
                                  ).format(student_name=student_user.get_full_name() or student_user.username))
        # Redirect back to the same page, maybe with a fragment identifier for the student row?
        # For now, just redirect back to the path.
        return redirect(request.path)

# Simple static help view
@method_decorator(login_required, name='dispatch')
class HelpView(TemplateView):
    """Renders the static help page for the checklists module."""
    template_name = 'checklists/help.html'
