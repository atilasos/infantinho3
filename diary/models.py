from django.db import models
from django.utils import timezone
from django.utils.translation import gettext_lazy as _

# Import related models from other apps
from users.models import User
from classes.models import Class 

class DiarySession(models.Model):
    """ Represents a single diary period (e.g., a week or month). """
    STATUS_CHOICES = [
        ('ACTIVE', _('Active')),
        ('ARCHIVED', _('Archived')),
    ]
    
    turma = models.ForeignKey(Class, on_delete=models.CASCADE, related_name='diary_sessions', verbose_name=_("class"))
    # date = models.DateField(_("date"), default=timezone.now) # Removed
    start_date = models.DateField(_("start date"), default=timezone.now)
    end_date = models.DateField(_("end date"), null=True, blank=True)
    status = models.CharField(_("status"), max_length=10, choices=STATUS_CHOICES, default='ACTIVE')
    
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['-start_date'] # Order by start date, newest first
        # unique_together = ('turma', 'date') # Removed
        # Add constraint: Only one ACTIVE session per turma? Requires DB constraints or clean() logic
        verbose_name = _("Diary Session")
        verbose_name_plural = _("Diary Sessions")

    def __str__(self):
        end_str = f" - {self.end_date.strftime('%Y-%m-%d')}" if self.end_date else _(" (Active)")
        return f"{_('Diary')} {self.turma.name} ({self.start_date.strftime('%Y-%m-%d')}{end_str})"

class DiaryEntry(models.Model):
    """ Represents an individual entry within a diary session column. """
    COLUMN_CHOICES = [
        ('GOSTEI', _('Liked')),
        ('NAO_GOSTEI', _('Disliked')),
        ('FIZEMOS', _('We Did')),
        ('QUEREMOS', _('We Want')),
    ]
    session = models.ForeignKey(DiarySession, on_delete=models.CASCADE, related_name='entries')
    column = models.CharField(_("column"), max_length=20, choices=COLUMN_CHOICES)
    content = models.TextField(_("content"))
    author = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True, related_name='diary_entries') # Who added this specific item?
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['created_at'] # Order entries within a session chronologically
        verbose_name = _("Diary Entry")
        verbose_name_plural = _("Diary Entries")

    def __str__(self):
        # Truncate content for display
        truncated_content = (self.content[:50] + '...') if len(self.content) > 50 else self.content
        return f"{self.get_column_display()}: {truncated_content}"
