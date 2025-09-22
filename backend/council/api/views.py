"""API endpoints for council decisions and student proposals."""
from django.utils.translation import gettext_lazy as _
from rest_framework import viewsets, mixins, status
from rest_framework.decorators import action
from rest_framework.exceptions import PermissionDenied, ValidationError
from rest_framework.response import Response

from core.permissions import IsAuthenticatedAndActive
from council.models import CouncilDecision, StudentProposal
from .serializers import CouncilDecisionSerializer, StudentProposalSerializer


def _role(user):
    return getattr(user, 'role', None)


def _is_teacher(user, turma):
    return hasattr(user, 'classes_taught') and turma in user.classes_taught.all()


def _is_student(user, turma):
    return hasattr(user, 'classes_attended') and turma in user.classes_attended.all()


def _is_admin(user):
    return user.is_superuser or _role(user) == 'admin'


class CouncilDecisionViewSet(viewsets.ModelViewSet):
    serializer_class = CouncilDecisionSerializer
    permission_classes = [IsAuthenticatedAndActive]
    filterset_fields = ['student_class_id', 'status', 'category']
    search_fields = ['description']

    def get_queryset(self):
        user = self.request.user
        role = _role(user)
        qs = CouncilDecision.objects.select_related('student_class', 'responsible')
        if user.is_superuser or role == 'admin':
            return qs
        if role == 'professor':
            return qs.filter(student_class__teachers=user)
        if role == 'aluno':
            return qs.filter(student_class__students=user)
        if role == 'encarregado':
            return qs.filter(student_class__students__encarregados_relations__encarregado=user).distinct()
        return qs.none()

    def perform_create(self, serializer):
        class_id = serializer.validated_data.get('student_class_id')
        from classes.models import Class
        turma = Class.objects.get(pk=class_id)
        if not (_is_admin(self.request.user) or _is_teacher(self.request.user, turma)):
            raise PermissionDenied(_('Apenas professores podem registar decisões.'))
        serializer.save()

    def perform_update(self, serializer):
        decision = self.get_object()
        if not (_is_admin(self.request.user) or _is_teacher(self.request.user, decision.student_class)):
            raise PermissionDenied(_('Sem permissão para atualizar esta decisão.'))
        serializer.save()

    def perform_destroy(self, instance):
        if not (_is_admin(self.request.user) or _is_teacher(self.request.user, instance.student_class)):
            raise PermissionDenied(_('Sem permissão para remover esta decisão.'))
        instance.delete()

    @action(detail=True, methods=['post'], url_path='status')
    def update_status(self, request, pk=None):
        decision = self.get_object()
        if not (_is_admin(request.user) or _is_teacher(request.user, decision.student_class)):
            raise PermissionDenied(_('Sem permissão para atualizar o estado.'))
        new_status = request.data.get('status')
        if new_status not in dict(CouncilDecision.Status.choices):
            raise ValidationError({'status': _('Estado inválido.')})
        decision.status = new_status
        decision.save(update_fields=['status', 'updated_at'])
        return Response(self.get_serializer(decision).data)


class StudentProposalViewSet(mixins.CreateModelMixin,
                             mixins.RetrieveModelMixin,
                             mixins.UpdateModelMixin,
                             mixins.DestroyModelMixin,
                             mixins.ListModelMixin,
                             viewsets.GenericViewSet):
    serializer_class = StudentProposalSerializer
    permission_classes = [IsAuthenticatedAndActive]
    filterset_fields = ['student_class_id', 'status']
    search_fields = ['text']

    def get_queryset(self):
        user = self.request.user
        role = _role(user)
        qs = StudentProposal.objects.select_related('student_class', 'author')
        if user.is_superuser or role == 'admin':
            return qs
        if role == 'professor':
            return qs.filter(student_class__teachers=user)
        if role == 'aluno':
            return qs.filter(author=user)
        return qs.none()

    def perform_create(self, serializer):
        class_id = serializer.validated_data.get('student_class_id')
        from classes.models import Class
        turma = Class.objects.get(pk=class_id)
        if not _is_student(self.request.user, turma):
            raise PermissionDenied(_('Só alunos da turma podem propor temas.'))
        serializer.save()

    def perform_update(self, serializer):
        proposal = self.get_object()
        user = self.request.user
        if user == proposal.author:
            serializer.save()
            return
        if not (_is_admin(user) or _is_teacher(user, proposal.student_class)):
            raise PermissionDenied(_('Sem permissão para atualizar esta proposta.'))
        serializer.save()

    def perform_destroy(self, instance):
        user = self.request.user
        if user != instance.author and not (_is_admin(user) or _is_teacher(user, instance.student_class)):
            raise PermissionDenied(_('Sem permissão para remover esta proposta.'))
        instance.delete()

    @action(detail=True, methods=['post'], url_path='status')
    def set_status(self, request, pk=None):
        proposal = self.get_object()
        if not (_is_admin(request.user) or _is_teacher(request.user, proposal.student_class)):
            raise PermissionDenied(_('Apenas professores podem alterar o estado.'))
        new_status = request.data.get('status')
        if new_status not in dict(StudentProposal.ProposalStatus.choices):
            raise ValidationError({'status': _('Estado inválido.')})
        proposal.status = new_status
        proposal.save(update_fields=['status'])
        return Response(self.get_serializer(proposal).data)
