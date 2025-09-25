"""API endpoints for checklist templates, statuses and marks."""
from rest_framework import viewsets, mixins
from rest_framework.exceptions import PermissionDenied

from django.utils.translation import gettext_lazy as _

from checklists.models import ChecklistTemplate, ChecklistStatus, ChecklistMark
from core.permissions import IsAuthenticatedAndActive
from .serializers import (
    ChecklistTemplateSerializer,
    ChecklistStatusSerializer,
    ChecklistMarkSerializer,
)


class ChecklistTemplateViewSet(viewsets.ModelViewSet):
    serializer_class = ChecklistTemplateSerializer
    permission_classes = [IsAuthenticatedAndActive]
    http_method_names = ['get', 'post', 'put', 'patch', 'delete', 'head', 'options']

    def get_queryset(self):
        user = self.request.user
        base_qs = ChecklistTemplate.objects.prefetch_related('items').all()
        role = getattr(user, 'role', None)

        if user.is_superuser or role == 'admin':
            return base_qs
        if role == 'professor':
            return base_qs.filter(classes__teachers=user).distinct()
        if role == 'aluno':
            return base_qs.filter(classes__students=user).distinct()
        if role == 'encarregado':
            return base_qs.filter(
                classes__students__encarregados_relations__encarregado=user
            ).distinct()
        return base_qs.none()

    def perform_create(self, serializer):
        user = self.request.user
        if not self._can_manage_templates(user):
            raise PermissionDenied(_('Apenas professores ou administradores podem criar modelos.'))
        serializer.save(created_by=user)

    def perform_update(self, serializer):
        user = self.request.user
        if not self._can_manage_templates(user):
            raise PermissionDenied(_('Apenas professores ou administradores podem atualizar modelos.'))
        serializer.save()

    def perform_destroy(self, instance):
        user = self.request.user
        if not self._can_manage_templates(user):
            raise PermissionDenied(_('Apenas professores ou administradores podem remover modelos.'))
        instance.delete()

    @staticmethod
    def _can_manage_templates(user):
        role = getattr(user, 'role', None)
        return bool(user.is_superuser or role in {'professor', 'admin'})


class ChecklistStatusViewSet(viewsets.ModelViewSet):
    serializer_class = ChecklistStatusSerializer
    permission_classes = [IsAuthenticatedAndActive]
    http_method_names = ['get', 'post', 'patch', 'head', 'options']

    def get_queryset(self):
        user = self.request.user
        role = getattr(user, 'role', None)
        base_qs = ChecklistStatus.objects.select_related(
            'template', 'student', 'student_class'
        ).prefetch_related('template__items', 'marks__item').order_by('-updated_at')

        if user.is_superuser or role == 'admin':
            return base_qs
        if role == 'professor':
            return base_qs.filter(student_class__teachers=user)
        if role == 'aluno':
            return base_qs.filter(student=user)
        if role == 'encarregado':
            return base_qs.filter(student__encarregados_relations__encarregado=user)
        return base_qs.none()

    def perform_create(self, serializer):
        serializer.save()

    def perform_update(self, serializer):
        user = self.request.user
        instance = serializer.instance
        role = getattr(user, 'role', None)

        if role == 'aluno' and instance.student_id != user.id:
            raise PermissionDenied(_('Aluno não pode alterar LV de outro aluno.'))
        if role == 'professor' and not instance.student_class.teachers.filter(id=user.id).exists() and not (user.is_superuser or role == 'admin'):
            raise PermissionDenied(_('Professor não associado à turma.'))

        serializer.save()


class ChecklistMarkViewSet(mixins.UpdateModelMixin,
                           mixins.RetrieveModelMixin,
                           mixins.ListModelMixin,
                           viewsets.GenericViewSet):
    serializer_class = ChecklistMarkSerializer
    permission_classes = [IsAuthenticatedAndActive]
    http_method_names = ['get', 'patch', 'head', 'options']

    def get_queryset(self):
        user = self.request.user
        role = getattr(user, 'role', None)
        base_qs = ChecklistMark.objects.select_related(
            'status_record', 'status_record__student', 'status_record__student_class', 'item'
        ).order_by('item__order')

        if user.is_superuser or role == 'admin':
            return base_qs
        if role == 'professor':
            return base_qs.filter(status_record__student_class__teachers=user)
        if role == 'aluno':
            return base_qs.filter(status_record__student=user)
        if role == 'encarregado':
            return base_qs.filter(
                status_record__student__encarregados_relations__encarregado=user,
                status_record__student_class__students__encarregados_relations__encarregado=user,
                mark_status__in=['COMPLETED', 'VALIDATED'],
            )
        return base_qs.none()

    def perform_update(self, serializer):
        user = self.request.user
        mark = self.get_object()
        role = getattr(user, 'role', None)

        if role == 'aluno' and mark.status_record.student_id != user.id:
            raise PermissionDenied('Cannot update marks outside your own checklist.')

        if role == 'professor' and not mark.status_record.student_class.teachers.filter(id=user.id).exists():
            raise PermissionDenied('Teacher must belong to the class to update marks.')

        if role not in {'aluno', 'professor'} and not user.is_superuser and role != 'admin':
            raise PermissionDenied('Role not permitted to update checklist marks.')

        serializer.save()
