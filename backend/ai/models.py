from __future__ import annotations

import uuid
from decimal import Decimal

from django.conf import settings
from django.core.validators import MinValueValidator
from django.db import models
from django.utils import timezone
from django.utils.translation import gettext_lazy as _


class AIInteractionSession(models.Model):
    class Persona(models.TextChoices):
        STUDENT = "student", _("Aluno")
        TEACHER = "teacher", _("Professor")
        GUARDIAN = "guardian", _("Encarregado")
        ADMIN = "admin", _("Administrador")
        STAFF = "staff", _("Equipa")

    session_id = models.UUIDField(default=uuid.uuid4, editable=False, unique=True)
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="ai_sessions",
    )
    persona = models.CharField(max_length=20, choices=Persona.choices)
    origin_app = models.CharField(
        max_length=50,
        help_text=_('Identificador lógico da área onde a sessão começou (ex: "blog", "pit", "checklists").'),
    )
    class_context = models.ForeignKey(
        "classes.Class",
        on_delete=models.CASCADE,
        related_name="ai_sessions",
        null=True,
        blank=True,
    )
    context_descriptor = models.CharField(
        max_length=120,
        blank=True,
        help_text=_('Descrição curta do contexto ativo (ex: "PIT 2.º período", "Projeto Energia").'),
    )
    context_payload = models.JSONField(
        default=dict,
        blank=True,
        help_text=_('Dados complementares serializados para reconstruir rapidamente o contexto pedagógico.'),
    )
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    last_interaction_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ("-last_interaction_at",)
        verbose_name = _("Sessão IA")
        verbose_name_plural = _("Sessões IA")

    def __str__(self) -> str:  # pragma: no cover - representação simples
        label = self.context_descriptor or self.origin_app
        return f"{self.user} · {label}"


class AIRequest(models.Model):
    class Status(models.TextChoices):
        PENDING = "pending", _("Pendente")
        COMPLETED = "completed", _("Concluído")
        SKIPPED = "skipped", _("Ignorado")
        ERRORED = "errored", _("Erro")

    session = models.ForeignKey(
        AIInteractionSession,
        on_delete=models.CASCADE,
        related_name="requests",
    )
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="ai_requests",
    )
    persona = models.CharField(max_length=20, choices=AIInteractionSession.Persona.choices)
    origin_app = models.CharField(max_length=50)
    raw_query = models.TextField(help_text=_('Texto original submetido pelo utilizador.'))
    optimized_prompt = models.TextField(blank=True)
    optimizer_trace = models.JSONField(default=dict, blank=True)
    intent_label = models.CharField(max_length=120, blank=True)
    target_model = models.CharField(max_length=40, blank=True)
    resolved_model = models.CharField(max_length=40, blank=True)
    meta_context = models.JSONField(default=dict, blank=True)
    status = models.CharField(max_length=20, choices=Status.choices, default=Status.PENDING)
    input_tokens = models.PositiveIntegerField(default=0)
    output_tokens = models.PositiveIntegerField(default=0)
    cost_estimate = models.DecimalField(
        max_digits=12,
        decimal_places=5,
        default=Decimal("0.00000"),
        validators=[MinValueValidator(Decimal("0.00000"))],
    )
    latency_ms = models.PositiveIntegerField(default=0)
    created_at = models.DateTimeField(auto_now_add=True)
    completed_at = models.DateTimeField(null=True, blank=True)

    class Meta:
        ordering = ("-created_at",)
        verbose_name = _("Pedido IA")
        verbose_name_plural = _("Pedidos IA")

    def mark_completed(
        self,
        model_name: str,
        tokens_in: int,
        tokens_out: int,
        cost: Decimal,
        latency_ms: int,
    ) -> None:
        self.resolved_model = model_name
        self.input_tokens = tokens_in
        self.output_tokens = tokens_out
        self.cost_estimate = cost
        self.latency_ms = latency_ms
        self.status = AIRequest.Status.COMPLETED
        self.completed_at = timezone.now()
        self.save(
            update_fields=[
                "resolved_model",
                "input_tokens",
                "output_tokens",
                "cost_estimate",
                "latency_ms",
                "status",
                "completed_at",
            ]
        )


class AIResponseLog(models.Model):
    request = models.OneToOneField(
        AIRequest,
        on_delete=models.CASCADE,
        related_name="response_log",
    )
    response_text = models.TextField()
    model_metadata = models.JSONField(default=dict, blank=True)
    guardrail_decision = models.JSONField(default=dict, blank=True)
    used_cache = models.BooleanField(default=False)
    user_feedback = models.CharField(
        max_length=20,
        blank=True,
        help_text=_('Resposta útil? valores possíveis: "helpful", "neutral", "not_helpful".'),
    )
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ("-created_at",)
        verbose_name = _("Resposta IA")
        verbose_name_plural = _("Respostas IA")

    def __str__(self) -> str:  # pragma: no cover
        preview = (self.response_text[:60] + "…") if len(self.response_text) > 60 else self.response_text
        return f"Resposta {self.request_id}: {preview}"


