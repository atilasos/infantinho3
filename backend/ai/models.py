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


# ============================================================================
# STUDENT PROFILE - ZDP Tracking
# ============================================================================

class StudentProfile(models.Model):
    """
    Perfil do aluno para personalização da IA baseada em ZDP.
    Tracks learning progress, preferences, and collaboration patterns.
    """
    
    ZDP_AUTONOMOUS = 'autonomous'
    ZDP_MINIMAL = 'minimal_support'
    ZDP_INTERMEDIATE = 'intermediate'
    ZDP_SUBSTANTIAL = 'substantial_support'
    ZDP_INTENSIVE = 'intensive'
    
    ZDP_LEVEL_CHOICES = [
        (ZDP_AUTONOMOUS, _('Autónomo')),
        (ZDP_MINIMAL, _('Apoio mínimo')),
        (ZDP_INTERMEDIATE, _('Apoio intermédio')),
        (ZDP_SUBSTANTIAL, _('Apoio substancial')),
        (ZDP_INTENSIVE, _('Apoio intensivo')),
    ]
    
    user = models.OneToOneField(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='ai_student_profile',
    )
    
    # ZDP tracking
    zdp_level = models.CharField(
        max_length=20,
        choices=ZDP_LEVEL_CHOICES,
        default=ZDP_INTERMEDIATE,
        help_text=_('Nível atual de apoio na ZDP'),
    )
    
    # Learning preferences (JSON)
    learning_preferences = models.JSONField(
        default=dict,
        blank=True,
        help_text=_('Preferências de aprendizagem: visual, auditiva, cinestésica, etc.'),
    )
    
    # Collaboration patterns
    preferred_collaborators = models.ManyToManyField(
        settings.AUTH_USER_MODEL,
        blank=True,
        related_name='collaboration_partners',
        help_text=_('Colegas com quem trabalha bem'),
    )
    collaboration_success_rate = models.FloatField(
        default=0.5,
        help_text=_('Taxa de sucesso em trabalhos colaborativos (0-1)'),
    )
    
    # Strengths and growth areas
    strengths = models.JSONField(
        default=list,
        blank=True,
        help_text=_('Lista de áreas fortes: ["matemática", "leitura", ...]'),
    )
    growth_areas = models.JSONField(
        default=list,
        blank=True,
        help_text=_('Lista de áreas a desenvolver'),
    )
    
    # Interaction history
    total_interactions = models.PositiveIntegerField(default=0)
    successful_scaffolds = models.PositiveIntegerField(
        default=0,
        help_text=_('Vezes em que o scaffolding nível 1-2 foi suficiente'),
    )
    needed_full_support = models.PositiveIntegerField(
        default=0,
        help_text=_('Vezes em que precisou de nível 3 (resposta completa)'),
    )
    
    # Timestamps
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        verbose_name = _('Perfil de Aluno (IA)')
        verbose_name_plural = _('Perfis de Alunos (IA)')
    
    def __str__(self):
        return f"{self.user} - ZDP: {self.get_zdp_level_display()}"
    
    def record_interaction(self, scaffolding_level: int, successful: bool = True):
        """
        Regista uma interação e atualiza o perfil ZDP.
        
        Args:
            scaffolding_level: 1, 2, or 3 (nível de apoio dado)
            successful: Se o aluno conseguiu avançar após o apoio
        """
        self.total_interactions += 1
        
        if scaffolding_level in (1, 2) and successful:
            self.successful_scaffolds += 1
        elif scaffolding_level == 3:
            self.needed_full_support += 1
        
        # Atualiza ZDP level baseado no histórico recente
        self._update_zdp_level()
        self.save()
    
    def _update_zdp_level(self):
        """Calcula o nível ZDP baseado no histórico de interações."""
        if self.total_interactions < 5:
            return  # Não há dados suficientes
        
        # Calcula taxa de scaffolding bem-sucedido
        if self.successful_scaffolds + self.needed_full_support > 0:
            success_rate = self.successful_scaffolds / (self.successful_scaffolds + self.needed_full_support)
        else:
            success_rate = 0.5
        
        # Mapeia para nível ZDP
        if success_rate >= 0.9:
            self.zdp_level = self.ZDP_AUTONOMOUS
        elif success_rate >= 0.75:
            self.zdp_level = self.ZDP_MINIMAL
        elif success_rate >= 0.5:
            self.zdp_level = self.ZDP_INTERMEDIATE
        elif success_rate >= 0.25:
            self.zdp_level = self.ZDP_SUBSTANTIAL
        else:
            self.zdp_level = self.ZDP_INTENSIVE
    
    def get_profile_dict(self) -> dict:
        """Retorna dict para usar em prompts personalizados."""
        return {
            'zdp_level': self.zdp_level,
            'learning_preferences': self.learning_preferences,
            'strengths': self.strengths,
            'growth_areas': self.growth_areas,
            'collaboration_success_rate': self.collaboration_success_rate,
        }


__all__ = [
    "AIInteractionSession",
    "AIRequest",
    "AIResponseLog",
    "LearnerContextSnapshot",
    "GroupLearningProfile",
    "TeacherFocusArea",
    "AIUsageQuota",
    "StudentProfile",
]
