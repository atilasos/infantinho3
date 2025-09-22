from django.db import models
from django.conf import settings
from django.utils.translation import gettext_lazy as _
from classes.models import Class


class Project(models.Model):
    class ProjectState(models.TextChoices):
        ACTIVE = 'active', _('Ativo')
        COMPLETED = 'completed', _('Concluído')
        CANCELED = 'canceled', _('Cancelado')

    student_class = models.ForeignKey(
        Class,
        on_delete=models.CASCADE,
        related_name='projects',
        verbose_name=_('turma')
    )
    title = models.CharField(_('título'), max_length=200)
    description = models.TextField(_('descrição/tema'), blank=True)
    members = models.ManyToManyField(
        settings.AUTH_USER_MODEL,
        related_name='projects',
        verbose_name=_('membros'),
        blank=True
    )
    state = models.CharField(_('estado'), max_length=20, choices=ProjectState.choices, default=ProjectState.ACTIVE)
    start_date = models.DateField(_('data início'), null=True, blank=True)
    end_date = models.DateField(_('data fim prevista'), null=True, blank=True)
    product_description = models.CharField(_('produto final previsto'), max_length=255, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = _('Projeto')
        verbose_name_plural = _('Projetos')
        ordering = ['-created_at']

    def __str__(self) -> str:
        return f"{self.title} — {self.student_class}"


class ProjectTask(models.Model):
    class TaskState(models.TextChoices):
        TODO = 'todo', _('Por fazer')
        IN_PROGRESS = 'in_progress', _('Em progresso')
        DONE = 'done', _('Feito')

    project = models.ForeignKey(Project, on_delete=models.CASCADE, related_name='tasks', verbose_name=_('projeto'))
    description = models.CharField(_('descrição'), max_length=255)
    responsible = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='project_tasks_responsible',
        verbose_name=_('responsável')
    )
    due_date = models.DateField(_('data limite'), null=True, blank=True)
    state = models.CharField(_('estado'), max_length=20, choices=TaskState.choices, default=TaskState.TODO)
    order = models.PositiveIntegerField(_('ordem'), default=0)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = _('Tarefa de Projeto')
        verbose_name_plural = _('Tarefas de Projeto')
        ordering = ['order', 'id']

    def __str__(self) -> str:
        return f"[{self.project.title}] {self.description}"


# Create your models here.
