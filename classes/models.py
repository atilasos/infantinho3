from django.db import models
from django.utils.translation import gettext_lazy as _
# Assuming User model is in users app -- REMOVED TO FIX CIRCULAR IMPORT
# from users.models import User 
from django.conf import settings # Import settings

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
        settings.AUTH_USER_MODEL, # Use settings.AUTH_USER_MODEL
        related_name='classes_attended',
        limit_choices_to={'role': 'aluno'}, # Ensure only users with 'aluno' role can be added
        verbose_name=_('students'),
        blank=True # Allow classes to be created before students are assigned
    )
    teachers = models.ManyToManyField(
        settings.AUTH_USER_MODEL, # Use settings.AUTH_USER_MODEL
        related_name='classes_taught',
        limit_choices_to={'role': 'professor'}, # Ensure only users with 'professor' role can be added
        verbose_name=_('teachers')
        # Typically a class should have at least one teacher, consider validation or making blank=False if needed after creation
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
