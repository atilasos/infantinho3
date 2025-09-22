"""API endpoints for cooperative projects."""
from django.utils.translation import gettext_lazy as _
from rest_framework import viewsets, mixins, status
from rest_framework.decorators import action
from rest_framework.exceptions import PermissionDenied, ValidationError
from rest_framework.response import Response

from core.permissions import IsAuthenticatedAndActive
from projects.models import Project, ProjectTask
from .serializers import ProjectSerializer, ProjectTaskSerializer


def _role(user):
    return getattr(user, 'role', None)


def _is_teacher(user, turma):
    return hasattr(user, 'classes_taught') and turma in user.classes_taught.all()


def _is_student(user, turma):
    return hasattr(user, 'classes_attended') and turma in user.classes_attended.all()


def _is_admin(user):
    return user.is_superuser or _role(user) == 'admin'


def _can_view_project(user, project):
    turma = project.student_class
    if not user.is_authenticated:
        return False
    if _is_admin(user) or _is_teacher(user, turma):
        return True
    if _is_student(user, turma):
        return True
    return project.members.filter(id=user.id).exists()


def _can_edit_project(user, project):
    if not user.is_authenticated:
        return False
    turma = project.student_class
    if _is_admin(user) or _is_teacher(user, turma):
        return True
    return project.members.filter(id=user.id).exists()


class ProjectViewSet(viewsets.ModelViewSet):
    serializer_class = ProjectSerializer
    permission_classes = [IsAuthenticatedAndActive]
    filterset_fields = ['student_class_id', 'state']
    search_fields = ['title', 'description']

    def get_queryset(self):
        user = self.request.user
        role = _role(user)
        qs = Project.objects.select_related('student_class').prefetch_related('members', 'tasks')
        if user.is_superuser or role == 'admin':
            return qs
        if role == 'professor':
            return qs.filter(student_class__teachers=user)
        if role == 'aluno':
            return qs.filter(student_class__students=user)
        if role == 'encarregado':
            return qs.filter(student_class__students__encarregados_relations__encarregado=user).distinct()
        return qs.filter(members=user)

    def perform_create(self, serializer):
        class_id = serializer.validated_data.get('student_class_id')
        user = self.request.user
        from classes.models import Class
        turma = Class.objects.get(pk=class_id)
        if not (_is_admin(user) or _is_teacher(user, turma) or _is_student(user, turma)):
            raise PermissionDenied(_('Apenas membros da turma podem criar projetos.'))
        serializer.context['request'] = self.request
        serializer.save()

    def perform_update(self, serializer):
        project = self.get_object()
        if not _can_edit_project(self.request.user, project):
            raise PermissionDenied(_('Sem permissão para editar este projeto.'))
        serializer.context['request'] = self.request
        serializer.save()

    def perform_destroy(self, instance):
        if not _can_edit_project(self.request.user, instance):
            raise PermissionDenied(_('Sem permissão para remover este projeto.'))
        instance.delete()

    @action(detail=True, methods=['post'], url_path='state')
    def change_state(self, request, pk=None):
        project = self.get_object()
        if not _can_edit_project(request.user, project):
            raise PermissionDenied(_('Sem permissão para alterar o estado.'))
        new_state = request.data.get('state')
        if new_state not in dict(Project.ProjectState.choices):
            raise ValidationError({'state': _('Estado inválido.')})
        project.state = new_state
        project.save(update_fields=['state', 'updated_at'])
        return Response(self.get_serializer(project).data)

    @action(detail=True, methods=['post'], url_path='add-member')
    def add_member(self, request, pk=None):
        project = self.get_object()
        if not _can_edit_project(request.user, project):
            raise PermissionDenied(_('Sem permissão para gerir membros.'))
        member_id = request.data.get('user_id')
        if not member_id:
            raise ValidationError({'user_id': _('É necessário indicar o utilizador.')})
        from django.contrib.auth import get_user_model
        User = get_user_model()
        try:
            member = User.objects.get(pk=member_id)
        except User.DoesNotExist as exc:
            raise ValidationError({'user_id': _('Utilizador inválido.')}) from exc
        turma = project.student_class
        if not (_is_admin(member) or _is_teacher(member, turma) or _is_student(member, turma)):
            raise ValidationError({'user_id': _('Utilizador não pertence à turma.')})
        project.members.add(member)
        return Response(self.get_serializer(project).data, status=status.HTTP_200_OK)

    @action(detail=True, methods=['post'], url_path='remove-member')
    def remove_member(self, request, pk=None):
        project = self.get_object()
        if not _can_edit_project(request.user, project):
            raise PermissionDenied(_('Sem permissão para gerir membros.'))
        member_id = request.data.get('user_id')
        if not member_id:
            raise ValidationError({'user_id': _('É necessário indicar o utilizador.')})
        project.members.remove(member_id)
        return Response(self.get_serializer(project).data, status=status.HTTP_200_OK)


class ProjectTaskViewSet(mixins.CreateModelMixin,
                         mixins.RetrieveModelMixin,
                         mixins.UpdateModelMixin,
                         mixins.DestroyModelMixin,
                         mixins.ListModelMixin,
                         viewsets.GenericViewSet):
    serializer_class = ProjectTaskSerializer
    permission_classes = [IsAuthenticatedAndActive]

    def get_queryset(self):
        user = self.request.user
        role = _role(user)
        qs = ProjectTask.objects.select_related('project', 'project__student_class').prefetch_related('project__members')
        if user.is_superuser or role == 'admin':
            return qs
        if role == 'professor':
            return qs.filter(project__student_class__teachers=user)
        if role == 'aluno':
            return qs.filter(project__members=user)
        return qs.none()

    def _assert_can_edit(self, project):
        if not _can_edit_project(self.request.user, project):
            raise PermissionDenied(_('Sem permissão para editar tarefas.'))

    def create(self, request, *args, **kwargs):
        project_id = request.data.get('project')
        if not project_id:
            raise ValidationError({'project': _('É necessário indicar o projeto.')})
        try:
            project = Project.objects.select_related('student_class').prefetch_related('members').get(pk=project_id)
        except Project.DoesNotExist as exc:
            raise ValidationError({'project': _('Projeto inválido.')}) from exc
        self._assert_can_edit(project)
        serializer = self.get_serializer(data=request.data, context={**self.get_serializer_context(), 'project': project})
        serializer.is_valid(raise_exception=True)
        serializer.save(project=project)
        headers = self.get_success_headers(serializer.data)
        return Response(serializer.data, status=status.HTTP_201_CREATED, headers=headers)

    def update(self, request, *args, **kwargs):
        partial = kwargs.pop('partial', False)
        instance = self.get_object()
        self._assert_can_edit(instance.project)
        serializer = self.get_serializer(
            instance,
            data=request.data,
            partial=partial,
            context={**self.get_serializer_context(), 'project': instance.project},
        )
        serializer.is_valid(raise_exception=True)
        self.perform_update(serializer)
        return Response(serializer.data)

    def destroy(self, request, *args, **kwargs):
        instance = self.get_object()
        self._assert_can_edit(instance.project)
        self.perform_destroy(instance)
        return Response(status=status.HTTP_204_NO_CONTENT)
