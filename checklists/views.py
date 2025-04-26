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
from collections import OrderedDict # For grouping marks in Turma view
import itertools # For grouping marks

from .models import ChecklistStatus, ChecklistTemplate, ChecklistItem, ChecklistMark
from classes.models import Class
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
class MyChecklistsView(ListView):
    """
    Displays a list of checklist statuses for the logged-in student.
    Separates lists into active and completed based on percentage.
    """
    model = ChecklistStatus
    template_name = 'checklists/my_checklists.html'
    context_object_name = 'checklist_statuses' # Renamed for clarity

    def get_queryset(self):
        """Fetches checklist statuses only for the logged-in user (student)."""
        return ChecklistStatus.objects.filter(
            student=self.request.user
        ).select_related('template', 'student_class').order_by('student_class__name', 'template__subject')

    def get_context_data(self, **kwargs):
        """Adds separate lists for active and completed checklists."""
        context = super().get_context_data(**kwargs)
        all_status = context['checklist_statuses']
        context['active_checklists'] = [s for s in all_status if s.percent_complete < 100]
        context['completed_checklists'] = [s for s in all_status if s.percent_complete >= 100]
        return context

@method_decorator(login_required, name='dispatch')
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
        # Order by item, then by latest marked_at within that item
        marks_qs = ChecklistMark.objects.filter(status=status).order_by('item_id', '-marked_at')
        
        latest_marks_by_item = {}
        for mark in marks_qs:
            if mark.item_id not in latest_marks_by_item:
                latest_marks_by_item[mark.item_id] = mark # First one is latest due to ordering
                
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
        
        # --- Logic to create/update mark (keeping history) ---
        mark = ChecklistMark.objects.create(
            status=status,
            item=item,
            mark_status=new_mark_status,
            comment=comment_text,
            marked_by=request.user,
            teacher_validated=False 
        )
        
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
                message = f"""Student {request.user.get_full_name() or request.user.username} updated the item '{item.description}' to '{mark.get_mark_status_display()}'.
Comment: {comment_text}

View class progress: {turma_url}"""
                send_mail(subject, message, settings.DEFAULT_FROM_EMAIL, teacher_emails, fail_silently=False)
            except Exception as e:
                print(f"Error sending checklist update notification to teachers: {e}")

        messages.success(request, _('Objective updated successfully!'))
        return redirect(f'{request.path}?highlight={item_id}')


@method_decorator(login_required, name='dispatch')
class ChecklistTurmaView(View):
    """
    Displays the checklist progress overview for an entire class (teacher/admin view).
    Handles GET requests to show the grid.
    Handles POST requests when a teacher validates or rectifies a student's mark.
    """
    template_name = 'checklists/checklist_turma.html'

    # TODO: Replace this with a decorator check
    def dispatch(self, request, *args, **kwargs):
        class_id = kwargs.get('class_id')
        turma = get_object_or_404(Class, id=class_id)
        if not is_prof_or_admin(request.user, turma): # Using helper for now
            messages.error(request, _('Access restricted to teachers of this class or administrators.'))
            return redirect('class_detail', class_id=class_id) 
        return super().dispatch(request, *args, **kwargs)

    def get(self, request, class_id, template_id):
        """Renders the class overview grid."""
        turma = get_object_or_404(Class, id=class_id)
        template = get_object_or_404(ChecklistTemplate, id=template_id)
        
        students = turma.students.all().order_by('first_name', 'last_name')
        items = ChecklistItem.objects.filter(template=template).order_by('order')
        
        # Fetch relevant statuses for students in this class
        status_qs = ChecklistStatus.objects.filter(template=template, student_class=turma)
        status_map = {s.student_id: s for s in status_qs}
        
        # Fetch all relevant marks for these statuses
        all_marks = ChecklistMark.objects.filter(
            status__in=status_qs
        ).select_related('marked_by').order_by('status__student_id', 'item_id', '-marked_at') # Order is crucial

        # Process in Python to get the latest mark per student/item (compatible with SQLite)
        marks_by_student_item = {}
        for mark in all_marks:
            key = (mark.status.student_id, mark.item_id)
            if key not in marks_by_student_item: # Since ordered by -marked_at, first encountered is latest
                marks_by_student_item[key] = mark

        # Calculate individual progress based on the latest marks found
        progresso_individual = {}
        for student_user in students:
            done = 0
            for item in items:
                mark = marks_by_student_item.get((student_user.id, item.id))
                if mark and mark.mark_status == 'completed':
                    done += 1
            total = items.count() # Use count() instead of len() for queryset
            progresso_individual[student_user.id] = int((done / total) * 100) if total > 0 else 0
            
        # Calculate collective progress
        progresso_coletivo = 0
        if students.exists():
            progresso_coletivo = int(sum(progresso_individual.values()) / students.count())
            
        context = {
            'turma': turma,
            'template': template,
            'students': students,
            'items': items,
            'marks_by_student_item': marks_by_student_item,
            'progresso_individual': progresso_individual,
            'progresso_coletivo': progresso_coletivo,
            'mark_status_choices': ChecklistMark.STATUS_CHOICES, 
        }
        return render(request, self.template_name, context)

    def post(self, request, class_id, template_id):
        """Handles teacher validation/rectification of a student's mark."""
        turma = get_object_or_404(Class, id=class_id)
        template = get_object_or_404(ChecklistTemplate, id=template_id)
        
        student_id = request.POST.get('student_id') 
        item_id = request.POST.get('item_id')
        new_mark_status = request.POST.get('mark_status') 
        comment_text = request.POST.get('comment', '') 
        
        if not (student_id and item_id and new_mark_status):
            messages.error(request, _('Insufficient data to validate/rectify.'))
            return redirect(request.path)
            
        student_user = get_object_or_404(turma.students, id=student_id)
        item = get_object_or_404(ChecklistItem, id=item_id, template=template)
        status = get_object_or_404(ChecklistStatus, template=template, student_class=turma, student=student_user)
        
        # --- Logic for teacher update (creates new mark, sets validated=True) --- 
        mark = ChecklistMark.objects.create(
            status=status,
            item=item,
            mark_status=new_mark_status,
            comment=comment_text,
            marked_by=request.user,
            teacher_validated=True     # Mark as teacher validated
        )

        # --- Send Notification to Student --- 
        if student_user.email:
            subject = f"[Infantinho] Checklist item updated by teacher in {template.name}"
            try:
                detail_url = request.build_absolute_uri(
                    reverse('checklists:checklist_detail', args=[template.id])
                )
                message = f"""Your teacher {request.user.get_full_name() or request.user.username} updated the item '{item.description}' to '{mark.get_mark_status_display()}'.
Comment: {comment_text}

View your checklist: {detail_url}"""
                send_mail(subject, message, settings.DEFAULT_FROM_EMAIL, [student_user.email], fail_silently=False)
            except Exception as e:
                 print(f"Error sending checklist update notification to student: {e}")
                 
        messages.success(request, _('Mark validated/rectified for {student_name}.'
                                  ).format(student_name=student_user.get_full_name() or student_user.username))
        return redirect(request.path)

# Simple static help view
@method_decorator(login_required, name='dispatch')
class HelpView(TemplateView):
    """Renders the static help page for the checklists module."""
    template_name = 'checklists/help.html'
    # Potentially add class context if help is class-specific
    # def get_context_data(self, **kwargs):
    #     context = super().get_context_data(**kwargs)
    #     # context['turma'] = get_object_or_404(Class, id=self.kwargs.get('class_id'))
    #     return context
