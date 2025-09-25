# checklists/models.py
from django.db import models
from django.utils.translation import gettext_lazy as _
from django.utils import timezone
from django.conf import settings

# Import related models
from classes.models import Class # Assuming year/level info might be here later
# Need User model for student and marker
# Use settings.AUTH_USER_MODEL to avoid potential circular imports
User = settings.AUTH_USER_MODEL 

class ChecklistTemplate(models.Model):
    """ Template for a checklist, e.g., 'Português 5º Ano'. """
    name = models.CharField(_("name"), max_length=150)
    # Add fields like applicable_year, subject if needed for filtering
    # applicable_year = models.IntegerField(_("applicable year"), null=True, blank=True)
    description = models.TextField(_("description"), blank=True)
    version = models.PositiveIntegerField(_('version'), default=1)
    is_published = models.BooleanField(_('published'), default=True)
    created_by = models.ForeignKey(
        User,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='authored_checklist_templates',
        verbose_name=_('author'),
    )
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    classes = models.ManyToManyField(
        Class, 
        blank=True, # Permite que um template não esteja associado a nenhuma turma
        related_name='checklist_templates', # Nome reverso explícito
        verbose_name=_('Associated Classes')
    )

    class Meta:
        ordering = ['name', '-version']
        verbose_name = _("Checklist Template")
        verbose_name_plural = _("Checklist Templates")
        constraints = [
            models.UniqueConstraint(fields=['name', 'version'], name='unique_template_name_version')
        ]

    def __str__(self):
        return f"{self.name} v{self.version}"

class ChecklistItem(models.Model):
    """ An individual item/learning objective within a ChecklistTemplate. """
    template = models.ForeignKey(ChecklistTemplate, on_delete=models.CASCADE, related_name='items')
    code = models.CharField(_("code"), max_length=20, blank=True) # e.g., OC1, L5
    text = models.TextField(_("text"), default="Default text - please update")
    order = models.PositiveIntegerField(_("order"), default=0) # For ordering within template
    contracted_in_council = models.BooleanField(
        _("negotiated in council"),
        default=False,
        help_text=_('Mark if this objective foi contratualizado em Conselho de Cooperação Educativa.')
    )

    class Meta:
        ordering = ['template', 'order', 'code']
        unique_together = ('template', 'code') # Code should be unique within a template
        verbose_name = _("Checklist Item")
        verbose_name_plural = _("Checklist Items")

    def __str__(self):
        return f"{self.code}: {self.text[:60]}..." if self.code else f"{self.text[:60]}..."

