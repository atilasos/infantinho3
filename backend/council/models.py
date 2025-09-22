from django.db import models
from django.conf import settings
from django.utils.translation import gettext_lazy as _
from classes.models import Class


class CouncilDecision(models.Model):
    class Category(models.TextChoices):
        RULE = 'rule', _('Regra')
        LEARNING_GOAL = 'learning_goal', _('Objetivo de Aprendizagem')
        ACTIVITY = 'activity', _('Atividade/Evento')
        OTHER = 'other', _('Outro')

    class Status(models.TextChoices):
        PENDING = 'pending', _('Pendente')
        IN_PROGRESS = 'in_progress', _('Em curso')
        DONE = 'done', _('Cumprido')

    student_class = models.ForeignKey(Class, on_delete=models.CASCADE, related_name='council_decisions', verbose_name=_('turma'))
    date = models.DateField(_('data'))
    description = models.TextField(_('descrição'))
    category = models.CharField(_('categoria'), max_length=20, choices=Category.choices)
    status = models.CharField(_('estado'), max_length=20, choices=Status.choices, default=Status.PENDING)
    responsible = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='council_responsibilities',
        verbose_name=_('responsável')
    )
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = _('Decisão de Conselho')
        verbose_name_plural = _('Decisões de Conselho')
        ordering = ['-date', '-created_at']

    def __str__(self) -> str:
        return f"{self.student_class} — {self.date} — {self.get_category_display()}"


class StudentProposal(models.Model):
    class ProposalStatus(models.TextChoices):
        PENDING = 'pending', _('Pendente')
        TAKEN = 'taken_to_council', _('Levado a Conselho')
        APPROVED = 'approved', _('Aprovado')
        REJECTED = 'rejected', _('Rejeitado')

    student_class = models.ForeignKey(Class, on_delete=models.CASCADE, related_name='student_proposals', verbose_name=_('turma'))
    author = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='student_proposals', verbose_name=_('autor'))
    text = models.TextField(_('texto'))
    date_submitted = models.DateField(_('data de submissão'), auto_now_add=True)
    status = models.CharField(_('estado'), max_length=20, choices=ProposalStatus.choices, default=ProposalStatus.PENDING)

    class Meta:
        verbose_name = _('Proposta de Aluno')
        verbose_name_plural = _('Propostas de Alunos')
        ordering = ['-date_submitted']

    def __str__(self) -> str:
        return f"{self.student_class} — {self.author}: {self.text[:30]}"


# Create your models here.
