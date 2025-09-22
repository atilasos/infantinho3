"""API endpoints supporting the PIT workflows."""
from django.utils.translation import gettext_lazy as _
from rest_framework import viewsets, mixins, status
from rest_framework.decorators import action
from rest_framework.exceptions import PermissionDenied, ValidationError
from rest_framework.response import Response

from core.permissions import IsAuthenticatedAndActive
from pit.models import IndividualPlan, PlanTask
from pit.views import (
    _notify_teachers_submission,
    _notify_student_status,
    _notify_teachers_self_evaluation,
    _notify_student_teacher_eval,
)
from .serializers import IndividualPlanSerializer, PlanTaskSerializer


def _user_role(user):
    return getattr(user, 'role', None)


class IndividualPlanViewSet(viewsets.ModelViewSet):
    serializer_class = IndividualPlanSerializer
    permission_classes = [IsAuthenticatedAndActive]
    filterset_fields = ['student_class_id', 'status']
    search_fields = ['period_label']

    def get_queryset(self):
        user = self.request.user
        role = _user_role(user)
        qs = IndividualPlan.objects.select_related('student', 'student_class').prefetch_related('tasks')

        if user.is_superuser or role == 'admin':
            return qs
        if role == 'professor':
            return qs.filter(student_class__teachers=user)
        if role == 'aluno':
            return qs.filter(student=user)
        if role == 'encarregado':
            return qs.filter(student__encarregados_relations__encarregado=user)
        return qs.none()

    def perform_update(self, serializer):
        plan = self.get_object()
        user = self.request.user
        role = _user_role(user)

        if role == 'aluno' and plan.student_id != user.id:
            raise PermissionDenied(_('Não pode editar PITs de outros alunos.'))
        if role == 'aluno' and plan.status not in {IndividualPlan.PlanStatus.DRAFT, IndividualPlan.PlanStatus.SUBMITTED}:
            raise PermissionDenied(_('Só é possível editar PITs em rascunho ou submetidos.'))
        if role == 'professor' and not plan.student_class.teachers.filter(id=user.id).exists():
            raise PermissionDenied(_('Professor não associado à turma.'))

        serializer.save()

    @action(detail=True, methods=['post'])
    def submit(self, request, pk=None):
        plan = self.get_object()
        if request.user != plan.student:
            raise PermissionDenied(_('Só o aluno autor pode submeter o PIT.'))
        if plan.status != IndividualPlan.PlanStatus.DRAFT:
            raise ValidationError(_('O PIT já foi submetido.'))
        plan.status = IndividualPlan.PlanStatus.SUBMITTED
        plan.save(update_fields=['status', 'updated_at'])
        _notify_teachers_submission(request, plan)
        return Response(self.get_serializer(plan).data)

    @action(detail=True, methods=['post'], url_path='teacher-decision')
    def teacher_decision(self, request, pk=None):
        plan = self.get_object()
        user = request.user
        if _user_role(user) != 'professor' or not plan.student_class.teachers.filter(id=user.id).exists():
            raise PermissionDenied(_('Apenas professores da turma podem decidir o PIT.'))

        decision = request.data.get('decision')
        if decision == 'approve':
            if plan.status != IndividualPlan.PlanStatus.SUBMITTED:
                raise ValidationError(_('Só é possível aprovar PITs submetidos.'))
            plan.status = IndividualPlan.PlanStatus.APPROVED
            plan.save(update_fields=['status', 'updated_at'])
            _notify_student_status(request, plan, approved=True)
        elif decision == 'return':
            plan.status = IndividualPlan.PlanStatus.DRAFT
            plan.save(update_fields=['status', 'updated_at'])
            _notify_student_status(request, plan, approved=False)
        else:
            raise ValidationError(_('Decisão inválida. Use "approve" ou "return".'))
        return Response(self.get_serializer(plan).data)

    @action(detail=True, methods=['post'], url_path='self-evaluation')
    def self_evaluation(self, request, pk=None):
        plan = self.get_object()
        if request.user != plan.student:
            raise PermissionDenied(_('Só o aluno pode registar a autoavaliação.'))
        if plan.status in {IndividualPlan.PlanStatus.DRAFT, IndividualPlan.PlanStatus.SUBMITTED}:
            raise ValidationError(_('A autoavaliação só fica disponível após a aprovação do PIT.'))
        self_eval = request.data.get('self_evaluation', '')
        plan.self_evaluation = self_eval
        if plan.status != IndividualPlan.PlanStatus.EVALUATED:
            plan.status = IndividualPlan.PlanStatus.CONCLUDED
        plan.save(update_fields=['self_evaluation', 'status', 'updated_at'])
        _notify_teachers_self_evaluation(request, plan)
        return Response(self.get_serializer(plan).data)

    @action(detail=True, methods=['post'], url_path='teacher-evaluation')
    def teacher_evaluation(self, request, pk=None):
        plan = self.get_object()
        user = request.user
        if _user_role(user) != 'professor' or not plan.student_class.teachers.filter(id=user.id).exists():
            raise PermissionDenied(_('Apenas professores da turma podem avaliar o PIT.'))
        if plan.status in {IndividualPlan.PlanStatus.DRAFT, IndividualPlan.PlanStatus.SUBMITTED}:
            raise ValidationError(_('Aguarde o aluno concluir ou autoavaliar o PIT antes da avaliação.'))
        evaluation = request.data.get('teacher_evaluation', '')
        plan.teacher_evaluation = evaluation
        plan.status = IndividualPlan.PlanStatus.EVALUATED
        plan.save(update_fields=['teacher_evaluation', 'status', 'updated_at'])
        _notify_student_teacher_eval(request, plan)
        return Response(self.get_serializer(plan).data)


