from django.db import models
from users.models import User
from classes.models import Class

# Create your models here.

class ChecklistTemplate(models.Model):
    nome = models.CharField(max_length=100)
    ano = models.CharField(max_length=20)  # Ex: "5º ano"
    disciplina = models.CharField(max_length=100)  # Ex: "Português"
    descricao = models.TextField(blank=True)
    criado_em = models.DateTimeField(auto_now_add=True)
    atualizado_em = models.DateTimeField(auto_now=True)

class ChecklistItem(models.Model):
    template = models.ForeignKey(ChecklistTemplate, on_delete=models.CASCADE, related_name='items')
    descricao = models.CharField(max_length=255)
    criterios = models.TextField(blank=True)  # Critérios/descritores (opcional)
    ordem = models.IntegerField()
    contratualizado_em_conselho = models.BooleanField(default=False)

class ChecklistStatus(models.Model):
    template = models.ForeignKey(ChecklistTemplate, on_delete=models.CASCADE, related_name='statuses')
    aluno = models.ForeignKey(User, on_delete=models.CASCADE, related_name='checklist_statuses')
    classe = models.ForeignKey(Class, on_delete=models.CASCADE, related_name='checklist_statuses')
    percent_complete = models.FloatField(default=0)
    atualizado_em = models.DateTimeField(auto_now=True)

class ChecklistMark(models.Model):
    STATUS_CHOICES = [
        ('nao_iniciado', 'Não iniciado'),
        ('em_progresso', 'Em progresso'),
        ('concluido', 'Concluído'),
    ]
    status = models.ForeignKey(ChecklistStatus, on_delete=models.CASCADE, related_name='marks')
    item = models.ForeignKey(ChecklistItem, on_delete=models.CASCADE, related_name='marks')
    estado = models.CharField(max_length=20, choices=STATUS_CHOICES, default='nao_iniciado')
    comentario = models.TextField(blank=True)
    criado_em = models.DateTimeField(auto_now_add=True)
    marcado_por = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, related_name='marks_made')
    validacao_professor = models.BooleanField(default=False)
