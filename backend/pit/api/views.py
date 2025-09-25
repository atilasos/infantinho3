"""API endpoints supporting the PIT workflows."""
from django.utils.translation import gettext_lazy as _
from datetime import date

from django.core.exceptions import ValidationError as DjangoValidationError
from django.http import HttpResponse
from django.utils.dateparse import parse_date
from django.utils.text import slugify

from rest_framework import viewsets, mixins, status
from rest_framework.decorators import action
from rest_framework.exceptions import PermissionDenied, ValidationError
from rest_framework.response import Response

from core.permissions import IsAuthenticatedAndActive
from classes.models import Class
from pit.models import IndividualPlan, PlanTask, PlanLogEntry
from pit.views import (
    _notify_teachers_submission,
    _notify_student_status,
    _notify_teachers_self_evaluation,
    _notify_student_teacher_eval,
)
from pit.services import generate_weekly_plan, render_plan_pdf, log_plan_event
from pit.api.permissions import IsPlanParticipant, IsPlanTaskParticipant
from django.contrib.auth import get_user_model
from .serializers import IndividualPlanSerializer, PlanTaskSerializer


def _user_role(user):
    return getattr(user, 'role', None)

User = get_user_model()


class IndividualPlanViewSet(viewsets.ModelViewSet):
    serializer_class = IndividualPlanSerializer
    permission_classes = [IsAuthenticatedAndActive, IsPlanParticipant]
    filterset_fields = ['student_class_id', 'status']
    search_fields = ['period_label']

    def get_queryset(self):
        user = self.request.user
        role = _user_role(user)
        qs = (
            IndividualPlan.objects.select_related('student', 'student_class', 'template', 'origin_plan')
            .prefetch_related('tasks', 'suggestions')
        )

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
        log_plan_event(
            plan=plan,
            action=PlanLogEntry.Action.UPDATED,
            actor=self.request.user,
            message='Plano atualizado pelo aluno/professor.',
            payload={'updated_fields': list(serializer.validated_data.keys())},
        )

    @action(detail=False, methods=['post'], url_path='generate')
    def generate(self, request):
        class_id = request.data.get('student_class_id')
        if not class_id:
            raise ValidationError({'student_class_id': 'Campo obrigatório.'})
        try:
            turma = Class.objects.get(pk=class_id)
        except Class.DoesNotExist as exc:
            raise ValidationError({'student_class_id': 'Turma inexistente.'}) from exc

        role = _user_role(request.user)
        if role == 'aluno':
            if not turma.students.filter(id=request.user.id).exists():
                raise PermissionDenied(_('Aluno não pertence à turma indicada.'))
            student = request.user
        elif role in {'professor', 'admin'} or request.user.is_superuser:
            if role == 'professor' and not turma.teachers.filter(id=request.user.id).exists():
                raise PermissionDenied(_('Professor não associado à turma.'))
            student_id = request.data.get('student_id')
            if not student_id:
                raise ValidationError({'student_id': 'Campo obrigatório para professores.'})
            try:
                student = User.objects.get(id=student_id)
            except User.DoesNotExist as exc:
                raise ValidationError({'student_id': 'Aluno não encontrado.'}) from exc
            if not student.classes_attended.filter(id=turma.id).exists():
                raise ValidationError({'student_id': 'Aluno não pertence à turma.'})
        else:
            raise PermissionDenied(_('Perfil sem permissão para gerar PIT.'))

        target_date_raw = request.data.get('target_date')
        target_date: date | None = None
        if target_date_raw:
            target_date = parse_date(str(target_date_raw))
            if target_date is None:
                raise ValidationError({'target_date': 'Data inválida. Use o formato YYYY-MM-DD.'})

        try:
            result = generate_weekly_plan(student=student, student_class=turma, target_date=target_date)
        except DjangoValidationError as exc:
            detail = exc.message_dict if hasattr(exc, 'message_dict') and exc.message_dict else exc.messages
            raise ValidationError(detail)

        serializer = self.get_serializer(result.plan)
        return Response(serializer.data, status=status.HTTP_201_CREATED)

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
        log_plan_event(
            plan=plan,
            action=PlanLogEntry.Action.STATUS_CHANGE,
            actor=request.user,
            message='PIT submetido pelo aluno.',
            payload={'from': IndividualPlan.PlanStatus.DRAFT, 'to': plan.status},
        )
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
            log_plan_event(
                plan=plan,
                action=PlanLogEntry.Action.STATUS_CHANGE,
                actor=user,
                message='PIT aprovado pelo professor.',
                payload={'from': IndividualPlan.PlanStatus.SUBMITTED, 'to': plan.status},
            )
        elif decision == 'return':
            plan.status = IndividualPlan.PlanStatus.DRAFT
            plan.save(update_fields=['status', 'updated_at'])
            _notify_student_status(request, plan, approved=False)
            log_plan_event(
                plan=plan,
                action=PlanLogEntry.Action.STATUS_CHANGE,
                actor=user,
                message='PIT devolvido para ajustes.',
                payload={'from': IndividualPlan.PlanStatus.SUBMITTED, 'to': plan.status},
            )
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
        log_plan_event(
            plan=plan,
            action=PlanLogEntry.Action.STATUS_CHANGE,
            actor=request.user,
            message='Autoavaliação registada pelo aluno.',
            payload={'status': plan.status},
        )
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
        log_plan_event(
            plan=plan,
            action=PlanLogEntry.Action.STATUS_CHANGE,
            actor=user,
            message='Professor registou devolução e avaliou o PIT.',
            payload={'status': plan.status},
        )
        return Response(self.get_serializer(plan).data)

    @action(detail=True, methods=['get'], url_path='export-pdf')
    def export_pdf(self, request, pk=None):
        plan = self.get_object()
        pdf_bytes = render_plan_pdf(plan)
        student_part = slugify((plan.student.get_full_name() or plan.student.username) if plan.student_id else 'aluno')
        class_part = slugify(plan.student_class.name) if plan.student_class_id and plan.student_class else 'turma'
        period_part = slugify(plan.period_label)
        filename = f"pit-{student_part}-{class_part}-{period_part}.pdf"
        response = HttpResponse(pdf_bytes, content_type='application/pdf')
        response['Content-Disposition'] = f'attachment; filename="{filename}"'
        return response


