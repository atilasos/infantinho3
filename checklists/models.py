# checklists/models.py
from django.db import models
from django.utils.translation import gettext_lazy as _
from django.utils import timezone

# Assuming User and Class models are imported from their respective apps
from users.models import User
from classes.models import Class

class ChecklistTemplate(models.Model):
    """
    Represents a template for a checklist, defining the subject, grade, and items.
    Example: "Portuguese - 5th Grade", "Mathematics - 7th Grade".
    """
    name = models.CharField(
        _('template name'), 
        max_length=150, # Increased length slightly
        help_text=_('Name of the checklist template, e.g., "Mathematics 7th Grade".')
    )
    # Changed from CharField to IntegerField for grade level
    grade_level = models.IntegerField(
        _('grade level'), 
        null=True, blank=True, # Allow templates not specific to one grade
        help_text=_('The grade level this template applies to (e.g., 5 for 5th grade). Leave blank if multi-grade.')
    )
    subject = models.CharField(
        _('subject'), 
        max_length=100,
        help_text=_('The subject area, e.g., "Portuguese", "Mathematics", "Science".')
    )
    description = models.TextField(
        _('description'), 
        blank=True,
        help_text=_('Optional description or general guidelines for this checklist.')
    )
    created_at = models.DateTimeField(auto_now_add=True, verbose_name=_('created at'))
    updated_at = models.DateTimeField(auto_now=True, verbose_name=_('updated at'))

    class Meta:
        verbose_name = _('Checklist Template')
        verbose_name_plural = _('Checklist Templates')
        ordering = ['grade_level', 'subject', 'name']

    def __str__(self):
        grade_str = f" - Grade {self.grade_level}" if self.grade_level else ""
        return f"{self.subject}{grade_str}: {self.name}"

class ChecklistItem(models.Model):
    """
    A specific item or learning objective within a ChecklistTemplate.
    Example: "Can multiply fractions", "Understands photosynthesis".
    """
    template = models.ForeignKey(
        ChecklistTemplate, 
        on_delete=models.CASCADE, 
        related_name='items',
        verbose_name=_('template')
    )
    description = models.CharField(
        _('description'), 
        max_length=255,
        help_text=_('The description of the learning objective or item.')
    )
    criteria = models.TextField(
        _('criteria'), 
        blank=True,
        help_text=_('Optional: Specific criteria or descriptors for achieving this item.')
    )
    order = models.IntegerField(
        _('order'), 
        default=0,
        help_text=_('Order in which this item appears in the checklist.')
    )
    # Flag indicating if this item was specifically agreed upon in a class council
    council_agreed = models.BooleanField(
        _('agreed in council'), 
        default=False,
        help_text=_('Was this item specifically agreed upon as a focus in a class council?')
    )

    class Meta:
        verbose_name = _('Checklist Item')
        verbose_name_plural = _('Checklist Items')
        ordering = ['template', 'order', 'description'] # Order by template, then by defined order

    def __str__(self):
        return f"({self.template.name}) {self.description[:60]}"

class ChecklistStatus(models.Model):
    """
    Tracks the overall status of a specific student's progress on a specific checklist template
    within a specific class context.
    Serves as the parent object for individual item marks (ChecklistMark).
    """
    template = models.ForeignKey(
        ChecklistTemplate, 
        on_delete=models.CASCADE, 
        related_name='statuses',
        verbose_name=_('template')
    )
    student = models.ForeignKey(
        User, 
        on_delete=models.CASCADE, 
        related_name='checklist_statuses',
        limit_choices_to={'role': 'aluno'}, # Ensure only students
        verbose_name=_('student')
    )
    # Link to the class the student is taking this checklist in
    student_class = models.ForeignKey(
        Class, 
        on_delete=models.CASCADE, 
        related_name='class_checklist_statuses', # Added related_name
        verbose_name=_('class') 
    )
    percent_complete = models.FloatField(
        _('percentage complete'), 
        default=0,
        help_text=_('Automatically calculated percentage of completed items.')
    )
    updated_at = models.DateTimeField(_('last updated'), auto_now=True)

    class Meta:
        verbose_name = _('Student Checklist Status')
        verbose_name_plural = _('Student Checklist Statuses')
        # Ensure a student has only one status entry per template per class
        unique_together = ('template', 'student', 'student_class') 
        ordering = ['student_class', 'student', 'template']

    def __str__(self):
        return f"{self.student.username} - {self.template.name} ({self.student_class.name}) - {self.percent_complete:.0f}%"

    def update_percent_complete(self):
        """Recalculates the completion percentage based on marks."""
        total_items = self.template.items.count()
        if total_items == 0:
            self.percent_complete = 0
        else:
            # Consider only validated marks? Or any 'completed' mark?
            # For now, count any 'completed' mark.
            completed_items = self.marks.filter(mark_status='completed').count()
            self.percent_complete = (completed_items / total_items) * 100
        self.save(update_fields=['percent_complete', 'updated_at'])

