"""Permission helpers for PIT resources."""
from rest_framework.permissions import BasePermission, SAFE_METHODS

from pit.models import IndividualPlan


class IsPlanParticipant(BasePermission):
    """Permite acesso a participantes do plano (aluno, professor, encarregado, admin)."""

    def has_permission(self, request, view):
        user = request.user
        if not user or not user.is_authenticated:
            return False
        role = getattr(user, 'role', None)
        if user.is_superuser or role in {'admin', 'professor', 'aluno', 'encarregado'}:
            return True
        return False

    def has_object_permission(self, request, view, obj: IndividualPlan):
        user = request.user
        role = getattr(user, 'role', None)
        if user.is_superuser or role == 'admin':
            return True
        if role == 'professor' and obj.student_class.teachers.filter(id=user.id).exists():
            return True
        if role == 'aluno' and obj.student_id == user.id:
            return True
        if role == 'encarregado' and request.method in SAFE_METHODS:
            return obj.student.encarregados_relations.filter(encarregado=user).exists()
        return False


class IsPlanTaskParticipant(BasePermission):
    """Permite acesso a tarefas de um plano apenas a participantes."""

    def has_permission(self, request, view):
        user = request.user
        if not user or not user.is_authenticated:
            return False
        role = getattr(user, 'role', None)
        if user.is_superuser or role in {'admin', 'professor', 'aluno'}:
            return True
        return False

    def has_object_permission(self, request, view, obj):
        plan = obj.plan
        user = request.user
        role = getattr(user, 'role', None)
        if user.is_superuser or role == 'admin':
            return True
        if role == 'professor' and plan.student_class.teachers.filter(id=user.id).exists():
            return True
        if role == 'aluno' and plan.student_id == user.id:
            return True
        return False
