from django.db import models
from django.conf import settings
from django.utils.translation import gettext_lazy as _
from classes.models import Class


class IndividualPlan(models.Model):
    class PlanStatus(models.TextChoices):
        DRAFT = 'draft', _('Rascunho')
        SUBMITTED = 'submitted', _('Submetido')
        APPROVED = 'approved', _('Aprovado')
        CONCLUDED = 'concluded', _('Concluído')
        EVALUATED = 'evaluated', _('Avaliado')

    student = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='individual_plans',
        verbose_name=_('aluno')
    )
    student_class = models.ForeignKey(
        Class,
        on_delete=models.CASCADE,
        related_name='individual_plans',
        verbose_name=_('turma')
    )
    period_label = models.CharField(
        _('período'),
        max_length=100,
        help_text=_('Identificador do período (ex.: "Semana 5 - Out 2025").')
    )
    start_date = models.DateField(_('data de início'), null=True, blank=True)
    end_date = models.DateField(_('data de fim'), null=True, blank=True)
    status = models.CharField(
        _('estado'),
        max_length=20,
        choices=PlanStatus.choices,
        default=PlanStatus.DRAFT
    )
    general_objectives = models.TextField(_('objetivos gerais'), blank=True)
    self_evaluation = models.TextField(_('autoavaliação do aluno'), blank=True)
    teacher_evaluation = models.TextField(_('avaliação do professor'), blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = _('Plano Individual de Trabalho')
        verbose_name_plural = _('Planos Individuais de Trabalho')
        ordering = ['-start_date', '-created_at']
        constraints = [
            models.UniqueConstraint(
                fields=['student', 'student_class', 'period_label'],
                name='unique_plan_per_period_per_class'
            )
        ]

    def __str__(self) -> str:
        return f"{self.student} · {self.student_class} · {self.period_label} ({self.get_status_display()})"


class PlanTask(models.Model):
    class TaskState(models.TextChoices):
        PENDING = 'pending', _('Pendente')
        IN_PROGRESS = 'in_progress', _('Em andamento')
        DONE = 'done', _('Feito')
        VALIDATED = 'validated', _('Validado')

    plan = models.ForeignKey(
        IndividualPlan,
        on_delete=models.CASCADE,
        related_name='tasks',
        verbose_name=_('plano')
    )
    description = models.CharField(_('descrição'), max_length=255)
    subject = models.CharField(_('disciplina/área'), max_length=100, blank=True)
    state = models.CharField(
        _('estado'),
        max_length=20,
        choices=TaskState.choices,
        default=TaskState.PENDING
    )
    evidence_link = models.URLField(_('ligação para evidência'), blank=True)
    teacher_feedback = models.TextField(_('feedback do professor'), blank=True)
    order = models.PositiveIntegerField(_('ordem'), default=0)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = _('Tarefa do Plano')
        verbose_name_plural = _('Tarefas do Plano')
        ordering = ['order', 'id']

    def __str__(self) -> str:
        return f"[{self.plan.period_label}] {self.description} ({self.get_state_display()})"


# Create your models here.
