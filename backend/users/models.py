from django.contrib.auth.models import AbstractUser, Group
from django.db import models
from django.core.exceptions import ValidationError
from django.utils.translation import gettext_lazy as _ # For potential future i18n in choices
from django.core.management.base import CommandError
from django.conf import settings # Added for settings.AUTH_USER_MODEL
# Import Class from the classes app -- REMOVED TO FIX CIRCULAR IMPORT
# from classes.models import Class

class User(AbstractUser):
    """
    Custom User model extending Django's AbstractUser.
    Includes fields for role, profile photo, and status (guest/active).
    Email field is inherited and should be used for login (especially with SSO).
    Username field is inherited and should ideally be populated with the email.
    """
    # Ensure email is unique, as it's used for login/SSO identification.
    email = models.EmailField(_('email address'), unique=True)
    must_change_password = models.BooleanField(
        _('must change password'),
        default=False,
        help_text=_('Force user to update the password after the next login.'),
    )
    student_number = models.CharField(
        _('student number'),
        max_length=32,
        unique=True,
        blank=True,
        null=True,
        help_text=_('Unique identifier provided by the school for students.'),
    )
    
    ROLE_CHOICES = [
        ('aluno', _('Aluno')),            # Student
        ('professor', _('Professor')),      # Teacher
        ('admin', _('Administrador')),    # Administrator
        ('encarregado', _('Encarregado de Educação')), # Guardian
        # Note: 'admin' role might overlap with is_superuser. Decide on usage.
        # 'convidado' is not a role, but a status.
    ]
    
    # Role assigned to the user after validation. Null for guests.
    role = models.CharField(
        _('role'),
        max_length=20, 
        choices=ROLE_CHOICES, 
        blank=True, 
        null=True, 
        default=None,
        help_text=_('The primary role of the user within the system.')
    )
    
    # Optional profile picture.
    photo = models.ImageField(
        _('profile photo'),
        upload_to='profile_photos/', 
        blank=True, 
        null=True,
        help_text=_('Optional user profile picture.')
    )
    
    # Tracks the user's status, starting as guest.
    status = models.CharField(
        _('status'),
        max_length=20, 
        default='convidado', # Default status for new users, especially via SSO
        # Changed outer quotes to double quotes to fix syntax error
        help_text=_("User status, e.g., 'convidado' (guest) or 'ativo' (active).")
    )

    def clean(self):
        """
        Ensures that users with 'convidado' status do not have a role assigned.
        """
        super().clean() # Call parent clean method
        if self.status == 'convidado' and self.role:
            raise ValidationError(_('Guests cannot have an assigned role.'))
        if self.student_number and self.role not in ('aluno', None, ''):
            raise ValidationError(_('Only student profiles can store a student number.'))
        # Add any other model-level validation here

    def is_guest(self) -> bool:
        """
        Checks if the user has the 'convidado' (guest) status.
        """
        return self.status == 'convidado'

    def promote_to_role(self, role_name: str):
        """
        Assigns a role to the user, changes their status to 'ativo',
        and adds them to the corresponding Django Group.
        Assumes Groups with names matching ROLE_CHOICES values exist.
        """
        if role_name not in dict(self.ROLE_CHOICES):
            raise ValueError(_('Invalid role specified.'))
            
        self.role = role_name
        self.status = 'ativo'
        
        # Add user to the corresponding Django Group
        try:
            # Group names should match the role_name ('aluno', 'professor', etc.)
            group = Group.objects.get(name=role_name)
            self.groups.add(group)
        except Group.DoesNotExist:
            # Handle case where group doesn't exist (log warning, maybe create it?)
            # For now, we assume groups are pre-created by migrations or admin.
            # print(f"Warning: Group '{role_name}' not found for user {self.username}")
            # Consider raising an error or logging more formally
            # pass 
            # Reraise the exception to ensure it's not swallowed silently
            raise CommandError(f"Group '{role_name}' does not exist. Please create it.") from None

        # Explicitly save only the fields changed by this method
        self.save(update_fields=['role', 'status'])

    def __str__(self):
        return self.get_full_name() or self.username

