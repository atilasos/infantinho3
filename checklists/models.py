from django.db import models
from users.models import User

# Create your models here.

class ChecklistTemplate(models.Model):
    nome = models.CharField(max_length=100)
    ano = models.IntegerField()

class ChecklistItem(models.Model):
    template = models.ForeignKey(ChecklistTemplate, on_delete=models.CASCADE, related_name='items')
    descricao = models.CharField(max_length=255)
    ordem = models.IntegerField()

class ChecklistStatus(models.Model):
    template = models.ForeignKey(ChecklistTemplate, on_delete=models.CASCADE, related_name='statuses')
    aluno = models.ForeignKey(User, on_delete=models.CASCADE, related_name='checklist_statuses')
    percent_complete = models.FloatField(default=0)
    updated_at = models.DateTimeField(auto_now=True)

class ChecklistMark(models.Model):
    status = models.ForeignKey(ChecklistStatus, on_delete=models.CASCADE, related_name='marks')
    item = models.ForeignKey(ChecklistItem, on_delete=models.CASCADE, related_name='marks')
    concluido = models.BooleanField(default=False)
    data = models.DateTimeField(auto_now=True)
    marcado_por = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, related_name='marks_made')