class PlanTaskViewSet(mixins.CreateModelMixin,
                      mixins.RetrieveModelMixin,
                      mixins.UpdateModelMixin,
                      mixins.DestroyModelMixin,
                      mixins.ListModelMixin,
                      viewsets.GenericViewSet):
    serializer_class = PlanTaskSerializer
    permission_classes = [IsAuthenticatedAndActive, IsPlanTaskParticipant]

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
        task = serializer.save(plan=plan)
        log_plan_event(
            plan=plan,
            action=PlanLogEntry.Action.UPDATED,
            actor=self.request.user,
            message='Tarefa adicionada ao plano.',
            payload={'task_id': task.id, 'description': task.description},
        )

    def perform_update(self, serializer):
        task = self.get_object()
        self._assert_can_edit(task)
        before = {field: getattr(task, field) for field in serializer.validated_data.keys()}
        serializer.save()
        after = {field: getattr(serializer.instance, field) for field in serializer.validated_data.keys()}
        changes = {
            field: {'from': before.get(field), 'to': after.get(field)}
            for field in serializer.validated_data.keys()
            if before.get(field) != after.get(field)
        }
        log_plan_event(
            plan=task.plan,
            action=PlanLogEntry.Action.UPDATED,
            actor=self.request.user,
            message='Tarefa atualizada.',
            payload={'task_id': task.id, 'changes': changes},
        )

    def perform_destroy(self, instance):
        self._assert_can_edit(instance)
        plan = instance.plan
        payload = {'task_id': instance.id, 'description': instance.description}
        instance.delete()
        log_plan_event(
            plan=plan,
            action=PlanLogEntry.Action.UPDATED,
            actor=self.request.user,
            message='Tarefa removida do plano.',
            payload=payload,
        )
