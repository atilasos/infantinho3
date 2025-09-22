from django.db import models
from django.utils.translation import gettext_lazy as _
from django.conf import settings # Import settings

from core.models import TimeStampedModel

class Class(models.Model):
    """
    Represents a class group (turma) within the school.
    Links teachers and students for a specific academic year or period.
    """
    name = models.CharField(
        _('class name'),
        max_length=100, # Increased max_length slightly 
        help_text=_('Name of the class, e.g., "5º A", "Turma Azul".')
    )
    year = models.IntegerField(
        _('academic year'),
        help_text=_('Starting year of the academic year (e.g., 2024 for 2024/2025) or the grade level (e.g., 5 for 5th grade).')
        # Consider adding validation or choices if year represents grade level
    )
    students = models.ManyToManyField(
        settings.AUTH_USER_MODEL,
        related_name='classes_attended',
        limit_choices_to={'role': 'aluno'},
        verbose_name=_('students'),
        blank=True,
    )
    teachers = models.ManyToManyField(
        settings.AUTH_USER_MODEL,
        related_name='classes_taught',
        limit_choices_to={'role': 'professor'},
        verbose_name=_('teachers'),
    )
    # Optional: Add a field for class coordinator (main teacher)
    # coordinator = models.ForeignKey(
    #     settings.AUTH_USER_MODEL, 
    #     on_delete=models.SET_NULL, 
    #     related_name='coordinated_classes', 
    #     null=True, 
    #     blank=True, 
    #     limit_choices_to={'role': 'professor'},
    #     verbose_name=_('coordinator')
    # )

    class Meta:
        verbose_name = _('Class')
        verbose_name_plural = _('Classes')
        ordering = ['year', 'name'] # Default ordering in admin/queries

    def __str__(self):
        """Returns a string representation of the class."""
        return f"{self.name} ({self.year})"

    # Add any custom methods relevant to the Class model here
    # Example:
    # def get_active_students_count(self):
    #     return self.students.filter(is_active=True).count()


class ClassMembership(TimeStampedModel):
    """Explicit membership linking users to classes with a role context."""

    class Roles(models.TextChoices):
        STUDENT = 'student', _('Aluno')
        TEACHER = 'teacher', _('Professor')
        GUARDIAN = 'guardian', _('Encarregado de Educação')
        ASSISTANT = 'assistant', _('Assistente')

    class_instance = models.ForeignKey(
        Class,
        on_delete=models.CASCADE,
        related_name='memberships',
        verbose_name=_('class'),
    )
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='class_memberships',
        verbose_name=_('user'),
    )
    role = models.CharField(
        _('role'),
        max_length=20,
        choices=Roles.choices,
    )
    assigned_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        null=True,
        blank=True,
        on_delete=models.SET_NULL,
        related_name='assigned_class_memberships',
        verbose_name=_('assigned by'),
    )
    is_active = models.BooleanField(
        _('is active'),
        default=True,
        help_text=_('Marks whether the membership is active.'),
    )

    class Meta:
        verbose_name = _('Class membership')
        verbose_name_plural = _('Class memberships')
        unique_together = ('class_instance', 'user')
        indexes = [
            models.Index(fields=('class_instance', 'role')),
            models.Index(fields=('user', 'role')),
        ]

    def __str__(self):
        return f"{self.user} -> {self.class_instance} ({self.get_role_display()})"
