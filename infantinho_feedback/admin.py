from django.contrib import admin
from django.utils.translation import gettext_lazy as _

from .models import FeedbackItem

@admin.register(FeedbackItem)
class FeedbackItemAdmin(admin.ModelAdmin):
    list_display = (
        'category',
        'author_display_name',
        'content_summary',
        'status',
        'created_at',
        'turma_display_name',
        'page_url'
    )
    list_filter = ('status', 'category', 'turma', 'created_at')
    search_fields = ('content', 'author__username', 'author__first_name', 'author__last_name', 'page_url')
    list_editable = ('status',)
    readonly_fields = ('created_at', 'updated_at', 'author') # Campos que não devem ser editados diretamente no form

    fieldsets = (
        (None, {
            'fields': ('category', 'content', 'page_url', 'turma')
        }),
        (_('Contexto do Autor (Não editável aqui)'), {
            'fields': ('author', 'created_at', 'updated_at'),
            'classes': ('collapse',)
        }),
        (_('Gestão Interna'), {
            'fields': ('status',)
        }),
    )

    def content_summary(self, obj):
        return (obj.content[:75] + '...') if len(obj.content) > 75 else obj.content
    content_summary.short_description = _('Conteúdo')

    def author_display_name(self, obj):
        if obj.author:
            return obj.author.get_full_name() or obj.author.username
        return _('Anónimo')
    author_display_name.short_description = _('Autor')
    author_display_name.admin_order_field = 'author' # Permite ordenar por esta coluna

    def turma_display_name(self, obj):
        if obj.turma:
            return obj.turma.name
        return '-'
    turma_display_name.short_description = _('Turma')
    turma_display_name.admin_order_field = 'turma' # Permite ordenar por esta coluna

    def get_queryset(self, request):
        # Ordenar por "Novo" primeiro, depois os outros status, e dentro disso por mais recente
        qs = super().get_queryset(request)
        qs = qs.extra(
            select={'is_novo': "status = 'NOVO'"}
        ).order_by('-is_novo', '-created_at')
        return qs