class ChecklistMark(models.Model):
    """
    Represents the status mark for a specific ChecklistItem by a specific student.
    Links back to the overall ChecklistStatus for that student/template.
    """
    # Renamed choices keys to English, kept Portuguese display text
    STATUS_CHOICES = [
        ('not_started', _('Não iniciado')),
        ('in_progress', _('Em progresso')),
        ('completed', _('Concluído')),
    ]
    
    # Link to the student's overall status for this checklist
    status = models.ForeignKey(
        ChecklistStatus, 
        on_delete=models.CASCADE, 
        related_name='marks',
        verbose_name=_('checklist status')
    )
    # Link to the specific item being marked
    item = models.ForeignKey(
        ChecklistItem, 
        on_delete=models.CASCADE, 
        related_name='marks',
        verbose_name=_('item')
    )
    # The status of this specific item mark
    mark_status = models.CharField(
        _('mark status'), 
        max_length=20, 
        choices=STATUS_CHOICES, 
        default='not_started'
    )
    # Optional comment from student or teacher about this item
    comment = models.TextField(
        _('comment'), 
        blank=True
    )
    created_at = models.DateTimeField(_('created at'), auto_now_add=True)
    # Who last updated this specific mark
    marked_by = models.ForeignKey(
        User, 
        on_delete=models.SET_NULL, 
        null=True, 
        blank=True, # Allow initial state to have no marker?
        related_name='marks_made',
        verbose_name=_('marked by')
    )
    marked_at = models.DateTimeField(
        _('marked at'),
        default=timezone.now # Timestamp of the last status change
    )
    # Flag indicating teacher validation of the 'completed' status
    teacher_validated = models.BooleanField(
        _('teacher validated'), 
        default=False,
        # Fixed Syntax: Use double quotes for outer string
        help_text=_("Indicates if a teacher has validated the 'completed' status.")
    )
    # Optional: Add fields for who validated and when, if needed
    # validated_by = models.ForeignKey(User, ..., null=True, blank=True, related_name='marks_validated')
    # validated_at = models.DateTimeField(..., null=True, blank=True)

    class Meta:
        verbose_name = _('Checklist Item Mark')
        verbose_name_plural = _('Checklist Item Marks')
        # Ensure only one mark per item per student status
        unique_together = ('status', 'item')
        ordering = ['status', 'item__order']

    def __str__(self):
        return f"Mark for {self.item.description[:30]} ({self.status.student.username}) - {self.get_mark_status_display()}"

    def save(self, *args, **kwargs):
        """Update timestamp on status change and recalculate parent status percentage."""
        update_parent = False
        # Check if status changed to update timestamp and parent % 
        if self.pk is not None:
            orig = ChecklistMark.objects.get(pk=self.pk)
            if orig.mark_status != self.mark_status:
                self.marked_at = timezone.now()
                update_parent = True # Update parent only if status changed
        else: # First save
            self.marked_at = timezone.now()
            if self.mark_status == 'completed': # Update parent if created as completed
                 update_parent = True
            
        # Reset validation if status is no longer 'completed'
        if self.mark_status != 'completed':
            self.teacher_validated = False
            
        super().save(*args, **kwargs)
        
        # Update the parent ChecklistStatus completion percentage after saving mark, if needed
        if update_parent:
             self.status.update_percent_complete()
