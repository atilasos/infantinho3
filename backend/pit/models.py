from django.db import models
from django.conf import settings
from django.utils.translation import gettext_lazy as _
from classes.models import Class


class PitTemplate(models.Model):
    """Modelo base do PIT, versionado por ciclo/turma."""

    name = models.CharField(_('nome'), max_length=150)
    description = models.TextField(_('descrição'), blank=True)
    cycle_label = models.CharField(
        _('ciclo/ano'), max_length=100, blank=True, help_text=_('Identificador pedagógico do modelo (ex.: 2.º ciclo).')
    )
    version = models.PositiveIntegerField(_('versão'), default=1)
    student_class = models.ForeignKey(
        Class,
        on_delete=models.CASCADE,
        related_name='pit_templates',
        verbose_name=_('turma'),
        null=True,
        blank=True,
        help_text=_('Opcionalmente restringe o modelo a uma turma específica.'),
    )
    is_active = models.BooleanField(_('publicado/ativo'), default=True)
    created_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='created_pit_templates',
        verbose_name=_('autor do modelo'),
    )
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = _('Modelo de PIT')
        verbose_name_plural = _('Modelos de PIT')
        ordering = ['-updated_at', '-created_at']
        constraints = [
            models.UniqueConstraint(
                fields=['student_class', 'version'],
                name='unique_template_version_per_class',
                condition=models.Q(student_class__isnull=False),
            ),
        ]

    def __str__(self) -> str:
        turma = f" — {self.student_class}" if self.student_class else ''
        return f"{self.name} v{self.version}{turma}"


class TemplateSection(models.Model):
    """Secção/área configurada no modelo."""

    template = models.ForeignKey(PitTemplate, on_delete=models.CASCADE, related_name='sections', verbose_name=_('modelo'))
    title = models.CharField(_('título da secção'), max_length=150)
    area_code = models.CharField(_('código da área/disciplina'), max_length=50, blank=True)
    order = models.PositiveIntegerField(_('ordem'), default=0)
    default_description = models.TextField(_('descrição base'), blank=True)

    class Meta:
        verbose_name = _('Secção do Modelo')
        verbose_name_plural = _('Secções do Modelo')
        ordering = ['template', 'order', 'id']

    def __str__(self) -> str:
        return f"{self.template.name} · {self.title}"


class TemplateSuggestion(models.Model):
    """Sugestões pré-carregadas pelo modelo (ex.: transportes do conselho)."""

    template = models.ForeignKey(PitTemplate, on_delete=models.CASCADE, related_name='suggestions', verbose_name=_('modelo'))
    section = models.ForeignKey(
        TemplateSection,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='suggestions',
        verbose_name=_('secção'),
    )
    text = models.CharField(_('texto da sugestão'), max_length=255)
    order = models.PositiveIntegerField(_('ordem'), default=0)
    is_pending = models.BooleanField(_('transportar como pendente'), default=False)

    class Meta:
        verbose_name = _('Sugestão do Modelo')
        verbose_name_plural = _('Sugestões do Modelo')
        ordering = ['template', 'order', 'id']

    def __str__(self) -> str:
        return f"{self.template.name} · {self.text[:40]}"


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
    template = models.ForeignKey(
        PitTemplate,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='plans',
        verbose_name=_('modelo aplicado'),
    )
    template_version = models.PositiveIntegerField(_('versão do modelo'), default=1)
    origin_plan = models.ForeignKey(
        'self',
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='generated_children',
        verbose_name=_('plano de origem'),
    )
    suggestions_imported = models.BooleanField(_('sugestões importadas'), default=False)
    pendings_imported = models.BooleanField(_('pendências importadas'), default=False)
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


class PlanSuggestion(models.Model):
    class SuggestionSource(models.TextChoices):
        TEMPLATE = 'template', _('Modelo')
        COUNCIL = 'council', _('Conselho')
        PENDING = 'pending', _('Pendência')
        MANUAL = 'manual', _('Manual')

    plan = models.ForeignKey(
        IndividualPlan,
        on_delete=models.CASCADE,
        related_name='suggestions',
        verbose_name=_('plano'),
    )
    text = models.CharField(_('texto'), max_length=255)
    origin = models.CharField(
        _('origem'),
        max_length=20,
        choices=SuggestionSource.choices,
        default=SuggestionSource.TEMPLATE,
    )
    order = models.PositiveIntegerField(_('ordem'), default=0)
    is_pending = models.BooleanField(_('marcar como pendente'), default=False)
    template_suggestion = models.ForeignKey(
        TemplateSuggestion,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='plan_suggestions',
        verbose_name=_('sugestão de modelo'),
    )
    from_task = models.ForeignKey(
        'PlanTask',
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='carried_suggestions',
        verbose_name=_('tarefa de origem'),
    )
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = _('Sugestão do Plano')
        verbose_name_plural = _('Sugestões do Plano')
        ordering = ['plan', 'order', 'id']

    def __str__(self) -> str:
        return f"{self.plan.period_label} · {self.text[:40]}"


class PlanSection(models.Model):
    plan = models.ForeignKey(
        IndividualPlan,
        on_delete=models.CASCADE,
        related_name='sections',
        verbose_name=_('plano'),
    )
    title = models.CharField(_('título da secção'), max_length=150)
    area_code = models.CharField(_('código da área/disciplina'), max_length=50, blank=True)
    order = models.PositiveIntegerField(_('ordem'), default=0)
    template_section = models.ForeignKey(
        TemplateSection,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='plan_sections',
        verbose_name=_('secção do modelo'),
    )

    class Meta:
        verbose_name = _('Secção do Plano')
        verbose_name_plural = _('Secções do Plano')
        ordering = ['plan', 'order', 'id']

    def __str__(self) -> str:
        return f"{self.plan.period_label} · {self.title}"


class PlanLogEntry(models.Model):
    class Action(models.TextChoices):
        GENERATED = 'generated_from_template', _('Gerado a partir do modelo')
        UPDATED = 'updated', _('Atualizado')
        STATUS_CHANGE = 'status_change', _('Mudança de estado')
        COMMENT = 'comment', _('Comentário')

    plan = models.ForeignKey(
        IndividualPlan,
        on_delete=models.CASCADE,
        related_name='log_entries',
        verbose_name=_('plano'),
    )
    action = models.CharField(_('ação'), max_length=50, choices=Action.choices)
    message = models.TextField(_('mensagem'), blank=True)
    payload = models.JSONField(_('detalhes'), blank=True, null=True)
    actor = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='pit_log_entries',
        verbose_name=_('autor'),
    )
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        verbose_name = _('Log do Plano')
        verbose_name_plural = _('Logs do Plano')
        ordering = ['-created_at']

    def __str__(self) -> str:
        return f"{self.plan.period_label} · {self.get_action_display()} · {self.created_at:%Y-%m-%d %H:%M}"


# Create your models here.