class PlanTaskViewSet(mixins.CreateModelMixin,
                      mixins.RetrieveModelMixin,
                      mixins.UpdateModelMixin,
                      mixins.DestroyModelMixin,
                      mixins.ListModelMixin,
                      viewsets.GenericViewSet):
    serializer_class = PlanTaskSerializer
    permission_classes = [IsAuthenticatedAndActive]

    def get_queryset(self):
        user = self.request.user
        role = _user_role(user)
        qs = PlanTask.objects.select_related('plan', 'plan__student', 'plan__student_class')

        if user.is_superuser or role == 'admin':
            return qs
        if role == 'professor':
            return qs.filter(plan__student_class__teachers=user)
        if role == 'aluno':
            return qs.filter(plan__student=user)
        return qs.none()

    def _assert_can_edit(self, task):
        user = self.request.user
        role = _user_role(user)
        if role == 'aluno' and task.plan.student_id != user.id:
            raise PermissionDenied(_('Não pode alterar tarefas de outro aluno.'))
        if role == 'professor' and not task.plan.student_class.teachers.filter(id=user.id).exists():
            raise PermissionDenied(_('Professor não associado à turma.'))
        if role not in {'aluno', 'professor'} and not self.request.user.is_superuser and role != 'admin':
            raise PermissionDenied(_('Perfil sem permissão para gerir tarefas.'))

    def _assert_can_access_plan(self, plan):
        user = self.request.user
        role = _user_role(user)
        if user.is_superuser or role == 'admin':
            return
        if role == 'aluno' and plan.student_id != user.id:
            raise PermissionDenied(_('Não pode agir sobre planos de outros alunos.'))
        if role == 'professor' and not plan.student_class.teachers.filter(id=user.id).exists():
            raise PermissionDenied(_('Professor não associado à turma.'))
        if role not in {'aluno', 'professor'}:
            raise PermissionDenied(_('Perfil sem permissão para gerir tarefas.'))

    def perform_create(self, serializer):
        plan_id = self.request.data.get('plan')
        if not plan_id:
            raise ValidationError({'plan': _('É necessário indicar o plano.')} )
        try:
            plan = IndividualPlan.objects.select_related('student', 'student_class').get(pk=plan_id)
        except IndividualPlan.DoesNotExist as exc:
            raise ValidationError({'plan': _('Plano inválido.')}) from exc
        self._assert_can_access_plan(plan)
        serializer.save(plan=plan)

    def perform_update(self, serializer):
        task = self.get_object()
        self._assert_can_edit(task)
        serializer.save()

    def perform_destroy(self, instance):
        self._assert_can_edit(instance)
        instance.delete()
