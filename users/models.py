from django.contrib.auth.models import AbstractUser
from django.db import models
from django.core.exceptions import ValidationError

class User(AbstractUser):
    ROLE_CHOICES = [
        ('aluno', 'Aluno'),
        ('professor', 'Professor'),
        ('admin', 'Administrador'),
        ('encarregado', 'Encarregado de Educação'),
    ]
    role = models.CharField(max_length=20, choices=ROLE_CHOICES, blank=True, null=True, default=None)
    photo = models.ImageField(upload_to='profile_photos/', blank=True, null=True)
    status = models.CharField(max_length=20, default='convidado')

    def clean(self):
        # Garantir que convidados não têm role atribuído
        if self.status == 'convidado' and self.role:
            raise ValidationError('Convidados não podem ter papel atribuído.')

    def is_guest(self):
        return self.status == 'convidado'

    def promote_to_role(self, role):
        if role not in dict(self.ROLE_CHOICES):
            raise ValueError('Papel inválido.')
        self.role = role
        self.status = 'ativo'
        self.save()
