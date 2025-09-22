from django.db import models
from django.utils import timezone
from django.utils.translation import gettext_lazy as _

# Import related models from other apps
from users.models import User
from classes.models import Class # Opcional, se quisermos ligar a uma turma

class FeedbackItem(models.Model):
    CATEGORY_CHOICES = [
        ('GOSTEI', _('Gostei')),
        ('ERRO', _('Encontrei um erro')),
        ('SUGIRO', _('Sugiro')),
    ]

    STATUS_CHOICES = [
        ('NOVO', _('Novo')),
        ('EM_ANALISE', _('Em Análise')),
        ('CONCLUIDO', _('Concluído')),
        ('REJEITADO', _('Rejeitado')),
    ]

    author = models.ForeignKey(
        User,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='infantinho_feedback_items',
        verbose_name=_("autor")
    )
    category = models.CharField(
        _("categoria"),
        max_length=10,
        choices=CATEGORY_CHOICES,
        default='SUGIRO'
    )
    content = models.TextField(_("conteúdo"))
    page_url = models.CharField(
        _("URL da página (opcional)"),
        max_length=255,
        blank=True,
        null=True,
        help_text=_("Se aplicável, a página onde o erro ocorreu ou a que a sugestão se refere.")
    )
    turma = models.ForeignKey(
        Class,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='infantinho_feedback_items_turma',
        verbose_name=_("turma (opcional)")
    )
    status = models.CharField(
        _("estado"),
        max_length=20,
        choices=STATUS_CHOICES,
        default='NOVO'
    )
    created_at = models.DateTimeField(_("data de criação"), auto_now_add=True)
    updated_at = models.DateTimeField(_("data de atualização"), auto_now=True)

    class Meta:
        ordering = ['-created_at']
        verbose_name = _("Item de Feedback (Infantinho)")
        verbose_name_plural = _("Itens de Feedback (Infantinho)")

    def __str__(self):
        author_display = self.author.get_full_name() or self.author.username if self.author else _('Anónimo')
        return f"{self.get_category_display()} - {author_display} - {self.content[:50]}"