class ChecklistMark(models.Model):
    """ Tracks the status of a specific ChecklistItem for a specific student checklist status. """
    STATUS_CHOICES = [
        ('NOT_STARTED', _('Not Started')),
        ('IN_PROGRESS', _('In Progress')),
        ('COMPLETED', _('Completed')),
        ('VALIDATED', _('Validated')), # Teacher validated completion
    ]
    
    # Link to the specific student's checklist status record
    status_record = models.ForeignKey(
        'ChecklistStatus', # Use string form if ChecklistStatus is defined later
        on_delete=models.CASCADE, 
        related_name='marks', 
        verbose_name=_('checklist status')
    )
    
    item = models.ForeignKey(ChecklistItem, on_delete=models.CASCADE, related_name='marks')
    
    # Renamed 'status' to 'mark_status'
    mark_status = models.CharField(
        _("status"), 
        max_length=20, 
        choices=STATUS_CHOICES, 
        default='NOT_STARTED'
    )
    
    marked_by = models.ForeignKey(
        User, 
        on_delete=models.SET_NULL, 
        null=True, blank=True, 
        related_name='marked_checklist_items'
    )
    marked_at = models.DateTimeField(_("marked at"), default=timezone.now) # Changed auto_now=True to default=timezone.now
    teacher_validated = models.BooleanField(_("teacher validated"), default=False) # Added teacher validation flag
    comment = models.TextField(_("comment"), blank=True) # Added comment field

    class Meta:
        ordering = ['status_record__student', 'item__order'] # Updated ordering
        # Updated unique_together to use status_record
        unique_together = ('status_record', 'item') 
        verbose_name = _("Checklist Mark")
        verbose_name_plural = _("Checklist Marks")

    def __str__(self):
        # Updated __str__ to use status_record and new field name
        student_username = self.status_record.student.username if self.status_record and self.status_record.student else 'N/A'
        item_code = self.item.code if self.item else 'N/A'
        return f"{student_username} - {item_code} - {self.get_mark_status_display()}"

    def save(self, *args, **kwargs):
        """ Override save to update parent status percentage and handle validation reset. """
        # Reset validation if student changes status from completed
        if not self.pk: # If creating
             self.marked_at = timezone.now() # Set initial timestamp
        else: # If updating
            # Check if mark_status changed *from* completed *by the student*
            try:
                orig = ChecklistMark.objects.get(pk=self.pk)
                if orig.mark_status == 'COMPLETED' and self.mark_status != 'COMPLETED' and self.marked_by == self.status_record.student:
                     self.teacher_validated = False
                     
                # Only update marked_at if relevant fields change? Or always update? Let's update if status/comment change.
                if orig.mark_status != self.mark_status or orig.comment != self.comment:
                    self.marked_at = timezone.now()
                    
            except ChecklistMark.DoesNotExist:
                pass # Should not happen if pk exists, but handle gracefully

        # Teacher action always sets validation (handled in view POST, but could be redundant here)
        # if self.marked_by != self.status_record.student and self.mark_status == 'COMPLETED':
        #    self.teacher_validated = True 
        
        # Ensure validation is False if status is not Completed
        if self.mark_status != 'COMPLETED':
            self.teacher_validated = False
            
        super().save(*args, **kwargs)
        # Update parent status after saving the mark
        if self.status_record:
            self.status_record.update_percent_complete()

class ChecklistStatus(models.Model):
    """Instância da LV para um aluno/turma específica."""

    class LVState(models.TextChoices):
        DRAFT = 'draft', _('Draft')
        SUBMITTED = 'submitted', _('Submitted')
        VALIDATED = 'validated', _('Validated')
        NEEDS_REVISION = 'needs_revision', _('Needs revision')
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
    template_version = models.PositiveIntegerField(_('template version'), default=1)
    state = models.CharField(_('state'), max_length=20, choices=LVState.choices, default=LVState.DRAFT)
    student_notes = models.TextField(_('student notes'), blank=True)
    started_at = models.DateTimeField(_('started at'), default=timezone.now)
    submitted_at = models.DateTimeField(_('submitted at'), null=True, blank=True)
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
            new_percent = 0
        else:
            # Count items marked as COMPLETED OR VALIDATED as 'done'
            # Use related_name 'marks' from ChecklistMark.status_record
            completed_or_validated_count = self.marks.filter(
                models.Q(mark_status='COMPLETED') | models.Q(mark_status='VALIDATED')
            ).count()
            new_percent = (completed_or_validated_count / total_items) * 100
        
        # Only save if percentage actually changed to avoid unnecessary updates/signals
        if self.percent_complete != new_percent:
            self.percent_complete = new_percent
            self.save(update_fields=['percent_complete', 'updated_at'])

    def initialise_marks(self):
        existing_items = set(self.marks.values_list('item_id', flat=True))
        pending = []
        for item in self.template.items.all():
            if item.id not in existing_items:
                pending.append(
                    ChecklistMark(
                        status_record=self,
                        item=item,
                        mark_status='NOT_STARTED',
                    )
                )
        if pending:
            ChecklistMark.objects.bulk_create(pending)

    def submit(self):
        self.state = self.LVState.SUBMITTED
        self.submitted_at = timezone.now()
        self.save(update_fields=['state', 'submitted_at', 'updated_at'])
