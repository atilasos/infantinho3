from django.db import models
from users.models import User
from classes.models import Class
from django.utils.translation import gettext_lazy as _
from ckeditor.fields import RichTextField
from django.core.exceptions import ValidationError

class Post(models.Model):
    turma = models.ForeignKey(Class, on_delete=models.CASCADE, related_name='posts')
    autor = models.ForeignKey(User, on_delete=models.CASCADE, related_name='posts')
    titulo = models.CharField(max_length=200, blank=True)
    conteudo = RichTextField()
    publicado_em = models.DateTimeField(auto_now_add=True)
    CATEGORIA_DIARIO_CHOICES = [
        ('GOSTEI', _('Gostei')),
        ('NAO_GOSTEI', _('Não Gostei')),
        ('QUEREMOS', _('Queremos')),
        ('FIZEMOS', _('Fizemos')),
    ]
    CATEGORIA_CHOICES = [
        ('DIARIO', _('Diário de Turma')),
        ('AVISO', _('Aviso')),
        ('PROJETO', _('Projeto')),
        ('OUTRO', _('Outro')),
    ]
    categoria = models.CharField(max_length=20, choices=CATEGORIA_CHOICES, default='DIARIO')
    subcategoria_diario = models.CharField(max_length=20, choices=CATEGORIA_DIARIO_CHOICES, blank=True)
    VISIBILIDADE_CHOICES = [
        ('INTERNA', _('Apenas membros da turma')),
        ('PUBLICA', _('Público (futuro)')),
    ]
    visibilidade = models.CharField(max_length=10, choices=VISIBILIDADE_CHOICES, default='INTERNA')
    removido = models.BooleanField(default=False)
    removido_por = models.ForeignKey(User, null=True, blank=True, on_delete=models.SET_NULL, related_name='posts_removidos')
    removido_em = models.DateTimeField(null=True, blank=True)
    motivo_remocao = models.CharField(max_length=255, blank=True)

    def __str__(self):
        return self.titulo or f"Post #{self.pk}"

    def get_category_display(self):
        return dict(self.CATEGORIA_CHOICES).get(self.categoria, self.categoria)

    def is_editable_by(self, user):
        if not user.is_authenticated:
            return False
        if hasattr(user, 'role') and user.role == 'admin':
            return True
        if self.autor == user:
            return True
        # Professores da turma podem editar/remover qualquer post da sua turma, exceto DIARIO
        if hasattr(user, 'role') and user.role == 'professor':
            if self.categoria != 'DIARIO' and self.turma in user.classes_taught.all():
                return True
        return False

    def is_visible_to(self, user):
        if not user.is_authenticated:
            return False
        if hasattr(user, 'role') and user.role == 'admin':
            return True
        # Diário de Turma: só professores e alunos da turma
        if self.categoria == 'DIARIO':
            return (self.turma in user.classes_attended.all()) or (self.turma in user.classes_taught.all())
        # Outros posts: se público, qualquer um pode ver
        if self.visibilidade == 'PUBLICA':
            return True
        # Se interna, só membros da turma e admin
        return (self.turma in user.classes_attended.all()) or (self.turma in user.classes_taught.all())

    def clean(self):
        if self.categoria == 'DIARIO' and not self.subcategoria_diario:
            raise ValidationError({'subcategoria_diario': 'Subcategoria é obrigatória para Diário de Turma.'})
        if self.categoria != 'DIARIO' and self.subcategoria_diario:
            self.subcategoria_diario = ''

    def remover(self, user, motivo=None):
        from django.utils import timezone
        if self.removido:
            return  # Não sobrescrever quem removeu
        self.removido = True
        self.removido_por = user
        self.removido_em = timezone.now()
        if motivo:
            self.motivo_remocao = motivo
        self.save()
        ModerationLog.objects.create(
            acao='REMOVER_POST',
            user=user,
            post=self,
            motivo=motivo,
            conteudo_snapshot=self.conteudo,
        )

class Comment(models.Model):
    post = models.ForeignKey(Post, on_delete=models.CASCADE, related_name='comments')
    autor = models.ForeignKey(User, on_delete=models.CASCADE, related_name='comments')
    conteudo = models.TextField()
    publicado_em = models.DateTimeField(auto_now_add=True)
    removido = models.BooleanField(default=False)
    removido_por = models.ForeignKey(User, null=True, blank=True, on_delete=models.SET_NULL, related_name='comments_removidos')
    removido_em = models.DateTimeField(null=True, blank=True)
    motivo_remocao = models.CharField(max_length=255, blank=True)

    def __str__(self):
        if self.removido:
            return str(_("Comentário removido por moderação"))
        return str(_(f"Comentário de {self.autor} em {self.post}"))

    def remover(self, user, motivo=None):
        from django.utils import timezone
        if self.removido:
            return  # Não sobrescrever quem removeu
        self.removido = True
        self.removido_por = user
        self.removido_em = timezone.now()
        if motivo:
            self.motivo_remocao = motivo
        self.save()
        ModerationLog.objects.create(
            acao='REMOVER_COMMENT',
            user=user,
            comment=self,
            motivo=motivo,
            conteudo_snapshot=self.conteudo,
        )

    # TODO: Adicionar campos de moderação/logs se necessário no futuro

class ModerationLog(models.Model):
    ACAO_CHOICES = [
        ('REMOVER_POST', 'Remover Post'),
        ('EDITAR_POST', 'Editar Post'),
        ('REMOVER_COMMENT', 'Remover Comentário'),
        ('EDITAR_COMMENT', 'Editar Comentário'),
        ('RESTAURAR_POST', 'Restaurar Post'),
    ]
    acao = models.CharField(max_length=20, choices=ACAO_CHOICES)
    user = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True)
    post = models.ForeignKey(Post, on_delete=models.SET_NULL, null=True, blank=True)
    comment = models.ForeignKey('Comment', on_delete=models.SET_NULL, null=True, blank=True)
    data = models.DateTimeField(auto_now_add=True)
    motivo = models.CharField(max_length=255, blank=True)
    conteudo_snapshot = models.TextField(blank=True)

    def __str__(self):
        return f"{self.get_acao_display()} por {self.user} em {self.data:%d/%m/%Y %H:%M}"