class LearnerContextSnapshot(models.Model):
    student = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="learner_context_snapshots",
    )
    class_context = models.ForeignKey(
        "classes.Class",
        on_delete=models.CASCADE,
        related_name="learner_context_snapshots",
        null=True,
        blank=True,
    )
    summary = models.TextField()
    strengths = models.JSONField(default=list, blank=True)
    needs = models.JSONField(default=list, blank=True)
    mem_competencies = models.JSONField(
        default=dict,
        blank=True,
        help_text=_('Pontuações ou comentários por competência MEM (ex: autonomia, cooperação).'),
    )
    last_pit_id = models.PositiveIntegerField(null=True, blank=True)
    last_checklist_update = models.DateTimeField(null=True, blank=True)
    source = models.CharField(max_length=50, default="system")
    generated_at = models.DateTimeField(auto_now_add=True)
    refreshed_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ("-refreshed_at",)
        unique_together = ("student", "class_context", "source")
        verbose_name = _("Snapshot de Aprendizagem")
        verbose_name_plural = _("Snapshots de Aprendizagem")

    def __str__(self) -> str:  # pragma: no cover
        return f"{self.student} · {self.class_context or 'global'}"


class GroupLearningProfile(models.Model):
    class_context = models.ForeignKey(
        "classes.Class",
        on_delete=models.CASCADE,
        related_name="group_learning_profiles",
    )
    label = models.CharField(max_length=120)
    summary = models.TextField()
    focus_competencies = models.JSONField(default=list, blank=True)
    metadata = models.JSONField(default=dict, blank=True)
    last_synced_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ("label",)
        verbose_name = _("Perfil de Grupo")
        verbose_name_plural = _("Perfis de Grupo")

    def __str__(self) -> str:  # pragma: no cover
        return f"{self.class_context}: {self.label}"


class TeacherFocusArea(models.Model):
    PRIORITY_LOW = "low"
    PRIORITY_MEDIUM = "medium"
    PRIORITY_HIGH = "high"
    PRIORITY_CHOICES = (
        (PRIORITY_LOW, _("Baixa")),
        (PRIORITY_MEDIUM, _("Média")),
        (PRIORITY_HIGH, _("Alta")),
    )

    teacher = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="focus_areas",
        limit_choices_to={"role": "professor"},
    )
    class_context = models.ForeignKey(
        "classes.Class",
        on_delete=models.CASCADE,
        related_name="focus_areas",
        null=True,
        blank=True,
    )
    focus_text = models.TextField()
    priority = models.CharField(max_length=10, choices=PRIORITY_CHOICES, default=PRIORITY_MEDIUM)
    active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    review_after = models.DateTimeField(null=True, blank=True)

    class Meta:
        ordering = ("-created_at",)
        verbose_name = _("Foco Pedagógico")
        verbose_name_plural = _("Focos Pedagógicos")

    def __str__(self) -> str:  # pragma: no cover
        return f"{self.teacher} · {self.get_priority_display()}"


class AIUsageQuota(models.Model):
    SCOPE_USER = "user"
    SCOPE_CLASS = "class"
    SCOPE_CHOICES = (
        (SCOPE_USER, _("Utilizador")),
        (SCOPE_CLASS, _("Turma")),
    )

    scope = models.CharField(max_length=10, choices=SCOPE_CHOICES)
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        null=True,
        blank=True,
        related_name="ai_usage_quotas",
    )
    class_context = models.ForeignKey(
        "classes.Class",
        on_delete=models.CASCADE,
        null=True,
        blank=True,
        related_name="ai_usage_quotas",
    )
    period_start = models.DateField()
    period_end = models.DateField()
    max_requests = models.PositiveIntegerField(default=0)
    max_cost = models.DecimalField(
        max_digits=12,
        decimal_places=5,
        default=Decimal("0.00000"),
        validators=[MinValueValidator(Decimal("0.00000"))],
    )
    requests_made = models.PositiveIntegerField(default=0)
    cost_accumulated = models.DecimalField(
        max_digits=12,
        decimal_places=5,
        default=Decimal("0.00000"),
        validators=[MinValueValidator(Decimal("0.00000"))],
    )
    last_reset_at = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = _("Quota IA")
        verbose_name_plural = _("Quotas IA")
        constraints = [
            models.UniqueConstraint(
                fields=("scope", "user", "class_context", "period_start", "period_end"),
                name="unique_ai_quota_per_scope_period",
            )
        ]

    def register_usage(self, cost: Decimal) -> None:
        self.requests_made += 1
        self.cost_accumulated += cost
        self.save(update_fields=["requests_made", "cost_accumulated"])

    def reset(self) -> None:
        self.requests_made = 0
        self.cost_accumulated = Decimal("0.00000")
        self.last_reset_at = timezone.now()
        self.save(update_fields=["requests_made", "cost_accumulated", "last_reset_at"])


__all__ = [
    "AIInteractionSession",
    "AIRequest",
    "AIResponseLog",
    "LearnerContextSnapshot",
    "GroupLearningProfile",
    "TeacherFocusArea",
    "AIUsageQuota",
]
