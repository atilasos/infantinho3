"""Shared helpers for diary permissions."""
from __future__ import annotations

from classes.models import Class


__all__ = [
    'can_access_diary',
    'can_moderate_diary',
]


def can_moderate_diary(user, turma: Class) -> bool:
    """Return True if the user can start/archive sessions for the given class."""
    if not user or not getattr(user, 'is_authenticated', False):
        return False
    if getattr(user, 'is_superuser', False):
        return True
    role = getattr(user, 'role', None)
    if role == 'admin':
        return True
    if role == 'professor':
        classes_taught = getattr(user, 'classes_taught', Class.objects.none())
        return turma in classes_taught.all()
    return False


def can_access_diary(user, turma: Class) -> bool:
    """Return True if the user can view/add entries to the diary."""
    if not user or not getattr(user, 'is_authenticated', False):
        return False
    if getattr(user, 'is_superuser', False):
        return True
    role = getattr(user, 'role', None)
    if role == 'admin':
        return True
    if role == 'professor':
        classes_taught = getattr(user, 'classes_taught', Class.objects.none())
        if turma in classes_taught.all():
            return True
    if role == 'aluno':
        classes_attended = getattr(user, 'classes_attended', Class.objects.none())
        if turma in classes_attended.all():
            return True
    if role == 'encarregado':
        # TODO: allow guardians once guardian-class relationship is formalised
        return False
    return False