class GuardianRelation(models.Model):
    """
    Represents the relationship between a student (aluno) and their guardian (encarregado).
    Allows a guardian user to be linked to one or more student users.
    """
    # The student user
    aluno = models.ForeignKey(
        User, 
        on_delete=models.CASCADE, 
        related_name='encarregados_relations',
        limit_choices_to={'role': 'aluno'}, # Optional: Ensure only students can be linked here
        verbose_name=_('student')
    )
    
    # The guardian user
    encarregado = models.ForeignKey(
        User, 
        on_delete=models.CASCADE, 
        related_name='educandos_relations',
        limit_choices_to={'role': 'encarregado'}, # Optional: Ensure only guardians can be linked here
        verbose_name=_('guardian')
    )
    
    # Describes the relationship, e.g., 'Pai', 'Mãe', 'Tutor Legal'.
    parentesco = models.CharField(
        _('relationship'),
        max_length=50, 
        blank=True,
        help_text=_('e.g., Father, Mother, Legal Tutor')
    )

    class Meta:
        # Ensures a guardian is linked only once to a specific student.
        unique_together = ('aluno', 'encarregado')
        verbose_name = _('Guardian Relationship')
        verbose_name_plural = _('Guardian Relationships')

    def __str__(self):
        aluno_name = self.aluno.get_full_name() or self.aluno.username
        encarregado_name = self.encarregado.get_full_name() or self.encarregado.username
        relation = f" ({self.parentesco})" if self.parentesco else ""
        return f"{encarregado_name} -> {aluno_name}{relation}"

class PreApprovedStudent(models.Model):
    """
    Represents a student email pre-approved for automatic class assignment upon first SSO login.
    """
    STATUS_CHOICES = [
        ('Pending', 'Pendente'),
        ('Claimed', 'Reivindicado'),
    ]

    email = models.EmailField(
        max_length=254,
        unique=True,
        verbose_name="Email do Aluno",
        help_text="O endereço de email Microsoft do aluno a ser pré-aprovado."
    )
    class_instance = models.ForeignKey(
        'classes.Class', # Use string reference
        on_delete=models.CASCADE,
        related_name='preapproved_students',
        verbose_name="Turma",
        help_text="A turma à qual o aluno será associado."
    )
    added_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL, # Mantém o registo se o utilizador que adicionou for apagado
        null=True,
        blank=True,
        related_name='added_preapproved_students',
        verbose_name="Adicionado Por",
        help_text="Utilizador (Admin/Professor) que adicionou este email."
    )
    date_added = models.DateTimeField(
        auto_now_add=True,
        verbose_name="Data de Adição"
    )
    status = models.CharField(
        max_length=10,
        choices=STATUS_CHOICES,
        default='Pending',
        verbose_name="Estado",
        help_text="Estado da pré-aprovação (Pendente ou Reivindicado após login do aluno)."
    )
    claimed_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL, # Mantém o registo se o aluno for apagado
        null=True,
        blank=True,
        related_name='claimed_preapprovals',
        verbose_name="Reivindicado Por",
        help_text="O utilizador Aluno que corresponde a este email após o login."
    )
    date_claimed = models.DateTimeField(
        null=True,
        blank=True,
        verbose_name="Data de Reivindicação"
    )

    class Meta:
        verbose_name = "Aluno Pré-Aprovado"
        verbose_name_plural = "Alunos Pré-Aprovados"
        ordering = ['class_instance', 'email']

    def __str__(self):
        # Need to handle potential error if class_instance isn't loaded yet in some contexts
        try:
            class_name = self.class_instance.name
        except AttributeError:
            class_name = "[Turma não carregada]"
        return f"{self.email} - Turma: {class_name} ({self.get_status_display()})"
